#!/usr/bin/env python3
"""Draw missing pixel italics without clipping or replacing existing artwork.

The upright pixels are sheared by one column per four rows about their own
baseline. Preserve the left bearing when the cell permits it; move the whole
letter left only enough to fit. For a glyph too wide for that shear, reduce
the slope until every original pixel fits. The advance gains the added ink
span, so the right bearing survives even for a letter filling the cell.
"""
import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import glyphs


def shear(rows, advance, baseline, em):
    original = {(x, y) for y, row in enumerate(rows)
                for x, value in enumerate(row) if value == '#'}
    if not original:
        return advance, rows, 4
    left = min(x for x, _ in original)
    right = max(x for x, _ in original)
    for divisor in range(4, 4 * em + 1):
        def shift(y):
            distance = baseline - y
            return (1 if distance >= 0 else -1) * ((2 * abs(distance) + divisor) // (2 * divisor))
        slanted = {(x + shift(y), y) for x, y in original}
        lo, hi = min(x for x, _ in slanted), max(x for x, _ in slanted)
        if hi - lo < em:
            break
    move = min(left - lo, em - 1 - hi)
    slanted = {(x + move, y) for x, y in slanted}
    assert min(x for x, _ in slanted) >= 0
    assert max(x for x, _ in slanted) < em
    assert len(slanted) == len(original)
    # Preserve the original right padding where the cell has room.
    width = min(em, hi + move + len(rows[0]) - right)
    new_advance = advance + (hi - lo) - (right - left)
    assert 1 <= new_advance < 2 * em
    return new_advance, [
        ''.join('#' if (x, y) in slanted else '.' for x in range(width))
        for y in range(em)], divisor


def draw(em):
    source = ROOT / 'font' / f'ui-{em}.txt'
    dest = ROOT / 'font' / f'ui-{em}-italic.txt'
    if dest.exists():
        raise ValueError(f'refusing to replace {dest.name}')
    header = ' '.join(line[2:].strip() for line in source.read_text().splitlines()
                      if line.startswith('# '))
    baseline = int(re.search(r'The baseline is row (\d+)', header)[1])
    xheight = int(re.search(r'x-height (?:row )?(\d+)', header)[1])
    original = glyphs.pixel_face(em)
    drawn = {ch: shear(rows, adv, baseline, em) for ch, (adv, rows) in original.items()}
    different = sum((adv, rows) != original[ch] for ch, (adv, rows, _) in drawn.items())
    # A grid which cannot express a slant gets no fake italic asset.
    if not different:
        print(f'{em}: no distinct italic at this grid; keep explicit fallback')
        return
    lines = [
        f'# Neuronte italic desktop face at an em of {em} pixels: printable ASCII and',
        '# the ellipsis, derived from this project\'s upright pixel drawing.',
        '# No external font or widths were used. Rows shear about the baseline',
        '# by (baseline - row) / 4, rounded to nearest with ties away from zero.',
        '# Preserve the left bearing where it fits; reduce shear for a glyph',
        '# wider than its cell. No ink pixel is clipped. Advances gain the added',
        '# ink span; bold adds the usual one-pixel strike in the drawer.',
        f'# The baseline is row {baseline} and the x-height row {xheight}; in the drawn cell',
        f'# the baseline is row {glyphs.UI_TOP[em] + baseline} below the pen (UI_TOP {glyphs.UI_TOP[em]}).',
        '# Generated reproducibly by tools/make-italic.py.',
    ]
    for ch, (adv, rows, _) in drawn.items():
        label = f'U+{ord(ch):04X}' if ch in (' ', '#') else ch
        lines += [f'{label} {adv}', *rows]
    dest.write_text('\n'.join(lines) + '\n')
    assert len(glyphs.pixel_face(em, str(dest))) == 96
    reduced = sum(divisor > 4 for _, _, divisor in drawn.values())
    print(f'{em}: {different}/96 changed drawings or advances; {reduced} reduced-shear glyphs')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sizes', nargs='+', type=int, choices=range(1, 33))
    for size in parser.parse_args().sizes:
        draw(size)
