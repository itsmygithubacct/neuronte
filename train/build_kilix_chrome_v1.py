"""Rebuild neuronte-kilix-chrome-v1: the symbols Kilix prints on its bars, alone.

usage: python3 train/build_kilix_chrome_v1.py [--files]

neuronte-kilix-chrome-v1 is train/standalone_bundle.py applied to the group
nets of units(), in order, with weights/neuronte-kilix-chrome-v1.list.txt
as its list and neuronte-split-v9.nrt as the bundle it stays apart from.
A program opens it before the terminal bundles and draws a symbol with the
first file whose neuronte_untrained() is 0. Every scalar outside the list
goes to the blank net and is reported untrained.

The symbols are those of font/kilix-chrome.txt, made by
train/kilix_chrome.py. Each training set of that file was cut into the
group nets its heading names. HALVED names the groups that failed the
declared gates and were trained again as two nets of half the symbols each
(the set NAMErI of train/kilix_chrome.py); LEFT_OUT names the nets that are
not in the bundle and why. A net is (set, group).
"""
import hashlib
import json
import sys
from pathlib import Path

import standalone_bundle
import kilix_chrome
from term_rest import groups

NAME = 'neuronte-kilix-chrome-v1'
BESIDE = 'neuronte-split-v9.nrt'
BESIDE_SHA = '0a92f223d47f1680929b2c5d7512d1a1728d4871e6653b33cbaad060e6bb90c0'

# (training set, group) retrained as two halves
HALVED = ()
# {(set, group): why it is not in the bundle}
LEFT_OUT = {}


def nets():
    """Every net trained to the end of the rule, in the file's order: [(set, group, [code points])]."""
    out = []
    for name, (count, cps) in kilix_chrome.primary().items():
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
    beside = weights / BESIDE
    if hashlib.sha256(beside.read_bytes()).hexdigest() != BESIDE_SHA:
        raise ValueError(f'{BESIDE} is not split-v9 {BESIDE_SHA[:8]}')
    listed = weights / f'{NAME}.list.txt'
    image, record = standalone_bundle.standalone([str(weights / f) for f in files()],
                                                 standalone_bundle.read_list(str(listed)), [str(beside)])
    record['list'] = {'file': listed.name, 'sha256': hashlib.sha256(listed.read_bytes()).hexdigest()}
    return image, {'schema': 'neuronte.kilix-chrome/v1', 'name': NAME, 'sha256': record['sha256'], 'bytes': len(image),
                   'sets': [[name, count] for name, (count, _) in kilix_chrome.primary().items()],
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
