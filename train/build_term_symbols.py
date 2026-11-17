"""Rebuild a bundle of terminal symbols that stands alone.

usage: python3 train/build_term_symbols.py BUNDLE [--files | --ink]     BUNDLE: math, symbol or dingbat

neuronte-term-math-v1, neuronte-term-symbol-v1 and neuronte-term-dingbat-v1
are each train/standalone_bundle.py applied to their group nets, in order,
with weights/NAME.list.txt as the list and neuronte-split-v9.nrt as the
bundle to stay apart from. None holds a copy of split-v9: a program opens
them beside it and draws a character with the one whose
neuronte_untrained() is 0. Every scalar outside a bundle's list goes to its
blank net and is reported untrained.

The characters are drawn by train/term_glyphs.py from font/term-TIER.txt.
The group nets are the groups of font/term-TIER-partition.json, set by set;
LEFT_OUT names the groups that are not in a bundle and why; OWNER_CHOSEN
names the groups that failed the gates declared for them and are in the
bundle because the owner chose so after seeing them, with the seed shipped.
"""
import hashlib
import json
import sys
from pathlib import Path

import glyphs
import standalone_bundle

BESIDE = 'neuronte-split-v9.nrt'
BESIDE_SHA = '0a92f223d47f1680929b2c5d7512d1a1728d4871e6653b33cbaad060e6bb90c0'

# bundle: (file name, tier of train/glyphs.py)
BUNDLES = {'math': ('neuronte-term-math-v1', 'tmath')}
# {bundle: {(training set, group): why it is not in the bundle}}
LEFT_OUT = {'math': {}}
# {bundle: {(training set, group): seed shipped}}: failed the declared gates, shipped by the owner's choice.
# The owner named no seed; of each such group the seed with the lower mean error over 8x16, 16x32 and 48x96
# ships, which is the rule declared for the groups that pass.
def _chosen(sets):
    return {(s, i): seed for s, groups in sets.items() for i, seed in groups.items()}


OWNER_CHOSEN = {'math': _chosen({'tmath12': {0: 1, 3: 1, 4: 1, 5: 0, 6: 1, 9: 1},
                                 'tmath10': {0: 1, 1: 1, 3: 1, 4: 0, 8: 0, 9: 1, 10: 1, 11: 1},
                                 'tmath8': {0: 1, 1: 1, 2: 0, 3: 0, 4: 0, 5: 1, 6: 1, 7: 0, 8: 1}})}


def groups(bundle):
    """[(training set, group, scalars)] of a bundle's tier, in order, left-out groups included."""
    partition = glyphs.term_partition(BUNDLES[bundle][1])
    return [(name, i, part) for name in glyphs.TERM_TIERS[BUNDLES[bundle][1]] for i, part in enumerate(partition[name])]


def files(bundle):
    name = BUNDLES[bundle][0]
    return [f'{name}-{s}-g{i}.json' for s, i, _ in groups(bundle) if (s, i) not in LEFT_OUT[bundle]]


def listed(bundle):
    """The bundle's characters: its tier less the groups left out, in code point order."""
    return sorted(c for s, i, part in groups(bundle) if (s, i) not in LEFT_OUT[bundle] for c in part)


def ink(bundle):
    """A character of the bundle, for a test that wants one with ink: the first of its list."""
    return listed(bundle)[0]


def drawings_sha256(bundle):
    """One hash of the listed characters' drawings today, coordinates rounded to nine places."""
    def norm(o):
        if isinstance(o, float):
            return round(o, 9) + 0.0
        return [norm(x) for x in o] if isinstance(o, (list, tuple)) else o

    want = set(listed(bundle))
    rows = sorted((ord(c), norm(shapes)) for c, _, shapes in glyphs.charset(BUNDLES[bundle][1]) if ord(c) in want)
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def list_text(bundle):
    """The list file: runs of code points, 8 to a line."""
    cps, runs = listed(bundle), []
    for c in cps:
        if runs and runs[-1][1] == c - 1:
            runs[-1][1] = c
        else:
            runs.append([c, c])
    toks = [f'U+{a:04X}' if a == b else f'U+{a:04X}..U+{b:04X}' for a, b in runs]
    name, tier = BUNDLES[bundle]
    head = (f'# {name}: the {len(cps)} characters it was trained on (train/glyphs.py tier {tier}'
            + (f', less {len(LEFT_OUT[bundle])} groups left out' if LEFT_OUT[bundle] else '') + ').\n'
            '# Written by train/build_term_symbols.py; tests/check_term_symbols.py compares.\n')
    return head + ''.join(' '.join(toks[i:i + 8]) + '\n' for i in range(0, len(toks), 8))


def build(bundle, weights):
    """Return the bundle and its record."""
    weights = Path(weights)
    name, tier = BUNDLES[bundle]
    beside = weights / BESIDE
    if hashlib.sha256(beside.read_bytes()).hexdigest() != BESIDE_SHA:
        raise ValueError(f'{BESIDE} is not split-v9 {BESIDE_SHA[:8]}')
    path = weights / f'{name}.list.txt'
    image, record = standalone_bundle.standalone([str(weights / f) for f in files(bundle)],
                                                 standalone_bundle.read_list(str(path)), [str(beside)])
    record['list'] = {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    left = [{'set': s, 'group': i, 'why': why} for (s, i), why in sorted(LEFT_OUT[bundle].items())]
    return image, {'schema': 'neuronte.term-symbols/v1', 'name': name, 'tier': tier, 'sha256': record['sha256'],
                   'bytes': len(image), 'groups': [[s, len(glyphs.term_partition(tier)[s])] for s in glyphs.TERM_TIERS[tier]],
                   'left_out': left,
                   'owner_chosen': [{'set': s, 'group': i, 'seed': seed}
                                    for (s, i), seed in sorted(OWNER_CHOSEN[bundle].items())],
                   'record': record}


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or args[0] not in BUNDLES or args[1:] not in ([], ['--files'], ['--ink']):
        sys.exit(__doc__.split('\n\n')[1])
    if args[1:] == ['--files']:      # for the Makefile
        print(' '.join('weights/' + f[:-5] for f in files(args[0])))
        sys.exit(0)
    if args[1:] == ['--ink']:        # a trained scalar for tests/test_api.c --standalone
        print(f'{ink(args[0]):04X}')
        sys.exit(0)
    weights = Path(__file__).resolve().parents[1] / 'weights'
    name = BUNDLES[args[0]][0]
    (weights / f'{name}.list.txt').write_text(list_text(args[0]))
    image, record = build(args[0], weights)
    (weights / f'{name}.nrt').write_bytes(image)
    (weights / f'{name}.provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'output': f'{name}.nrt', 'sha256': record['sha256'], 'bytes': len(image),
                      'group_nets': record['record']['group_nets'], 'scalars': record['record']['trained_scalars']}))
