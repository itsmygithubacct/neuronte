#!/usr/bin/env python3
"""Export desktop placement metadata; --check detects drift from the drawings."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
from glyphs import UI_TOP  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'font/ui-tops.json'
    data = json.dumps({'schema': 'neuronte.ui-tops/v1',
                       'tops': {str(em): row for em, row in sorted(UI_TOP.items())}},
                      indent=2) + '\n'
    if args.check:
        if not path.is_file() or path.read_text(encoding='utf-8') != data:
            parser.exit(1, 'font/ui-tops.json is stale; run make ui-metadata\n')
        print('UI placement metadata matches train/glyphs.py')
    else:
        path.write_text(data, encoding='utf-8')


if __name__ == '__main__':
    main()
