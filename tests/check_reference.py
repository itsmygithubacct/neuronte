"""Check the C library against an independent numpy evaluation of the net.

usage: python3 tests/check_reference.py LIB.so WEIGHTS.json WEIGHTS.nrt
       python3 tests/check_reference.py LIB.so --bundle BUNDLE.nrt NET.json...
                                        [--gate GATE.json] [--fallback I]
       python3 tests/check_reference.py LIB.so --drawing DRAWING.nrt NET.json FACE.txt
       python3 tests/check_reference.py LIB.so --drawing DRAWING.nrt NET.json ADVANCES.txt

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

For a drawing file of one net and an advances file, such as
font/ui-large-advances.txt, which has no pixels to compare, the net is
checked the same way at larger cells too. Every advance in the file,
regular and bold, must be the steps the packer read from the advances
file, and the pixels it gives at each of the ems in SOFT_EMS. Then
characters drawn blended by neuronte_draw_text() at those ems, regular
and bold, must be the numpy coverage composited the same way, to one
level in 255, and the pen must move by the sum of the advances.
"""
import ctypes
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train"))
import pack  # noqa: E402
import snap  # noqa: E402
import strokes  # noqa: E402


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
        self.colour = doc.get("format") == "neuronte-colour-weights"
        self.records = {}
        self.snap_px = 14
        self.k = 1
        self.doc = doc
        if self.colour:
            self.k = doc["shape"]["glyph_layers"]
            self.head = layers({"layers": doc["head"]})

    def bind(self, info):
        self.records = {scalar: rec for scalar, rec in info["records"]}
        self.snap_px = info["snap"]
        self.info = info

    def entries_of(self, s):
        """Palette index of each layer. A distance net is entry 0."""
        if not self.colour:
            return [0]
        c = code(s, self.masks)
        w, b = self.head["h1"]
        hid = np.maximum(c @ w.T + b, 0)
        ow, ob = self.head["out"]
        logits = hid @ ow.T + ob
        out = []
        for k in range(self.k):
            bits = 0
            for bit in range(5):
                if logits[k * 5 + bit] > 0:
                    bits |= 1 << bit
            out.append(bits)
        return out

    def _samples(self, s, cw, ch, ss, snap):
        rec = self.records.get(normal(s)) if snap else None
        if rec is None:
            xs = (np.arange(cw * ss) + 0.5) / (cw * ss)
            ys = (np.arange(ch * ss) + 0.5) / (ch * ss) * 2
            return xs, ys
        xs = snap_mod.sample_positions(cw, ss, snap_mod.knots([a for a, _ in rec], cw, cw), cw)
        ys = snap_mod.sample_positions(ch, ss, snap_mod.knots([b for _, b in rec], ch / 2, ch), ch / 2)
        return xs, ys

    def _field(self, s, xs, ys):
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
        return h @ L["out"][0].T + L["out"][1]

    def layer_masks(self, s, cw, ch, ss, snap=None):
        """One mask per layer, shape (K, ch, cw), and the palette indices."""
        if snap is None:
            snap = cw < self.snap_px and normal(s) in self.records
        xs, ys = self._samples(s, cw, ch, ss, snap)
        field = self._field(s, xs, ys)
        cov = np.clip(0.5 + field * self.tau * cw * ss, 0, 1)
        cov = cov.reshape(ch, ss, cw, ss, self.k).mean((1, 3))
        return np.moveaxis(cov, -1, 0), self.entries_of(s)

    def coverage(self, s, cw, ch, ss):
        if self.colour:
            masks, ent = self.layer_masks(s, cw, ch, ss)
            return composite_alpha(masks, ent)
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


# The probe module is named snap, which is also a local. Keep the module.
snap_mod = snap


def composite_alpha(masks, entries):
    """Alpha of the layers composited back to front. Entry 1 clears."""
    a = np.zeros(masks.shape[1:], np.float64)
    for k in range(masks.shape[0]):
        c = masks[k]
        if entries[k] == 1:
            a = a * (1 - c)
        else:
            a = c + a * (1 - c)
    return a


def composite_pixels(masks, entries, fg, palette, bg):
    """The cell blended over an opaque background, the way the C draw call does."""
    r = np.zeros(masks.shape[1:])
    g = np.zeros(masks.shape[1:])
    b = np.zeros(masks.shape[1:])
    a = np.zeros(masks.shape[1:])
    for k in range(masks.shape[0]):
        c = masks[k]
        keep = 1 - c
        ent = entries[k]
        if ent == 1:
            r, g, b, a = r * keep, g * keep, b * keep, a * keep
            continue
        if 2 <= ent <= 31:
            ir, ig, ib = (int(x) for x in palette[ent * 3:ent * 3 + 3])
        else:
            ir, ig, ib = fg
        r = ir * c + r * keep
        g = ig * c + g * keep
        b = ib * c + b * keep
        a = c + a * keep
    height, width = a.shape
    out = np.empty((height, width), np.uint32)
    bg_px = 0xFF000000 | (bg[0] << 16) | (bg[1] << 8) | bg[2]
    for y in range(height):
        for x in range(width):
            pa = float(a[y, x])
            if not pa > 0:
                out[y, x] = bg_px
                continue
            src = (int(min(255, max(0, r[y, x] / pa + 0.5))) << 16 |
                   int(min(255, max(0, g[y, x] / pa + 0.5))) << 8 |
                   int(min(255, max(0, b[y, x] / pa + 0.5))))
            out[y, x] = blend_pixel(bg_px, src, pa)
    return out


def blend_pixel(dst, color, a):
    """The C blend(): straight source colour, source-over, round half up."""
    da = (dst >> 24) / 255.0
    oa = a + da * (1.0 - a)
    if oa <= 0:
        return 0
    ch = []
    for sh in (16, 8, 0):
        sc = (color >> sh) & 0xFF
        dc = (dst >> sh) & 0xFF
        ch.append((sc * a + dc * da * (1.0 - a)) / oa)
    return ((int(oa * 255.0 + 0.5) << 24) | (int(ch[0] + 0.5) << 16) |
            (int(ch[1] + 0.5) << 8) | int(ch[2] + 0.5))


args = sys.argv[1:]
failed = False
lib_path = args[0]
face_em = 0
soft_adv = None  # {scalar: (regular, bold)} in steps, for a drawing file with an advances file
SOFT_EMS = (33, 36, 40, 44, 48, 64, 96, 128)
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
        soft_adv = pack.read_advances(face_path)
    else:
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
if len(nets) == 1 and nets[0].colour:
    nets[0].bind(pack.read_colour(made))


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
lib.neuronte_layers.argtypes = [ctypes.c_void_p]
lib.neuronte_layers.restype = ctypes.c_int
lib.neuronte_set_snap.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.neuronte_set_snap.restype = ctypes.c_int
lib.neuronte_set_theme.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.neuronte_set_theme.restype = ctypes.c_int
lib.neuronte_palette.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_uint8)]
lib.neuronte_palette.restype = ctypes.c_int
lib.neuronte_coverage_layers.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_int, ctypes.POINTER(ctypes.c_float),
                                         ctypes.POINTER(ctypes.c_uint8)]
lib.neuronte_coverage_layers.restype = ctypes.c_int
lib.neuronte_draw_scalar.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_int,
                                     ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                     ctypes.c_int, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32]
lib.neuronte_draw_scalar.restype = ctypes.c_int
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
if soft_adv:
    # The face's own characters, at the larger cells it is drawn in.
    cases += [(ord(c), cw, 2 * cw, 1) for c in "Ag@\u2026" for cw in (48, 64)] + [(ord("g"), 96, 192, 1)]
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

if len(nets) == 1 and nets[0].colour:
    net = nets[0]
    info = net.info
    H, K, R = info["hidden_width"], info["layers"], info["head_width"]
    trunk = 2 * H * H + (93 + K) * H + K
    head_n = R * (65 + 5 * K) + 5 * K
    if lib.neuronte_layers(handle) != K:
        print(f"FAIL layers {lib.neuronte_layers(handle)}, file says {K}")
        failed = True
    if info["floats"].size != trunk + head_n:
        print(f"FAIL head shape: {info['floats'].size} floats, trunk {trunk} head {head_n}")
        failed = True
    if info["head_width"] != net.doc["shape"]["head_width"]:
        print("FAIL palette-head width disagrees with the JSON")
        failed = True
    for theme, side in ((0, "dark"), (1, "light")):
        rgb = (ctypes.c_uint8 * 96)()
        if lib.neuronte_palette(handle, theme, rgb) != 0 or bytes(rgb) != info[side]:
            print(f"FAIL {side} palette")
            failed = True
    # The drawing and palette the weights name: font/icons.txt, or another
    # colour drawing such as the Kilix flame.
    drawing_path, palette_path = (os.path.join(pack.ROOT, rel) for rel in pack.colour_sources(net.doc))
    pal = strokes.palette(palette_path)
    icons = strokes.parse_layers(drawing_path, pal)
    saw_edge = False
    for scalar, rec in info["records"]:
        probed = snap_mod.probe(icons[chr(scalar)])
        while len(probed) < K:
            probed.append(([], []))
        for got, want in zip(rec, probed):
            for axis in (0, 1):
                if len(got[axis]) != len(want[axis]):
                    print(f"FAIL U+{scalar:04X} axis {axis} has {len(got[axis])} edges, probe has {len(want[axis])}")
                    failed = True
                    continue
                for (pos, rising), (pp, pr) in zip(got[axis], want[axis]):
                    if pos != float(np.float32(pp)) or rising != int(bool(pr)):
                        print(f"FAIL U+{scalar:04X} edge {pos} {rising} against the probe {pp} {pr}")
                        failed = True
                    else:
                        saw_edge = True
    if not saw_edge:
        print("FAIL the edge table has no edge to round-trip")
        failed = True
    for scalar in net.records:
        drawn = icons[chr(scalar)]
        want = [pal[drawn[i][0]][0] if i < len(drawn) else 0 for i in range(K)]
        if net.entries_of(scalar) != want:
            print(f"FAIL U+{scalar:04X} head returns {net.entries_of(scalar)}, drawings say {want}")
            failed = True
    if net.entries_of(0x41) != [0] * K:
        print(f"FAIL an unlabelled scalar returned {net.entries_of(0x41)}")
        failed = True

    def c_masks(scalar, cw, ch, ss):
        buf = (ctypes.c_float * (K * ch * cw))()
        ent = (ctypes.c_uint8 * K)()
        rc = lib.neuronte_coverage_layers(handle, scalar, cw, ch, ss, buf, ent)
        if rc != 0:
            print(f"FAIL coverage_layers U+{scalar:04X} {cw}x{ch} returned {rc}")
            return None, None
        arr = np.frombuffer(buf, np.float32).reshape(K, ch, cw).copy()
        return arr, [ent[i] for i in range(K)]

    themes = {0: ((0x11, 0x15, 0x1C), (0xE9, 0xE6, 0xDF)),
              1: ((0xFA, 0xFA, 0xF7), (0x1E, 0x23, 0x30))}
    # 12 px is under the file threshold. 16 px is not, unless the threshold is raised.
    for cw, snap_on, snap_off in ((12, -1, 0), (16, 17, -1)):
        ch, ss = cw * 2, 2
        for scalar in net.records:
            for snapping, threshold in ((True, snap_on), (False, snap_off)):
                if lib.neuronte_set_snap(handle, threshold) != 0:
                    print(f"FAIL set_snap({threshold})")
                    failed = True
                    continue
                got, ent = c_masks(scalar, cw, ch, ss)
                if got is None:
                    failed = True
                    continue
                want_m, want_e = net.layer_masks(scalar, cw, ch, ss, snap=snapping)
                if ent != want_e:
                    print(f"FAIL U+{scalar:04X} {cw}px snap {snapping} entries {ent}, want {want_e}")
                    failed = True
                d = float(np.abs(got.astype(np.float64) - want_m).max())
                worst = max(worst, d)
                if d > 1e-3:
                    print(f"FAIL U+{scalar:04X} {cw}px snap {snapping}: masks differ by {d:.2e}")
                    failed = True
                for theme, (bg, fg) in themes.items():
                    if lib.neuronte_set_theme(handle, theme) != 0:
                        print(f"FAIL set_theme({theme})")
                        failed = True
                        continue
                    pix = (ctypes.c_uint32 * (ch * cw))()
                    bg_px = 0xFF000000 | (bg[0] << 16) | (bg[1] << 8) | bg[2]
                    fg_px = 0xFF000000 | (fg[0] << 16) | (fg[1] << 8) | fg[2]
                    for i in range(ch * cw):
                        pix[i] = bg_px
                    rc = lib.neuronte_draw_scalar(handle, pix, cw, cw, ch, 0, 0, cw, ch, scalar, fg_px)
                    if rc != 0:
                        print(f"FAIL draw U+{scalar:04X} returned {rc}")
                        failed = True
                        continue
                    ref = composite_pixels(want_m, want_e, fg, info["dark" if theme == 0 else "light"], bg)
                    drawn = np.frombuffer(pix, np.uint32).reshape(ch, cw).copy()
                    channels = []
                    for shift in (24, 16, 8, 0):
                        channels.append(np.abs(((drawn >> shift) & 0xFF).astype(int) -
                                               ((ref >> shift) & 0xFF).astype(int)).max())
                    if max(channels) > 1:
                        print(f"FAIL U+{scalar:04X} {cw}px theme {theme} snap {snapping}: "
                              f"pixels differ by {max(channels)} levels")
                        failed = True
    # U+F04C, the paused icon, sits on whole pixels at 16 px. A drawing
    # without it, such as the flame, skips this check.
    if 0xF04C in net.records:
        if lib.neuronte_set_snap(handle, 0) != 0:
            print("FAIL set_snap(0) for the grid-aligned icon")
            failed = True
        else:
            off, _ = c_masks(0xF04C, 16, 32, 2)
            if lib.neuronte_set_snap(handle, 17) != 0:
                print("FAIL set_snap(17) for the grid-aligned icon")
                failed = True
            else:
                on, _ = c_masks(0xF04C, 16, 32, 2)
                if off is None or on is None or off.tobytes() != on.tobytes():
                    print("FAIL a grid-aligned icon changed at 16 px with snapping on")
                    failed = True
if face_em:
    import glyphs  # noqa: E402
    em, drawn = face_em, 0
    lib.neuronte_set_binary.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.neuronte_draw_text.argtypes = ([ctypes.c_void_p, ctypes.c_void_p] + [ctypes.c_int] * 7
                                       + [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32])
    lib.neuronte_set_binary(handle, 1)
    W, H, X, Y = 2 * em + 4, 2 * em + 4, 2, 2
    for ch_, (adv, art) in sorted(glyphs.pixel_face(em, face_path).items()):
        ink = np.array([[c == "#" for c in r] for r in art])
        for bold in (0, 1):
            want = np.zeros((H, W), bool)
            for dx in range(bold + 1):
                want[Y + glyphs.UI_TOP[em]:Y + glyphs.UI_TOP[em] + em, X + dx:X + dx + ink.shape[1]] |= ink
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
if soft_adv:
    lib.neuronte_advance_steps.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int]
    lib.neuronte_advance.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int]
    lib.neuronte_advance_scalar.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    lib.neuronte_advance_scalar.restype = ctypes.c_uint32
    lib.neuronte_advances.argtypes = [ctypes.c_void_p]
    lib.neuronte_text_width.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
    lib.neuronte_set_binary.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.neuronte_draw_text.argtypes = ([ctypes.c_void_p, ctypes.c_void_p] + [ctypes.c_int] * 7
                                       + [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32])
    if lib.neuronte_advances(handle) != len(soft_adv):
        print(f"FAIL the file has {lib.neuronte_advances(handle)} advances, the advances file {len(soft_adv)}")
        failed = True
    measured = 0
    for v, steps in sorted(soft_adv.items()):
        for bold in (0, 1):
            got = lib.neuronte_advance_steps(handle, v, bold)
            if got != steps[bold]:
                print(f"FAIL U+{v:04X} weight {bold}: {got} steps, the advances file says {steps[bold]}")
                failed = True
            for em in SOFT_EMS:
                got = lib.neuronte_advance(handle, v, bold, em)
                measured += 1
                if got != pack.pixels(steps[bold], em):
                    print(f"FAIL U+{v:04X} weight {bold} at {em} px: {got} pixels, the packer says "
                          f"{pack.pixels(steps[bold], em)}")
                    failed = True
    for v in (0x4E2D, 0x7F, 0xE9):
        if v not in soft_adv and lib.neuronte_advance_scalar(handle, v) != 0x3F:
            print(f"FAIL U+{v:04X} is not measured as the fallback U+003F")
            failed = True
    lib.neuronte_set_binary(handle, 0)
    net = nets[0]
    texts = ["A", "g", "@", "W", "\u2026", "Ag"]
    drawn = 0
    for em in (36, 48, 64):
        for text in texts:
            for bold in (0, 1):
                X, Y = 3, 2
                pens = [X]
                for c in text[:-1]:
                    pens.append(pens[-1] + pack.pixels(soft_adv[ord(c)][bold], em))
                total = pens[-1] - X + pack.pixels(soft_adv[ord(text[-1])][bold], em)
                W, H = pens[-1] + em + 2 + 3, 2 * em + 4
                want = np.zeros((H, W))
                for c, x in zip(text, pens):
                    cov = net.coverage(ord(c), em, 2 * em, 1)
                    if bold:
                        wide = np.zeros((2 * em, em + 1))
                        wide[:, :em] = cov
                        wide[:, 1:] = np.maximum(wide[:, 1:], cov)
                        cov = wide
                    area = want[Y:Y + 2 * em, x:x + cov.shape[1]]
                    area[:] = cov + area * (1 - cov)
                buf = np.zeros((H, W), np.uint32)
                data = text.encode()
                rc = lib.neuronte_draw_text(handle, buf.ctypes.data, W, W, H, X, Y, em, bold, data, len(data),
                                            0xFFFFFFFF)
                drawn += 1
                width = lib.neuronte_text_width(handle, data, len(data), bold, em)
                if rc != total or width != total:
                    print(f"FAIL {text!r} weight {bold} at {em} px: the pen moved {rc} and the width is {width}, "
                          f"want {total}")
                    failed = True
                d = int(np.abs((buf >> 24).astype(int) - np.floor(want * 255 + 0.5).astype(int)).max())
                if d > 1:
                    print(f"FAIL {text!r} weight {bold} at {em} px: alpha differs by {d} levels")
                    failed = True
    print(f"check_reference: {measured} advances at {len(SOFT_EMS)} ems as packed, "
          f"{drawn} lines drawn blended as numpy composites them")
lib.neuronte_close(handle)
print(f"check_reference: {len(cases)} cells, {routes} routes, largest coverage difference {worst:.2e}")
print("check_reference: FAILED" if failed else "check_reference: passed")
sys.exit(1 if failed else 0)
