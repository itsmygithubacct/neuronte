"""Pack weights JSON into the binary file the C library loads.

usage: python3 train/pack.py WEIGHTS.json OUT.nrt

Layout, all little-endian:

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


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = pack(sys.argv[1])
    with open(sys.argv[2], "wb") as fh:
        fh.write(data)
    print(sys.argv[2], len(data), "bytes")
