"""Check split-v7: split-v6 with the qualified ASCII character groups.

usage: python3 tests/check_split_v7.py LIB.so

split-v7 is train/known_bundle.py applied to split-v6 with the four
neuronte-ascii-groups-v1 nets as known-only ASCII experts (expert 0). It must
be, at once:

1. split-v6 plus ASCII: rebuilt byte for byte from split-v6 and the group
   JSON; its first six members are split-v6's (Braille is neuronte-braille-v1);
   every scalar 0..0x10FFFF and 0xFFFFFFFF outside printable ASCII routes as
   in split-v6, and draws the same pixels for every range scalar; printable
   ASCII routes to the group that holds it.
2. The ASCII package plus Braille: the same counts, range table and gate as
   neuronte-split-ascii-groups-v1, and the same member bytes except member 5,
   the Braille expert.
3. Its ASCII pixels equal the qualified direct file, neuronte-ascii-groups-v1,
   at all 19 qualification sizes, so tests/check_ascii_next.py's teacher gates
   carry over. tests/check_braille_v1.py gates its Braille member.
"""
import ctypes as C
import json
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import known_bundle  # noqa: E402
import pack  # noqa: E402

W = ROOT / 'weights'
V6, V7 = W / 'neuronte-split-v6.nrt', W / 'neuronte-split-v7.nrt'
PACKAGE, DIRECT = W / 'neuronte-split-ascii-groups-v1.nrt', W / 'neuronte-ascii-groups-v1.nrt'
GROUPS = [W / f'neuronte-ascii-groups-v1-p{i}.json' for i in range(4)]
BRAILLE = W / 'neuronte-braille-v1.nrt'
ASCII = range(0x20, 0x7F)
REPRESENTATIVES = [0, 1, 127, 0xa0, 0x391, 0x410, 0x2500, 0x2588, 0x2801, 0x1f600, 0x10ffff, 0xffffffff]


def fail(message):
    print(f'FAIL {message}')
    sys.exit(1)


def parts(data):
    nets, nranges = struct.unpack_from('<2I', data, 12)
    lengths = struct.unpack_from(f'<{nets}I', data, 28)
    start = len(data) - sum(lengths)
    members, off = [], start
    for n in lengths:
        members.append(data[off:off + n])
        off += n
    table = [struct.unpack_from('<3I', data, 28 + 4 * nets + 12 * i) for i in range(nranges)]
    return data[12:28], table, data[28 + 4 * nets:start], members


if len(sys.argv) != 2:
    sys.exit(__doc__.split('\n\n')[1])
lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(C.c_void_p)]
lib.neuronte_close.argtypes = [C.c_void_p]
lib.neuronte_route.argtypes = [C.c_void_p, C.c_uint32]
lib.neuronte_coverage.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_int, C.c_int, C.POINTER(C.c_float)]

v6, v7, package = V6.read_bytes(), V7.read_bytes(), PACKAGE.read_bytes()
rebuilt, proof = known_bundle.replace_known(v6, [str(p) for p in GROUPS], 0)
if rebuilt != v7:
    fail('split-v7 is not known_bundle(split-v6, ascii-groups-v1, expert 0)')
if proof['replaced_scalars'] != 95 or proof['original_members'] != 6:
    fail(f'unexpected replacement proof {proof}')
p6, p7, pp = parts(v6), parts(v7), parts(package)
if p7[3][:6] != p6[3]:
    fail('the first six members are not split-v6\'s')
if p7[3][5] != BRAILLE.read_bytes():
    fail('member 5 is not neuronte-braille-v1')
if p7[0] != pp[0] or p7[1] != pp[1] or p7[2] != pp[2]:
    fail('the counts, range table or gate differ from neuronte-split-ascii-groups-v1')
if [i for i, (a, b) in enumerate(zip(p7[3], pp[3])) if a != b] != [5]:
    fail('split-v7 differs from the ASCII package in members other than Braille')
print(f'check_split_v7: bytes: split-v6 + {len(GROUPS)} ASCII groups; the ASCII package with member 5 = braille-v1')

handles = []


def open_model(path):
    handle = C.c_void_p()
    if lib.neuronte_open_file(str(path).encode(), C.byref(handle)) != 0:
        fail(f'cannot open {path.name}')
    handles.append(handle)
    return handle


def coverage(handle, scalars, w, h):
    out = np.empty((len(scalars), h, w), np.float32)
    for i, c in enumerate(scalars):
        if lib.neuronte_coverage(handle, int(c), w, h, 0, out[i].ctypes.data_as(C.POINTER(C.c_float))) != 0:
            fail(f'U+{int(c):04X} {w}x{h}: coverage failed')
    return out


try:
    h6, h7, hd = open_model(V6), open_model(V7), open_model(DIRECT)
    group = {c: i for i, path in enumerate(GROUPS) for c in pack.scalars(str(path))[1]}
    if sorted(group) != list(ASCII):
        fail('the groups do not hold exactly printable ASCII')
    route = lib.neuronte_route
    moved = kept = 0
    for c in list(range(0x110000)) + [0xFFFFFFFF]:
        r7 = route(h7, c)
        if c in group:
            if r7 != 6 + group[c]:
                fail(f'U+{c:04X} routes to {r7}, not ASCII group {group[c]}')
            moved += 1
        elif r7 != route(h6, c):
            fail(f'U+{c:04X} routes to {r7}, split-v6 to {route(h6, c)}')
        else:
            kept += 1
    print(f'check_split_v7: routes: {moved} ASCII scalars to their groups; all {kept:,} others as split-v6')
    scalars = np.array(sorted({c for lo, hi, _ in p7[1] for c in range(lo, min(hi, 0x10ffff) + 1)
                               if not 0xd800 <= c <= 0xdfff}), np.int64)
    other = scalars[(scalars < 0x20) | (scalars > 0x7e)]
    for w, h in ((5, 10), (8, 16), (16, 32)):
        if not np.array_equal(coverage(h7, other, w, h), coverage(h6, other, w, h)):
            fail(f'{w}x{h}: a non-ASCII range scalar draws differently from split-v6')
    if not np.array_equal(coverage(h7, REPRESENTATIVES, 9, 17), coverage(h6, REPRESENTATIVES, 9, 17)):
        fail('9x17: a representative scalar draws differently from split-v6')
    evidence = json.loads((W / 'neuronte-ascii-next.validation.json').read_text())
    model = next(m for m in evidence['models'] if m['direct'] == DIRECT.name)
    sizes = sorted({tuple(s['cell']) for s in model['scores']})
    if len(sizes) != 19:
        fail(f'expected 19 qualification sizes, found {len(sizes)}')
    for w, h in sizes:
        if not np.array_equal(coverage(h7, list(ASCII), w, h), coverage(hd, list(ASCII), w, h)):
            fail(f'{w}x{h}: ASCII draws differently from {DIRECT.name}')
    print(f'check_split_v7: pixels: {len(other)} non-ASCII range scalars as split-v6 at 3 sizes; '
          f'ASCII as {DIRECT.name} at {len(sizes)} sizes')
finally:
    for handle in handles:
        lib.neuronte_close(handle)
print('check_split_v7: passed')
