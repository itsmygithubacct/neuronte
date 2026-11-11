"""Train a colour glyph net on the icons: the drawn ones and those made by rule.

usage: python3 train/colour.py OUT.json --form A|B [--layers K] [--width W]
                               [--steps N] [--device cuda] [--seed S]

Form A is one net with K distance outputs, one per layer. Form B has one
output and takes the layer number as an input, one-hot. At the same width
the two have the same parameter count to within one hidden width. Both
are trained on the same points with the same targets: for each icon, 128
points anywhere in the cell and 384 of 1024 candidates near an edge,
shared equally among the layers it uses. Layers an icon does not use are
trained to "outside everywhere".

Both carry the palette head: from the 64 code features to each layer's
palette entry, as 5 bits a layer. It runs once per glyph, so it is not
part of the per-pixel cost.

Writes the weights as JSON, for form A in the format train/pack.py packs
(neuronte-colour-weights, version 1), and prints one JSON line of scores:
- each used layer's IoU at 12, 16 and 32 px, as glyphs are scored, with
  2 x 2 samples below 24 px and 1 above, as the library draws;
- any unused layer that draws a pixel;
- the composited icon against the composited target, on the dark and the
  light theme: mean error and the share of pixels off by more than 32
  of 255;
- the palette head, which must return every written entry exactly.
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
p.add_argument("--form", required=True, choices=["A", "B"])
p.add_argument("--layers", type=int, default=6, help="K, the most layers a glyph can have")
p.add_argument("--width", type=int, default=128, help="hidden layer width")
p.add_argument("--head-width", type=int, default=32, help="palette head hidden width")
p.add_argument("--steps", type=int, default=20000)
p.add_argument("--device", default="cuda")
p.add_argument("--seed", type=int, default=0)
p.add_argument("--pen", type=float, default=0.075, help="default pen radius in cell widths")
p.add_argument("--grid", type=int, default=256, help="target grid nodes per cell width")
a = p.parse_args()
torch.manual_seed(a.seed)
torch.set_default_device(a.device)

ENTRY_BITS, PALETTE_SIZE = 5, 32
THEMES = {"dark": ((0x11, 0x15, 0x1C), (0xE9, 0xE6, 0xDF)), "light": ((0xFA, 0xFA, 0xF7), (0x1E, 0x23, 0x30))}


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


SOURCES = {os.path.relpath(f, strokes.ROOT): sha(f) for f in
           (strokes.ICONS, strokes.PALETTE, os.path.join(strokes.ROOT, "train", "glyphs.py"))}
SOURCES["train/colour.py"] = sha(os.path.abspath(__file__))
TAU, OCT, W, N, K = 0.15, 6, a.width, a.grid, a.layers
PAL = strokes.palette()
# Drawings in font/icons.txt, plus the powerline and progress glyphs made by rule.
ICONS = glyphs.colour_icons(pal=PAL)
CHARS = list(ICONS)
G = len(CHARS)
assert max(len(v) for v in ICONS.values()) <= K, "an icon has more layers than K"
USED = torch.tensor([[k < len(ICONS[c]) for k in range(K)] for c in CHARS])
ENTRY = torch.tensor([[PAL[ICONS[c][k][0]][0] if k < len(ICONS[c]) else 0 for k in range(K)] for c in CHARS])
NX, NY = N + 1, 2 * N + 1
EMPTY = np.full((NY, NX), -1.0, np.float32)
FIELD = torch.tensor(np.stack([np.stack([glyphs.field(ICONS[c][k][1], N, a.pen, TAU) if k < len(ICONS[c]) else EMPTY
                                         for k in range(K)]) for c in CHARS]).astype(np.float16)).reshape(-1)
MASKS = strokes.masks()
MB = torch.tensor([[(m >> i) & 1 for i in range(21)] for m in MASKS], dtype=torch.float32)
LAB = torch.tensor([ord(c) for c in CHARS])
SPAN = torch.tensor([1.0, 2.0])


def target(gi, xy):
    """Target fields (B, K, M) for characters gi at points xy (B, M, 2)."""
    u, v = xy[..., 0] * N, xy[..., 1] * N
    i0, j0 = u.floor().clamp(0, N - 1), v.floor().clamp(0, 2 * N - 1)
    fu, fv = (u - i0)[:, None], (v - j0)[:, None]
    base = (gi[:, None] * K + torch.arange(K)[None]) * (NX * NY)
    k = base[..., None] + (j0.long() * NX + i0.long())[:, None]
    f00, f01, f10, f11 = (FIELD[k + d].float() for d in (0, 1, NX, NX + 1))
    return (f00 * (1 - fu) + f01 * fu) * (1 - fv) + (f10 * (1 - fu) + f11 * fu) * fv


def code(v):
    b = ((v[:, None] >> torch.arange(21)) & 1).float()
    return 2 * torch.cat([b, torch.remainder(b @ MB.T, 2)], 1) - 1


def pos(xy):
    f = [xy[..., :1] * 2 - 1, xy[..., 1:] - 1]
    for o in range(OCT):
        w = 2 * math.pi * 2 ** o
        f += [torch.sin(w * xy), torch.cos(w * xy)]
    return torch.cat(f, -1)


extra, outs = (0, K) if a.form == "A" else (K, 1)
net = torch.nn.Sequential(torch.nn.Linear(26 + 64 + extra, W), torch.nn.ReLU(),
                          torch.nn.Linear(W, W), torch.nn.ReLU(),
                          torch.nn.Linear(W, W), torch.nn.ReLU(),
                          torch.nn.Linear(W, outs))
head = torch.nn.Sequential(torch.nn.Linear(64, a.head_width), torch.nn.ReLU(),
                           torch.nn.Linear(a.head_width, K * ENTRY_BITS))
ONEHOT = torch.eye(K)


def field(c, xy):
    """Distances (B, K, M) for codes c (B, 64) at points xy (B, M, 2)."""
    x = torch.cat([pos(xy), c[:, None, :].expand(-1, xy.shape[1], -1)], -1)
    if a.form == "A":
        return net(x).permute(0, 2, 1)
    B, M = x.shape[:2]
    x = torch.cat([x[:, None].expand(B, K, M, x.shape[-1]), ONEHOT[None, :, None, :].expand(B, K, M, K)], -1)
    return net(x).squeeze(-1)


def entries(c):
    bits = head(c).reshape(-1, K, ENTRY_BITS)
    return bits, ((bits > 0).long() << torch.arange(ENTRY_BITS)).sum(-1)


gi = torch.arange(G)
CF = code(LAB)
EBITS = ((ENTRY[..., None] >> torch.arange(ENTRY_BITS)) & 1).float()
params = list(net.parameters()) + list(head.parameters())
opt = torch.optim.Adam(params, lr=2e-3)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.steps)
for step in range(a.steps):
    cand = torch.rand(G, 1024, 2) * SPAN
    tc = target(gi, cand)
    # Each used layer gets an equal share of the edge points, however short
    # its edge: rank the candidates by nearness to each layer's edge, and
    # take them round-robin by rank.
    rank = tc.abs().argsort(-1).argsort(-1).float().masked_fill(~USED[..., None], float("inf"))
    near = rank.amin(1).topk(384, dim=1, largest=False).indices
    xy = torch.cat([cand[:, :128], torch.gather(cand, 1, near[..., None].expand(-1, -1, 2))], 1)
    loss = (field(CF, xy) - target(gi, xy)).abs().mean()
    bits, _ = entries(CF)
    hloss = torch.nn.functional.binary_cross_entropy_with_logits(bits, EBITS)
    opt.zero_grad()
    (loss + 0.1 * hloss).backward()
    opt.step()
    sched.step()


def grid(wpx, ss):
    xs = (torch.arange(wpx * ss) + 0.5) / (wpx * ss)
    ys = (torch.arange(2 * wpx * ss) + 0.5) / (2 * wpx * ss) * 2
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    return torch.stack([xx, yy], -1).reshape(1, -1, 2)


@torch.no_grad()
def cover(wpx, ss):
    xy = grid(wpx, ss)
    out = []
    for i in range(0, G, 4):
        c = CF[i:i + 4]
        f = field(c, xy.expand(c.shape[0], -1, -1))
        cv = (0.5 + f * TAU * wpx * ss).clamp(0, 1)
        out.append(cv.reshape(-1, K, 2 * wpx, ss, wpx, ss).mean((3, 5)))
    return torch.cat(out)


@torch.no_grad()
def truth(wpx, ss=8):
    xy = grid(wpx, ss)
    rows = [(target(gi[i:i + 1], xy) > 0).float() for i in range(G)]
    return torch.cat(rows).reshape(G, K, 2 * wpx, ss, wpx, ss).mean((3, 5))


def colours(theme):
    bg, fg = (torch.tensor(c, dtype=torch.float32) / 255 for c in THEMES[theme])
    table = torch.zeros(PALETTE_SIZE, 3)
    table[0] = fg
    for n, dark, light in PAL.values():
        if n >= 2:
            table[n] = torch.tensor(dark if theme == "dark" else light, dtype=torch.float32) / 255
    return bg, table


def composite(cov, ent, theme):
    """Back to front: an entry paints its colour, entry 1 (clear) takes away."""
    bg, table = colours(theme)
    rgb = torch.zeros(*cov.shape[:1], *cov.shape[2:], 3)
    alpha = torch.zeros(*cov.shape[:1], *cov.shape[2:], 1)
    for k in range(K):
        c = cov[:, k, ..., None]
        clear = (ent[:, k] == 1).float()[:, None, None, None]
        col = table[ent[:, k]][:, None, None, :]
        rgb = clear * rgb * (1 - c) + (1 - clear) * (col * c + rgb * (1 - c))
        alpha = clear * alpha * (1 - c) + (1 - clear) * (c + alpha * (1 - c))
    return rgb + bg * (1 - alpha)


def label(g, k):
    return f"U+{ord(CHARS[g]):04X} layer {k}"


with torch.no_grad():
    _, pred = entries(CF)
head_wrong = int(((pred != ENTRY) & USED).sum())
res = {"form": a.form, "layers": K, "icons": G, "width": W, "steps": a.steps, "seed": a.seed,
       "params": sum(q.numel() for q in net.parameters()), "head_params": sum(q.numel() for q in head.parameters()),
       "final_loss": float(loss.detach()), "head_wrong": head_wrong}
for wpx, ss in ((12, 2), (16, 2), (32, 1)):
    t, n = truth(wpx), cover(wpx, ss)
    ti, ni = t > 0.5, n > 0.5
    u = (ti | ni).sum((2, 3)).float()
    iou = torch.where(u > 0, (ti & ni).sum((2, 3)).float() / u.clamp_min(1), torch.ones_like(u))
    used = iou[USED]
    order = iou.masked_fill(~USED, 2).reshape(-1).argsort()[:3]
    r = {"iou_mean": round(float(used.mean()), 4), "iou_min": round(float(used.min()), 4),
         "worst": [label(int(i) // K, int(i) % K) for i in order],
         "stray_unused": int((ni & ~USED[..., None, None]).any(-1).any(-1).sum())}
    for theme in THEMES:
        err = (composite(n, pred, theme) - composite(t, ENTRY, theme)).abs() * 255
        r[theme] = {"mean_err": round(float(err.mean()), 2), "off_gt32": round(float((err.amax(-1) > 32).float().mean()), 4)}
    res[f"w{wpx}_s{ss}"] = r


def f32(t):
    return [float(x) for x in t.detach().cpu().numpy().astype(np.float32).ravel()]


def layers_of(seq, names):
    lin = [m for m in seq if isinstance(m, torch.nn.Linear)]
    return {name: {"rows": l.weight.shape[0], "cols": l.weight.shape[1], "weight": f32(l.weight), "bias": f32(l.bias)}
            for name, l in zip(names, lin)}


# Form A is the form train/pack.py packs. Form B stays the experiment's file.
doc = {
    "format": "neuronte-colour-weights" if a.form == "A" else "neuronte-colour-weights-experimental",
    "version": 1 if a.form == "A" else 0,
    "shape": {"form": a.form, "glyph_layers": K, "position_octaves": OCT, "code_bits": 64, "hidden_width": W,
              "hidden_layers": 3, "tau": TAU, "parity_masks": [f"0x{m:06X}" for m in MASKS],
              "entry_bits": ENTRY_BITS, "head_width": a.head_width},
    "palette": {name: {"entry": n, "dark": f"#{d[0]:02X}{d[1]:02X}{d[2]:02X}" if d else None,
                       "light": f"#{li[0]:02X}{li[1]:02X}{li[2]:02X}" if li else None}
                for name, (n, d, li) in PAL.items()},
    "training": {"set": "icons", "labelled": " ".join(f"U+{ord(c):04X}" for c in CHARS), "sources_sha256": SOURCES,
                 "pen_radius": a.pen, "grid": N, "steps": a.steps, "seed": a.seed},
    "layers": layers_of(net, ["l1", "l2", "l3", "out"]),
    "head": layers_of(head, ["h1", "out"]),
}
with open(a.out, "w") as fh:
    json.dump(doc, fh)
print(json.dumps(res, ensure_ascii=False))
