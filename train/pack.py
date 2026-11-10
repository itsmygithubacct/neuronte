"""Pack weights JSON into the binary file the C library loads.

usage: python3 train/pack.py WEIGHTS.json OUT.nrt

Layout, all little-endian:

    0   8 bytes   "NEURONTE"
    8   u32       format version, 1
    12  u32       position octaves, 6
    16  u32       code bits, 64
    20  u32       hidden width, 128
    24  u32       hidden layers, 3
    28  f32       tau
    32  43 x u32  parity masks
    204 f32 ...   l1 weight (128 x 90, row-major), l1 bias, l2 weight, l2 bias,
                  l3 weight, l3 bias, out weight (1 x 128), out bias

179,408 bytes in all.
"""
import json
import struct
import sys

import numpy as np

SHAPE = {"position_octaves": 6, "code_bits": 64, "hidden_width": 128, "hidden_layers": 3}
LAYERS = [("l1", 128, 90), ("l2", 128, 128), ("l3", 128, 128), ("out", 1, 128)]
LENGTH = 204 + 4 * 44801


def load(path):
    with open(path) as fh:
        doc = json.load(fh)
    if doc.get("format") != "neuronte-weights" or doc.get("version") != 1:
        raise SystemExit(f"{path}: not a version 1 Neuronte weights file")
    shape = doc["shape"]
    for k, v in SHAPE.items():
        if shape.get(k) != v:
            raise SystemExit(f"{path}: {k} is {shape.get(k)}, this packer is for {v}")
    masks = [int(m, 16) for m in shape["parity_masks"]]
    if len(masks) != 43 or any(not 0 < m < 1 << 21 for m in masks):
        raise SystemExit(f"{path}: parity masks must be 43 values over 21 bits")
    layers = {}
    for name, rows, cols in LAYERS:
        layer = doc["layers"][name]
        w = np.asarray(layer["weight"], np.float32)
        b = np.asarray(layer["bias"], np.float32)
        if (layer["rows"], layer["cols"]) != (rows, cols) or w.size != rows * cols or b.size != rows:
            raise SystemExit(f"{path}: layer {name} is not {rows} x {cols}")
        if not (np.isfinite(w).all() and np.isfinite(b).all()):
            raise SystemExit(f"{path}: layer {name} holds a value that is not finite")
        layers[name] = (w.reshape(rows, cols), b)
    return float(np.float32(shape["tau"])), masks, layers


def pack(path):
    tau, masks, layers = load(path)
    out = bytearray(b"NEURONTE")
    out += struct.pack("<5I", 1, 6, 64, 128, 3)
    out += struct.pack("<f", tau)
    out += struct.pack("<43I", *masks)
    for name, _, _ in LAYERS:
        w, b = layers[name]
        out += w.astype("<f4").tobytes() + b.astype("<f4").tobytes()
    assert len(out) == LENGTH, len(out)
    return bytes(out)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    data = pack(sys.argv[1])
    with open(sys.argv[2], "wb") as fh:
        fh.write(data)
    print(sys.argv[2], len(data), "bytes")
