"""Check a neuronte-wide bundle: wide pictographs, symbols and fullwidth forms drawn for a box of two cells.

usage: python3 tests/check_wide.py LIB.so NAME

NAME is one of neuronte-wide-forms-v1, neuronte-wide-symbols-v1,
neuronte-wide-pictographs-v1, neuronte-wide-pictographs2-v1 (the
pictographs are two files: one holds at most 127 group nets),
neuronte-wide-supplement-v1. It must be, at once:

1. Reproducible: rebuilt byte for byte by its build script from the group
   JSON and its list, its provenance exactly the rebuild's.
2. Its list and nothing else: the list, NAME.symbols.txt, is the bundle's
   characters (train/wide.py) less the nets left out, in order; the members
   are the group nets packed from their JSON, in order, then the blank net;
   no gate.
3. Apart from the other wide bundles and outside the listed-bundle rule, and
   no wider: no NAME.list.txt (some of its code points are drawn for one cell
   in a terminal bundle, and this file draws them for another box); no
   character in two of the five wide bundles; the five drawn together are
   1,335 characters.
4. Routed exactly: every scalar 0..0x10FFFF and 0xFFFFFFFF. A listed
   character goes to the group net trained on it and is reported trained;
   every other scalar goes to the blank net and is reported untrained.
5. Pixel-exact: each listed character draws as its group net alone at the
   19 qualification sizes and at the cells a program asks for a two-cell
   box (W x 2H: 16x34, 18x36, 20x38, 20x40, 36x72), automatic sampling, and
   at 8x16, 16x32 and 48x96 with one sample; sampled other scalars draw an
   empty cell. Every character has ink in its 18x18 box (18x36 asked, each
   pair of rows averaged).
6. Recorded honestly: NAME.validation.json names this bundle and the
   declared gates (v2.3, kind symbols) and, for each group, the hashes of
   both seeds and whether both passed. Only a net whose two seeds passed is
   in the bundle, as the seed the rule selects; a group is halved exactly
   when it failed; a half that failed is left out, unless the owner named it
   to ship after looking at it (FAILED_SHIPPED): then it is in the bundle as
   its lower-error seed and the record says it failed.
"""
import ctypes as C
import hashlib
import importlib
import json
import random
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import pack  # noqa: E402
import standalone_bundle  # noqa: E402
import wide  # noqa: E402

W = ROOT / 'weights'
SCRIPTS = {'neuronte-wide-forms-v1': 'build_wide_forms_v1', 'neuronte-wide-symbols-v1': 'build_wide_symbols_v1',
           'neuronte-wide-pictographs-v1': 'build_wide_pictographs_v1',
           'neuronte-wide-pictographs2-v1': 'build_wide_pictographs2_v1', 'neuronte-wide-supplement-v1': 'build_wide_supplement_v1'}
SIZES = ((3, 6), (4, 8), (5, 10), (6, 12), (7, 13), (8, 16), (9, 17), (12, 24), (13, 27), (16, 32), (17, 35),
         (23, 47), (24, 48), (25, 49), (31, 63), (32, 64), (33, 61), (48, 96), (64, 128))
BOX_CELLS = ((16, 34), (18, 36), (20, 38), (20, 40), (36, 72))       # the cell asked for a two-cell box W x H: W x 2H
S1_SIZES = ((8, 16), (16, 32), (48, 96))
GATES_SHA = '2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4'   # gates v2.3, declared 2026-11-18T00:25Z
WIDE_COUNT = 1335


def fail(message):
    print(f'FAIL {message}')
    sys.exit(1)


def sha(data):
    return hashlib.sha256(data).hexdigest()


sys.stdout.reconfigure(line_buffering=True)
if len(sys.argv) != 3 or sys.argv[2] not in SCRIPTS:
    sys.exit(__doc__.split('\n\n')[1])
NAME = sys.argv[2]
build = importlib.import_module(SCRIPTS[NAME]).BUNDLE
TAG = f'check_wide {NAME}'
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
    fail(f'the bundle is not {SCRIPTS[NAME]}.py applied to the group nets')
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
listed = standalone_bundle.read_list(str(W / build.list))
if listed != want:
    fail('the list is not the bundle\'s characters less the nets left out, in order')
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
print(f'{TAG}: bytes: {len(files)} group nets and the blank net, {len(table)} characters, no gate; rebuilt byte for byte')

# 3. Apart, and no wider.
if (W / f'{NAME}.list.txt').exists():
    fail(f'{NAME}.list.txt exists: this bundle draws some terminal bundles\' code points again for two cells')
drawn = {b: [c for _, (_, cps) in importlib.import_module(s).BUNDLE.sets().items() for c in cps] for b, s in SCRIPTS.items()}
every = [c for cps in drawn.values() for c in cps]
if len(every) != len(set(every)) or len(every) != WIDE_COUNT:
    fail(f'the five wide bundles draw {len(set(every))} characters ({len(every)} with repeats), not {WIDE_COUNT} apart')
left = [c for name, i, part in build.nets() if (name, i) in build.left_out for c in part]
if sorted(listed + left) != sorted(drawn[NAME]):
    fail('the list and the characters left out are not the bundle\'s characters')
print(f'{TAG}: characters: {len(listed)} of its {len(drawn[NAME])}' + (f', {len(left)} left out' if left else '') +
      f'; none in another of the five wide bundles ({WIDE_COUNT} drawn in all)')

# 6. The validation record.
validation = json.loads((W / f'{NAME}.validation.json').read_text())
if validation['bundle_sha256'] != sha(shipped):
    fail('the validation record names another bundle')
if validation['gates_sha256'] != GATES_SHA:
    fail('the validation record was not judged by the declared gates')
records, halved = {}, []
for part in validation['sets']:
    for g in part['groups']:
        if g['kind'] != 'symbols':
            fail(f"{part['set']} group {g['group']}: judged as {g['kind']}, not as the declared symbols")
        if g['halved'] != (not g['both_seeds_pass']):
            fail(f"{part['set']} group {g['group']}: a group is halved exactly when it failed")
        if g['halved']:
            halved.append((part['set'], g['group']))
            for h in g['halves']:
                records[h['set'], h['group']] = h
        else:
            records[part['set'], g['group']] = g
if sorted(halved) != sorted(build.halved):
    fail('the validation record and HALVED disagree')
if list(records) != [(name, i) for name, i, _ in build.nets()]:
    fail('the validation record does not cover the nets of the rule, in order')
seen = []
for key, g in records.items():
    owner = key in build.failed_shipped
    if g['shipped'] != (key not in build.left_out) or g['shipped'] != (g['both_seeds_pass'] or owner):
        fail(f'{key}: in the bundle exactly when both seeds passed or the owner named it, and LEFT_OUT says the same')
    if bool(g.get('failed_gates_shipped_by_owner')) != (owner and not g['both_seeds_pass']):
        fail(f'{key}: the record does not say it failed and ships by the owner\'s word')
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
    if g['shipped_seed'] != (g['lower_error_seed'] if owner and not g['both_seeds_pass'] else g['selected_seed']):
        fail(f'{key}: ships the seed the rule did not select')
    seen.append(path)
if seen != files:
    fail('the validation record does not cover the shipped group nets, in order')
if validation['nets_shipped'] != len(files) or validation['nets_left_out'] != len(build.left_out) or \
        validation['groups_halved'] != len(build.halved) or \
        validation.get('nets_failed_shipped_by_owner', []) != [f'{a}:{b}' for a, b in sorted(build.failed_shipped)]:
    fail('the validation record miscounts its nets')
nf = len(build.failed_shipped)
print(f'{TAG}: record: {len(files)} nets in the bundle, ' + (f'{len(files) - nf} with both seeds passing the declared gates and '
      f'{nf} that failed them, in by the owner\'s word; ' if nf else 'each with both seeds passing the declared gates; ') +
      f'{len(build.halved)} groups halved, {len(build.left_out)} nets left out')

handles = []
tmp = tempfile.TemporaryDirectory(prefix='wide-check-')


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

    # 4. Routes.
    blank = len(files)
    for c in list(range(0x110000)) + [0xFFFFFFFF]:
        r, u = lib.neuronte_route(bundle, c), lib.neuronte_untrained(bundle, c)
        if c in group:
            if r != group[c] or u != 0:
                fail(f'U+{c:04X} routes to {r} (untrained {u}), not to its group net {group[c]}')
        elif r != blank or u != 1:
            fail(f'U+{c:04X} routes to {r} (untrained {u}), not to the blank net')
    print(f'{TAG}: routes: {len(group)} characters to their group nets; every other scalar to the blank net, reported untrained')

    # 5. Pixels.
    for i, path in enumerate(files):
        alone = open_bytes(members[i], f'g{i}.nrt')
        own = sorted(c for c in group if group[c] == i)
        for w, h in SIZES + BOX_CELLS:
            if not np.array_equal(coverage(bundle, own, w, h), coverage(alone, own, w, h)):
                fail(f'{w}x{h}: {path.name} draws differently in the bundle')
        for w, h in S1_SIZES:
            if not np.array_equal(coverage(bundle, own, w, h, 1), coverage(alone, own, w, h, 1)):
                fail(f'{w}x{h} samples=1: {path.name} draws differently in the bundle')
        box = coverage(bundle, own, 18, 36).reshape(len(own), 18, 2, 18).mean(2)
        if not (box.reshape(len(own), -1).max(1) > 0.5).all():
            fail(f'{path.name}: a character has no ink in its 18x18 box')
    rng = random.Random(20261118)
    others = sorted(({rng.randrange(0x110000) for _ in range(300)} | {0, 0x20, 0x41, 0xFFFD, 0x10FFFF, 0xD800, 0x110000, 0xFFFFFFFF} |
                     set(every)) - set(group))
    for w, h in ((1, 2), (8, 16), (18, 36), (25, 49)):
        for s in (0, 1):
            if coverage(bundle, others, w, h, s).any():
                fail(f'{w}x{h} samples={s}: a scalar outside the list has ink')
    print(f'{TAG}: pixels: {len(group)} characters as their group nets alone at {len(SIZES)} sizes, {len(BOX_CELLS)} two-cell '
          f'requests and S1 at 3, each with ink in its 18x18 box; {len(others)} other scalars, the other wide bundles\' among them, '
          f'an empty cell')
finally:
    for handle in handles:
        lib.neuronte_close(handle)
    tmp.cleanup()
print(f'{TAG}: passed')
