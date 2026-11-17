"""Check neuronte-term-letters-v1: the new letters, as a bundle that stands alone.

usage: python3 tests/check_term_letters_v1.py LIB.so

It must be, at once:

1. Reproducible: rebuilt byte for byte by train/build_term_letters_v1.py
   from the group JSON and its list, its provenance exactly the rebuild's.
2. Its list and nothing else: the list is the characters of
   font/term-letters.txt less the halves left out; the members are the group
   nets packed from their JSON, in order, then the blank net; no gate.
3. Routed exactly: every scalar 0..0x10FFFF and 0xFFFFFFFF. A listed
   character goes to the group net trained on it and is reported trained;
   every other scalar goes to the blank net and is reported untrained. No
   listed character is in split-v9's table or term-latin-v1's.
4. Pixel-exact: each listed character draws as its group net alone at the
   19 qualification sizes, automatic sampling, and at 8x16, 16x32 and 48x96
   with one sample; sampled other scalars draw an empty cell.
5. Recorded honestly: neuronte-term-letters-v1.validation.json names this
   bundle and the gates file and, for each group and each half, the hashes
   of both seeds and whether both passed the gates. A group or half is in
   the bundle exactly when both its seeds passed, as the seed the gates'
   rule selects; a group that did not pass is cut in two, and a half that
   did not pass is left out, its characters in no list.
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
import build_term_letters_v1 as build  # noqa: E402
import glyphs  # noqa: E402
import pack  # noqa: E402
import standalone_bundle  # noqa: E402

W = ROOT / 'weights'
NAME = build.NAME
SIZES = ((3, 6), (4, 8), (5, 10), (6, 12), (7, 13), (8, 16), (9, 17), (12, 24), (13, 27), (16, 32), (17, 35),
         (23, 47), (24, 48), (25, 49), (31, 63), (32, 64), (33, 61), (48, 96), (64, 128))
S1_SIZES = ((8, 16), (16, 32), (48, 96))


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
    fail('the bundle is not train/build_term_letters_v1.py applied to the group nets')
if record != json.loads((W / f'{NAME}.provenance.json').read_text()):
    fail('the provenance differs from the rebuild')

# 2. The list, the members.
files = [W / f for f in build.files()]
sets = glyphs.term_letters_sets()
if [name for name, _ in build.GROUPS] != list(sets):
    fail('GROUPS is not the sets of font/term-letters.txt, in order')
group, want = {}, []
for (name, part), path in zip(build.units(sets), files):
    if path.name != name:
        fail('units() and files() disagree')
    if sorted(pack.scalars(str(path))[1]) != sorted(part):
        fail(f'{path.name} was not trained on its part of the set')
    for c in part:
        group[c] = files.index(path)
    want += part
listed = standalone_bundle.read_list(str(W / f'{NAME}.list.txt'))
if listed != want:
    fail('the list is not font/term-letters.txt less the halves left out, in its order')
nets, nranges, fallback, gate = struct.unpack_from('<4I', shipped, 12)
lengths = struct.unpack_from(f'<{nets}I', shipped, 28)
members, off = [], len(shipped) - sum(lengths)
if off != 28 + 4 * nets + 12 * nranges:
    fail('there are bytes between the table and the members')
for n in lengths:
    members.append(shipped[off:off + n])
    off += n
if gate != 0 or nets != len(files) + 1 or fallback != len(files):
    fail('not group nets, then the blank net as the fallback, and no gate')
if members[:-1] != [pack.pack(str(f)) for f in files] or members[-1] != standalone_bundle.blank():
    fail('the members are not the group JSON, in order, and the blank net')
table = standalone_bundle.read_table(shipped)
if table != group:
    fail('the table is not each listed character to its group net')
beside = {}
for other, _ in build.BESIDE:
    beside.update(standalone_bundle.read_table((W / other).read_bytes()))
if set(table) & set(beside):
    fail('a listed character is in split-v9 or term-latin-v1')
print(f'check_term_letters_v1: bytes: {len(files)} group nets and the blank net, {len(table)} characters, no gate; '
      f'rebuilt byte for byte; none of them in split-v9 or term-latin-v1')

# 5. The validation record.
validation = json.loads((W / f'{NAME}.validation.json').read_text())
if validation['bundle_sha256'] != sha(shipped):
    fail('the validation record names another bundle')
seen, halved, left = [], {}, 0
for u in validation['units']:
    key = (u['set'], u['group'])
    passed = all(s['gates_passed'] for s in u['seeds'].values())
    if u['both_seeds_pass'] != passed:
        fail(f'{key}: both_seeds_pass is not what the seeds say')
    if not u['half']:
        if passed == (key in build.HALVED):
            fail(f'{key}: a group is cut in two exactly when it did not pass')
    else:
        if key not in build.HALVED or passed != (u['half'] in build.HALVED[key]):
            fail(f'{key}{u["half"]}: a half is in the bundle exactly when it passed')
    if u['shipped'] != (passed and (bool(u['half']) or key not in build.HALVED)):
        fail(f'{key}{u["half"]}: shipped is not what the gates say')
    if not u['shipped']:
        left += bool(u['half'])
        continue
    path = W / u['file']
    chosen = u['seeds'][str(u['shipped_seed'])]
    if path.name != f'{NAME}-{key[0]}-g{key[1]}{u["half"]}.json' or sha(path.read_bytes()) != chosen['sha256']:
        fail(f'{key}{u["half"]}: the shipped file is not the seed the record names')
    if json.loads(path.read_text())['training']['seed'] != u['shipped_seed'] or u['shipped_seed'] != u['selected_seed']:
        fail(f'{key}{u["half"]}: the shipped file is not the seed the rule selects')
    seen.append(path)
if seen != files:
    fail('the validation record does not cover the shipped group nets, in order')
if validation['groups_shipped'] != len(files) or validation['halves_left_out'] != left:
    fail('the validation record miscounts')
if validation['characters_shipped'] != len(table):
    fail('the validation record miscounts its characters')
print(f'check_term_letters_v1: record: {len(files)} group nets shipped, each with both seeds passing gates '
      f'{validation["gates"]["sha256"][:8]}; {left} halves left out')

handles = []
tmp = tempfile.TemporaryDirectory(prefix='term-letters-check-')


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
        if c in group:
            if r != group[c] or u != 0:
                fail(f'U+{c:04X} routes to {r} (untrained {u}), not to its group net {group[c]}')
        elif r != blank or u != 1:
            fail(f'U+{c:04X} routes to {r} (untrained {u}), not to the blank net')
    print(f'check_term_letters_v1: routes: {len(group)} characters to their group nets; every other scalar to the '
          f'blank net, reported untrained')

    # 4. Pixels.
    for i, path in enumerate(files):
        alone = open_bytes(members[i], f'g{i}.nrt')
        own = sorted(c for c in group if group[c] == i)
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
    others = sorted(({rng.randrange(0x110000) for _ in range(300)} | set(beside) | {0, 0x20, 0x41, 0xFFFD, 0x10FFFF, 0xD800,
                                                                                 0x110000, 0xFFFFFFFF}) - set(group))
    for w, h in ((1, 2), (8, 16), (9, 17), (25, 49)):
        for s in (0, 1):
            if coverage(bundle, others, w, h, s).any():
                fail(f'{w}x{h} samples={s}: a scalar outside the list has ink')
    print(f'check_term_letters_v1: pixels: {len(group)} characters as their group nets alone at {len(SIZES)} sizes '
          f'and S1 at 3; {len(others)} other scalars, all of split-v9\'s and term-latin-v1\'s among them, an empty cell')
finally:
    for handle in handles:
        lib.neuronte_close(handle)
    tmp.cleanup()
print('check_term_letters_v1: passed')
