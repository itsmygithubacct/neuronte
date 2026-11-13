"""Check the RC9 Braille expert and the bundle that carries it.

usage: python3 tests/check_braille_v1.py LIB.so BRAILLE.nrt SPLIT_V6.nrt SPLIT_V5.nrt

1. SPLIT_V6 is SPLIT_V5 with only its Braille member replaced: the same
   counts, range table and gate, byte for byte; the other members byte for
   byte; and the Braille member is BRAILLE.nrt, a version 6 tiled net.
2. All 256 patterns, drawn by BRAILLE.nrt by itself and through SPLIT_V6,
   are the same bit for bit, at 8 x 16, 16 x 32 and 48 x 96 pixels with
   automatic samples: the established sizes the expert was selected at.
   At each, against the teacher, the expert must pass the selection's G1
   and G2: every pattern binary-exact (coverage above one half exactly
   where the teacher's is); mean absolute error at most the previous
   Braille member's (drawn through SPLIT_V5) + 0.0015; and 99th percentile
   absolute error at most 0.06.

The teacher is the Braille training target from train/glyphs.py, sampled
8 x 8 times per pixel as the selection's quality gates sampled it. Its
float32 masks must match the gated teacher's digests below first.
"""
import ctypes as C
import hashlib
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import glyphs  # noqa: E402

# sha256 of the teacher's float32 masks for the 256 patterns, (256, H, W).
TEACHER = {
    (8, 16): '392c0ba393ef601d6fd5c4350f9c595cf41e6d1feffe3732add702cd3a72ed3f',
    (16, 32): '53795dd0418432117bee02d8004e4b44f72ddf15b553e3c18c4e0d5f6ef26ae6',
    (48, 96): 'aefea3ca8c5767212360f8ae245d40c7b798c599f091877b23dc305e573676d6',
}
MAE_BUDGET, P99_LIMIT = .0015, .06
FIRST, LAST = 0x2800, 0x28FF


def fail(message):
    print(f'FAIL {message}')
    sys.exit(1)


def parts(data):
    """(counts, ranges, ranges and gate bytes, members) of a version 2 bundle."""
    if data[:8] != b'NEURONTE' or struct.unpack_from('<I', data, 8)[0] != 2:
        fail('not a version 2 bundle')
    counts = struct.unpack_from('<4I', data, 12)
    nets, ranges = counts[:2]
    lengths = struct.unpack_from(f'<{nets}I', data, 28)
    start = len(data) - sum(lengths)
    table = [struct.unpack_from('<3I', data, 28 + 4 * nets + 12 * i) for i in range(ranges)]
    members, off = [], start
    for n in lengths:
        members.append(data[off:off + n])
        off += n
    return counts, table, data[28 + 4 * nets:start], members


def teacher(cell, samples=8, n=256):
    w, h = cell
    xs = (np.arange(w * samples, dtype=np.float32) + .5) / (w * samples)
    ys = (np.arange(h * samples, dtype=np.float32) + .5) / (h * samples) * 2
    xx, yy = np.meshgrid(xs, ys)
    u, v = xx * n, yy * n
    x0 = np.minimum(np.floor(u).astype(int), n - 1)
    y0 = np.minimum(np.floor(v).astype(int), 2 * n - 1)
    fx, fy = u - x0.astype(np.float32), v - y0.astype(np.float32)
    out = []
    for f in FIELDS:
        top = f[y0, x0] * (1 - fx) + f[y0, x0 + 1] * fx
        bottom = f[y0 + 1, x0] * (1 - fx) + f[y0 + 1, x0 + 1] * fx
        out.append((top * (1 - fy) + bottom * fy > 0).reshape(h, samples, w, samples).mean((1, 3)))
    return np.asarray(out, dtype=np.float32)


def coverage(lib, path, cell):
    handle = C.c_void_p()
    if lib.neuronte_open_file(str(path).encode(), C.byref(handle)) != 0:
        fail(f'cannot open {path}')
    w, h = cell
    out = np.empty((LAST - FIRST + 1, h, w), np.float32)
    buf = (C.c_float * (w * h))()
    try:
        for i, cp in enumerate(range(FIRST, LAST + 1)):
            if lib.neuronte_coverage(handle, cp, w, h, 0, buf) != 0:
                fail(f'{path.name} U+{cp:04X} {w}x{h}: coverage failed')
            out[i] = np.frombuffer(buf, np.float32).reshape(h, w)
    finally:
        lib.neuronte_close(handle)
    return out


if len(sys.argv) != 5:
    sys.exit(__doc__.split('\n\n')[1])
lib = C.CDLL(sys.argv[1])
lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(C.c_void_p)]
lib.neuronte_coverage.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_int, C.c_int, C.POINTER(C.c_float)]
lib.neuronte_close.argtypes = [C.c_void_p]
braille, split6, split5 = (Path(p) for p in sys.argv[2:])

expert = braille.read_bytes()
if expert[:8] != b'NEURONTE' or struct.unpack_from('<I', expert, 8)[0] != 6:
    fail(f'{braille.name} is not a version 6 tiled net')
new, old = parts(split6.read_bytes()), parts(split5.read_bytes())
if new[0] != old[0] or new[1] != old[1] or new[2] != old[2]:
    fail('the counts, range table or gate differ from the previous bundle')
routes = [net for first, last, net in new[1] if first <= FIRST and LAST <= last]
if len(routes) != 1 or [(f, l) for f, l, n in new[1] if n == routes[0]] != [(FIRST, LAST)]:
    fail('the Braille block is not exactly one member\'s range')
b = routes[0]
for i, (m6, m5) in enumerate(zip(new[3], old[3])):
    if i != b and m6 != m5:
        fail(f'member {i} differs from the previous bundle')
if new[3][b] != expert:
    fail(f'the Braille member is not {braille.name}')
if old[3][b] == expert:
    fail('the Braille member was not replaced')
print(f'check_braille_v1: {split6.name} is {split5.name} with member {b} replaced by {braille.name}')

FIELDS = [glyphs.field(s, 256, glyphs.PEN, .15).astype(np.float16).astype(np.float32)
          for _, _, s in glyphs.charset('braille')]
if len(FIELDS) != 256:
    fail('the Braille set is not 256 patterns')
for cell, digest in TEACHER.items():
    truth = teacher(cell)
    want = truth > .5
    if hashlib.sha256(truth.astype('<f4').tobytes()).hexdigest() != digest:
        fail(f'the {cell[0]}x{cell[1]} teacher is not the one the expert was selected against')
    alone, routed = coverage(lib, braille, cell), coverage(lib, split6, cell)
    before = coverage(lib, split5, cell)
    if not np.array_equal(alone, routed):
        fail(f'{cell[0]}x{cell[1]}: the bundle draws Braille differently from {braille.name}')
    wrong = ((alone > .5) != want).reshape(256, -1).any(1)
    if wrong.any():
        bad = ', '.join(f'U+{FIRST + i:04X}' for i in np.nonzero(wrong)[0][:8])
        fail(f'{cell[0]}x{cell[1]}: {int(wrong.sum())} patterns are not binary-exact: {bad}')
    err = np.abs(alone.astype(np.float64) - truth)
    mae, p99 = float(err.mean()), float(np.quantile(err, .99))
    old = float(np.abs(before.astype(np.float64) - truth).mean())
    if mae > old + MAE_BUDGET:
        fail(f'{cell[0]}x{cell[1]}: mean error {mae:.6f} is over {old:.6f} + {MAE_BUDGET}')
    if p99 > P99_LIMIT:
        fail(f'{cell[0]}x{cell[1]}: 99th percentile error {p99:.4f} is over {P99_LIMIT}')
    print(f'check_braille_v1: {cell[0]}x{cell[1]}: 256/256 patterns exact, mean error {mae:.6f} '
          f'(previous {old:.6f}), 99th percentile {p99:.4f}')
print('check_braille_v1: passed')
