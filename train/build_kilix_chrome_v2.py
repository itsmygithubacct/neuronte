"""Rebuild neuronte-kilix-chrome-v2: the symbols Kilix prints on its bars, for a box of two cells.

usage: python3 train/build_kilix_chrome_v2.py [--files]

neuronte-kilix-chrome-v2 is train/standalone_bundle.py applied to the group
nets of units(), in order, with weights/neuronte-kilix-chrome-v2.symbols.txt
as its list. It holds the code points of neuronte-kilix-chrome-v1 and the
sun and the cloud, all but the bell drawn for the box of two terminal cells
that Kilix gives a symbol when a blank cell follows it. A program asks it
for such a box W x H as the cell W x 2H and averages each pair of rows.
Every scalar outside the list goes to the blank net and is reported
untrained.

It stays apart from no other bundle: it is opened for a box no terminal
bundle draws, it has v1's code points on purpose, and two of them are in a
terminal bundle as one-cell characters. So its list is not a
NAME.list.txt, which tests/check_bundle_lists.py would hold apart from
every other; tests/check_kilix_chrome_v2.py checks it instead.

The symbols are those of font/kilix-chrome-2.txt, made by
train/kilix_chrome2.py. Each training set of that file was cut into the
group nets its heading names. HALVED names the groups that failed the
declared gates and were trained again as two nets of half the symbols each
(the set NAMErI of train/kilix_chrome2.py); LEFT_OUT names the nets that are
not in the bundle and why. A net is (set, group).
"""
import hashlib
import json
import sys
from pathlib import Path

import standalone_bundle
import kilix_chrome2
from term_rest import groups

NAME = 'neuronte-kilix-chrome-v2'
LIST = f'{NAME}.symbols.txt'

# (training set, group) retrained as two halves
HALVED = (('tchwb', 0), ('tchwb', 1),)
# {(set, group): why it is not in the bundle}
LEFT_OUT = {}


def nets():
    """Every net trained to the end of the rule, in the file's order: [(set, group, [code points])]."""
    out = []
    for name, (count, cps) in kilix_chrome2.primary().items():
        for i, run in enumerate(groups(cps, count)):
            if (name, i) in HALVED:
                out += [(f'{name}r{i}', h, half) for h, half in enumerate(groups(run, 2))]
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
    listed = weights / LIST
    image, record = standalone_bundle.standalone([str(weights / f) for f in files()],
                                                 standalone_bundle.read_list(str(listed)), [])
    record['list'] = {'file': listed.name, 'sha256': hashlib.sha256(listed.read_bytes()).hexdigest()}
    return image, {'schema': 'neuronte.kilix-chrome/v2', 'name': NAME, 'sha256': record['sha256'], 'bytes': len(image),
                   'sets': [[name, count] for name, (count, _) in kilix_chrome2.primary().items()],
                   'one_cell': [f'U+{c:04X}' for c in kilix_chrome2.one_cell()],
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
