"""Check split-v7-symbol-v1: split-v7 with the symbol-v1 group nets.

usage: python3 tests/check_split_v7_symbol.py LIB.so

split-v7-symbol-v1 is train/known_bundle.py applied to split-v7 with the four
neuronte-symbol-v1 group nets as known-only replacements for expert 2 (the
original symbol expert). It must be, at once:

1. Reproducible: rebuilt byte for byte from split-v7 and the group JSON.
2. split-v7 everywhere else: the same member count plus four; every scalar
   0..0x10FFFF and 0xFFFFFFFF outside the 49 symbols routes as in split-v7,
   and every other labelled scalar (tiled Braille, ASCII groups, draw, accent,
   pixel) plus thousands of untrained scalars cover exactly as in split-v7.
3. symbol-v1 for the 49 symbols: each routes to the group trained on it, and
   its coverage equals that group net alone and split-v5-symbol-v1, bit for
   bit, at small, odd, non-divisible and large cells, so the symbol-v1 gates
   carry over (weights/neuronte-symbol-v1.md).
4. A first (uncached) draw equals a repeated (cached) draw.
5. A planted defect fails it: the same bundle built with group 0's seed-1 net
   differs in bytes and in group 0's symbol pixels.
"""
import ctypes as C
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'train'))
import known_bundle  # noqa: E402
import pack  # noqa: E402

W = ROOT/'weights'
V7, OUT = W/'neuronte-split-v7.nrt', W/'neuronte-split-v7-symbol-v1.nrt'
V5_SYMBOL = W/'neuronte-split-v5-symbol-v1.nrt'
GROUPS = [W/f'neuronte-symbol-v1-g{i}.json' for i in range(4)]
SYMBOL_EXPERT = 2
SIZES = ((8, 16), (16, 32), (48, 96), (1, 2), (3, 6), (5, 9), (7, 13), (11, 21), (23, 47), (24, 48), (25, 49),
         (33, 61), (64, 128))

lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
lib.neuronte_open.argtypes = [C.c_void_p, C.c_size_t, C.POINTER(C.c_void_p)]
lib.neuronte_close.argtypes = [C.c_void_p]
lib.neuronte_nets.argtypes = [C.c_void_p]
lib.neuronte_route.argtypes = [C.c_void_p, C.c_uint32]
lib.neuronte_coverage.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_int, C.c_int, C.POINTER(C.c_float)]
lib.neuronte_draw_scalar.argtypes = [C.c_void_p, C.POINTER(C.c_uint32), C.c_int, C.c_int, C.c_int, C.c_int,
                                     C.c_int, C.c_int, C.c_int, C.c_uint32, C.c_uint32]
keep = []


def opened(data):
    keep.append(data)
    h = C.c_void_p()
    assert lib.neuronte_open(data, len(data), C.byref(h)) == 0
    return h


def coverage(h, scalar, w, hh):
    buf = (C.c_float*(w*hh))()
    assert lib.neuronte_coverage(h, scalar, w, hh, 0, buf) == 0
    return bytes(buf)


def draw(h, scalar, w, hh):
    buf = (C.c_uint32*(w*hh))()
    assert lib.neuronte_draw_scalar(h, buf, w, w, hh, 0, 0, w, hh, scalar, 0xFFFFFFFF) == 0
    return bytes(buf)


data, base = OUT.read_bytes(), V7.read_bytes()
rebuilt, _ = known_bundle.replace_known(base, GROUPS, SYMBOL_EXPERT)
assert rebuilt == data, 'committed bundle differs from its rebuild'

new, old, v5s = opened(data), opened(base), opened(V5_SYMBOL.read_bytes())
nets = [opened(pack.pack(str(p))) for p in GROUPS]
first = lib.neuronte_nets(old)
assert lib.neuronte_nets(new) == first+len(GROUPS)
labels = [pack.scalars(str(p))[1] for p in GROUPS]
symbols = set().union(*labels)
assert sum(map(len, labels)) == len(symbols) == 49
assert symbols == pack.scalars(str(W/'neuronte-symbol-v0.json'))[1]

moved = 0
for s in list(range(0x110000))+[0xFFFFFFFF]:
    r = lib.neuronte_route(new, s)
    if s in symbols:
        assert lib.neuronte_route(old, s) == SYMBOL_EXPERT
        moved += 1
    else:
        assert r == lib.neuronte_route(old, s), hex(s)
assert moved == 49

cases = 0
for i, group in enumerate(labels):
    for s in sorted(group):
        assert lib.neuronte_route(new, s) == first+i, hex(s)
        for w, hh in SIZES:
            c = coverage(new, s, w, hh)
            assert c == coverage(nets[i], s, w, hh) == coverage(v5s, s, w, hh), (hex(s), w, hh)
            cases += 1

others = set().union(*(pack.scalars(str(W/f))[1] for f in (
    'neuronte-ascii-v0.json', 'neuronte-draw-v2.json', 'neuronte-accent-v2.json',
    'neuronte-pixel-v1.json', 'neuronte-braille-v0.json')))
assert not others & symbols
rng = random.Random(20261113)
unknown = {rng.randrange(0x110000) for _ in range(3000)} | {0, 0xFFFD, 0x25A0, 0x2600, 0x10FFFF}
unknown -= symbols | others
same = 0
for s in sorted(others | unknown):
    for w, hh in ((8, 16), (7, 13), (25, 49)):
        assert coverage(new, s, w, hh) == coverage(old, s, w, hh), (hex(s), w, hh)
        same += 1

fresh = opened(data)
for w, hh in ((8, 16), (23, 47), (24, 48), (25, 49)):
    first_draw = [draw(fresh, s, w, hh) for s in sorted(symbols)]
    assert first_draw == [draw(fresh, s, w, hh) for s in sorted(symbols)]
wrong, _ = known_bundle.replace_known(base, [W/'neuronte-symbol-v1-g0.seed1.json', *GROUPS[1:]], SYMBOL_EXPERT)
assert wrong != data
bad = opened(wrong)
assert any(coverage(bad, s, 8, 16) != coverage(nets[0], s, 8, 16) for s in labels[0]), 'planted defect not detected'
lib.neuronte_close(bad)
for h in [new, old, v5s, fresh, *nets]:
    lib.neuronte_close(h)
print(f'check_split_v7_symbol: bytes rebuild exactly; all 1,114,113 routes equal split-v7 except the 49 '
      f'symbols; {cases} symbol cases equal their group nets and split-v5-symbol-v1; {len(others)} other '
      f'labels and {len(unknown)} untrained scalars ({same} coverages) equal split-v7; cached draws equal first draws; planted seed-1 defect detected')
