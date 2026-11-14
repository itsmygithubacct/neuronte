"""split-v5-symbol-v1: reproducible bytes, exact symbol labels, everything else unchanged.

usage: python3 tests/check_symbol_v1.py build/libneuronte.so

1. Rebuilding from split-v5 and the four committed group nets with
   train/known_bundle.py (--expert 2) gives the committed bytes.
2. Each of the 49 symbol labels routes to the group net that was trained on
   it, and its coverage equals that net packed alone, bit for bit, at the
   established cells and at small, odd and non-divisible ones, including
   widths 23, 24 and 25.
3. Every other split-v5 label, plus thousands of untrained scalars, routes
   and covers exactly as split-v5 does.
4. A first (uncached) draw equals a repeated (cached) draw.
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
GROUPS = [W/f'neuronte-symbol-v1-g{i}.json' for i in range(4)]
BUNDLE = W/'neuronte-split-v5-symbol-v1.nrt'
SYMBOL_EXPERT = 2
SIZES = ((8, 16), (16, 32), (48, 96), (1, 2), (3, 6), (5, 9), (7, 13), (7, 14), (11, 21), (13, 27),
         (17, 35), (23, 46), (23, 47), (24, 48), (25, 49), (25, 50), (33, 61), (64, 128))

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


base = (W/'neuronte-split-v5.nrt').read_bytes()
data = BUNDLE.read_bytes()
rebuilt, _ = known_bundle.replace_known(base, GROUPS, SYMBOL_EXPERT)
assert rebuilt == data, 'committed bundle differs from its rebuild'

new, old = opened(data), opened(base)
nets = [opened(pack.pack(str(p))) for p in GROUPS]
first = lib.neuronte_nets(new)-len(GROUPS)
assert first == lib.neuronte_nets(old)
labels = [pack.scalars(str(p))[1] for p in GROUPS]
symbols = set().union(*labels)
assert sum(map(len, labels)) == len(symbols) == 49
assert symbols == pack.scalars(str(W/'neuronte-symbol-v0.json'))[1]
cases = 0
for i, group in enumerate(labels):
    for s in sorted(group):
        assert lib.neuronte_route(old, s) == SYMBOL_EXPERT
        assert lib.neuronte_route(new, s) == first+i, hex(s)
        for w, hh in SIZES:
            assert coverage(new, s, w, hh) == coverage(nets[i], s, w, hh), (hex(s), w, hh)
            cases += 1

others = set().union(*(pack.scalars(str(W/f))[1] for f in (
    'neuronte-ascii-v0.json', 'neuronte-draw-v2.json', 'neuronte-accent-v2.json',
    'neuronte-pixel-v1.json', 'neuronte-braille-v0.json')))
rng = random.Random(20261113)
unknown = {rng.randrange(0x110000) for _ in range(3000)} | {0, 0xFFFD, 0x25A0, 0x2600, 0x10FFFF, 0x110000, 0xFFFFFFFF}
unknown -= symbols | others
same = 0
for s in sorted(others | unknown):
    assert lib.neuronte_route(new, s) == lib.neuronte_route(old, s), hex(s)
    if s < 0x110000:
        for w, hh in ((8, 16), (7, 13), (25, 49)):
            assert coverage(new, s, w, hh) == coverage(old, s, w, hh), (hex(s), w, hh)
            same += 1

fresh = opened(data)
for w, hh in ((8, 16), (23, 47), (24, 48), (25, 49)):
    first_draw = [draw(fresh, s, w, hh) for s in sorted(symbols)]
    assert first_draw == [draw(fresh, s, w, hh) for s in sorted(symbols)]
for h in [new, old, fresh, *nets]:
    lib.neuronte_close(h)
print(f'check_symbol_v1: bytes rebuild exactly; {cases} symbol label cases equal their group nets; '
      f'{len(others)} other labels and {len(unknown)} untrained scalars ({same} coverages) equal split-v5; '
      'cached draws equal first draws')
