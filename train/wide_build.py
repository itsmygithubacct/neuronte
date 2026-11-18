"""Build one of the neuronte-wide bundles: two-cell drawings of the wide characters (see train/wide.py).

Each bundle is train/standalone_bundle.py applied to the group nets of
units(), in order, with weights/NAME.symbols.txt as its list. A program asks
it for a box of two cells W x H as the cell W x 2H and averages each pair of
rows, as for neuronte-kilix-chrome-v2. Every scalar outside the list goes
to the blank net and is reported untrained.

Its list is a NAME.symbols.txt and not a NAME.list.txt: some of its code
points are drawn for one cell in a terminal bundle (neuronte-term-rest-v1,
neuronte-term-blocks-v1) or in neuronte-kilix-chrome-v1, and this file
draws them again for a box no terminal bundle draws, so it is outside the
rule of tests/check_bundle_lists.py. tests/check_wide.py holds each table
to its list.

The build script of each bundle (train/build_wide_*_v1.py) names its
HALVED groups, those that failed the declared gates and were trained again
as two nets of half the characters each (the set NAMErI of train/wide.py),
and its LEFT_OUT nets with the reason. A net is (set, group).
"""
import hashlib
import json
import sys
from pathlib import Path

import standalone_bundle
import wide
from term_rest import groups


class Bundle:
    def __init__(self, name, halved, left_out):
        self.name, self.halved, self.left_out = name, tuple(halved), dict(left_out)
        self.list = f'{name}.symbols.txt'

    def sets(self):
        """{set: (group nets, [code points])} of this bundle, in order."""
        prim = wide.primary()
        return {s: prim[s] for s in wide.bundles()[self.name]}

    def nets(self):
        """Every net trained to the end of the rule, in order: [(set, group, [code points])]."""
        out = []
        for name, (count, cps) in self.sets().items():
            for i, run in enumerate(groups(cps, count)):
                if (name, i) in self.halved:
                    out += [(f'{name}r{i}', h, half) for h, half in enumerate(groups(run, 2))]
                else:
                    out.append((name, i, run))
        return out

    def units(self):
        """The nets in the bundle, in order."""
        return [u for u in self.nets() if (u[0], u[1]) not in self.left_out]

    def files(self):
        return [f'{self.name}-{name}-g{i}.json' for name, i, _ in self.units()]

    def build(self, weights):
        """Return the bundle and its record."""
        weights = Path(weights)
        listed = weights / self.list
        image, record = standalone_bundle.standalone([str(weights / f) for f in self.files()],
                                                     standalone_bundle.read_list(str(listed)), [])
        record['list'] = {'file': listed.name, 'sha256': hashlib.sha256(listed.read_bytes()).hexdigest()}
        return image, {'schema': 'neuronte.wide/v1', 'name': self.name, 'sha256': record['sha256'], 'bytes': len(image),
                       'box': 'two cells: asked W x 2H for a box W x H, each pair of rows averaged',
                       'sets': [[name, count] for name, (count, _) in self.sets().items()],
                       'halved': [list(g) for g in self.halved],
                       'left_out': [{'set': s, 'group': g, 'why': why} for (s, g), why in sorted(self.left_out.items())],
                       'record': record}

    def main(self, argv):
        if argv == ['--files']:      # for the Makefile
            print(' '.join('weights/' + f[:-5] for f in self.files()))
            return 0
        if argv:
            print(f'usage: build script [--files]', file=sys.stderr)
            return 2
        weights = Path(__file__).resolve().parents[1] / 'weights'
        image, record = self.build(weights)
        (weights / f'{self.name}.nrt').write_bytes(image)
        (weights / f'{self.name}.provenance.json').write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps({'output': f'{self.name}.nrt', 'sha256': record['sha256'], 'bytes': len(image),
                          'group_nets': record['record']['group_nets'], 'scalars': record['record']['trained_scalars']}))
        return 0
