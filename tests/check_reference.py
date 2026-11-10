"""Check the C library against an independent numpy evaluation of the net.

usage: python3 tests/check_reference.py build/libneuronte.so WEIGHTS.json WEIGHTS.nrt

The numpy side reads the JSON weights and works in float64. The C side
loads the packed file and works in float32. They must agree to 1e-3 in
coverage, and the packed file must be exactly what train/pack.py makes
from the JSON.
"""
import ctypes
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train"))
import pack  # noqa: E402

lib_path, json_path, nrt_path = sys.argv[1:4]
failed = False

with open(nrt_path, "rb") as fh:
    nrt = fh.read()
if nrt != pack.pack(json_path):
    print("FAIL the packed file is not what pack.py makes from the JSON")
    failed = True

with open(json_path) as fh:
    doc = json.load(fh)
L = {k: (np.asarray(v["weight"], np.float32).astype(np.float64).reshape(v["rows"], v["cols"]),
         np.asarray(v["bias"], np.float32).astype(np.float64)) for k, v in doc["layers"].items()}
TAU = float(np.float32(doc["shape"]["tau"]))
MASKS = [int(m, 16) for m in doc["shape"]["parity_masks"]]


def code(s):
    if s > 0x10FFFF or 0xD800 <= s <= 0xDFFF:
        s = 0xFFFD
    bits = [(s >> i) & 1 for i in range(21)] + [bin(s & m).count("1") & 1 for m in MASKS]
    return np.array([1.0 if b else -1.0 for b in bits])


def pos(x, y):
    f = [2 * x - 1, y - 1]
    for k in range(6):
        w = 2 * math.pi * 2 ** k
        f += [np.sin(w * x), np.sin(w * y), np.cos(w * x), np.cos(w * y)]
    return np.stack(f, -1)


def coverage(s, cw, ch, ss):
    xs = (np.arange(cw * ss) + 0.5) / (cw * ss)
    ys = (np.arange(ch * ss) + 0.5) / (ch * ss) * 2
    yy, xx = np.meshgrid(ys, xs, indexing="ij")
    p = pos(xx.ravel(), yy.ravel())
    inp = np.concatenate([p, np.broadcast_to(code(s), (p.shape[0], 64))], 1)
    h = np.maximum(inp @ L["l1"][0].T + L["l1"][1], 0)
    h = np.maximum(h @ L["l2"][0].T + L["l2"][1], 0)
    h = np.maximum(h @ L["l3"][0].T + L["l3"][1], 0)
    f = (h @ L["out"][0].T + L["out"][1])[:, 0]
    v = np.clip(0.5 + f * TAU * cw * ss, 0, 1).reshape(ch, ss, cw, ss)
    return v.mean((1, 3))


lib = ctypes.CDLL(os.path.abspath(lib_path))
lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
lib.neuronte_coverage.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
lib.neuronte_close.argtypes = [ctypes.c_void_p]
handle = ctypes.c_void_p()
rc = lib.neuronte_open_file(nrt_path.encode(), ctypes.byref(handle))
if rc != 0:
    raise SystemExit(f"neuronte_open_file returned {rc}")

cases = [(s, cw, ch, ss)
         for s in (0x20, 0x41, 0x67, 0x40, 0x7E, 0x30, 0xE9, 0x2500, 0x256C, 0x2588, 0x28FF,
                   0x25C6, 0x4E2D, 0xFFFD, 0x10FFFF, 0xD800)
         for cw, ch, ss in ((8, 16, 2), (16, 32, 2), (33, 61, 1))]
worst = 0.0
for s, cw, ch, ss in cases:
    out = (ctypes.c_float * (cw * ch))()
    rc = lib.neuronte_coverage(handle, s, cw, ch, ss, out)
    if rc != 0:
        print(f"FAIL coverage U+{s:04X} {cw}x{ch} returned {rc}")
        failed = True
        continue
    c = np.frombuffer(out, np.float32).reshape(ch, cw).astype(np.float64)
    d = float(np.abs(c - coverage(s, cw, ch, ss)).max())
    worst = max(worst, d)
    if d > 1e-3:
        print(f"FAIL U+{s:04X} {cw}x{ch} samples {ss}: C and numpy differ by {d:.2e}")
        failed = True
lib.neuronte_close(handle)
print(f"check_reference: {len(cases)} cells, largest coverage difference {worst:.2e}")
print("check_reference: FAILED" if failed else "check_reference: passed")
sys.exit(1 if failed else 0)
