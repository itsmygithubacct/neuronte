"""Rebuild neuronte-term-blocks-v1: four blocks made by rule, alone.

usage: python3 train/build_term_blocks_v1.py [--files | --tiled]

neuronte-term-blocks-v1 is train/standalone_bundle.py applied to the
members in MEMBERS, in order, with weights/neuronte-term-blocks-v1.list.txt
as its list and neuronte-split-v9.nrt as the bundle it stays apart from.
It holds no copy of split-v9: a program opens both and draws a character
with the one whose neuronte_untrained() is 0. Every scalar outside the
list goes to the blank net and is reported untrained.

The characters are the Yijing hexagrams, the Tai Xuan Jing figures, the
domino tiles and the playing cards, drawn by train/term_blocks.py from
font/term-blocks.txt. MEMBERS names each training set of that file and
the form it ships in: "tiled", one tiled net whose tiles are the cells of
term_blocks.TILE_GRID (train/tile_member.py), or a number, that many
ordinary group nets over the set cut into contiguous groups. HALVES names
the groups that ship as their two halves, each a net of its own (the
remedy for a group that failed the gates whole): group 3 as "3a" and
"3b". LEFT_OUT names what is not in the bundle and why.

--files prints the group nets and --tiled the tiled nets, for the Makefile.
"""
import hashlib
import json
import sys
from pathlib import Path

import standalone_bundle

NAME = 'neuronte-term-blocks-v1'
BESIDE = 'neuronte-split-v9.nrt'
BESIDE_SHA = '0a92f223d47f1680929b2c5d7512d1a1728d4871e6653b33cbaad060e6bb90c0'

# (training set, form)
MEMBERS = (('tblkhex', 'tiled'), ('tblkdig', 1), ('tblktet', 'tiled'), ('tblkdomh', 'tiled'), ('tblkdomv', 'tiled'),
           ('tblkcard', 'tiled'))
# {(training set, group)}: the groups that ship as two halves
HALVES = set()
# {(training set, group; None for a tiled net, "3a" for a half): why it is not in the bundle}
LEFT_OUT = {}


def parts(name, form, scalars):
    """(group, its characters) of each part a set is cut into: None and all of
    them for a tiled net; the contiguous groups, a group in HALVES as its halves."""
    if form == 'tiled':
        return [(None, list(scalars))]
    n, out = len(scalars), []
    for i in range(form):
        if (name, i) in HALVES:
            cut = [n * j // (2 * form) for j in (2 * i, 2 * i + 1, 2 * i + 2)]
            out += [(f'{i}a', scalars[cut[0]:cut[1]]), (f'{i}b', scalars[cut[1]:cut[2]])]
        else:
            out.append((i, scalars[n * i // form:n * (i + 1) // form]))
    return out


def members():
    """(file, training set, group or None) of each member, in order."""
    out = []
    for name, form in MEMBERS:
        for group, _ in parts(name, form, ()):
            out.append((f'{NAME}-{name}.json' if group is None else f'{NAME}-{name}-g{group}.json', name, group))
    return [m for m in out if (m[1], m[2]) not in LEFT_OUT]


def files():
    return [m[0] for m in members()]


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
    return image, {'schema': 'neuronte.term-blocks/v1', 'name': NAME, 'sha256': record['sha256'], 'bytes': len(image),
                   'members': [list(m) for m in MEMBERS], 'halves': sorted(list(h) for h in HALVES),
                   'left_out': [{'set': s, 'group': g, 'why': why}
                                for (s, g), why in sorted(LEFT_OUT.items(), key=lambda kv: (kv[0][0], str(kv[0][1])))],
                   'record': record}


if __name__ == '__main__':
    if sys.argv[1:] in (['--files'], ['--tiled']):      # for the Makefile
        want = sys.argv[1] == '--tiled'
        print(' '.join('weights/' + f[:-5] for f, _, group in members() if (group is None) == want))
        sys.exit(0)
    if len(sys.argv) != 1:
        sys.exit(__doc__.split('\n\n')[1])
    weights = Path(__file__).resolve().parents[1] / 'weights'
    image, record = build(weights)
    (weights / f'{NAME}.nrt').write_bytes(image)
    (weights / f'{NAME}.provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'output': f'{NAME}.nrt', 'sha256': record['sha256'], 'bytes': len(image),
                      'members': record['record']['group_nets'], 'scalars': record['record']['trained_scalars']}))
