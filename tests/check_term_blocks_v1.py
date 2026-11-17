"""Check neuronte-term-blocks-v1: four blocks made by rule, as a bundle that stands alone.

usage: python3 tests/check_term_blocks_v1.py LIB.so

It must be, at once:

1. Reproducible: rebuilt byte for byte by train/build_term_blocks_v1.py
   from its members' JSON and its list, its provenance exactly the
   rebuild's.
2. Its list and nothing else: the list is the characters of
   font/term-blocks.txt less what is left out; the members are the JSON
   packed in order, then the blank net; no gate. A tiled member is cut as
   term_blocks.TILE_GRID says, each tile drawn by its own net from the
   character's own scalar, and was trained on its whole set; a group net
   was trained on its contiguous group, or on one half of it.
3. Routed exactly: every scalar 0..0x10FFFF and 0xFFFFFFFF. A listed
   character goes to the member trained on it and is reported trained;
   every other scalar goes to the blank net and is reported untrained. No
   listed character is in split-v9's table.
4. Pixel-exact: each listed character draws as its member alone at the 19
   qualification sizes, automatic sampling, and at 8x16, 16x32 and 48x96
   with one sample; sampled other scalars, among them the scalars inside
   a tiled member's range that it was not trained on, draw an empty cell.
5. Recorded honestly: neuronte-term-blocks-v1.validation.json names this
   bundle and the common gates file (gates-v2.3), and for each member the file
   shipped, its seed, the hashes of both seeds and whether both passed
   the gates; a member in the bundle passed with both seeds and ships the
   seed the rule selects.
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
import build_term_blocks_v1 as build  # noqa: E402
import pack  # noqa: E402
import standalone_bundle  # noqa: E402
import term_blocks  # noqa: E402

W = ROOT / 'weights'
NAME = build.NAME
SIZES = ((3, 6), (4, 8), (5, 10), (6, 12), (7, 13), (8, 16), (9, 17), (12, 24), (13, 27), (16, 32), (17, 35),
         (23, 47), (24, 48), (25, 49), (31, 63), (32, 64), (33, 61), (48, 96), (64, 128))
S1_SIZES = ((8, 16), (16, 32), (48, 96))
GATES_SHA = '2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4'   # gates-v2.3.json


def fail(message):
    print(f'FAIL {message}')
    sys.exit(1)


def sha(data):
    return hashlib.sha256(data).hexdigest()


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
shipped = (W / f'{NAME}.nrt').read_bytes()
rebuilt, record = build.build(W)
if rebuilt != shipped:
    fail('the bundle is not train/build_term_blocks_v1.py applied to its members')
if record != json.loads((W / f'{NAME}.provenance.json').read_text()):
    fail('the provenance differs from the rebuild')

# 2. The list, the members.
sets = term_blocks.sets()
if [name for name, _ in build.MEMBERS] != list(sets):
    fail('MEMBERS is not the sets of font/term-blocks.txt, in order')
forms = dict(build.MEMBERS)
kept = build.members()
files = [W / f for f, _, _ in kept]
member_of, want, tiled, inside = {}, [], 0, set()
for name, cps in sets.items():
    form = forms[name]
    for i, part in build.parts(name, form, cps):
        if (name, i) in build.LEFT_OUT:
            continue
        path = W / (f'{NAME}-{name}.json' if i is None else f'{NAME}-{name}-g{i}.json')
        if sorted(pack.scalars(str(path))[1]) != sorted(part):
            fail(f'{path.name} was not trained on {name}' + ('' if i is None else f' group {i}'))
        if form != 'tiled' and not part:
            fail(f'{name} group {i} is empty')
        doc = json.loads(path.read_text())
        if i is None:
            columns, rows = term_blocks.TILE_GRID[name]
            first, last = min(part), max(part)
            mask = (1 << (last - first).bit_length()) - 1
            if doc['format'] != 'neuronte-tiled-weights' or (doc['first'], doc['last']) != (f'U+{first:04X}', f'U+{last:04X}'):
                fail(f'{path.name} is not a tiled net over {name}')
            if (doc['columns'] != [float(np.float32(c / columns)) for c in range(columns)] + [1.0]
                    or doc['rows'] != [float(np.float32(2 * r / rows)) for r in range(rows)] + [2.0]):
                fail(f'{path.name} is not cut {columns} by {rows}')
            if doc['tiles'] != [{'net': t, 'mask': f'0x{mask:X}', 'base': f'U+{first:04X}', 'code': 'extract'}
                                for t in range(columns * rows)] or len(doc['nets']) != columns * rows:
                fail(f'{path.name}: a tile does not get the character\'s own scalar and its own net')
            for t, net in enumerate(doc['nets']):
                ex = net['training']['experiment']
                region = [t % columns / columns, (t % columns + 1) / columns, 2 * (t // columns) / rows,
                          2 * (t // columns + 1) / rows]
                if (ex['index'] != t or any(abs(a - b) > 1e-12 for a, b in zip(ex['region'], region))
                        or ex['scalars'] != list(part) or net['training']['seed'] != doc['training']['seed']):
                    fail(f'{path.name}: net {t} was not trained on tile {t} of every character of {name}')
            tiled += 1
            inside |= set(range(first, last + 1)) - set(part)
        elif doc['format'] != 'neuronte-weights':
            fail(f'{path.name} is not a group net')
        for c in part:
            member_of[c] = files.index(path)
        want += part
listed = standalone_bundle.read_list(str(W / f'{NAME}.list.txt'))
if listed != want:
    fail('the list is not font/term-blocks.txt less what is left out, in its order')
nets, nranges, fallback, gate = struct.unpack_from('<4I', shipped, 12)
lengths = struct.unpack_from(f'<{nets}I', shipped, 28)
members, off = [], len(shipped) - sum(lengths)
if off != 28 + 4 * nets + 12 * nranges:
    fail('there are bytes between the table and the members')
for n in lengths:
    members.append(shipped[off:off + n])
    off += n
if gate != 0 or nets != len(files) + 1 or fallback != len(files):
    fail('not the members, then the blank net as the fallback, and no gate')
if members[:-1] != [pack.pack(str(f)) for f in files] or members[-1] != standalone_bundle.blank():
    fail('the members are not the JSON, in order, and the blank net')
table = standalone_bundle.read_table(shipped)
if table != member_of:
    fail('the table is not each listed character to its member')
v9 = standalone_bundle.read_table((W / build.BESIDE).read_bytes())
if set(table) & set(v9):
    fail('a listed character is in split-v9')
print(f'check_term_blocks_v1: bytes: {tiled} tiled nets, {len(files) - tiled} group nets and the blank net, '
      f'{len(table)} characters, no gate; rebuilt byte for byte; none of them in split-v9')

# 5. The validation record.
validation = json.loads((W / f'{NAME}.validation.json').read_text())
if validation['bundle_sha256'] != sha(shipped) or validation['gates_sha256'] != GATES_SHA:
    fail('the validation record names another bundle or other gates')
seen = []
for m in validation['members']:
    key = (m['set'], m['group'])
    if m['shipped'] != (key in [(s, g) for _, s, g in kept]):
        fail(f'{key}: the validation record and the bundle disagree')
    if not m['shipped']:
        if m['both_seeds_pass'] or key not in build.LEFT_OUT:
            fail(f'{key}: not shipped, yet passing or not named in LEFT_OUT')
        continue
    path = W / m['file']
    chosen = m['seeds'][str(m['shipped_seed'])]
    if sha(path.read_bytes()) != chosen['sha256']:
        fail(f'{key}: the shipped file is not the seed the record names')
    if json.loads(path.read_text())['training']['seed'] != m['shipped_seed']:
        fail(f'{key}: the shipped file is not seed {m["shipped_seed"]}')
    if not m['both_seeds_pass'] or not all(s['gates_passed'] and s['reference_check_passed'] for s in m['seeds'].values()):
        fail(f'{key}: in the bundle without both seeds passing')
    if m['shipped_seed'] != m['selected_seed']:
        fail(f'{key}: ships the seed the rule did not select')
    lower = min(m['seeds'], key=lambda s: (m['seeds'][s]['mean_established_mae'], s))
    if int(lower) != m['selected_seed']:
        fail(f'{key}: the selected seed is not the lower-error one')
    seen.append(path)
if seen != files:
    fail('the validation record does not cover the shipped members, in order')
if validation['members_shipped'] != len(files) or validation['characters_trained'] != len(table):
    fail('the validation record miscounts')
print(f'check_term_blocks_v1: record: {len(files)} members shipped, each with both seeds passing gates-v2.3 '
      f'{GATES_SHA[:8]}; {len(build.LEFT_OUT)} left out')

handles = []
tmp = tempfile.TemporaryDirectory(prefix='term-blocks-check-')


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


try:
    bundle = open_bytes(shipped, 'bundle.nrt')

    # 3. Routes.
    blank = len(files)
    for c in list(range(0x110000)) + [0xFFFFFFFF]:
        r, u = lib.neuronte_route(bundle, c), lib.neuronte_untrained(bundle, c)
        if c in member_of:
            if r != member_of[c] or u != 0:
                fail(f'U+{c:04X} routes to {r} (untrained {u}), not to its member {member_of[c]}')
        elif r != blank or u != 1:
            fail(f'U+{c:04X} routes to {r} (untrained {u}), not to the blank net')
    print(f'check_term_blocks_v1: routes: {len(member_of)} characters to their members; every other scalar to the '
          f'blank net, reported untrained')

    # 4. Pixels.
    for i, path in enumerate(files):
        alone = open_bytes(members[i], f'm{i}.nrt')
        own = sorted(c for c in member_of if member_of[c] == i)
        for w, h in SIZES:
            if not np.array_equal(coverage(bundle, own, w, h), coverage(alone, own, w, h)):
                fail(f'{w}x{h}: {path.name} draws differently in the bundle')
        for w, h in S1_SIZES:
            if not np.array_equal(coverage(bundle, own, w, h, 1), coverage(alone, own, w, h, 1)):
                fail(f'{w}x{h} samples=1: {path.name} draws differently in the bundle')
        ink = coverage(bundle, own, 16, 32)
        if not (ink.reshape(len(own), -1).max(1) > 0.5).all():
            fail(f'{path.name}: a character has no ink at 16x32')
    rng = random.Random(20261117)
    others = sorted(({rng.randrange(0x110000) for _ in range(300)} | set(v9) | inside
                     | {0, 0x20, 0x41, 0xFFFD, 0x10FFFF, 0xD800, 0x110000, 0xFFFFFFFF}) - set(member_of))
    for w, h in ((1, 2), (8, 16), (9, 17), (25, 49)):
        for s in (0, 1):
            if coverage(bundle, others, w, h, s).any():
                fail(f'{w}x{h} samples={s}: a scalar outside the list has ink')
    print(f'check_term_blocks_v1: pixels: {len(member_of)} characters as their members alone at {len(SIZES)} sizes '
          f'and S1 at 3; {len(others)} other scalars, all of split-v9\'s and the {len(inside)} unlisted scalars inside '
          f'a tiled range among them, an empty cell')
finally:
    for handle in handles:
        lib.neuronte_close(handle)
    tmp.cleanup()
print('check_term_blocks_v1: passed')
