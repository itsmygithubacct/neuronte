"""Check neuronte-term-rest-v1: Hebrew, Lao and one-colour faces, as a bundle that stands alone.

usage: python3 tests/check_term_rest_v1.py LIB.so

It must be, at once:

1. Reproducible: rebuilt byte for byte by train/build_term_rest_v1.py from
   the group JSON and its list, its provenance exactly the rebuild's.
2. Its list and nothing else: the list is the characters of
   font/term-rest.txt less the nets left out; the members are the group
   nets packed from their JSON, in order, then the blank net; no gate.
3. Routed exactly: every scalar 0..0x10FFFF and 0xFFFFFFFF. A listed
   character goes to the group net trained on it and is reported trained;
   every other scalar goes to the blank net and is reported untrained. No
   listed character is in split-v9's table.
4. Pixel-exact: each listed character draws as its group net alone at the
   19 qualification sizes, automatic sampling, and at 8x16, 16x32 and 48x96
   with one sample; sampled other scalars draw an empty cell.
5. Recorded honestly: neuronte-term-rest-v1.validation.json names this
   bundle and the declared gates and, for each group, the hashes of both
   seeds and whether both passed. Only a net whose two seeds passed is in
   the bundle, as the seed the rule selects; a group is halved exactly
   when it failed; a half that failed is left out.
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
import build_term_rest_v1 as build  # noqa: E402
import pack  # noqa: E402
import standalone_bundle  # noqa: E402

W = ROOT / 'weights'
NAME = build.NAME
SIZES = ((3, 6), (4, 8), (5, 10), (6, 12), (7, 13), (8, 16), (9, 17), (12, 24), (13, 27), (16, 32), (17, 35),
         (23, 47), (24, 48), (25, 49), (31, 63), (32, 64), (33, 61), (48, 96), (64, 128))
S1_SIZES = ((8, 16), (16, 32), (48, 96))
GATES_SHA = 'dd3cc2ea30ccb49d001c28a905bcc6e2a2d11edfcd6a741464fda91162b10e70'   # gates v2.2 of 2026-11-17: gates v2, a rule not applied where the drawing itself fails it


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
    fail('the bundle is not train/build_term_rest_v1.py applied to the group nets')
if record != json.loads((W / f'{NAME}.provenance.json').read_text()):
    fail('the provenance differs from the rebuild')

# 2. The list, the members.
files = [W / f for f in build.files()]
group, want = {}, []
for name, i, part in build.units():
    path = W / f'{NAME}-{name}-g{i}.json'
    if sorted(pack.scalars(str(path))[1]) != sorted(part):
        fail(f'{path.name} was not trained on group {i} of {name}')
    for c in part:
        group[c] = files.index(path)
    want += part
listed = standalone_bundle.read_list(str(W / f'{NAME}.list.txt'))
if listed != want:
    fail('the list is not font/term-rest.txt less the nets left out, in its order')
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
print(f'check_term_rest_v1: bytes: {len(files)} group nets and the blank net, {len(table)} characters, no gate; '
      f'rebuilt byte for byte; none of them in split-v9')

# 5. The validation record.
validation = json.loads((W / f'{NAME}.validation.json').read_text())
if validation['bundle_sha256'] != sha(shipped):
    fail('the validation record names another bundle')
if validation['gates_sha256'] != GATES_SHA:
    fail('the validation record was not judged by the declared gates')
records, halved = {}, []
for part in validation['sets']:
    for g in part['groups']:
        if g['halved'] != (not g['both_seeds_pass']):
            fail(f"{part['set']} group {g['group']}: a group is halved exactly when it failed")
        if g['halved']:
            halved.append((part['set'], g['group']))
            for h in g['halves']:
                records[h['set'], h['group']] = h
        else:
            records[part['set'], g['group']] = g
if sorted(halved) != sorted(build.HALVED):
    fail('the validation record and HALVED disagree')
if list(records) != [(name, i) for name, i, _ in build.nets()]:
    fail('the validation record does not cover the nets of the rule, in order')
seen = []
for key, g in records.items():
    if g['shipped'] != (key not in build.LEFT_OUT) or g['shipped'] != g['both_seeds_pass']:
        fail(f'{key}: in the bundle exactly when both seeds passed, and LEFT_OUT says the same')
    if g['both_seeds_pass'] != all(s['gates_passed'] for s in g['seeds'].values()):
        fail(f'{key}: both_seeds_pass is not what the seeds say')
    if not g['shipped']:
        continue
    path = W / g['file']
    chosen = g['seeds'][str(g['shipped_seed'])]
    if path != W / f'{NAME}-{key[0]}-g{key[1]}.json' or sha(path.read_bytes()) != chosen['sha256']:
        fail(f'{key}: the shipped file is not the seed the record names')
    if json.loads(path.read_text())['training']['seed'] != g['shipped_seed']:
        fail(f'{key}: the shipped file is not seed {g["shipped_seed"]}')
    if g['shipped_seed'] != g['selected_seed']:
        fail(f'{key}: ships the seed the rule did not select')
    seen.append(path)
if seen != files:
    fail('the validation record does not cover the shipped group nets, in order')
if validation['nets_shipped'] != len(files) or validation['nets_left_out'] != len(build.LEFT_OUT) or \
        validation['groups_halved'] != len(build.HALVED):
    fail('the validation record miscounts its nets')
print(f'check_term_rest_v1: record: {len(files)} nets in the bundle, each with both seeds passing the declared gates; '
      f'{len(build.HALVED)} groups halved, {len(build.LEFT_OUT)} nets left out')

handles = []
tmp = tempfile.TemporaryDirectory(prefix='term-rest-check-')


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
    print(f'check_term_rest_v1: routes: {len(group)} characters to their group nets; every other scalar to the '
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
    print(f'check_term_rest_v1: pixels: {len(group)} characters as their group nets alone at {len(SIZES)} sizes '
          f'and S1 at 3; {len(others)} other scalars, all of split-v9\'s among them, an empty cell')
finally:
    for handle in handles:
        lib.neuronte_close(handle)
    tmp.cleanup()
print('check_term_rest_v1: passed')
