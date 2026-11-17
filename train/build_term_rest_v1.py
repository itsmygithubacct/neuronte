"""Rebuild neuronte-term-rest-v1: Hebrew, Lao and one-colour faces, alone.

usage: python3 train/build_term_rest_v1.py [--files]

neuronte-term-rest-v1 is train/standalone_bundle.py applied to the group
nets of units(), in order, with weights/neuronte-term-rest-v1.list.txt as
its list and neuronte-split-v9.nrt as the bundle it stays apart from. It
holds no copy of split-v9: a program opens both and draws a character with
the one whose neuronte_untrained() is 0. Every scalar outside the list goes
to the blank net and is reported untrained.

The characters are those of font/term-rest.txt, made by train/term_rest.py.
Each training set of that file was cut into the group nets its heading
names. HALVED names the groups that failed the declared gates and were
trained again as two nets of half the characters each (the set NAMErI of
train/term_rest.py); LEFT_OUT names the nets that are not in the bundle
and why. A net is (set, group): ('trsth', 2) is group 2 of trsth, and
('trsthr2', 0) the first half of that group after it was halved.
"""
import hashlib
import json
import sys
from pathlib import Path

import standalone_bundle
import term_rest

NAME = 'neuronte-term-rest-v1'
BESIDE = 'neuronte-split-v9.nrt'
BESIDE_SHA = '0a92f223d47f1680929b2c5d7512d1a1728d4871e6653b33cbaad060e6bb90c0'

# (training set, group) retrained as two halves
HALVED = (('trstd', 3),)
# {(set, group): why it is not in the bundle}
LEFT_OUT = {}


def nets():
    """Every net trained to the end of the rule, in the file's order: [(set, group, [code points])]."""
    out = []
    for name, (count, cps) in term_rest.primary().items():
        for i, run in enumerate(term_rest.groups(cps, count)):
            if (name, i) in HALVED:
                out += [(f'{name}r{i}', h, half) for h, half in enumerate(term_rest.groups(run, 2))]
            else:
                out.append((name, i, run))
    return out


def units():
    """The nets in the bundle, in order."""
    return [u for u in nets() if (u[0], u[1]) not in LEFT_OUT]


def files():
    return [f'{NAME}-{name}-g{i}.json' for name, i, _ in units()]


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
    return image, {'schema': 'neuronte.term-rest/v1', 'name': NAME, 'sha256': record['sha256'], 'bytes': len(image),
                   'sets': [[name, count] for name, (count, _) in term_rest.primary().items()],
                   'halved': [list(g) for g in HALVED],
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
