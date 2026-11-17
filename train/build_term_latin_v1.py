"""Rebuild neuronte-term-latin-v1: composed Latin, Greek and Cyrillic letters, alone.

usage: python3 train/build_term_latin_v1.py [--files]

neuronte-term-latin-v1 is train/standalone_bundle.py applied to the group
nets in GROUPS, in order, with weights/neuronte-term-latin-v1.list.txt as
its list and neuronte-split-v9.nrt as the bundle it stays apart from. It
holds no copy of split-v9: a program opens both and draws a character with
the one whose neuronte_untrained() is 0. Every scalar outside the list goes
to the blank net and is reported untrained.

The characters are letters split-v9 has with one to three marks, drawn by
train/glyphs.py's term_latin() from font/term-latin.txt. GROUPS names each
training set of that file and how many group nets it was cut into;
LEFT_OUT names the groups that are not in the bundle and why.
"""
import hashlib
import json
import sys
from pathlib import Path

import standalone_bundle

NAME = 'neuronte-term-latin-v1'
BESIDE = 'neuronte-split-v9.nrt'
BESIDE_SHA = '0a92f223d47f1680929b2c5d7512d1a1728d4871e6653b33cbaad060e6bb90c0'

# (training set, group nets it was cut into)
GROUPS = (('tlvu', 6), ('tlvl', 6), ('tlau', 6), ('tlal', 6), ('tl2u', 3), ('tl2l', 3), ('tlbu', 5), ('tlbl', 5),
          ('tlcu', 2), ('tlcl', 2), ('tlgu', 12), ('tlgl', 16), ('tlgs', 2))
# {(training set, group): why it is not in the bundle}
LEFT_OUT = {}


def files():
    return [f'{NAME}-{name}-g{i}.json' for name, count in GROUPS for i in range(count) if (name, i) not in LEFT_OUT]


def build(weights):
    """Return the bundle and its record."""
    weights = Path(weights)
    beside = weights / BESIDE
    if hashlib.sha256(beside.read_bytes()).hexdigest() != BESIDE_SHA:
        raise ValueError(f'{BESIDE} is not split-v9 {BESIDE_SHA[:8]}')
    listed = weights / f'{NAME}.list.txt'
    image, record = standalone_bundle.standalone([str(weights / f) for f in files()],
                                                 standalone_bundle.read_list(str(listed)), [str(beside)])
    record['list'] = {'file': listed.name, 'sha256': hashlib.sha256(listed.read_bytes()).hexdigest()}
    return image, {'schema': 'neuronte.term-latin/v1', 'name': NAME, 'sha256': record['sha256'], 'bytes': len(image),
                   'groups': [list(g) for g in GROUPS],
                   'left_out': [{'set': s, 'group': g, 'why': why} for (s, g), why in sorted(LEFT_OUT.items())],
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
