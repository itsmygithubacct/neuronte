"""Desktop faces drawn by several smaller nets: character groups and an ink band.

usage: python3 train/face_parts.py OUT_DIR --set ui24 [--groups K] [--band]
                                   [--width W] [--steps N] [--seeds 0,1]
                                   [--device cuda] [--log-every N]

A face set (uiEM, uiEMi or uilarge, train/glyphs.py) is cut two ways.

--groups K splits its characters, in set order, into K contiguous groups
whose sizes differ by at most one. Each group has its own net, and a
bundle's range table sends each scalar to its group's net, as the ASCII
character groups do.

--band draws only the rows that can hold ink with a trained net. The
design cell (0..1 across, 0..2 down) is cut into three row tiles of a
version 6 tiled net: above the ink, the ink band and below it. For a
pixel face the band is the em rows from UI_TOP[em]: y from UI_TOP / em to
(UI_TOP + em) / em, which fall on whole pixel rows at the face's em. For
uilarge it is BAND_LARGE, chosen to hold all of the ink. The tiles above
and below are drawn by EMPTY, a width-1 net that is outside the ink
everywhere: no weights, an output bias of -8.

Training is train.py's recipe, unchanged except that each net sees only
its group's characters and its tile's region: Adam at 0.002 with a cosine
schedule, 1,024 candidate points per character per step, of which the
first 128 and the 128 nearest an edge are fitted to the target field by
mean absolute error. The target is glyphs.field on train.py's grid, read
bilinearly at the point's position in the whole cell, so a band net sees
exactly the original target in its own (stretched) coordinates; the
tau of a full-width tile is the cell's. No unlabelled scalars are used
(the faces train with --unlabelled 0). Every group of both seeds trains
in one batch with independent parameters and Adam state; the nets of one
seed start from that seed's initial net and share its random draws.

Outputs, in OUT_DIR: one neuronte-weights JSON per net (NAME-gG-sS.json),
for --band one neuronte-tiled-weights JSON per net (NAME-gG-sS.tiled.json),
NAME-sS.scores.json with the exact-pixel score at the face's em, and
NAME.identity.json. Pack them with pack.py.
MIT licence; see LICENSE.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glyphs  # noqa: E402
import strokes  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TAU, OCT, GRID = 0.15, 6, 256
BAND_LARGE = (0.578125, 1.625)  # uilarge ink is 0.6055..1.5938 (field nodes); over half a pixel clear at 33 px
EMPTY_BIAS = -8.0


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def face_em(name):
    em = name[2:].removesuffix("i")
    return int(em) if name.startswith("ui") and em.isdigit() else None


def f32(v):
    return float(np.float32(v))


def band(name):
    """(y0, y1): the ink band of a face in design units, exact float32 values."""
    em = face_em(name)
    if em is not None:
        return f32(glyphs.UI_TOP[em] / em), f32((glyphs.UI_TOP[em] + em) / em)
    if name == "uilarge":
        return BAND_LARGE
    raise ValueError(f"no ink band for set {name}")


def groups(n, k):
    if not 1 <= k <= n:
        raise ValueError("groups must be 1 to the number of characters")
    return [list(range(n * i // k, n * (i + 1) // k)) for i in range(k)]


def empty_net(masks):
    zero = lambda r, c: {"rows": r, "cols": c, "weight": [0.0] * (r * c), "bias": [0.0] * r}
    layers = {"l1": zero(1, 90), "l2": zero(1, 1), "l3": zero(1, 1), "out": zero(1, 1)}
    layers["out"]["bias"] = [EMPTY_BIAS]
    return {"format": "neuronte-weights", "version": 1,
            "shape": {"position_octaves": OCT, "code_bits": 64, "hidden_width": 1, "hidden_layers": 3,
                      "tau": TAU, "parity_masks": [f"0x{m:06X}" for m in masks]},
            "training": {"set": "empty", "labelled": "", "note": "constructed, not trained: outside the ink everywhere"},
            "layers": layers}


def tiled_doc(net, empty, y0, y1):
    return {"format": "neuronte-tiled-weights", "version": 1, "first": 0, "last": 0x1FFFFF,
            "columns": [0.0, 1.0], "rows": [0.0, y0, y1, 2.0], "nets": [empty, net],
            "tiles": [{"net": 0, "mask": 0, "base": 0, "code": "place"},
                      {"net": 1, "mask": 0x1FFFFF, "base": 0, "code": "place"},
                      {"net": 0, "mask": 0, "base": 0, "code": "place"}]}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out", type=Path)
    p.add_argument("--set", required=True, choices=[s for s in glyphs.SETS if s.startswith("ui")])
    p.add_argument("--groups", type=int, default=1)
    p.add_argument("--band", action="store_true")
    p.add_argument("--width", type=int, default=128)
    p.add_argument("--steps", type=int, default=20000)
    p.add_argument("--seeds", default="0,1")
    p.add_argument("--device", default="cuda")
    p.add_argument("--log-every", type=int, default=1000)
    p.add_argument("--name", help="file stem; default SET-[b]gK-wW-NNk")
    a = p.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")]
    if len(set(seeds)) != len(seeds) or not 1 <= a.width <= 1024 or a.steps < 1:
        p.error("distinct seeds, a width of 1 to 1024 and a positive step count")
    import torch
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_default_device(a.device)
    name = a.name or f"{a.set}-{'b' if a.band else ''}g{a.groups}-w{a.width}-{a.steps // 1000}k"
    a.out.mkdir(parents=True, exist_ok=True)

    sources = {f: digest(ROOT / f) for f in glyphs.sources(a.set) + ["train/face_parts.py", "font/code-masks.txt"]}
    pen = glyphs.PENS.get(a.set, glyphs.PEN)
    rows = glyphs.charset(a.set)
    chars = [c for c, _, _ in rows]
    G = len(chars)
    parts = groups(G, a.groups)
    y0, y1 = band(a.set) if a.band else (0.0, 2.0)
    field = np.stack([glyphs.field(s, GRID, pen, TAU) for _, _, s in rows]).astype(np.float16)
    if a.band:
        # Nothing may be inked outside the band. A pixel face's pen is 1.1 pixels
        # wide, so its dots overhang their rows by 0.05 pixel: allow 0.1 pixel.
        em = face_em(a.set)
        slack = 0.1 / em if em else 0.0
        ys = np.arange(2 * GRID + 1) / GRID
        outside = (ys < y0 - slack) | (ys > y1 + slack)
        if (field[:, outside, :] > 0).any():
            raise SystemExit(f"{a.set}: ink outside the band {y0}..{y1}")
    FIELD = torch.tensor(field).reshape(-1)
    N = GRID
    NX, NY = N + 1, 2 * N + 1
    masks = strokes.masks()
    MB = torch.tensor([[(m >> i) & 1 for i in range(21)] for m in masks], dtype=torch.float32)

    members = [{"group": g, "seed": s, "chars": parts[g]} for s in seeds for g in range(len(parts))]
    M, per = len(members), max(len(x) for x in parts)
    if any(len(x) != per for x in parts):
        raise SystemExit("groups of unequal size are not batched here; choose K dividing the set")
    gi = torch.tensor([m["chars"] for m in members])  # (M, per) glyph indices
    lab = torch.tensor([[ord(chars[i]) for i in m["chars"]] for m in members])

    def code(v):
        b = ((v[..., None] >> torch.arange(21)) & 1).float()
        return 2 * torch.cat([b, torch.remainder(b @ MB.T, 2)], -1) - 1

    def pos(xy):
        f = [xy[..., :1] * 2 - 1, xy[..., 1:] - 1]
        for k in range(OCT):
            w = 2 * math.pi * 2 ** k
            f += [torch.sin(w * xy), torch.cos(w * xy)]
        return torch.cat(f, -1)

    def target(xy):
        """Original field at local points xy (M, per, P, 2), mapped into the band."""
        gx = xy[..., 0]
        gy = y0 + xy[..., 1] * ((y1 - y0) / 2)
        u, v = gx * N, gy * N
        i0, j0 = u.floor().clamp(0, N - 1), v.floor().clamp(0, 2 * N - 1)
        fu, fv = u - i0, v - j0
        k = gi[..., None] * (NX * NY) + j0.long() * NX + i0.long()
        f00, f01, f10, f11 = (FIELD[k + d].float() for d in (0, 1, NX, NX + 1))
        return (f00 * (1 - fu) + f01 * fu) * (1 - fv) + (f10 * (1 - fu) + f11 * fu) * fv

    W = a.width
    inits, gens = {}, {}
    for s in seeds:
        torch.manual_seed(s)
        net = torch.nn.Sequential(torch.nn.Linear(90, W), torch.nn.ReLU(), torch.nn.Linear(W, W), torch.nn.ReLU(),
                                  torch.nn.Linear(W, W), torch.nn.ReLU(), torch.nn.Linear(W, 1))
        inits[s] = [l for l in net if isinstance(l, torch.nn.Linear)]
        gen = torch.Generator(device=a.device)
        gen.manual_seed(s)
        gens[s] = gen
    weights = [torch.nn.Parameter(torch.stack([inits[m["seed"]][i].weight.detach() for m in members])) for i in range(4)]
    biases = [torch.nn.Parameter(torch.stack([inits[m["seed"]][i].bias.detach() for m in members])) for i in range(4)]
    opt = torch.optim.Adam(weights + biases, lr=2e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.steps)
    CF = code(lab)  # (M, per, 64)

    def evaluate(xy, cf):
        m, g, pts, _ = xy.shape
        h = torch.cat([pos(xy), cf[:, :, None].expand(-1, -1, pts, -1)], -1).reshape(m, g * pts, 90)
        for i in range(4):
            h = torch.baddbmm(biases[i][:, None], h, weights[i].transpose(1, 2))
            if i < 3:
                h = torch.relu(h)
        return h.reshape(m, g, pts)

    span = torch.tensor([1.0, 2.0])
    seed_of = [m["seed"] for m in members]
    started = time.monotonic()
    log = []
    for step in range(a.steps):
        draws = {s: torch.rand(per, 1024, 2, generator=gens[s]) * span for s in seeds}
        cand = torch.stack([draws[s] for s in seed_of])
        tc = target(cand)
        near = tc.abs().topk(128, dim=2, largest=False).indices
        xy = torch.cat([cand[:, :, :128], torch.gather(cand, 2, near[..., None].expand(-1, -1, -1, 2))], 2)
        y = torch.cat([tc[:, :, :128], torch.gather(tc, 2, near)], 2)
        losses = (evaluate(xy, CF) - y).abs().mean((1, 2))
        opt.zero_grad()
        losses.sum().backward()
        opt.step()
        sched.step()
        if (step + 1) % a.log_every == 0 or step + 1 == a.steps:
            last = losses.detach().cpu().tolist()
            if not all(math.isfinite(v) for v in last):
                raise SystemExit("nonfinite training loss")
            log.append({"step": step + 1, "seconds": round(time.monotonic() - started, 1), "losses": last})
            print(json.dumps(log[-1]), file=sys.stderr, flush=True)

    identity = {"schema": "neuronte.face-parts/v1", "set": a.set, "groups": [[chars[i] for i in g] for g in parts],
                "band": [y0, y1] if a.band else None, "width": W, "steps": a.steps, "seeds": seeds,
                "pen_radius": pen, "grid": GRID, "tau": TAU, "unlabelled_weight": 0.0,
                "sources_sha256": sources, "torch": str(torch.__version__), "cuda": torch.version.cuda,
                "device": torch.cuda.get_device_name(0) if a.device.startswith("cuda") else a.device,
                "tf32": False, "recipe": "train.py: Adam 0.002 cosine; 1024 candidates, first 128 and nearest 128 "
                                         "per character per step; L1 on the clamped field over tau",
                "seconds": round(time.monotonic() - started, 1), "log": log}
    (a.out / f"{name}.identity.json").write_text(json.dumps(identity, indent=1) + "\n")
    hex_masks = [f"0x{m:06X}" for m in masks]
    empty = empty_net(masks)
    docs = {}
    for k, m in enumerate(members):
        g, s = m["group"], m["seed"]
        doc = {"format": "neuronte-weights", "version": 1,
               "shape": {"position_octaves": OCT, "code_bits": 64, "hidden_width": W, "hidden_layers": 3,
                         "tau": TAU, "parity_masks": hex_masks},
               "training": {"set": a.set, "labelled": " ".join(f"U+{ord(chars[i]):04X}" for i in m["chars"]),
                            "sources_sha256": sources, "pen_radius": pen, "grid": GRID, "steps": a.steps,
                            "seed": s, "unlabelled_weight": 0.0,
                            "face_parts": {"name": name, "group": g, "groups": len(parts),
                                           "band": [y0, y1] if a.band else None,
                                           "final_loss": log[-1]["losses"][k]}},
               "layers": {nm: {"rows": int(w.shape[1]), "cols": int(w.shape[2]),
                               "weight": [float(x) for x in w[k].detach().cpu().numpy().astype(np.float32).ravel()],
                               "bias": [float(x) for x in b[k].detach().cpu().numpy().astype(np.float32).ravel()]}
                          for nm, w, b in zip(("l1", "l2", "l3", "out"), weights, biases)}}
        docs[g, s] = doc
        (a.out / f"{name}-g{g}-s{s}.json").write_text(json.dumps(doc) + "\n")
        if a.band:
            (a.out / f"{name}-g{g}-s{s}.tiled.json").write_text(json.dumps(tiled_doc(doc, empty, y0, y1)) + "\n")

    # Score: every character at the face's em, as the library samples it, against
    # the drawing's 8 x 8 truth (train.py's exact-pixel score).
    em = face_em(a.set)
    sizes = (em,) if em else (32, 48, 64, 96)
    with torch.no_grad():
        for s in seeds:
            res = {"name": name, "set": a.set, "seed": s, "groups": len(parts), "band": a.band, "width": W,
                   "steps": a.steps, "final_losses": [log[-1]["losses"][k] for k, m in enumerate(members) if m["seed"] == s]}
            for wpx in sizes:
                ss = 2 if wpx < 24 else 1
                xs = (torch.arange(wpx * ss) + 0.5) / (wpx * ss)
                ys = (torch.arange(2 * wpx * ss) + 0.5) / (2 * wpx * ss) * 2
                yy, xx = torch.meshgrid(ys, xs, indexing="ij")
                inside = ((yy >= y0) & (yy < y1)).reshape(-1)
                gxy = torch.stack([xx, yy], -1).reshape(-1, 2)
                local = gxy[inside].clone()
                local[:, 1] = (local[:, 1] - y0) / (y1 - y0) * 2
                cov = torch.zeros(G, gxy.shape[0])
                for k, m in enumerate(members):
                    if m["seed"] != s:
                        continue
                    for i in m["chars"]:
                        pts = local[None, None]
                        hh = torch.cat([pos(pts), CF[k, m["chars"].index(i)][None, None, None].expand(1, 1, pts.shape[2], -1)], -1)
                        hh = hh.reshape(1, -1, 90)
                        for li in range(4):
                            hh = torch.baddbmm(biases[li][k:k + 1, None], hh, weights[li][k:k + 1].transpose(1, 2))
                            if li < 3:
                                hh = torch.relu(hh)
                        cov[i, inside] = (0.5 + hh.reshape(-1) * TAU * wpx * ss).clamp(0, 1)
                cov = cov.reshape(G, 2 * wpx, ss, wpx, ss).mean((2, 4)).reshape(G, -1)
                # truth at 8 x 8 samples, as train.py
                t8 = 8
                xs8 = (torch.arange(wpx * t8) + 0.5) / (wpx * t8)
                ys8 = (torch.arange(2 * wpx * t8) + 0.5) / (2 * wpx * t8) * 2
                yy8, xx8 = torch.meshgrid(ys8, xs8, indexing="ij")
                g8 = torch.stack([xx8, yy8], -1).reshape(1, 1, -1, 2)
                truth = []
                for i in range(G):
                    gx, gy = g8[..., 0], g8[..., 1]
                    u, v = gx * N, gy * N
                    i0, j0 = u.floor().clamp(0, N - 1), v.floor().clamp(0, 2 * N - 1)
                    fu, fv = u - i0, v - j0
                    kk = i * (NX * NY) + j0.long() * NX + i0.long()
                    f00, f01, f10, f11 = (FIELD[kk + d].float() for d in (0, 1, NX, NX + 1))
                    tv = (f00 * (1 - fu) + f01 * fu) * (1 - fv) + (f10 * (1 - fu) + f11 * fu) * fv
                    truth.append((tv > 0).float().reshape(2 * wpx, t8, wpx, t8).mean((1, 3)).reshape(-1))
                t = torch.stack(truth)
                ti, ni = t > 0.5, cov > 0.5
                wrong = ti != ni
                firm = wrong & ((t - 0.5).abs() >= 0.1)
                u_ = (ti | ni).sum(1).float()
                iou = torch.where(u_ > 0, (ti & ni).sum(1).float() / u_.clamp_min(1), torch.ones_like(u_))
                r = {"iou_mean": float(iou.mean()), "iou_min": float(iou.min()),
                     "exact": int((~wrong.any(1)).sum()), "wrong_pixels": int(wrong.sum()),
                     "differ": [f"U+{ord(chars[i]):04X} {chars[i]}" for i in wrong.any(1).nonzero().flatten().tolist()],
                     "firm_exact": int((~firm.any(1)).sum()), "firm_wrong_pixels": int(firm.sum()),
                     "soft_mae_inked": float((cov - t).abs()[(t > 0) | (cov > 0)].mean()),
                     "soft_over_half": int(((cov - t).abs() > 0.5).sum()),
                     "soft_over_quarter": int(((cov - t).abs() > 0.25).sum())}
                res[f"w{wpx}_s{ss}"] = r
            (a.out / f"{name}-s{s}.scores.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
            print(json.dumps({k: v for k, v in res.items()}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
