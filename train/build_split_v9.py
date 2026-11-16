"""Rebuild split-v9: split-v8 with known-only nets for the terminal characters.

usage: python3 train/build_split_v9.py

split-v9 is train/known_bundle.py's add_known applied to neuronte-split-v8.nrt
once, with the group nets in ADDITIONS, in order. The characters they were
trained on were in no table row of split-v8 (the gate chose a net that never
saw them); each now gets a row to the group net trained on it. split-v8's
21 members, its table rows and its gate stay byte for byte, so every other
scalar, trained or not, routes and draws as in split-v8. All fourteen groups
failed their declared gates; the owner chose seed 0 of each after review.
"""
import hashlib
import json
import sys
from pathlib import Path

import known_bundle

NAME = 'neuronte-split-v9'
BASE = 'neuronte-split-v8.nrt'
BASE_SHA = '445b53caa40c6cd02a1b324458bf5ae549b1ab304043ac0eeb3d4871e6461168'

# (part, group JSON, how it was chosen)
SELECTION = 'seed 0, chosen by the owner after a side-by-side review; failed its declared gates (see neuronte-split-v9.validation.json)'
ADDITIONS = [
    ('symbol', [f'neuronte-tsymbol-v1-g{i}.json' for i in range(9)], SELECTION),
    ('greek', [f'neuronte-tgreek-v1-g{i}.json' for i in range(2)], SELECTION),
    ('cyrillic', [f'neuronte-tcyrillic-v1-g{i}.json' for i in range(3)], SELECTION),
]


def build(weights, additions=ADDITIONS):
    """Return the bundle and its record."""
    weights = Path(weights)
    base = (weights / BASE).read_bytes()
    if hashlib.sha256(base).hexdigest() != BASE_SHA:
        raise ValueError(f'{BASE} is not split-v8 445b53ca')
    image, record = known_bundle.add_known(base, [weights / f for _, files, _ in additions for f in files])
    return image, {
        'schema': 'neuronte.split-v9/v1', 'name': NAME, 'base': BASE, 'base_sha256': BASE_SHA,
        'sha256': hashlib.sha256(image).hexdigest(), 'bytes': len(image), 'members': record['members'],
        'parts': [{'part': part, 'files': files, 'selection': selection} for part, files, selection in additions],
        'record': record,
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
