"""Train the Neuronte net on the stroke lists.

usage: python3 train/train.py OUT.json [--steps N] [--device cuda] [--seed S]

Needs torch. Writes the weights as JSON and prints one JSON line of
scores. The target at a point is clamp((r - d) / tau, -1, 1), where d is
the exact distance to the nearest stroke centre line. No bitmap is made.
"""
import argparse
import hashlib
import json
import math
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strokes  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("out")
p.add_argument("--steps", type=int, default=20000)
p.add_argument("--device", default="cuda")
p.add_argument("--seed", type=int, default=0)
p.add_argument("--pen", type=float, default=0.075, help="pen radius in cell widths")
p.add_argument("--unlabelled", type=float, default=1.0, help="weight of the term for scalars with no stroke list")
a = p.parse_args()
torch.manual_seed(a.seed)
torch.set_default_device(a.device)

TAU, OCT, W, R = 0.15, 6, 128, a.pen
CHARS = [chr(c) for c in range(32, 127)]
G = len(CHARS)
MASKS = strokes.masks()
glyphs = strokes.parse()
S = max(len(glyphs[c]) for c in CHARS)
seg = np.full((G, S, 4), 50.0, np.float32)  # padding segments lie far outside the cell
for g, ch in enumerate(CHARS):
    for i, s in enumerate(glyphs[ch]):
        seg[g, i] = s
SEG = torch.tensor(seg)
MB = torch.tensor([[(m >> i) & 1 for i in range(21)] for m in MASKS], dtype=torch.float32)
SPAN = torch.tensor([1.0, 2.0])


def target(gi, xy):
    """Clamped signed field for characters gi at points xy (B, N, 2)."""
    s = SEG[gi]
    a0, ab = s[:, None, :, 0:2], s[:, None, :, 2:4] - s[:, None, :, 0:2]
    q = xy[:, :, None, :]
    t = ((q - a0) * ab).sum(-1) / (ab * ab).sum(-1).clamp_min(1e-12)
    d = (q - (a0 + t.clamp(0, 1)[..., None] * ab)).norm(dim=-1).min(-1).values
    return ((R - d) / TAU).clamp(-1, 1)


def code(v):
    b = ((v[:, None] >> torch.arange(21)) & 1).float()
    return 2 * torch.cat([b, torch.remainder(b @ MB.T, 2)], 1) - 1


def pos(xy):
    f = [xy[..., :1] * 2 - 1, xy[..., 1:] - 1]
    for k in range(OCT):
        w = 2 * math.pi * 2 ** k
        f += [torch.sin(w * xy), torch.cos(w * xy)]
    return torch.cat(f, -1)


net = torch.nn.Sequential(torch.nn.Linear(26 + 64, W), torch.nn.ReLU(),
                          torch.nn.Linear(W, W), torch.nn.ReLU(),
                          torch.nn.Linear(W, W), torch.nn.ReLU(),
                          torch.nn.Linear(W, 1))


def field(c, xy):
    return net(torch.cat([pos(xy), c[:, None, :].expand(-1, xy.shape[1], -1)], -1)).squeeze(-1)


gi = torch.arange(G)
CF = code(torch.arange(32, 32 + G))
opt = torch.optim.Adam(net.parameters(), lr=2e-3)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.steps)
for step in range(a.steps):
    cand = torch.rand(G, 1024, 2) * SPAN
    tc = target(gi, cand)
    near = tc.abs().topk(128, dim=1, largest=False).indices  # the candidates nearest an edge
    xy = torch.cat([cand[:, :128], torch.gather(cand, 1, near[..., None].expand(-1, -1, 2))], 1)
    y = torch.cat([tc[:, :128], torch.gather(tc, 1, near)], 1)
    loss = (field(CF, xy) - y).abs().mean()
    if a.unlabelled > 0:
        U = 64
        v = torch.randint(0, 0x110000, (U,))
        v = torch.where(((v >= 32) & (v < 32 + G)) | ((v >= 0xD800) & (v <= 0xDFFF)), v + 0x1000, v)
        pu = torch.rand(1, 256, 2) * SPAN
        su = torch.sigmoid(8 * field(code(v), pu.expand(U, -1, -1)))
        m = su.mean(1)
        dd = (su[:, None] - su[None]).abs().mean(-1)
        st = (target(gi, pu.expand(G, -1, -1)) > 0).float()
        dt = (su[:, None] - st[None]).abs().mean(-1)
        loss = loss + a.unlabelled * ((torch.relu(0.08 - m) + torch.relu(m - 0.25)).mean()
                                      + torch.relu(0.12 - dd)[~torch.eye(U, dtype=torch.bool)].mean()
                                      + torch.relu(0.12 - dt).mean())
    opt.zero_grad()
    loss.backward()
    opt.step()
    sched.step()


def grid(wpx, ss):
    xs = (torch.arange(wpx * ss) + 0.5) / (wpx * ss)
    ys = (torch.arange(2 * wpx * ss) + 0.5) / (2 * wpx * ss) * 2
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    return torch.stack([xx, yy], -1).reshape(1, -1, 2)


@torch.no_grad()
def cover(c, wpx, ss):
    xy = grid(wpx, ss)
    out = []
    for i in range(0, c.shape[0], 8):
        f = field(c[i:i + 8], xy.expand(c[i:i + 8].shape[0], -1, -1))
        cv = (0.5 + f * TAU * wpx * ss).clamp(0, 1)
        out.append(cv.reshape(-1, 2 * wpx, ss, wpx, ss).mean((2, 4)))
    return torch.cat(out)


@torch.no_grad()
def truth(wpx, ss=8):
    xy = grid(wpx, ss)
    rows = [(target(gi[i:i + 1], xy) > 0).float() for i in range(G)]
    return torch.cat(rows).reshape(G, 2 * wpx, ss, wpx, ss).mean((2, 4))


res = {"steps": a.steps, "seed": a.seed, "pen": R, "unlabelled": a.unlabelled,
       "params": sum(q.numel() for q in net.parameters()), "final_loss": float(loss.detach())}
for wpx in (8, 16, 48):
    t = truth(wpx).reshape(G, -1)
    for ss in (1, 2):
        n = cover(CF, wpx, ss).reshape(G, -1)
        ti, ni = t > 0.5, n > 0.5
        u = (ti | ni).sum(1).float()
        iou = torch.where(u > 0, (ti & ni).sum(1).float() / u.clamp_min(1), torch.ones_like(u))
        res[f"w{wpx}_s{ss}"] = {"iou_mean": round(float(iou.mean()), 4), "iou_min": round(float(iou.min()), 4),
                                "worst": CHARS[int(iou.argmin())],
                                "nearest_ok": int((torch.cdist(n, t, p=1).argmin(1) == gi).sum())}

with open(strokes.STROKES, "rb") as fh:
    strokes_sha = hashlib.sha256(fh.read()).hexdigest()
lin = [m for m in net if isinstance(m, torch.nn.Linear)]


def f32(t):
    return [float(x) for x in t.detach().cpu().numpy().astype(np.float32).ravel()]


doc = {
    "format": "neuronte-weights",
    "version": 1,
    "shape": {"position_octaves": OCT, "code_bits": 64, "hidden_width": W, "hidden_layers": 3,
              "tau": TAU, "parity_masks": [f"0x{m:06X}" for m in MASKS]},
    "training": {"labelled": "U+0020..U+007E", "strokes_sha256": strokes_sha, "pen_radius": R,
                 "steps": a.steps, "seed": a.seed, "unlabelled_weight": a.unlabelled},
    "layers": {name: {"rows": l.weight.shape[0], "cols": l.weight.shape[1],
                      "weight": f32(l.weight), "bias": f32(l.bias)}
               for name, l in zip(["l1", "l2", "l3", "out"], lin)},
}
with open(a.out, "w") as fh:
    json.dump(doc, fh)
print(json.dumps(res))
