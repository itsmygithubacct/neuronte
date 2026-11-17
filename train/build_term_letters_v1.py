"""Rebuild neuronte-term-letters-v1: new letters of Latin, Greek and Cyrillic, alone.

usage: python3 train/build_term_letters_v1.py [--files]

neuronte-term-letters-v1 is train/standalone_bundle.py applied to the group
nets files() names, in order, with weights/neuronte-term-letters-v1.list.txt
as its list and neuronte-split-v9.nrt and neuronte-term-latin-v1.nrt as the
bundles it stays apart from. It holds no copy of either: a program opens
them side by side and draws a character with the one whose
neuronte_untrained() is 0. Every scalar outside the list goes to the blank
net and is reported untrained.

The characters are letters neither of those bundles has, drawn by
train/term_letters.py from font/term-letters.txt. GROUPS names each training
set of that file and how many group nets it was cut into. A group that did
not pass the gates was cut into two halves and each half trained once more;
HALVED names those groups and which of their halves ('a' the first, 'b' the
second) passed and are in the bundle. The characters of a half that is not
in the bundle are not in the list: no net draws them.
"""
import hashlib
import json
import sys
from pathlib import Path

import standalone_bundle

NAME = 'neuronte-term-letters-v1'
BESIDE = (('neuronte-split-v9.nrt', '0a92f223d47f1680929b2c5d7512d1a1728d4871e6653b33cbaad060e6bb90c0'),
          ('neuronte-term-latin-v1.nrt', 'd54279bcbb190178f61a10c1d55f9840cadbd6f1b858a9993c232dc0106a473b'))

# (training set, group nets it was cut into)
GROUPS = (('tletip', 10), ('tletlu', 13), ('tletll', 11), ('tletdg', 6), ('tletcu', 12), ('tletcl', 12),
          ('tletgu', 4), ('tletgl', 4), ('tletsc', 8), ('tletmu', 4), ('tletml', 10), ('tletsb', 1), ('tletsp', 7))
# {(training set, group): the halves in the bundle} for each group cut in two
HALVED = {('tletml', 8): 'a', ('tletsb', 0): 'ab'}


def cut(scalars, count, i):
    """Group i of count, as train/split_expert.py cuts a set."""
    n = len(scalars)
    return scalars[n * i // count:n * (i + 1) // count]


def units(sets):
    """[(file, scalars)] of the bundle, in order; sets is glyphs.term_letters_sets()."""
    out = []
    for name, count in GROUPS:
        scalars = list(sets[name])
        for i in range(count):
            if (name, i) not in HALVED:
                out.append((f'{NAME}-{name}-g{i}.json', cut(scalars, count, i)))
                continue
            for half in HALVED[name, i]:
                out.append((f'{NAME}-{name}-g{i}{half}.json', cut(scalars, 2 * count, 2 * i + 'ab'.index(half))))
    return out


def files():
    out = []
    for name, count in GROUPS:
        for i in range(count):
            out += [f'{NAME}-{name}-g{i}{half}.json' for half in HALVED.get((name, i), ('',))]
    return out


def build(weights):
    """Return the bundle and its record."""
    weights = Path(weights)
    for name, want in BESIDE:
        if want and hashlib.sha256((weights / name).read_bytes()).hexdigest() != want:
            raise ValueError(f'{name} is not {want[:8]}')
    listed = weights / f'{NAME}.list.txt'
    image, record = standalone_bundle.standalone([str(weights / f) for f in files()],
                                                 standalone_bundle.read_list(str(listed)),
                                                 [str(weights / name) for name, _ in BESIDE])
    record['list'] = {'file': listed.name, 'sha256': hashlib.sha256(listed.read_bytes()).hexdigest()}
    return image, {'schema': 'neuronte.term-letters/v1', 'name': NAME, 'sha256': record['sha256'], 'bytes': len(image),
                   'groups': [list(g) for g in GROUPS],
                   'halved': [{'set': s, 'group': g, 'in_bundle': list(h)} for (s, g), h in sorted(HALVED.items())],
                   'record': record}


if __name__ == '__main__':
    if sys.argv[1:] == ['--files']:      # for the Makefile
        print(' '.join('weights/' + f[:-5] for f in files()))
        sys.exit(0)
    if len(sys.argv) != 1:
        sys.exit(__doc__.split('\n\n')[1])
    weights = Path(__file__).resolve().parents[1] / 'weights'
    image, record = build(weights)
    (weights / f'{NAME}.nrt').write_bytes(image)
    (weights / f'{NAME}.provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'output': f'{NAME}.nrt', 'sha256': record['sha256'], 'bytes': len(image),
                      'group_nets': record['record']['group_nets'], 'scalars': record['record']['trained_scalars']}))
