"""Check split-v9: split-v8 with known-only nets for the terminal characters.

usage: python3 tests/check_split_v9.py LIB.so

split-v9 is train/build_split_v9.py: train/known_bundle.py's add_known
applied once to split-v8 with the group nets that passed their declared
gates. It must be, at once:

1. Reproducible: rebuilt byte for byte from split-v8 (445b53ca) and the
   group JSON, its provenance exactly the rebuild's.
2. split-v8 plus appended members: split-v8's 21 members first, byte for
   byte, then the group nets packed from their JSON, in order; split-v8's
   table rows all kept; the gate split-v8's with one zero row and one
   suppressed bias per appended member.
3. Routed as split-v8 everywhere except the added characters: every scalar
   0..0x10FFFF and 0xFFFFFFFF. An added character was in no table row of
   split-v8 and now goes to the group net trained on it.
4. Pixel-exact: every character split-v8 was trained on (its whole table)
   draws as in split-v8 at the 19 ASCII qualification sizes, automatic
   sampling, and at 8x16, 16x32 and 48x96 with one sample; sampled unknown
   and invalid scalars draw as in split-v8; each added character draws as
   its group net alone at the same sizes.
5. Recorded honestly: neuronte-split-v9.validation.json names this bundle,
   seed 0 of each group as the evaluated file, and that every group failed
   its declared gates (the owner chose them after review).
"""
import ctypes as C
import hashlib
import json
import random
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import build_split_v9  # noqa: E402
import pack  # noqa: E402

W = ROOT / 'weights'
V8, V9 = W / 'neuronte-split-v8.nrt', W / 'neuronte-split-v9.nrt'
V8_SHA = '445b53caa40c6cd02a1b324458bf5ae549b1ab304043ac0eeb3d4871e6461168'
SIZES = ((3, 6), (4, 8), (5, 10), (6, 12), (7, 13), (8, 16), (9, 17), (12, 24), (13, 27), (16, 32), (17, 35),
         (23, 47), (24, 48), (25, 49), (31, 63), (32, 64), (33, 61), (48, 96), (64, 128))
S1_SIZES = ((8, 16), (16, 32), (48, 96))
REPRESENTATIVES = [0, 1, 127, 0xa0, 0x37e, 0x3a2, 0x4e00, 0x1f600, 0xfffd, 0x10ffff, 0xd800, 0x110000, 0xffffffff]


def fail(message):
    print(f'FAIL {message}')
    sys.exit(1)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parts(data):
    """(header counts, range table, gate bytes, members) of a version 2 bundle."""
    nets, nranges = struct.unpack_from('<2I', data, 12)
    lengths = struct.unpack_from(f'<{nets}I', data, 28)
    start = len(data) - sum(lengths)
    members, off = [], start
    for n in lengths:
        members.append(data[off:off + n])
        off += n
    table = [struct.unpack_from('<3I', data, 28 + 4 * nets + 12 * i) for i in range(nranges)]
    return struct.unpack_from('<4I', data, 12), table, data[28 + 4 * nets + 12 * nranges:start], members


sys.stdout.reconfigure(line_buffering=True)
if len(sys.argv) != 2:
    sys.exit(__doc__.split('\n\n')[1])
lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(C.c_void_p)]
lib.neuronte_close.argtypes = [C.c_void_p]
lib.neuronte_route.argtypes = [C.c_void_p, C.c_uint32]
lib.neuronte_untrained.argtypes = [C.c_void_p, C.c_uint32]
lib.neuronte_coverage.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_int, C.c_int, C.POINTER(C.c_float)]

# 1. Bytes.
v8, v9 = V8.read_bytes(), V9.read_bytes()
if sha(v8) != V8_SHA:
    fail('neuronte-split-v8.nrt is not split-v8 445b53ca')
rebuilt, record = build_split_v9.build(W)
if rebuilt != v9:
    fail('split-v9 is not train/build_split_v9.py applied to split-v8')
if record != json.loads(V9.with_suffix('.provenance.json').read_text()):
    fail('split-v9 provenance differs from the rebuild')
files = [W / f for _, fs, _ in build_split_v9.ADDITIONS for f in fs]
if not files:
    fail('split-v9 adds no group nets')
group = {}  # scalar -> index of its group among the appended nets
for i, path in enumerate(files):
    for c in pack.scalars(str(path))[1]:
        if c in group:
            fail(f'U+{c:04X} is in two group nets')
        group[c] = i

# 2. split-v8 plus appended members.
p8, p9 = parts(v8), parts(v9)
k8, extra = p8[0][0], len(files)
if p9[3][:k8] != p8[3]:
    fail('the first members are not split-v8\'s')
if p9[3][k8:] != [pack.pack(str(f)) for f in files]:
    fail('the appended members are not the group JSON, in order')
if p9[0] != (k8 + extra, len(p9[1]), p8[0][2], p8[0][3]):
    fail('the header differs from split-v8 beyond the appended members and ranges')
if [r for r in p9[1] if r[2] < k8] != p8[1]:
    fail('split-v8\'s table rows are not all kept')
added_rows = {c for lo, hi, n in p9[1] if n >= k8 for c in range(lo, hi + 1)}
if added_rows != set(group) or any(group[c] != n - k8 for lo, hi, n in p9[1] if n >= k8 for c in range(lo, hi + 1)):
    fail('the added table rows are not the group nets\' scalars')
g = p8[0][3]
rows = 172 + 4 * (g * 65 + k8 * g)
if (p9[2][:rows] != p8[2][:rows] or p9[2][rows:rows + 4 * extra * g] != bytes(4 * extra * g) or
        p9[2][rows + 4 * extra * g:-4 * extra] != p8[2][rows:] or
        p9[2][-4 * extra:] != struct.pack(f'<{extra}f', *[-1e30] * extra)):
    fail('the gate is not split-v8\'s with suppressed outputs appended')
validation = json.loads((W / 'neuronte-split-v9.validation.json').read_text())
chosen = [g['seeds']['0']['file'] for part in validation['parts'] for g in part['groups']]
if (validation['bundle_sha256'] != sha(v9) or validation['selected_seed'] != 0 or
        validation['original_quality_gates_passed'] is not False or chosen != [f.name for f in files] or
        any(g['both_seeds_pass'] for part in validation['parts'] for g in part['groups']) or
        any(sha((W / s['file']).read_bytes()) != s['sha256'] for part in validation['parts'] for g in part['groups']
            for s in g['seeds'].values())):
    fail('the validation record no longer records seed 0 of each evaluated group and their failed gates')
print(f'check_split_v9: bytes: split-v8 445b53ca + {extra} group nets ({len(group)} characters); '
      f'{k8} members, {len(p8[1])} rows and the gate kept')

handles = []
tmp = tempfile.TemporaryDirectory(prefix='split-v9-check-')


def open_bytes(data, name):
    handle = C.c_void_p()
    path = Path(tmp.name) / name
    path.write_bytes(data)
    if lib.neuronte_open_file(str(path).encode(), C.byref(handle)) != 0:
        fail(f'cannot open {name}')
    handles.append(handle)
    return handle


def coverage(handle, scalars, w, h, samples=0):
    out = np.empty((len(scalars), h, w), np.float32)
    for i, c in enumerate(scalars):
        if lib.neuronte_coverage(handle, int(c), w, h, samples, out[i].ctypes.data_as(C.POINTER(C.c_float))) != 0:
            fail(f'U+{int(c):04X} {w}x{h}: coverage failed')
    return out


def same(a, b, scalars, what):
    for w, h in SIZES:
        if not np.array_equal(coverage(a, scalars, w, h), coverage(b, scalars, w, h)):
            fail(f'{w}x{h}: {what}')
    for w, h in S1_SIZES:
        if not np.array_equal(coverage(a, scalars, w, h, 1), coverage(b, scalars, w, h, 1)):
            fail(f'{w}x{h} samples=1: {what}')


try:
    h8, h9 = open_bytes(v8, 'v8.nrt'), open_bytes(v9, 'v9.nrt')

    # 3. Routes.
    moved = kept = 0
    for c in list(range(0x110000)) + [0xFFFFFFFF]:
        r, r8 = lib.neuronte_route(h9, c), lib.neuronte_route(h8, c)
        if c in group:
            if r != k8 + group[c] or lib.neuronte_untrained(h8, c) != 1 or lib.neuronte_untrained(h9, c) != 0:
                fail(f'U+{c:04X} routes to {r}, not group net {k8 + group[c]}, or was trained in split-v8')
            moved += 1
        elif r != r8:
            fail(f'U+{c:04X} routes to {r}, split-v8 to {r8}')
        else:
            kept += 1
    print(f'check_split_v9: routes: {moved} added characters to their group nets; all {kept:,} others as split-v8')

    # 4. Pixels.
    old = sorted({c for lo, hi, _ in p8[1] for c in range(lo, min(hi, 0x10ffff) + 1)
                  if not 0xd800 <= c <= 0xdfff})
    same(h9, h8, old, 'a split-v8 character draws differently')
    rng = random.Random(20261116)
    unknown = sorted(({rng.randrange(0x110000) for _ in range(300)} - set(old) - set(group) -
                      set(range(0xd800, 0xe000))) | set(REPRESENTATIVES) - set(group))
    for w, h in ((9, 17), (25, 49)):
        for s in (0, 1):
            if not np.array_equal(coverage(h9, unknown, w, h, s), coverage(h8, unknown, w, h, s)):
                fail(f'{w}x{h} samples={s}: an unknown or invalid scalar draws differently')
    for i, path in enumerate(files):
        alone = open_bytes(pack.pack(str(path)), f'g{i}.nrt')
        same(h9, alone, sorted(c for c in group if group[c] == i), f'{path.name} draws differently in split-v9')
    print(f'check_split_v9: pixels: {len(old)} split-v8 characters as split-v8 at {len(SIZES)} sizes and S1 at 3; '
          f'{len(unknown)} unknown and invalid scalars as split-v8; {len(group)} added characters as their '
          f'group nets alone')
finally:
    for handle in handles:
        lib.neuronte_close(handle)
    tmp.cleanup()
print('check_split_v9: passed')
