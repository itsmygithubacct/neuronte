"""Rebuild a term-scripts bundle: styled alphabets, Canadian syllabics, other scripts.

usage: python3 train/build_term_scripts.py NAME [--files]

NAME is one of the keys of BUNDLES. Each bundle is train/standalone_bundle.py
applied to its group nets, in order, with weights/NAME.list.txt as its list
and neuronte-split-v9.nrt as the bundle it stays apart from. It holds no
copy of split-v9: a program opens both and draws a character with the one
whose neuronte_untrained() is 0. Every scalar outside the list goes to the
blank net and is reported untrained.

The characters are those of font/term-scripts.txt, made by
train/term_scripts.py. For each bundle, "groups" names its training sets
and how many group nets each was cut into. A group that failed the common
gates was trained once more as two halves, from a set of the file that
lists its characters again ("again"); a group or half that still failed is
not in the bundle ("left_out"), and its characters stay untrained.
"""
import hashlib
import json
import sys
from pathlib import Path

import standalone_bundle
import term_scripts

BESIDE = 'neuronte-split-v9.nrt'
BESIDE_SHA = '0a92f223d47f1680929b2c5d7512d1a1728d4871e6653b33cbaad060e6bb90c0'

# name: the sets its characters come from, in order, each with the number
# of group nets it was cut into; the failed groups trained again as two
# halves, {(set, group): the set that lists its characters again}; and the
# groups or halves not in the bundle, {(set, group): why}.
BUNDLES = {
    'neuronte-term-mathalpha-v1': {
        'groups': (('tscrmp', 10), ('tscrmn', 2), ('tscrmdu', 2), ('tscrmdl', 3)),
        'again': {},
        'left_out': {},
    },
    'neuronte-term-syllabics-v1': {
        'groups': (('tscrsa', 12), ('tscrsb', 3)),
        'again': {},
        'left_out': {},
    },
    'neuronte-term-scripts-v1': {
        'groups': (('tscrl', 6),),
        'again': {},
        'left_out': {},
    },
}


def nets(name):
    """[(training set, group, groups in that set)] for the bundle's group nets, in order."""
    spec, out = BUNDLES[name], []
    for part, count in spec['groups']:
        for i in range(count):
            if (part, i) in spec['again']:
                again = spec['again'][(part, i)]
                out += [(again, j, 2) for j in range(2) if (again, j) not in spec['left_out']]
            elif (part, i) not in spec['left_out']:
                out.append((part, i, count))
    return out


def group(part, i, count):
    """The characters of one group net: the contiguous cut split_expert.py makes."""
    cps = term_scripts.sets()[part]
    return cps[len(cps) * i // count:len(cps) * (i + 1) // count]


def files(name):
    return [f'{name}-{part}-g{i}.json' for part, i, _ in nets(name)]


def characters(name):
    """The bundle's characters, in the order of its group nets."""
    return [c for part, i, count in nets(name) for c in group(part, i, count)]


def build(weights, name):
    """Return the bundle and its record."""
    weights, spec = Path(weights), BUNDLES[name]
    beside = weights / BESIDE
    if hashlib.sha256(beside.read_bytes()).hexdigest() != BESIDE_SHA:
        raise ValueError(f'{BESIDE} is not split-v9 {BESIDE_SHA[:8]}')
    for (part, i), again in spec['again'].items():
        if sorted(term_scripts.sets()[again]) != sorted(group(part, i, dict(spec['groups'])[part])):
            raise ValueError(f'{again} is not the characters of group {i} of {part}')
    listed = weights / f'{name}.list.txt'
    image, record = standalone_bundle.standalone([str(weights / f) for f in files(name)],
                                                 standalone_bundle.read_list(str(listed)), [str(beside)])
    record['list'] = {'file': listed.name, 'sha256': hashlib.sha256(listed.read_bytes()).hexdigest()}
    return image, {'schema': 'neuronte.term-scripts/v1', 'name': name, 'sha256': record['sha256'], 'bytes': len(image),
                   'groups': [list(g) for g in spec['groups']],
                   'again': [{'set': s, 'group': g, 'as': a} for (s, g), a in sorted(spec['again'].items())],
                   'left_out': [{'set': s, 'group': g, 'why': why} for (s, g), why in sorted(spec['left_out'].items())],
                   'record': record}


if __name__ == '__main__':
    if len(sys.argv) not in (2, 3) or sys.argv[1] not in BUNDLES or sys.argv[2:] not in ([], ['--files']):
        sys.exit(__doc__.split('\n\n')[1] + '\nNAME: ' + ' '.join(BUNDLES))
    name = sys.argv[1]
    if sys.argv[2:] == ['--files']:      # for the Makefile
        print(' '.join('weights/' + f[:-5] for f in files(name)))
        sys.exit(0)
    weights = Path(__file__).resolve().parents[1] / 'weights'
    image, record = build(weights, name)
    (weights / f'{name}.nrt').write_bytes(image)
    (weights / f'{name}.provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'output': f'{name}.nrt', 'sha256': record['sha256'], 'bytes': len(image),
                      'group_nets': record['record']['group_nets'], 'scalars': record['record']['trained_scalars']}))
