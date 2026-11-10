"""Train the gate a bundle's router asks about scalars outside its table.

usage: python3 train/gate.py OUT.json NET.json... [--width G] [--steps N]
                             [--fallback I] [--blocks Blocks.txt]

The gate is a small net over a scalar's 64 code features (the ones the
nets take) with one output per net; the highest picks the net. It learns,
for each Unicode block, the net that was trained on the most scalars in
it, and for blocks no net knows, the fallback net. So a scalar no net was
trained on is drawn by the net of its neighbours. The block list is read
from Unicode's Blocks.txt at training time. Prints one JSON line of
scores: how often the gate agrees with that rule, for the scalars the nets
know, the others in their blocks, and a sample of the rest.
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack  # noqa: E402
import strokes  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("out")
p.add_argument("nets", nargs="+")
p.add_argument("--width", type=int, default=32)
p.add_argument("--steps", type=int, default=3000)
p.add_argument("--fallback", type=int, default=0)
p.add_argument("--blocks", default="/usr/share/unicode/Blocks.txt")
p.add_argument("--seed", type=int, default=0)
a = p.parse_args()
torch.set_num_threads(1)  # the tensors are small: threads only add overhead
torch.manual_seed(a.seed)
rng = np.random.default_rng(a.seed)

names, known = zip(*(pack.scalars(n) for n in a.nets))
K = len(names)
blocks = []
with open(a.blocks, "rb") as fh:
    BLOCKS_SHA = hashlib.sha256(fh.read()).hexdigest()
with open(a.blocks) as fh:
    BLOCKS_NAME = fh.readline().lstrip("# ").strip()
    for ln in fh:
        ln = ln.split("#")[0].strip()
        if ln:
            span, name = ln.split(";")
            lo, hi = span.split("..")
            blocks.append((int(lo, 16), int(hi, 16), name.strip()))


def rule(v):
    """The net the gate should pick for scalar v."""
    for i, k in enumerate(known):
        if v in k:
            return i
    for lo, hi, _ in blocks:
        if lo <= v <= hi:
            counts = [sum(lo <= s <= hi for s in k) for k in known]
            return int(np.argmax(counts)) if max(counts) else a.fallback
    return a.fallback


trained = sorted(set().union(*known))
near = sorted({v for lo, hi, _ in blocks if any(lo <= s <= hi for s in trained)
               for v in range(lo, hi + 1)} - set(trained) - set(range(0xD800, 0xE000)))
seen = set(trained) | set(near)
far = np.array([v for v in rng.integers(0, 0x110000, 200000).tolist()
                if not 0xD800 <= v <= 0xDFFF and v not in seen])
label = {v: rule(int(v)) for v in trained + near}
far_label = np.full(len(far), a.fallback)

MB = torch.tensor([[(m >> i) & 1 for i in range(21)] for m in strokes.masks()], dtype=torch.float32)


def code(v):
    b = ((v[:, None] >> torch.arange(21)) & 1).float()
    return 2 * torch.cat([b, torch.remainder(b @ MB.T, 2)], 1) - 1


net = torch.nn.Sequential(torch.nn.Linear(64, a.width), torch.nn.ReLU(), torch.nn.Linear(a.width, K))
opt = torch.optim.Adam(net.parameters(), lr=1e-2)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.steps)
T = torch.tensor(trained)
TY = torch.tensor([label[v] for v in trained])
N = torch.tensor(near)
NY = torch.tensor([label[v] for v in near])
for step in range(a.steps):
    fv = torch.randint(0, 0x110000, (1024,))
    nv = N[torch.randint(0, len(N), (1024,))]
    # A random scalar outside every block a net knows goes to the fallback.
    keep = ~torch.isin(fv, torch.cat([T, N]))
    v = torch.cat([T, nv, fv[keep]])
    y = torch.cat([TY, NY[torch.searchsorted(N, nv)], torch.full((int(keep.sum()),), a.fallback)])
    w = torch.cat([torch.full((len(T),), 4.0), torch.ones(len(nv)), torch.ones(int(keep.sum()))])
    loss = (torch.nn.functional.cross_entropy(net(code(v)), y, reduction="none") * w).mean()
    opt.zero_grad()
    loss.backward()
    opt.step()
    sched.step()


@torch.no_grad()
def agree(v, y):
    if len(v) == 0:
        return None
    return round(float((net(code(torch.as_tensor(v))).argmax(1) == torch.as_tensor(y)).float().mean()), 5)


res = {"nets": list(names), "width": a.width, "steps": a.steps,
       "params": sum(q.numel() for q in net.parameters()),
       "trained": agree(T, TY), "trained_count": len(T),
       "same_block": agree(N, NY), "same_block_count": len(N),
       "elsewhere": agree(far, far_label), "elsewhere_sample": len(far)}
lin = [m for m in net if isinstance(m, torch.nn.Linear)]


def f32(t):
    return [float(x) for x in t.detach().numpy().astype(np.float32).ravel()]


doc = {"format": "neuronte-gate", "version": 1, "nets": list(names), "hidden_width": a.width,
       "parity_masks": [f"0x{m:06X}" for m in strokes.masks()], "fallback": a.fallback,
       "training": {"blocks": BLOCKS_NAME, "blocks_sha256": BLOCKS_SHA, "steps": a.steps, "seed": a.seed},
       "scores": res,
       "layers": {n: {"rows": l.weight.shape[0], "cols": l.weight.shape[1],
                      "weight": f32(l.weight), "bias": f32(l.bias)}
                  for n, l in zip(["l1", "out"], lin)}}
with open(a.out, "w") as fh:
    json.dump(doc, fh)
print(json.dumps(res))
