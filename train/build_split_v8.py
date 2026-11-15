"""Rebuild split-v8: split-v7 with every selected known-only expert replacement.

usage: python3 train/build_split_v8.py

split-v8 is train/known_bundle.py applied to neuronte-split-v7.nrt once per
entry of REPLACEMENTS, in order. Each entry names the split-v7 expert whose
labelled table routes move and the group JSON that take them. split-v7's ten
members, including every replaced expert, stay byte for byte and keep
drawing unknown characters; each step appends its members and suppressed gate
outputs. To add a replacement, append one entry.
"""
import hashlib
import json
import sys
from pathlib import Path

import known_bundle

NAME = 'neuronte-split-v8'
BASE = 'neuronte-split-v7.nrt'

# (part, split-v7 expert, group JSON, how it was chosen)
REPLACEMENTS = [
    ('symbol', 2, [f'neuronte-symbol-v1-g{i}.json' for i in range(4)],
     'neuronte-symbol-v1 seed 0; passed its declared gates in both seeds'),
    ('pixel', 4, [f'neuronte-pixel-groups-v1-p{i}.json' for i in range(4)],
     'neuronte-pixel-groups-v1 seed 1; failed the declared strict geometry gates; '
     'selected by the owner after visual review'),
    ('accent', 3, [f'neuronte-accent-groups-v1-p{i}.json' for i in range(3)],
     'neuronte-accent-groups-v1 seed 0; failed the declared strict gates; '
     'selected by the owner after visual review'),
]


def build(weights, replacements=REPLACEMENTS):
    """Return the bundle and its record: one known_bundle record per step."""
    weights = Path(weights)
    base = (weights / BASE).read_bytes()
    image, steps = base, []
    for part, expert, files, selection in replacements:
        image, record = known_bundle.replace_known(image, [weights / f for f in files], expert)
        steps.append({'part': part, 'expert': expert, 'selection': selection, 'record': record})
    return image, {
        'schema': 'neuronte.split-v8/v1', 'name': NAME, 'base': BASE,
        'base_sha256': hashlib.sha256(base).hexdigest(),
        'sha256': hashlib.sha256(image).hexdigest(), 'bytes': len(image),
        'members': steps[-1]['record']['members'] if steps else None,
        'steps': steps,
    }


if __name__ == '__main__':
    if len(sys.argv) != 1:
        sys.exit(__doc__.split('\n\n')[1])
    weights = Path(__file__).resolve().parents[1] / 'weights'
    image, record = build(weights)
    (weights / f'{NAME}.nrt').write_bytes(image)
    (weights / f'{NAME}.provenance.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({'output': f'{NAME}.nrt', 'sha256': record['sha256'], 'bytes': len(image),
                      'members': record['members']}))
