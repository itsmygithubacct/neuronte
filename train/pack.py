"""Pack weights JSON into the binary file the C library loads.

usage: python3 train/pack.py WEIGHTS.json OUT.nrt
       python3 train/pack.py --bundle OUT.nrt NET.json... [--gate GATE.json]
                             [--fallback I]

The first form packs one net. The second packs a bundle of nets with a
router: each scalar a net was trained on is drawn by that net, so no two
nets may share one. Other scalars go to the gate (from train/gate.py, made
for the same nets in the same order) or, with no gate, to net I (0).

One net, version 1, all little-endian:

    0   8 bytes   "NEURONTE"
    8   u32       format version, 1
    12  u32       position octaves, 6
    16  u32       code bits, 64
    20  u32       hidden width H, a multiple of 8 from 8 to 1024
    24  u32       hidden layers, 3
    28  f32       tau
    32  43 x u32  parity masks
    204 f32 ...   l1 weight (H x 90, row-major), l1 bias, l2 weight (H x H),
                  l2 bias, l3 weight (H x H), l3 bias, out weight (1 x H),
                  out bias

204 + 4 (2 H^2 + 94 H + 1) bytes in all: 179,408 for H = 128 and
620,752 for H = 256.

A bundle, version 2:

    0   8 bytes   "NEURONTE"
    8   u32       format version, 2
    12  u32       nets K, 1 to 16
    16  u32       table ranges R
    20  u32       fallback net, below K
    24  u32       gate hidden width G, 0 for no gate, at most 256
    28  K x u32   the length of each net
        R x 3 u32 first scalar, last scalar, net; sorted, not overlapping
        when G > 0: 43 x u32 parity masks, then f32 gate l1 weight
                  (G x 64, row-major), l1 bias, out weight (K x G), out bias
        the K nets, each a whole version 1 file
"""
import json
import struct
import sys

import numpy as np

SHAPE = {"position_octaves": 6, "code_bits": 64, "hidden_layers": 3}


def layers(h):
    return [("l1", h, 90), ("l2", h, h), ("l3", h, h), ("out", 1, h)]


def length(h):
    return 204 + 4 * (2 * h * h + 94 * h + 1)


def load(path):
    with open(path) as fh:
        doc = json.load(fh)
    if doc.get("format") != "neuronte-weights" or doc.get("version") != 1:
        raise SystemExit(f"{path}: not a version 1 Neuronte weights file")
    shape = doc["shape"]
    for k, v in SHAPE.items():
        if shape.get(k) != v:
            raise SystemExit(f"{path}: {k} is {shape.get(k)}, this packer is for {v}")
    h = shape.get("hidden_width")
    if not (isinstance(h, int) and 8 <= h <= 1024 and h % 8 == 0):
        raise SystemExit(f"{path}: hidden width {h} is not a multiple of 8 from 8 to 1024")
    masks = [int(m, 16) for m in shape["parity_masks"]]
    if len(masks) != 43 or any(not 0 < m < 1 << 21 for m in masks):
        raise SystemExit(f"{path}: parity masks must be 43 values over 21 bits")
    out = {}
    for name, rows, cols in layers(h):
        layer = doc["layers"][name]
        w = np.asarray(layer["weight"], np.float32)
        b = np.asarray(layer["bias"], np.float32)
        if (layer["rows"], layer["cols"]) != (rows, cols) or w.size != rows * cols or b.size != rows:
            raise SystemExit(f"{path}: layer {name} is not {rows} x {cols}")
        if not (np.isfinite(w).all() and np.isfinite(b).all()):
            raise SystemExit(f"{path}: layer {name} holds a value that is not finite")
        out[name] = (w.reshape(rows, cols), b)
    return h, float(np.float32(shape["tau"])), masks, out


def pack(path):
    """The version 1 image of one net."""
    h, tau, masks, weights = load(path)
    out = bytearray(b"NEURONTE")
    out += struct.pack("<5I", 1, 6, 64, h, 3)
    out += struct.pack("<f", tau)
    out += struct.pack("<43I", *masks)
    for name, _, _ in layers(h):
        w, b = weights[name]
        out += w.astype("<f4").tobytes() + b.astype("<f4").tobytes()
    assert len(out) == length(h), len(out)
    return bytes(out)


def scalars(path):
    """The scalars a net was trained on, from its JSON."""
    with open(path) as fh:
        doc = json.load(fh)
    out = set()
    for tok in doc["training"]["labelled"].split():
        lo, _, hi = tok.partition("..")
        out.update(range(int(lo[2:], 16), int((hi or lo)[2:], 16) + 1))
    # The first ASCII weights were made before sets had names.
    return doc["training"].get("set", "ascii"), out


def table(nets):
    """Sorted (first, last, net) ranges over the scalars each net knows."""
    owner = {}
    for i, path in enumerate(nets):
        for v in scalars(path)[1]:
            if v in owner:
                raise SystemExit(f"U+{v:04X} is in both {nets[owner[v]]} and {path}")
            owner[v] = i
    out = []
    for v in sorted(owner):
        if out and out[-1][1] == v - 1 and out[-1][2] == owner[v]:
            out[-1][1] = v
        else:
            out.append([v, v, owner[v]])
    return out


def load_gate(path, names):
    with open(path) as fh:
        doc = json.load(fh)
    if doc.get("format") != "neuronte-gate" or doc.get("version") != 1:
        raise SystemExit(f"{path}: not a version 1 Neuronte gate")
    if doc["nets"] != names:
        raise SystemExit(f"{path}: made for nets {doc['nets']}, the bundle has {names}")
    g, k = doc["hidden_width"], len(names)
    if not (isinstance(g, int) and 1 <= g <= 256):
        raise SystemExit(f"{path}: gate width {g} is not 1 to 256")
    masks = [int(m, 16) for m in doc["parity_masks"]]
    if len(masks) != 43 or any(not 0 < m < 1 << 21 for m in masks):
        raise SystemExit(f"{path}: parity masks must be 43 values over 21 bits")
    out = bytearray(struct.pack("<43I", *masks))
    for name, rows, cols in (("l1", g, 64), ("out", k, g)):
        layer = doc["layers"][name]
        w = np.asarray(layer["weight"], np.float32)
        b = np.asarray(layer["bias"], np.float32)
        if (layer["rows"], layer["cols"]) != (rows, cols) or w.size != rows * cols or b.size != rows:
            raise SystemExit(f"{path}: gate layer {name} is not {rows} x {cols}")
        if not (np.isfinite(w).all() and np.isfinite(b).all()):
            raise SystemExit(f"{path}: gate layer {name} holds a value that is not finite")
        out += w.astype("<f4").tobytes() + b.astype("<f4").tobytes()
    return g, bytes(out)


def bundle(nets, gate=None, fallback=0):
    if not 1 <= len(nets) <= 16:
        raise SystemExit("a bundle holds 1 to 16 nets")
    if not 0 <= fallback < len(nets):
        raise SystemExit(f"fallback {fallback} is not one of the {len(nets)} nets")
    images = [pack(p) for p in nets]
    ranges = table(nets)
    g, gate_bytes = load_gate(gate, [scalars(p)[0] for p in nets]) if gate else (0, b"")
    out = bytearray(b"NEURONTE")
    out += struct.pack("<5I", 2, len(nets), len(ranges), fallback, g)
    out += struct.pack(f"<{len(nets)}I", *map(len, images))
    for r in ranges:
        out += struct.pack("<3I", *r)
    out += gate_bytes
    for im in images:
        out += im
    return bytes(out), ranges


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--bundle"] and len(args) >= 3:
        gate, fallback, nets = None, 0, []
        it = iter(args[2:])
        for a in it:
            if a == "--gate":
                gate = next(it)
            elif a == "--fallback":
                fallback = int(next(it))
            else:
                nets.append(a)
        data, ranges = bundle(nets, gate, fallback)
        out = args[1]
        print(out, len(data), "bytes,", len(nets), "nets,", len(ranges), "ranges,",
              "a gate" if gate else f"fallback net {fallback}")
    elif len(args) == 2 and not args[0].startswith("--"):
        data, out = pack(args[0]), args[1]
        print(out, len(data), "bytes")
    else:
        raise SystemExit(__doc__)
    with open(out, "wb") as fh:
        fh.write(data)
