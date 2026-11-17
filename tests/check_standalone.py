"""A standalone bundle of group nets: routes, pixels, the blank net, refusals.

usage: python3 tests/check_standalone.py build/libneuronte.so

Built here from the two shipped neuronte-tgreek-v1 group nets, which
split-v9 also holds. A trained scalar goes to its net and draws exactly as
that net alone and as split-v9 draws it. Any other scalar goes to the blank
net, is reported untrained, draws an empty cell at every size, and in mode
1 draws the library's untrained mark. The packer refuses a list that is
not the nets' scalars, a net given twice, and a bundle it must stay apart
from that already has a listed scalar.
"""
import ctypes as C
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "train"))
import pack  # noqa: E402
import standalone_bundle as sb  # noqa: E402

lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
P, F = C.c_void_p, C.POINTER(C.c_float)
lib.neuronte_open.argtypes = [C.c_void_p, C.c_size_t, C.POINTER(P)]
lib.neuronte_close.argtypes = [P]
lib.neuronte_route.argtypes = [P, C.c_uint32]
lib.neuronte_untrained.argtypes = [P, C.c_uint32]
lib.neuronte_set_untrained.argtypes = [P, C.c_int]
lib.neuronte_coverage.argtypes = [P, C.c_uint32, C.c_int, C.c_int, C.c_int, F]
lib.neuronte_coverage_styled.argtypes = [P, C.c_uint32, C.c_int, C.c_int, C.c_int, C.c_uint, F]
SIZES = ((1, 2), (3, 6), (6, 12), (8, 16), (9, 17), (16, 32), (48, 96))
keep = []


def opened(data):
    h = P()
    keep.append(data)
    assert lib.neuronte_open(data, len(data), C.byref(h)) == 0
    return h


def cover(h, s, w, hh, samples=0):
    buf = (C.c_float * (w * hh))()
    assert lib.neuronte_coverage(h, s, w, hh, samples, buf) == 0
    return np.frombuffer(buf, np.float32).copy()


def drawn(h, s, w, hh):
    """The cell as the draw calls see it, which is where mode 1 applies."""
    buf = (C.c_float * (w * hh))()
    assert lib.neuronte_coverage_styled(h, s, w, hh, 0, 0, buf) == 0
    return np.frombuffer(buf, np.float32).copy()


def refused(what, *args):
    try:
        sb.standalone(*args)
    except SystemExit as e:
        assert str(e), what
        return str(e)
    raise AssertionError(f"accepted: {what}")


nets = [str(ROOT / f"weights/neuronte-tgreek-v1-g{g}.json") for g in (0, 1)]
owner = {v: i for i, p in enumerate(nets) for v in pack.scalars(p)[1]}
listed = sorted(owner)
assert len(listed) == 20
image, record = sb.standalone(nets, listed)
again, _ = sb.standalone(nets, list(reversed(listed)))
assert image == again, "the bundle depends on the list's order"
assert record["sha256"] == sb.digest(image) and record["bytes"] == len(image)
assert record["members"] == 3 and record["group_nets"] == 2 and record["trained_scalars"] == 20
assert record["fallback"] == {"member": 2, "kind": "blank", "hidden_width": 1, "distance": sb.BLANK,
                              "image_sha256": sb.digest(sb.blank()), "bytes": pack.length(1)}
assert sb.read_table(image) == owner

v9 = (ROOT / "weights/neuronte-split-v9.nrt").read_bytes()
v9_table = sb.read_table(v9)
assert set(listed) <= set(v9_table)
bundle, split, alone = opened(image), opened(v9), [opened(pack.pack_v1(p)) for p in nets]
probes = (set(range(0, 0x110000, 257)) | {0, 0x20, 0x41, 0x7F, 0x385, 0x387, 0x3AD + 0x100, 0x1F00, 0x2500,
                                           0xD7FF, 0xD800, 0xDFFF, 0xE000, 0xFFFD, 0x10FFFF, 0x110000,
                                           0xFFFFFFFF}) - set(listed)
unknown = next(s for s in (0x0E01, 0x0E02, 0x1234) if s not in v9_table)
try:
    for mode in (0, 1):
        assert lib.neuronte_set_untrained(bundle, mode) == 0
        for s in listed:
            assert lib.neuronte_route(bundle, s) == owner[s]
            assert lib.neuronte_untrained(bundle, s) == 0
            for w, hh in SIZES:
                a = cover(bundle, s, w, hh)
                assert a.tobytes() == cover(alone[owner[s]], s, w, hh).tobytes(), (hex(s), w, hh)
                assert a.tobytes() == cover(split, s, w, hh).tobytes(), (hex(s), w, hh)
                assert drawn(bundle, s, w, hh).tobytes() == drawn(split, s, w, hh).tobytes()
        for s in probes:
            assert lib.neuronte_route(bundle, s) == 2, hex(s)
            assert lib.neuronte_untrained(bundle, s) == 1, hex(s)
    # The blank net: no ink at any size or sampling.
    lib.neuronte_set_untrained(bundle, 0)
    for s in sorted(probes)[::7] + [0x41, 0x1F00, 0xFFFD]:
        for w, hh in SIZES + ((2, 4), (5, 10), (7, 13), (24, 48), (64, 128)):
            for samples in (0, 1, 3):
                assert not cover(bundle, s, w, hh, samples).any(), (hex(s), w, hh, samples)
            assert not drawn(bundle, s, w, hh).any()
    # Mode 1: the library's mark, the one split-v9 draws for a scalar it lacks.
    lib.neuronte_set_untrained(bundle, 1)
    lib.neuronte_set_untrained(split, 1)
    for w, hh in SIZES:
        mark = drawn(split, unknown, w, hh)
        for s in (0x41, 0x1F00, 0x2500, 0x10FFFF):
            assert drawn(bundle, s, w, hh).tobytes() == mark.tobytes(), (hex(s), w, hh)
    assert drawn(split, unknown, 8, 16).any()
finally:
    for h in [bundle, split, *alone]:
        lib.neuronte_close(h)

assert "not the list" in refused("a list one short", nets, listed[:-1])
assert "not the list" in refused("a list one long", nets, listed + [0x41])
assert "is in both" in refused("a net twice", nets + nets[:1], listed)
assert "already has 20" in refused("apart from split-v9", nets, listed, [str(ROOT / "weights/neuronte-split-v9.nrt")])
assert "no table" in refused("apart from a single net", nets, listed, [str(ROOT / "weights/neuronte-accent-v2.nrt")])
with tempfile.TemporaryDirectory(prefix="standalone-") as tmp:
    path = Path(tmp) / "x.list.txt"
    path.write_text("# a list\nU+0386 U+0388..U+038A  # three\nU+038C\n")
    assert sb.read_list(str(path)) == [0x386, 0x388, 0x389, 0x38A, 0x38C]
    for bad in ("U+0041 U+0041\n", "U+0042..U+0041\n", "0041\n", "U+D800\n", "# nothing\n"):
        path.write_text(bad)
        try:
            sb.read_list(str(path))
        except SystemExit:
            pass
        else:
            raise AssertionError(f"accepted a bad list: {bad!r}")
print(f"standalone bundle: 20 scalars to 2 nets exactly as split-v9 draws them, {len(probes)} others blank and "
      "reported untrained, the mark in mode 1, 5 refusals")
