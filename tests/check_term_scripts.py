"""Check a term-scripts bundle: styled alphabets, syllabics or other scripts, as a bundle that stands alone.

usage: python3 tests/check_term_scripts.py LIB.so NAME

NAME is a key of train/build_term_scripts.py's BUNDLES. The bundle must
be, at once:

1. Reproducible: rebuilt byte for byte by train/build_term_scripts.py from
   the group JSON and its list, its provenance exactly the rebuild's.
2. Its list and nothing else: the list is the characters of its training
   sets in font/term-scripts.txt, a failed group's characters taken from
   the set that trains them again as two halves, less the groups left
   out; the members are the group nets packed from their JSON, in order,
   then the blank net; no gate.
3. Routed exactly: every scalar 0..0x10FFFF and 0xFFFFFFFF. A listed
   character goes to the group net trained on it and is reported trained;
   every other scalar goes to the blank net and is reported untrained. No
   listed character is in split-v9's table.
4. Pixel-exact: each listed character draws as its group net alone at the
   19 qualification sizes, automatic sampling, and at 8x16, 16x32 and 48x96
   with one sample; sampled other scalars draw an empty cell.
5. Recorded honestly: NAME.validation.json names this bundle and the
   common gates file and, for each group, the file shipped, its seed, the
   hashes of both seeds and whether both seeds passed. Every group in the
   bundle passed with both seeds and ships the seed the rule selects; a
   group that is left out did not pass.
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
import build_term_scripts as build  # noqa: E402
import pack  # noqa: E402
import standalone_bundle  # noqa: E402

W = ROOT / 'weights'
SIZES = ((3, 6), (4, 8), (5, 10), (6, 12), (7, 13), (8, 16), (9, 17), (12, 24), (13, 27), (16, 32), (17, 35),
         (23, 47), (24, 48), (25, 49), (31, 63), (32, 64), (33, 61), (48, 96), (64, 128))
S1_SIZES = ((8, 16), (16, 32), (48, 96))
GATES_SHA256 = 'dd3cc2ea30ccb49d001c28a905bcc6e2a2d11edfcd6a741464fda91162b10e70'   # gates-v2.2.json, the common gates the groups were judged by


def fail(message):
    print(f'FAIL {message}')
    sys.exit(1)


def sha(data):
    return hashlib.sha256(data).hexdigest()


sys.stdout.reconfigure(line_buffering=True)
if len(sys.argv) != 3 or sys.argv[2] not in build.BUNDLES:
    sys.exit(__doc__.split('\n\n')[1])
NAME = sys.argv[2]
SPEC = build.BUNDLES[NAME]
TAG = f'check_term_scripts {NAME}'
lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(C.c_void_p)]
lib.neuronte_close.argtypes = [C.c_void_p]
lib.neuronte_route.argtypes = [C.c_void_p, C.c_uint32]
lib.neuronte_untrained.argtypes = [C.c_void_p, C.c_uint32]
lib.neuronte_coverage.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_int, C.c_int, C.POINTER(C.c_float)]

# 1. Bytes.
shipped = (W / f'{NAME}.nrt').read_bytes()
rebuilt, record = build.build(W, NAME)
if rebuilt != shipped:
    fail('the bundle is not train/build_term_scripts.py applied to the group nets')
if record != json.loads((W / f'{NAME}.provenance.json').read_text()):
    fail('the provenance differs from the rebuild')

# 2. The list, the members.
files = [W / f for f in build.files(NAME)]
sets = build.term_scripts.sets()
if any(part not in sets for part, _ in SPEC['groups']):
    fail('a training set of the bundle is not in font/term-scripts.txt')
for (part, i), again in SPEC['again'].items():
    if (part, i) in SPEC['left_out']:
        fail(f'{part} group {i} is both trained again and left out')
    if sorted(sets[again]) != sorted(build.group(part, i, dict(SPEC['groups'])[part])):
        fail(f'{again} is not the characters of group {i} of {part}')
group, want = {}, []
for index, (part, i, count) in enumerate(build.nets(NAME)):
    own = build.group(part, i, count)
    path = W / f'{NAME}-{part}-g{i}.json'
    if path != files[index] or sorted(pack.scalars(str(path))[1]) != sorted(own):
        fail(f'{path.name} was not trained on group {i} of {part}')
    for c in own:
        if c in group:
            fail(f'U+{c:04X} is in two group nets')
        group[c] = index
    want += own
listed = standalone_bundle.read_list(str(W / f'{NAME}.list.txt'))
if listed != want:
    fail('the list is not the characters of the group nets, in their order')
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
v9 = standalone_bundle.read_table((W / build.BESIDE).read_bytes())
if set(table) & set(v9):
    fail('a listed character is in split-v9')
print(f'{TAG}: bytes: {len(files)} group nets and the blank net, {len(table)} characters, no gate; '
      f'rebuilt byte for byte; none of them in split-v9')

# 5. The validation record.
validation = json.loads((W / f'{NAME}.validation.json').read_text())
if validation['bundle_sha256'] != sha(shipped):
    fail('the validation record names another bundle')
if validation['gates_sha256'] != GATES_SHA256:
    fail('the validation record names other gates')
seen, known = [], set()
for g in validation['groups']:
    key = (g['set'], g['group'])
    known.add(key)
    both = all(s['gates_passed'] for s in g['seeds'].values())
    if g['both_seeds_pass'] != both:
        fail(f'{key}: both_seeds_pass is not what the seeds say')
    if key in SPEC['again']:
        if g['shipped'] or both or g.get('trained_again_as') != SPEC['again'][key]:
            fail(f'{key}: trained again, so it failed and is not shipped itself')
        continue
    if g['shipped'] != (key not in SPEC['left_out']):
        fail(f'{key}: the validation record and left_out disagree')
    if g['shipped'] != both:
        fail(f'{key}: a group ships when both seeds pass, and only then')
    if not g['shipped']:
        continue
    path = W / g['file']
    chosen = g['seeds'][str(g['shipped_seed'])]
    if path != W / f'{NAME}-{key[0]}-g{key[1]}.json' or sha(path.read_bytes()) != chosen['sha256']:
        fail(f'{key}: the shipped file is not the seed the record names')
    if json.loads(path.read_text())['training']['seed'] != g['shipped_seed']:
        fail(f'{key}: the shipped file is not seed {g["shipped_seed"]}')
    if g['shipped_seed'] != g['selected_seed']:
        fail(f'{key}: the group ships the seed the rule did not select')
    seen.append(path)
if seen != files:
    fail('the validation record does not cover the shipped group nets, in order')
expected = {(part, i) for part, count in SPEC['groups'] for i in range(count)} | {(a, j) for a in SPEC['again'].values() for j in range(2)}
if known != expected:
    fail('the validation record does not name every group trained')
if validation['groups_shipped'] != len(files) or validation['characters_trained'] != len(group):
    fail('the validation record miscounts')
print(f'{TAG}: record: {len(known)} groups trained, {len(files)} shipped, each with both seeds passing the common gates')

handles = []
tmp = tempfile.TemporaryDirectory(prefix='term-scripts-check-')


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
    print(f'{TAG}: routes: {len(group)} characters to their group nets; every other scalar to the '
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
    others = sorted(({rng.randrange(0x110000) for _ in range(300)} | set(v9) | {0, 0x20, 0x41, 0xFFFD, 0x10FFFF, 0xD800,
                                                                                 0x110000, 0xFFFFFFFF}) - set(group))
    for w, h in ((1, 2), (8, 16), (9, 17), (25, 49)):
        for s in (0, 1):
            if coverage(bundle, others, w, h, s).any():
                fail(f'{w}x{h} samples={s}: a scalar outside the list has ink')
    print(f'{TAG}: pixels: {len(group)} characters as their group nets alone at {len(SIZES)} sizes '
          f'and S1 at 3; {len(others)} other scalars, all of split-v9\'s among them, an empty cell')
finally:
    for handle in handles:
        lib.neuronte_close(handle)
    tmp.cleanup()
print(f'{TAG}: passed')
