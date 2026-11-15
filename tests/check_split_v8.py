"""Check split-v8: split-v7 with the symbol, pixel and accent group replacements.

usage: python3 tests/check_split_v8.py LIB.so

split-v8 is train/build_split_v8.py: train/known_bundle.py applied to
split-v7 once per replacement (symbol expert 2, pixel expert 4, accent
expert 3). It must be, at once:

1. Reproducible and named: rebuilt byte for byte from split-v7 and the group
   JSON, its provenance exactly the rebuild's, and split-v7 itself the
   ASCII/Braille bundle b6e8ad1a, so no other file can take that name.
2. split-v7 plus appended members: split-v7's ten members first, byte for
   byte; then each step's members, packed from its JSON; the gate is
   split-v7's with one zero row and one suppressed bias per appended member.
3. Routed as split-v7 everywhere except the replaced experts' known scalars:
   every scalar 0..0x10FFFF and 0xFFFFFFFF. A replaced scalar was on its
   expert in split-v7 and now goes to the group trained on it.
4. Pixel-exact, part by part, with each part's selected and reviewed source:
   ASCII and Braille as split-v7; symbol as split-v7-symbol-v1 (b98a5b05);
   pixel as the reviewed pixel bundle (a45671b6) and accent as the reviewed
   pixel+accent bundle (924ddff9), both rebuilt here from split-v7 with
   known_bundle and bound by sha256, at each part's reviewed sizes; every
   other range scalar, sampled unknown scalars and invalid input as
   split-v7. Accent coverage also matches the reviewed native buffer hashes.
5. tests/check_braille_v1.py passes against a control with the same
   replacements and the previous Braille member.

These are integration checks. The pixel and accent groups failed their
declared strict gates and were selected after review; their validation
records must still say so, and nothing here turns that into a pass.
"""
import ctypes as C
import hashlib
import json
import random
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import build_split_v8  # noqa: E402
import known_bundle  # noqa: E402
import pack  # noqa: E402

W = ROOT / 'weights'
V7, V8 = W / 'neuronte-split-v7.nrt', W / 'neuronte-split-v8.nrt'
V7_SHA = 'b6e8ad1ac6fbc2370fbacc14727180954b4fc6d23cf7c0506a93116853f92f1f'
SYMBOL_REF = W / 'neuronte-split-v7-symbol-v1.nrt'
SYMBOL_SHA = 'b98a5b05'
PIXEL_SHA = 'a45671b6faa733ec2b1c3b459671c63d224cbd8ee3960d0e0b289952265a245d'
ACCENT_SHA = '924ddff934813d3d7541a9cb29b2cbfe46d38aacaba5be80b0fec5e2db122384'
PACKAGE = W / 'neuronte-split-ascii-groups-v1.nrt'
BRAILLE = W / 'neuronte-braille-v1.nrt'
EXPECTED = [('symbol', 2, 49), ('pixel', 4, 327), ('accent', 3, 318)]
ASCII, BRAILLE_RANGE = list(range(0x20, 0x7F)), list(range(0x2800, 0x2900))
SYMBOL_SIZES = ((8, 16), (16, 32), (48, 96), (1, 2), (3, 6), (5, 9), (7, 13), (11, 21), (23, 47), (24, 48),
                (25, 49), (33, 61), (64, 128))
REPRESENTATIVES = [0, 1, 127, 0xa0, 0x391, 0x410, 0x2500, 0x2591, 0x2801, 0x25a0, 0x2600, 0x1f600,
                   0xfffd, 0x10ffff, 0xffffffff]


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
lib.neuronte_coverage.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_int, C.c_int, C.POINTER(C.c_float)]

# 1. Bytes and names.
v7, v8 = V7.read_bytes(), V8.read_bytes()
if sha(v7) != V7_SHA:
    fail('neuronte-split-v7.nrt is not the ASCII/Braille split-v7 (b6e8ad1a)')
rebuilt, record = build_split_v8.build(W)
if rebuilt != v8:
    fail('split-v8 is not train/build_split_v8.py applied to split-v7')
if record != json.loads(V8.with_suffix('.provenance.json').read_text()):
    fail('split-v8 provenance differs from the rebuild')
steps = [(s['part'], s['expert'], s['record']['replaced_scalars']) for s in record['steps']]
if steps != EXPECTED or record['base_sha256'] != V7_SHA or record['members'] != 21:
    fail(f'unexpected replacement steps {steps}')
groups = {}  # part -> list of (json path, scalars)
for part, expert, files, _ in build_split_v8.REPLACEMENTS:
    groups[part] = [(W / f, pack.scalars(str(W / f))[1]) for f in files]

# 2. split-v7 plus appended members.
p7, p8 = parts(v7), parts(v8)
if p8[3][:10] != p7[3]:
    fail('the first ten members are not split-v7\'s')
appended = [pack.pack(str(path)) for part in groups for path, _ in groups[part]]
if p8[3][10:] != appended:
    fail('the appended members are not the group JSON, in order')
if p8[0] != (21, len(p8[1]), p7[0][2], p7[0][3]):
    fail('the header differs from split-v7 beyond the appended members and ranges')
g, extra = p7[0][3], 11
rows = 172 + 4 * (g * 65 + 10 * g)
if (p8[2][:rows] != p7[2][:rows] or p8[2][rows:rows + 4 * extra * g] != bytes(4 * extra * g) or
        p8[2][rows + 4 * extra * g:-4 * extra] != p7[2][rows:] or
        p8[2][-4 * extra:] != struct.pack(f'<{extra}f', *[-1e30] * extra)):
    fail('the gate is not split-v7\'s with eleven suppressed outputs appended')

# The selected sources, bound by sha256.
symbol_ref, _ = known_bundle.replace_known(v7, [p for p, _ in groups['symbol']], 2)
if sha(symbol_ref)[:8] != SYMBOL_SHA or symbol_ref != SYMBOL_REF.read_bytes():
    fail('split-v7-symbol-v1 is not known_bundle(split-v7, symbol-v1, expert 2)')
pixel_ref, _ = known_bundle.replace_known(v7, [p for p, _ in groups['pixel']], 4)
if sha(pixel_ref) != PIXEL_SHA:
    fail('the rebuilt pixel source is not the reviewed a45671b6')
accent_ref, _ = known_bundle.replace_known(pixel_ref, [p for p, _ in groups['accent']], 3)
if sha(accent_ref) != ACCENT_SHA:
    fail('the rebuilt accent source is not the reviewed 924ddff9')
pixel_validation = json.loads((W / 'neuronte-pixel-groups-v1.validation.json').read_text())
accent_validation = json.loads((W / 'neuronte-accent-groups-v1.validation.json').read_text())
if (pixel_validation['selected_seed'], pixel_validation['original_quality_gates_passed'],
        pixel_validation['selected_bundle_sha256']) != (1, False, PIXEL_SHA):
    fail('the pixel validation record no longer records seed 1, its failed gates and a45671b6')
if (accent_validation['selected_seed'], accent_validation['original_quality_gates_passed']) != (0, False):
    fail('the accent validation record no longer records seed 0 and its failed gates')
symbol_validation = json.loads((W / 'neuronte-symbol-v1.validation.json').read_text())
if symbol_validation['selected_seed'] != 0:
    fail('the symbol validation record no longer records seed 0')
for part, ref in (('pixel', W / 'neuronte-pixel-groups-v1.nrt'), ('accent', W / 'neuronte-accent-groups-v1.nrt')):
    if pack.bundle([str(p) for p, _ in groups[part]])[0] != ref.read_bytes():
        fail(f'{ref.name} is not the direct composition of its group JSON')
print('check_split_v8: bytes: split-v7 b6e8ad1a + symbol (2), pixel (4) and accent (3) groups; '
      'ten members and the gate kept; sources b98a5b05, a45671b6 and 924ddff9 rebuilt')

handles, keep = [], []


def open_bytes(data):
    keep.append(data)
    handle = C.c_void_p()
    path = Path(tmp.name) / f'm{len(keep)}.nrt'
    path.write_bytes(data)
    if lib.neuronte_open_file(str(path).encode(), C.byref(handle)) != 0:
        fail(f'cannot open model {len(keep)}')
    handles.append(handle)
    return handle


def coverage(handle, scalars, w, h, samples=0):
    out = np.empty((len(scalars), h, w), np.float32)
    for i, c in enumerate(scalars):
        if lib.neuronte_coverage(handle, int(c), w, h, samples, out[i].ctypes.data_as(C.POINTER(C.c_float))) != 0:
            fail(f'U+{int(c):04X} {w}x{h}: coverage failed')
    return out


def same(a, b, scalars, cells, what, samples=(0,)):
    for s in samples:
        for w, h in cells:
            if not np.array_equal(coverage(a, scalars, w, h, s), coverage(b, scalars, w, h, s)):
                fail(f'{w}x{h} samples={s}: {what}')


tmp = tempfile.TemporaryDirectory(prefix='split-v8-check-')
try:
    h7, h8 = open_bytes(v7), open_bytes(v8)
    hs, hp, ha = open_bytes(symbol_ref), open_bytes(pixel_ref), open_bytes(accent_ref)

    # 3. Routes.
    target, first = {}, 10
    for part, expert, _ in EXPECTED:
        for i, (_, scalars) in enumerate(groups[part]):
            for c in scalars:
                if c in target:
                    fail(f'U+{c:04X} is in two replacement groups')
                target[c] = (first + i, expert)
        first += len(groups[part])
    route = lib.neuronte_route
    moved = kept = 0
    for c in list(range(0x110000)) + [0xFFFFFFFF]:
        r, r7 = route(h8, c), route(h7, c)
        if c in target:
            if r7 != target[c][1] or r != target[c][0]:
                fail(f'U+{c:04X} routes to {r} (split-v7 {r7}), not group member {target[c][0]}')
            moved += 1
        elif r != r7:
            fail(f'U+{c:04X} routes to {r}, split-v7 to {r7}')
        else:
            kept += 1
    print(f'check_split_v8: routes: {moved} replaced scalars to their groups; all {kept:,} others as split-v7')

    # 4. Pixels, part by part.
    symbols = sorted(c for _, s in groups['symbol'] for c in s)
    pixels = sorted(c for _, s in groups['pixel'] for c in s)
    accents = sorted(c for _, s in groups['accent'] for c in s)
    if pixels != pixel_validation['corpus'] or accents != accent_validation['corpus']:
        fail('the pixel or accent groups do not hold their reviewed repertoire')
    ascii_evidence = json.loads((W / 'neuronte-ascii-next.validation.json').read_text())
    model = next(m for m in ascii_evidence['models'] if m['direct'] == 'neuronte-ascii-groups-v1.nrt')
    ascii_sizes = sorted({tuple(s['cell']) for s in model['scores']})
    if len(ascii_sizes) != 19:
        fail(f'expected 19 ASCII qualification sizes, found {len(ascii_sizes)}')
    same(h8, h7, ASCII, ascii_sizes, 'ASCII draws differently from split-v7')
    same(h8, h7, BRAILLE_RANGE, ((8, 16), (16, 32), (25, 49), (48, 96)), 'Braille draws differently from split-v7')
    same(h8, hs, symbols, SYMBOL_SIZES, 'a symbol draws differently from split-v7-symbol-v1')
    same(h8, hs, symbols, ((8, 16), (16, 32), (48, 96)), 'a symbol draws differently from split-v7-symbol-v1', (1,))
    pixel_sizes = sorted({tuple(s['cell']) for s in pixel_validation['scores'] if s['seed'] == 1})
    if len(pixel_sizes) != 22:
        fail(f'expected 22 reviewed pixel sizes, found {len(pixel_sizes)}')
    same(h8, hp, pixels, pixel_sizes, 'a pixel glyph draws differently from the reviewed a45671b6', (0, 1))
    scores = accent_validation['scores']
    if len(scores) != 28:
        fail(f'expected 28 reviewed accent geometries, found {len(scores)}')
    for score in scores:
        w, h = score['cell']
        actual = coverage(h8, accents, w, h, score['samples'])
        if not np.array_equal(actual, coverage(ha, accents, w, h, score['samples'])):
            fail(f'{w}x{h} samples={score["samples"]}: an accent glyph draws differently from the reviewed 924ddff9')
        if sha(actual.astype('<f4').tobytes()) != score['coverage_float32_sha256']:
            fail(f'{w}x{h} samples={score["samples"]}: accent coverage differs from the reviewed native buffers')
    print(f'check_split_v8: pixels: ASCII as split-v7 at {len(ascii_sizes)} sizes, Braille at 4; '
          f'49 symbols as split-v7-symbol-v1 at {len(SYMBOL_SIZES)} sizes and S1 at 3; '
          f'327 pixel glyphs as a45671b6 at 22 sizes, automatic and S1; '
          f'318 accents as 924ddff9 and the reviewed buffers at {len(scores)} geometries')
    replaced = set(target) | set(ASCII) | set(BRAILLE_RANGE)
    scalars = sorted({c for lo, hi, _ in p8[1] for c in range(lo, min(hi, 0x10ffff) + 1)
                      if not 0xd800 <= c <= 0xdfff})
    other = [c for c in scalars if c not in replaced]
    same(h8, h7, other, ((5, 10), (8, 16), (16, 32)), 'another range scalar draws differently from split-v7')
    rng = random.Random(20261114)
    unknown = sorted(({rng.randrange(0x110000) for _ in range(1000)} - set(scalars) - set(range(0xd800, 0xe000)))
                     | set(REPRESENTATIVES) - replaced)
    same(h8, h7, unknown, ((9, 17), (25, 49)), 'an unknown or invalid scalar draws differently from split-v7', (0, 1))
    print(f'check_split_v8: pixels: {len(other)} other range scalars as split-v7 at 3 sizes; '
          f'{len(unknown)} unknown and invalid scalars as split-v7 at 2 sizes, automatic and S1')
finally:
    for handle in handles:
        lib.neuronte_close(handle)
    tmp.cleanup()

# 5. The ASCII package with the same replacements keeps the previous Braille
# member, so it is the control for the existing Braille teacher gates.
with tempfile.TemporaryDirectory(prefix='split-v8-braille-') as directory:
    control = Path(directory) / 'previous-braille.nrt'
    image = PACKAGE.read_bytes()
    for part, expert, files, _ in build_split_v8.REPLACEMENTS:
        image, _ = known_bundle.replace_known(image, [W / f for f in files], expert)
    control.write_bytes(image)
    result = subprocess.run([sys.executable, str(ROOT / 'tests/check_braille_v1.py'),
                             str(Path(sys.argv[1]).resolve()), str(BRAILLE), str(V8), str(control)])
    if result.returncode != 0:
        fail('tests/check_braille_v1.py failed on split-v8')
print('check_split_v8: passed')
