"""Train the Neuronte net.

usage: python3 train/train.py OUT.json [--set ascii|full|...] [--width W]
                              [--steps N] [--device cuda] [--seed S]

Needs torch and numpy. Writes the weights as JSON and prints one JSON
line of scores. The target at a point is the field glyphs.py makes: the
signed distance to the ink edge over tau, clamped to -1..1, held on a grid
of nodes 1/256 cell width apart and read between them bilinearly.

The pen is the set's own (glyphs.PENS) unless --pen gives one. The
scores at cell widths 10 and 11 also count pixels, for a face shown as
binary letters at those sizes: how many characters are exactly their
drawing's pixels, and which are not, over all pixels and over the firm
ones, those whose drawing is not within 0.1 of half covered.
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
import glyphs  # noqa: E402
import strokes  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("out")
p.add_argument("--set", default="ascii", choices=list(glyphs.SETS))
p.add_argument("--width", type=int, default=128, help="hidden layer width")
p.add_argument("--steps", type=int, default=20000)
p.add_argument("--device", default="cuda")
p.add_argument("--seed", type=int, default=0)
p.add_argument("--pen", type=float, default=None, help="pen radius in cell widths; default: the set's own")
p.add_argument("--grid", type=int, default=256, help="target grid nodes per cell width")
p.add_argument("--unlabelled", type=float, default=1.0, help="weight of the term for scalars with no glyph")
a = p.parse_args()
if a.pen is None:
    a.pen = glyphs.PENS.get(a.set, glyphs.PEN)
torch.manual_seed(a.seed)
torch.set_default_device(a.device)


def sha(rel):
    with open(os.path.join(strokes.ROOT, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# Taken now, so the record names the files the targets were made from.
SOURCES = {f: sha(f) for f in glyphs.sources(a.set)}
TAU, OCT, W, N = 0.15, 6, a.width, a.grid
SET = glyphs.charset(a.set)
CHARS = [c for c, _, _ in SET]
TIERS = [t for _, t, _ in SET]
G = len(CHARS)
MASKS = strokes.masks()
FIELD = torch.tensor(np.stack([glyphs.field(s, N, a.pen, TAU) for _, _, s in SET]).astype(np.float16)).reshape(-1)
NX, NY = N + 1, 2 * N + 1
LAB = torch.tensor([ord(c) for c in CHARS])
MB = torch.tensor([[(m >> i) & 1 for i in range(21)] for m in MASKS], dtype=torch.float32)
SPAN = torch.tensor([1.0, 2.0])


def target(gi, xy):
    """The target field for characters gi at points xy (B, M, 2), read
    bilinearly from the grid."""
    u, v = xy[..., 0] * N, xy[..., 1] * N
    i0, j0 = u.floor().clamp(0, N - 1), v.floor().clamp(0, 2 * N - 1)
    fu, fv = u - i0, v - j0
    k = gi[:, None] * (NX * NY) + j0.long() * NX + i0.long()
    f00, f01, f10, f11 = (FIELD[k + d].float() for d in (0, 1, NX, NX + 1))
    return (f00 * (1 - fu) + f01 * fu) * (1 - fv) + (f10 * (1 - fu) + f11 * fu) * fv


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
CF = code(LAB)
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
        v = torch.where(torch.isin(v, LAB) | ((v >= 0xD800) & (v <= 0xDFFF)), v + 0x1000, v)
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


def label(i):
    return f"U+{ord(CHARS[i]):04X} {CHARS[i]}"


res = {"set": a.set, "chars": G, "width": W, "steps": a.steps, "seed": a.seed, "pen": a.pen,
       "unlabelled": a.unlabelled, "params": sum(q.numel() for q in net.parameters()),
       "final_loss": float(loss.detach())}
tier_idx = {t: torch.tensor([i for i, x in enumerate(TIERS) if x == t]) for t in dict.fromkeys(TIERS)}
PIXEL_SIZES = (10, 11)  # where a face is shown as binary letters
for wpx in (4, 5, 8, 10, 11, 16, 48):
    t = truth(wpx).reshape(G, -1)
    # Targets that differ by under half a pixel of ink at this size, such
    # as space and U+00A0, count as one when checking the nearest.
    twin = torch.cdist(t, t, p=1) < 0.5
    for ss in (1, 2):
        n = cover(CF, wpx, ss).reshape(G, -1)
        ti, ni = t > 0.5, n > 0.5
        u = (ti | ni).sum(1).float()
        iou = torch.where(u > 0, (ti & ni).sum(1).float() / u.clamp_min(1), torch.ones_like(u))
        nearest = torch.cdist(n, t, p=1).argmin(1)
        r = {"iou_mean": round(float(iou.mean()), 4), "iou_min": round(float(iou.min()), 4),
             "worst": [label(int(i)) for i in iou.argsort()[:3]],
             "nearest_ok": int(twin[gi, nearest].sum())}
        if len(tier_idx) > 1:
            r["tiers"] = {k: round(float(iou[ix].mean()), 4) for k, ix in tier_idx.items()}
        if wpx in PIXEL_SIZES:
            wrong = ti != ni
            firm = wrong & ((t - 0.5).abs() >= 0.1)
            r["exact"] = int((~wrong.any(1)).sum())
            r["differ"] = [label(int(i)) for i in wrong.any(1).nonzero().flatten()]
            r["wrong_pixels"] = int(wrong.sum())
            r["firm_exact"] = int((~firm.any(1)).sum())
            r["firm_differ"] = [label(int(i)) for i in firm.any(1).nonzero().flatten()]
            r["firm_wrong_pixels"] = int(firm.sum())
        res[f"w{wpx}_s{ss}"] = r


def ranges(scalars):
    out, s = [], sorted(scalars)
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[j] + 1:
            j += 1
        out.append(f"U+{s[i]:04X}" + (f"..U+{s[j]:04X}" if j > i else ""))
        i = j + 1
    return " ".join(out)


lin = [m for m in net if isinstance(m, torch.nn.Linear)]


def f32(t):
    return [float(x) for x in t.detach().cpu().numpy().astype(np.float32).ravel()]


doc = {
    "format": "neuronte-weights",
    "version": 1,
    "shape": {"position_octaves": OCT, "code_bits": 64, "hidden_width": W, "hidden_layers": 3,
              "tau": TAU, "parity_masks": [f"0x{m:06X}" for m in MASKS]},
    "training": {"set": a.set, "labelled": ranges(ord(c) for c in CHARS),
                 "sources_sha256": SOURCES,
                 "pen_radius": a.pen, "grid": N, "steps": a.steps, "seed": a.seed,
                 "unlabelled_weight": a.unlabelled},
    "layers": {name: {"rows": l.weight.shape[0], "cols": l.weight.shape[1],
                      "weight": f32(l.weight), "bias": f32(l.bias)}
               for name, l in zip(["l1", "l2", "l3", "out"], lin)},
}
with open(a.out, "w") as fh:
    json.dump(doc, fh)
print(json.dumps(res, ensure_ascii=False))
