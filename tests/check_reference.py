"""Check the C library against an independent numpy evaluation of the net.

usage: python3 tests/check_reference.py LIB.so WEIGHTS.json WEIGHTS.nrt
       python3 tests/check_reference.py LIB.so --bundle BUNDLE.nrt NET.json...
                                        [--gate GATE.json] [--fallback I]
       python3 tests/check_reference.py LIB.so --drawing DRAWING.nrt NET.json FACE.txt

The numpy side reads the JSON weights and works in float64. The C side
loads the packed file and works in float32. They must agree to 1e-3 in
coverage, and the packed file must be exactly what train/pack.py makes
from the JSON. For a bundle, the net the C router picks for each case must
also be the one this file picks: the table, then the gate, evaluated here
in numpy, or the fallback net.

For a drawing file of one net and the advances of a pixel face, such as
font/ui-10.txt, the net is checked the same way at the face's em too.
Then every character of the face, drawn by neuronte_draw_text() at that
em with neuronte_set_binary() on, regular and bold, must be exactly the
face's pixels, and the pen must move by the face's advance.
"""
import ctypes
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train"))
import pack  # noqa: E402


def normal(s):
    return 0xFFFD if s > 0x10FFFF or 0xD800 <= s <= 0xDFFF else s


def code(s, masks):
    s = normal(s)
    bits = [(s >> i) & 1 for i in range(21)] + [bin(s & m).count("1") & 1 for m in masks]
    return np.array([1.0 if b else -1.0 for b in bits])


def layers(doc):
    return {k: (np.asarray(v["weight"], np.float32).astype(np.float64).reshape(v["rows"], v["cols"]),
                np.asarray(v["bias"], np.float32).astype(np.float64)) for k, v in doc["layers"].items()}


class Net:
    def __init__(self, path):
        with open(path) as fh:
            doc = json.load(fh)
        self.L = layers(doc)
        self.tau = float(np.float32(doc["shape"]["tau"]))
        self.masks = [int(m, 16) for m in doc["shape"]["parity_masks"]]

    def coverage(self, s, cw, ch, ss):
        xs = (np.arange(cw * ss) + 0.5) / (cw * ss)
        ys = (np.arange(ch * ss) + 0.5) / (ch * ss) * 2
        yy, xx = np.meshgrid(ys, xs, indexing="ij")
        x, y = xx.ravel(), yy.ravel()
        f = [2 * x - 1, y - 1]
        for k in range(6):
            w = 2 * math.pi * 2 ** k
            f += [np.sin(w * x), np.sin(w * y), np.cos(w * x), np.cos(w * y)]
        p = np.stack(f, -1)
        inp = np.concatenate([p, np.broadcast_to(code(s, self.masks), (p.shape[0], 64))], 1)
        L = self.L
        h = np.maximum(inp @ L["l1"][0].T + L["l1"][1], 0)
        h = np.maximum(h @ L["l2"][0].T + L["l2"][1], 0)
        h = np.maximum(h @ L["l3"][0].T + L["l3"][1], 0)
        f = (h @ L["out"][0].T + L["out"][1])[:, 0]
        return np.clip(0.5 + f * self.tau * cw * ss, 0, 1).reshape(ch, ss, cw, ss).mean((1, 3))


args = sys.argv[1:]
failed = False
lib_path = args[0]
face_em = 0
if args[1:2] == ["--bundle"]:
    nrt_path, rest, gate_path, fallback, json_paths = args[2], iter(args[3:]), None, 0, []
    for a in rest:
        if a == "--gate":
            gate_path = next(rest)
        elif a == "--fallback":
            fallback = int(next(rest))
        else:
            json_paths.append(a)
    made, table = pack.bundle(json_paths, gate_path, fallback)
    gate = None
    if gate_path:
        with open(gate_path) as fh:
            gdoc = json.load(fh)
        gate = (layers(gdoc), [int(m, 16) for m in gdoc["parity_masks"]])
elif args[1:2] == ["--drawing"] and len(args) == 5:
    nrt_path, json_paths, face_path = args[2], [args[3]], args[4]
    made, table, gate, fallback = pack.drawing([args[3], face_path])[0], [], None, 0
    face = pack.read_face(face_path)
    if face is None:
        raise SystemExit(f"{face_path} is not a pixel face")
    face_em = face[1]
elif len(args) == 3:
    json_paths, nrt_path = [args[1]], args[2]
    made, table, gate, fallback = pack.pack(args[1]), [], None, 0
else:
    raise SystemExit(__doc__)

with open(nrt_path, "rb") as fh:
    if fh.read() != made:
        print("FAIL the packed file is not what pack.py makes from the JSON")
        failed = True
nets = [Net(p) for p in json_paths]


def route(s):
    s = normal(s)
    for first, last, net in table:
        if first <= s <= last:
            return net
    if gate:
        L, masks = gate
        h = np.maximum(code(s, masks) @ L["l1"][0].T + L["l1"][1], 0)
        return int(np.argmax(h @ L["out"][0].T + L["out"][1]))
    return fallback


lib = ctypes.CDLL(os.path.abspath(lib_path))
lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
lib.neuronte_coverage.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_int, ctypes.POINTER(ctypes.c_float)]
lib.neuronte_route.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
lib.neuronte_close.argtypes = [ctypes.c_void_p]
handle = ctypes.c_void_p()
rc = lib.neuronte_open_file(nrt_path.encode(), ctypes.byref(handle))
if rc != 0:
    raise SystemExit(f"neuronte_open_file returned {rc}")

scalars = [0x20, 0x41, 0x67, 0x40, 0x7E, 0x30, 0xE9, 0x2500, 0x256C, 0x2588, 0x2592, 0x28FF,
           0x25C6, 0x4E2D, 0xFFFD, 0x10FFFF, 0xD800,
           # sextants, octants and two of the octant substitutes
           0x1FB00, 0x1FB3B, 0x1CD00, 0x1CD74, 0x1CDE5, 0x1CEA0, 0x1FBE6]
# A few from each range of the table, its ends among them.
for first, last, _ in table[::max(1, len(table) // 12)]:
    scalars += [first, last]
scalars = list(dict.fromkeys(scalars))
routes = 0
# The two Symbols for Legacy Computing blocks, which hold the mosaics.
for s in scalars + list(range(0, 0x3000, 7)) + list(range(0x1CC00, 0x1CEC0, 3)) + list(range(0x1FB00, 0x1FC00, 3)):
    want, got = route(s), lib.neuronte_route(handle, s)
    routes += 1
    if want != got:
        print(f"FAIL U+{s:04X} routed to net {got}, want {want}")
        failed = True
sizes = [(8, 16, 2), (16, 32, 2), (33, 61, 1)] + ([(face_em, 2 * face_em, 2)] if face_em else [])
cases = [(s, cw, ch, ss) for s in scalars for cw, ch, ss in sizes]
worst = 0.0
for s, cw, ch, ss in cases:
    out = (ctypes.c_float * (cw * ch))()
    rc = lib.neuronte_coverage(handle, s, cw, ch, ss, out)
    if rc != 0:
        print(f"FAIL coverage U+{s:04X} {cw}x{ch} returned {rc}")
        failed = True
        continue
    c = np.frombuffer(out, np.float32).reshape(ch, cw).astype(np.float64)
    d = float(np.abs(c - nets[route(s)].coverage(s, cw, ch, ss)).max())
    worst = max(worst, d)
    if d > 1e-3:
        print(f"FAIL U+{s:04X} {cw}x{ch} samples {ss}: C and numpy differ by {d:.2e}")
        failed = True
if face_em:
    import glyphs  # noqa: E402
    em, drawn = face_em, 0
    lib.neuronte_set_binary.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.neuronte_draw_text.argtypes = ([ctypes.c_void_p, ctypes.c_void_p] + [ctypes.c_int] * 7
                                       + [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32])
    lib.neuronte_set_binary(handle, 1)
    W, H, X, Y = 2 * em + 4, 2 * em + 4, 2, 2
    for ch_, (adv, art) in sorted(glyphs.pixel_face(em).items()):
        ink = np.array([[c == "#" for c in r] for r in art])
        for bold in (0, 1):
            want = np.zeros((H, W), bool)
            for dx in range(bold + 1):
                want[Y + glyphs.UI_TOP:Y + glyphs.UI_TOP + em, X + dx:X + dx + ink.shape[1]] |= ink
            buf = np.zeros((H, W), np.uint32)
            text = ch_.encode()
            rc = lib.neuronte_draw_text(handle, buf.ctypes.data, W, W, H, X, Y, em, bold, text, len(text), 0xFFFFFFFF)
            drawn += 1
            if rc != adv + bold:
                print(f"FAIL U+{ord(ch_):04X} weight {bold}: the pen moved {rc}, want {adv + bold}")
                failed = True
            if ((buf != 0) != want).any() or ((buf != 0) & (buf != 0xFFFFFFFF)).any():
                print(f"FAIL U+{ord(ch_):04X} weight {bold}: {int(((buf != 0) != want).sum())} pixels are not the face's")
                failed = True
    print(f"check_reference: {drawn} binary letters at {em} px, each exactly its drawing")
lib.neuronte_close(handle)
print(f"check_reference: {len(cases)} cells, {routes} routes, largest coverage difference {worst:.2e}")
print("check_reference: FAILED" if failed else "check_reference: passed")
sys.exit(1 if failed else 0)
