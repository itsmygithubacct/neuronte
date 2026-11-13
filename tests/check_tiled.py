"""Check tiled (version 6) nets: the packer, the C runtime and an
independent NumPy evaluation (tests/tiled_reference.py).

usage: python3 tests/check_tiled.py LIB.so [--stream STREAM_LIB.so]
                                    [--tiled TILED.json TILED.nrt]...

With no files it builds its own fixtures from small random nets: a whole
wrapper of each, which must draw bit for bit what the net draws alone;
grids with uneven edges, shared nets, place and extract codes; an
identity mapping across 64 nets, as an ASCII split would use; and a
16 x 16 grid whose tiles get no samples at small cells. The C coverage
must agree with float64 NumPy to TOL at sizes from 1 x 1 to 64 x 128,
with 1, 2, 3 and automatic samples. A bundle with a tiled member must
route and draw through it. Malformed tiled JSON must be refused by the
packer.

--stream names a build with NEURONTE_TILE_KEEP_MAX=0, which evaluates
every sample where it is summed instead of keeping each tile's samples.
Its coverage must be bit for bit the same. --tiled adds trained files,
each checked against the reference on every glyph of its range at 8 x 16
and 16 x 32 and on a spread of glyphs at the other sizes.
"""
import copy
import ctypes as C
import json
import os
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "train"))
sys.path.insert(0, str(ROOT / "tests"))
import pack  # noqa: E402
import strokes  # noqa: E402
from tiled_reference import Distance, Tiled  # noqa: E402

TOL = 1e-4
SIZES = [(1, 1), (1, 2), (2, 4), (3, 6), (4, 8), (5, 10), (7, 13), (8, 16), (9, 17), (10, 21), (11, 23),
         (16, 32), (17, 35), (23, 46), (23, 47), (24, 48), (25, 49), (25, 50), (16, 16), (32, 16),
         (12, 40), (33, 61), (48, 96), (64, 128)]
SAMPLES = (0, 1, 2, 3)
failed = False


def fail(msg):
    global failed
    print("FAIL", msg)
    failed = True


def f32(v):
    return float(np.float32(v))


def fixture(width, seed, labelled="U+2800..U+28FF", set_name="braille", tau=.15):
    rng = np.random.default_rng(seed)
    layers = {}
    for name, rows, cols in pack.layers(width):
        layers[name] = {"rows": rows, "cols": cols,
                        "weight": rng.normal(0, .6 if name == "l1" else .4, (rows, cols)).astype(np.float32).ravel().tolist(),
                        "bias": rng.normal(0, .2, rows).astype(np.float32).tolist()}
    return {"format": "neuronte-weights", "version": 1,
            "shape": {"position_octaves": 6, "code_bits": 64, "hidden_layers": 3,
                      "hidden_width": width, "tau": f32(tau),
                      "parity_masks": [hex(m) for m in strokes.masks()]},
            "layers": layers, "training": {"set": set_name, "labelled": labelled}}


def tiled(columns, rows, tiles, nets, first="U+2800", last="U+28FF", set_name="braille",
          labelled="U+2800..U+28FF"):
    return {"format": "neuronte-tiled-weights", "version": 1,
            "training": {"set": set_name, "labelled": labelled},
            "first": first, "last": last, "columns": [f32(e) for e in columns], "rows": [f32(e) for e in rows],
            "tiles": tiles, "nets": nets}


def tile(net, mask, base="U+2800", code="place"):
    return {"net": net, "mask": mask, "base": base, "code": code}


def fixtures():
    """(name, tiled JSON document, scalars to try, sizes)."""
    nets = [fixture(w, 10 + i) for i, w in enumerate((1, 3, 4, 7, 8))]
    braille = list(range(0x2800, 0x2900, 37)) + [0x2800, 0x28FF, 0x2855, 0x28AA]
    out = []
    for i, n in enumerate(nets):
        out.append((f"whole-h{n['shape']['hidden_width']}",
                    tiled([0, 1], [0, 2], [tile(0, "0xFF")], [n]), braille, SIZES))
    uneven_x, uneven_y = [0, .3, .7, 1], [0, .37, 1.1, 1.5, 2]
    out.append(("uneven-place", tiled(uneven_x, uneven_y,
                                      [tile(k % 5, hex(1 << (k % 8))) for k in range(12)], nets), braille, SIZES))
    out.append(("uneven-extract-shared",
                tiled(uneven_x, uneven_y,
                      [tile(k % 2, hex((0x3 << (k % 7)) & 0xFF), "U+2800" if k % 3 else "U+0041", "extract")
                       for k in range(12)], nets[1:3]), braille, SIZES))
    out.append(("dots-shared", tiled([0, .5, 1], [0, .5, 1, 1.5, 2],
                                     [tile(0, m, code="extract") for m in
                                      ("0x01", "0x08", "0x02", "0x10", "0x04", "0x20", "0x40", "0x80")],
                                     [nets[3]]), braille, SIZES))
    # A range that starts inside the masks: codes come from scalar - first.
    out.append(("offset-origin", tiled([0, .5, 1], [0, 2],
                                       [tile(0, "0x0F", "U+2800"), tile(1, "0x07", "U+0040")], nets[2:4],
                                       first="U+2803"), [0x2803, 0x2804, 0x280A, 0x2811, 0x28FF, 0x27FF], SIZES[::2]))
    many = [fixture(1 + i % 3, 100 + i, set_name="ascii", labelled="U+0020..U+007E") for i in range(64)]
    ascii_x = [i / 16 for i in range(17)]
    out.append(("identity-64", tiled(ascii_x, [0, .5, 1, 1.5, 2],
                                     [tile(k, "0x1FFFFF", "U+0000") for k in range(64)], many,
                                     first="U+0000", last="U+007F", set_name="ascii", labelled="U+0020..U+007E"),
                list(range(0x20, 0x7F, 9)) + [0x7E, 0x2800, 0xD800, 0x110000], SIZES[::3]))
    grid = [i / 16 for i in range(17)]
    out.append(("grid-16x16", tiled(grid, [2 * g for g in grid],
                                    [tile(k % 3, hex(k & 0xFF), code="extract" if k % 2 else "place") for k in range(256)],
                                    nets[:3]), braille[:3], SIZES[::4]))
    return out


lib_path = None
stream_path = None
extra = []
args = iter(sys.argv[1:])
for a in args:
    if a == "--stream":
        stream_path = next(args)
    elif a == "--tiled":
        extra.append((next(args), next(args)))
    elif lib_path is None:
        lib_path = a
    else:
        raise SystemExit(__doc__)
if lib_path is None:
    raise SystemExit(__doc__)


def load(path):
    lib = C.CDLL(os.path.abspath(path))
    lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(C.c_void_p)]
    lib.neuronte_open.argtypes = [C.c_void_p, C.c_size_t, C.POINTER(C.c_void_p)]
    lib.neuronte_close.argtypes = [C.c_void_p]
    lib.neuronte_coverage.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_int, C.c_int, C.POINTER(C.c_float)]
    lib.neuronte_route.argtypes = [C.c_void_p, C.c_uint32]
    lib.neuronte_nets.argtypes = [C.c_void_p]
    lib.neuronte_parameters.argtypes = [C.c_void_p]
    lib.neuronte_parameters.restype = C.c_size_t
    lib.neuronte_set_binary.argtypes = [C.c_void_p, C.c_int]
    lib.neuronte_set_samples.argtypes = [C.c_void_p, C.c_int]
    lib.neuronte_draw_scalar.argtypes = [C.c_void_p, C.POINTER(C.c_uint32), C.c_int, C.c_int, C.c_int,
                                         C.c_int, C.c_int, C.c_int, C.c_int, C.c_uint32, C.c_uint32]
    return lib


LIB = load(lib_path)
STREAM = load(stream_path) if stream_path else None


def open_file(lib, path):
    h = C.c_void_p()
    rc = lib.neuronte_open_file(str(path).encode(), C.byref(h))
    if rc != 0:
        raise SystemExit(f"neuronte_open_file({path}) returned {rc}")
    return h


def coverage(lib, h, s, cw, ch, ss):
    buf = (C.c_float * (cw * ch))()
    rc = lib.neuronte_coverage(h, s, cw, ch, ss, buf)
    if rc != 0:
        raise SystemExit(f"neuronte_coverage U+{s:04X} {cw}x{ch} {ss} returned {rc}")
    return np.frombuffer(buf, np.float32).reshape(ch, cw).copy()


def auto(cw):
    return 2 if cw < 24 else 1


def params(width):
    return 2 * width * width + 94 * width + 1


def check_layout(name, doc, image):
    """The packed bytes, read back by the format's own description."""
    if image[:8] != b"NEURONTE":
        fail(f"{name}: magic")
        return
    version, cols, rows, m, first, last = struct.unpack_from("<6I", image, 8)
    want = (6, len(doc["columns"]) - 1, len(doc["rows"]) - 1, len(doc["nets"]),
            int(doc["first"][2:], 16), int(doc["last"][2:], 16))
    if (version, cols, rows, m, first, last) != want:
        fail(f"{name}: header {(version, cols, rows, m, first, last)} != {want}")
    off = 32
    xs = struct.unpack_from(f"<{cols + 1}f", image, off); off += 4 * (cols + 1)
    ys = struct.unpack_from(f"<{rows + 1}f", image, off); off += 4 * (rows + 1)
    if list(xs) != doc["columns"] or list(ys) != doc["rows"]:
        fail(f"{name}: edges")
    for k, t in enumerate(doc["tiles"]):
        rec = struct.unpack_from("<4I", image, off); off += 16
        want = (t["net"], int(t["mask"], 16), int(t["base"][2:], 16), int(t["code"] == "extract"))
        if rec != want:
            fail(f"{name}: tile {k} {rec} != {want}")
    lengths = struct.unpack_from(f"<{m}I", image, off); off += 4 * m
    for i, net in enumerate(doc["nets"]):
        member = image[off:off + lengths[i]]
        if lengths[i] != 204 + 4 * params(net["shape"]["hidden_width"]) or struct.unpack_from("<I", member, 8)[0] != 1:
            fail(f"{name}: net {i} is not a version 1 image of its width")
        off += lengths[i]
    if off != len(image):
        fail(f"{name}: {len(image) - off} trailing bytes")


def compare(name, h, ref, scalars, sizes, stream_h=None, tol=TOL):
    worst, n = 0.0, 0
    for s in scalars:
        for cw, chh in sizes:
            for ss in SAMPLES:
                got = coverage(LIB, h, s, cw, chh, ss)
                want = ref.coverage(s, cw, chh, ss or auto(cw))
                d = float(np.abs(got - want).max())
                worst = max(worst, d)
                n += 1
                if d > tol:
                    fail(f"{name} U+{s:04X} {cw}x{chh} samples {ss}: C and NumPy differ by {d:.2e}")
                if stream_h is not None:
                    other = coverage(STREAM, stream_h, s, cw, chh, ss)
                    if other.tobytes() != got.tobytes():
                        fail(f"{name} U+{s:04X} {cw}x{chh} samples {ss}: kept and streamed samples differ")
    return worst, n


def refused(doc, expect, what):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(doc, fh)
    try:
        pack.pack(fh.name)
    except SystemExit as e:
        if expect not in str(e):
            fail(f"packer refused {what} with {e!r}, expected {expect!r}")
        return
    finally:
        os.unlink(fh.name)
    fail(f"packer accepted {what}")


with tempfile.TemporaryDirectory(prefix="neuronte-tiled-") as tmp:
    tmp = Path(tmp)
    total = 0
    for name, doc, scalars, sizes in fixtures():
        src = tmp / f"{name}.json"
        src.write_text(json.dumps(doc))
        image = pack.pack(str(src))
        check_layout(name, doc, image)
        nrt = tmp / f"{name}.nrt"
        nrt.write_bytes(image)
        h = open_file(LIB, nrt)
        sh = open_file(STREAM, nrt) if STREAM else None
        if LIB.neuronte_nets(h) != 1:
            fail(f"{name}: a tiled file is one net, got {LIB.neuronte_nets(h)}")
        want_params = sum(params(n["shape"]["hidden_width"]) for n in doc["nets"])
        if LIB.neuronte_parameters(h) != want_params:
            fail(f"{name}: parameters {LIB.neuronte_parameters(h)} != {want_params}")
        mem = C.create_string_buffer(image, len(image))
        hm = C.c_void_p()
        if LIB.neuronte_open(mem, len(image), C.byref(hm)) != 0:
            fail(f"{name}: neuronte_open refused the image neuronte_open_file took")
        worst, n = compare(name, h, Tiled(doc), scalars, sizes, sh)
        total += n
        for s in scalars[:3]:
            if coverage(LIB, hm, s, 9, 17, 2).tobytes() != coverage(LIB, h, s, 9, 17, 2).tobytes():
                fail(f"{name}: memory and file handles differ")
        if name.startswith("whole-"):
            # The wrapper must be the net itself, bit for bit, at every size.
            alone = tmp / f"{name}-alone.nrt"
            alone.write_bytes(pack.image_v1(*pack.load_doc(doc["nets"][0], name)))
            ha = open_file(LIB, alone)
            for s in scalars:
                for cw, chh in SIZES:
                    for ss in SAMPLES:
                        if coverage(LIB, ha, s, cw, chh, ss).tobytes() != coverage(LIB, h, s, cw, chh, ss).tobytes():
                            fail(f"{name} U+{s:04X} {cw}x{chh} samples {ss}: wrapper differs from the net")
            # A cell past the keep limit is evaluated where it is summed.
            for cw, chh, ss in ((1100, 2200, 2), (4096, 4, 1)):
                if coverage(LIB, ha, 0x28FF, cw, chh, ss).tobytes() != coverage(LIB, h, 0x28FF, cw, chh, ss).tobytes():
                    fail(f"{name} {cw}x{chh} samples {ss}: wrapper differs from the net past the keep limit")
            # Drawing through the cache: cold, then warm, then the net alone.
            draws = []
            for handle in (h, h, ha):
                LIB.neuronte_set_samples(handle, 0)
                canvas = (C.c_uint32 * (40 * 40))()
                for k, s in enumerate(scalars[:4]):
                    rc = LIB.neuronte_draw_scalar(handle, canvas, 40, 40, 40, 1 + 9 * k, 3, 9, 17, s, 0xFFC0A080)
                    if rc != 0:
                        fail(f"{name}: draw returned {rc}")
                draws.append(bytes(canvas))
            if draws[0] != draws[1] or draws[0] != draws[2]:
                fail(f"{name}: cold, warm and untiled drawing differ")
            LIB.neuronte_close(ha)
        else:
            # Binary drawing must be the tiled coverage's own cut.
            LIB.neuronte_set_binary(h, 1)
            LIB.neuronte_set_samples(h, 0)
            for s in scalars[:4]:
                for cw, chh in ((8, 16), (25, 49)):
                    canvas = (C.c_uint32 * (cw * chh))()
                    LIB.neuronte_draw_scalar(h, canvas, cw, cw, chh, 0, 0, cw, chh, s, 0xFFFFFFFF)
                    ink = np.frombuffer(canvas, np.uint32).reshape(chh, cw) != 0
                    if not np.array_equal(ink, coverage(LIB, h, s, cw, chh, 0) > .5):
                        fail(f"{name} U+{s:04X} {cw}x{chh}: binary drawing is not the coverage cut")
        print(f"{name}: {len(doc['nets'])} net(s), {len(doc['tiles'])} tiles, {n} cases, worst {worst:.2e}")
        LIB.neuronte_close(h)
        LIB.neuronte_close(hm)
        if sh:
            STREAM.neuronte_close(sh)

    # A bundle: a distance net for ASCII, the tiled net for Braille.
    ascii_net = fixture(4, 77, labelled="U+0020..U+007E", set_name="ascii")
    braille = fixtures()[7][1]
    paths = []
    for nm, d in (("ascii", ascii_net), ("braille", braille)):
        p = tmp / f"bundle-{nm}.json"
        p.write_text(json.dumps(d))
        paths.append(str(p))
    made, table = pack.bundle(paths)
    (tmp / "bundle.nrt").write_bytes(made)
    hb = open_file(LIB, tmp / "bundle.nrt")
    ref_b, ref_a = Tiled(braille), Distance(ascii_net)
    for s, net in ((0x41, 0), (0x2800, 1), (0x28C3, 1), (0x28FF, 1)):
        if LIB.neuronte_route(hb, s) != net:
            fail(f"bundle routes U+{s:04X} to {LIB.neuronte_route(hb, s)}, want {net}")
    for cw, chh in ((8, 16), (23, 47)):
        d = float(np.abs(coverage(LIB, hb, 0x28C3, cw, chh, 0) - ref_b.coverage(0x28C3, cw, chh, auto(cw))).max())
        if d > TOL:
            fail(f"bundle member coverage differs by {d:.2e}")
    if LIB.neuronte_parameters(hb) != params(4) + sum(params(n["shape"]["hidden_width"]) for n in braille["nets"]):
        fail("bundle parameters")
    LIB.neuronte_close(hb)
    print("bundle: route, member coverage and parameters checked")

    # Packer validation.
    base = fixtures()[7][1]
    bad = []
    d = copy.deepcopy(base); d["version"] = 2; bad.append((d, "not a version 1 tiled", "version 2"))
    d = copy.deepcopy(base); d["first"] = "U+2900"; bad.append((d, "increasing 21-bit", "first after last"))
    d = copy.deepcopy(base); d["last"] = "U+200000"; bad.append((d, "increasing 21-bit", "last past U+1FFFFF"))
    d = copy.deepcopy(base); d["first"] = True; bad.append((d, "is not U+XXXX", "boolean first"))
    d = copy.deepcopy(base); d["columns"] = [0, .3, 1]; bad.append((d, "exact float32", "inexact edge"))
    d = copy.deepcopy(base); d["columns"] = [0, .5, .5, 1]; bad.append((d, "rise strictly", "repeated edge"))
    d = copy.deepcopy(base); d["columns"] = [.25, .5, 1]; bad.append((d, "rise strictly", "first edge not 0"))
    d = copy.deepcopy(base); d["rows"] = [0, 1, 1.5]; bad.append((d, "rise strictly", "last row edge not 2"))
    d = copy.deepcopy(base); d["columns"] = [0, 1]; bad.append((d, "need 4 tiles", "tile count"))
    d = copy.deepcopy(base); d["columns"] = [i / 17 for i in range(18)]; bad.append((d, "2 to 17 edges", "17 columns"))
    d = copy.deepcopy(base); d["nets"] = []; bad.append((d, "1 to 64", "no nets"))
    d = copy.deepcopy(base); d["nets"] = d["nets"] * 65; bad.append((d, "1 to 64", "65 nets"))
    d = copy.deepcopy(base); d["nets"] = d["nets"] * 9; bad.append((d, "more nets than tiles", "9 nets for 8 tiles"))
    d = copy.deepcopy(base); d["tiles"][3]["net"] = 1; bad.append((d, "is not one of", "net index"))
    d = copy.deepcopy(base); d["tiles"][3]["net"] = True; bad.append((d, "is not one of", "boolean net index"))
    d = copy.deepcopy(base); d["tiles"][3]["mask"] = "0x200000"; bad.append((d, "21-bit", "wide mask"))
    d = copy.deepcopy(base); d["tiles"][3]["code"] = "spread"; bad.append((d, "place or extract", "unknown code"))
    d = copy.deepcopy(base); d["tiles"][3]["extra"] = 1; bad.append((d, "exactly net, mask", "extra key"))
    d = copy.deepcopy(base); d["tiles"][3].update(base="U+1FFFFF", mask="0x3"); bad.append((d, "pass U+1FFFFF", "extract overflow"))
    d = copy.deepcopy(base); d["nets"] = d["nets"] * 2; bad.append((d, "draw no tile", "unused net"))
    d = copy.deepcopy(base); d["nets"][0]["version"] = 2; bad.append((d, "not a version 1", "bad member"))
    for doc, expect, what in bad:
        refused(doc, expect, what)
    print(f"packer: {len(bad)} malformed files refused")

    for js, nrt in extra:
        doc = json.loads(Path(js).read_text())
        if Path(nrt).read_bytes() != pack.pack(js):
            fail(f"{nrt} is not what pack.py makes from {js}")
        h = open_file(LIB, nrt)
        sh = open_file(STREAM, nrt) if STREAM else None
        first, last = int(doc["first"][2:], 16), int(doc["last"][2:], 16)
        ref = Tiled(doc)
        every = list(range(first, last + 1))
        w1, n1 = compare(Path(nrt).name, h, ref, every, [(8, 16), (16, 32)], sh)
        w2, n2 = compare(Path(nrt).name, h, ref, every[::17] + [last], SIZES, sh)
        total += n1 + n2
        print(f"{Path(nrt).name}: {n1 + n2} cases, worst {max(w1, w2):.2e}")
        LIB.neuronte_close(h)
        if sh:
            STREAM.neuronte_close(sh)

if failed:
    sys.exit(1)
print(f"check_tiled: {total} coverage cases against NumPy{' and the streaming build' if STREAM else ''}, "
      "wrappers, bundle and packer validation passed")
