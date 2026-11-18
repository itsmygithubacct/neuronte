#!/usr/bin/env python3
"""Make the Latin-1 pixel faces: font/ui-EM-latin1.txt and font/ui-EM-latin1-italic.txt.

usage: python3 tools/make-latin1-face.py --write EM [--signs FILE]
       python3 tools/make-latin1-face.py --check

A Latin-1 face holds the 96 characters of font/ui-EM.txt, copied block for
block, then U+00A0..U+00FF. Of those, the 58 that are a letter and a mark
(by the Unicode decomposition), U+00A0 and the four spacing marks are made
here from the face's own letters and the marks drawn for that em in
font/ui-latin1-marks.txt. The other 38 (glyphs.LATIN1_SIGNS) are drawn by
hand in font/ui-EM-latin1.txt itself; --write keeps them as they are (or
takes them from --signs FILE, a face file holding them, the first time).

Composition, by the face's rows (baseline and x-height from its header,
the cap top from H):
- a mark above a small letter sits over the letter's ink, centred, its
  lowest row one clear row above the x-height (no clear row if there is
  no room); i loses its dot. The first variant of the mark, in file order,
  that fits in the em is used.
- a mark above a capital (its NAME.cap variant where one is drawn for the
  em) sits in the top rows of the em, one clear row above the capital
  (none below 9 px). The capital is lowered onto the
  baseline by leaving out as many of its rows as the mark needs: each
  time the inner row most like the row above it (fewest pixels differ),
  the upper one of a tie, so that straight stems shorten first.
- the cedilla hangs from the row below the baseline, under the middle of
  the letter's lowest ink row; at 3 px, where there is no row below the
  baseline, it is left out.
- U+00A0 is the space; the spacing marks (U+00A8, U+00AF, U+00B4, U+00B8)
  stand alone at the grave accent's advance, where they stand over a small
  letter (the cedilla below the baseline).
The advance is always the base letter's. Rows never grow past the em.
At 1 and 2 px there is no row for a mark: each letter with a mark is its
letter, U+00A0 the space, and each spacing mark the grave accent.

The italic face is the upright Latin-1 face sheared by tools/make-italic.py's
rule (one column per four rows about the baseline), as every italic face
from 3 px is made from its upright face. --check rebuilds every face and its
italic in memory and compares them with the files.
"""
import argparse
import importlib.util
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import glyphs  # noqa: E402

_spec = importlib.util.spec_from_file_location('make_italic', ROOT / 'tools' / 'make-italic.py')
make_italic = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(make_italic)

MARKS_FILE = ROOT / 'font' / 'ui-latin1-marks.txt'
EMS = range(1, 17)
ITALIC_EMS = range(3, 17)
COMBINING = {0x300: 'grave', 0x301: 'acute', 0x302: 'circumflex', 0x303: 'tilde', 0x308: 'diaeresis',
             0x30A: 'ring', 0x327: 'cedilla'}
SPACING = {0xA8: 'diaeresis', 0xAF: 'macron', 0xB4: 'acute', 0xB8: 'cedilla'}


def path(em, italic=False):
    return ROOT / 'font' / f'ui-{em}-latin1{"-italic" if italic else ""}.txt'


def metrics(em):
    """(baseline row, x-height row) from font/ui-EM.txt's header."""
    head = ' '.join(l[2:].strip() for l in (ROOT / 'font' / f'ui-{em}.txt').read_text().splitlines()
                    if l.startswith('# '))
    return (int(re.search(r'baseline is row (\d+)', head)[1]),
            int(re.search(r'x-height (?:row )?(\d+)', head)[1]))


def read_marks():
    """{name: [(ems, rows)]} in file order. A block is 'NAME LO-HI' then its rows."""
    out, cur = {}, None
    for num, raw in enumerate(MARKS_FILE.read_text().splitlines(), 1):
        if raw.startswith('# ') or not raw:
            continue
        if ' ' in raw:
            name, _, span = raw.partition(' ')
            lo, _, hi = span.partition('-')
            cur = []
            out.setdefault(name, []).append((range(int(lo), int(hi or lo) + 1), cur))
        elif cur is None or set(raw) - set('.#'):
            raise ValueError(f'{MARKS_FILE}:{num}: a row is . and #, after a mark line')
        else:
            cur.append(raw)
    for name, variants in out.items():
        for _, rows in variants:
            if not rows or len({len(r) for r in rows}) != 1:
                raise ValueError(f'{MARKS_FILE}: a variant of {name} is not rows of one length')
    return out


def ink(rows):
    return {(x, y) for y, r in enumerate(rows) for x, v in enumerate(r) if v == '#'}


def draw(pixels, width, em):
    width = max([width] + [x + 1 for x, _ in pixels])
    if width > em or any(x < 0 or not 0 <= y < em for x, y in pixels):
        raise ValueError('a composed letter does not fit in the em')
    return [''.join('#' if (x, y) in pixels else '.' for x in range(width)) for y in range(em)]


def lowered(pixels, n):
    """The capital with n of its inner rows left out, moved down onto its old bottom."""
    pixels = set(pixels)
    for _ in range(n):
        ys = sorted({y for _, y in pixels})
        top, bottom = ys[0], ys[-1]
        row = lambda y: {x for x, yy in pixels if yy == y}
        best = min(range(top + 1, bottom), key=lambda y: (len(row(y) ^ row(y - 1)), y))
        pixels = {(x, y + 1 if y < best else y) for x, y in pixels if y != best}
    return pixels


def placed(mark_rows, cx, bottom, em):
    """The mark's pixels with its middle column at cx and its last row at row bottom, moved right
    or left to stay in the em's columns; rows below the em are left out (a cedilla at 3 px)."""
    w, h = len(mark_rows[0]), len(mark_rows)
    x0 = min(max(0, round(cx - (w - 1) / 2)), em - w)
    return {(x0 + x, bottom - h + 1 + y) for x, y in ink(mark_rows) if bottom - h + 1 + y < em}


def compose(em, face, marks):
    """{char: (advance, rows)} for U+00A0 and the 57 + 4 characters made from a letter or alone."""
    base_row, x_row = metrics(em)
    cap_top = min(y for _, y in ink(face['H'][1]))
    variants = {n: [rows for ems, rows in v if em in ems] for n, v in marks.items()}
    out = {'\u00a0': face[' ']}
    tiny = em <= 2
    for c in range(0xA1, 0x100):
        ch = chr(c)
        nfd = unicodedata.normalize('NFD', ch)
        if c in SPACING:
            letter, name = None, SPACING[c]
        elif len(nfd) == 2 and nfd[0] in face and ord(nfd[1]) in COMBINING:
            letter, name = nfd[0], COMBINING[ord(nfd[1])]
        else:
            continue
        if tiny:
            out[ch] = face[letter or '`']
            continue
        if not variants[name]:
            raise ValueError(f'{em} px: no {name} is drawn for this em')
        adv, rows = face[letter or '`']
        pix = set() if letter is None else ink(rows)
        width = len(rows[0])
        if letter == 'i' and name != 'cedilla':
            pix = {(x, y) for x, y in pix if y >= x_row}
        if letter is None:
            cx = (width - 1) / 2
        else:
            xs = [x for x, _ in pix]
            cx = (min(xs) + max(xs)) / 2
        if name == 'cedilla':
            low = max(y for _, y in pix) if pix else base_row
            xs = [x for x, y in pix if y == low] or [round(cx)]
            mark = variants[name][0]
            pix |= placed(mark, (min(xs) + max(xs)) / 2, base_row + len(mark), em)
        elif letter is not None and letter.isupper():
            mark = (variants.get(name + '.cap') or variants[name])[0]
            gap = 1 if em >= 9 else 0
            need = len(mark) + gap - cap_top
            body = lowered(pix, need) if need > 0 else pix
            pix = body | placed(mark, cx, len(mark) - 1, em)
        else:
            for mark in variants[name]:
                for gap in (1, 0):
                    bottom = x_row - 1 - gap
                    if bottom - len(mark) + 1 >= 0:
                        break
                else:
                    continue
                break
            else:
                raise ValueError(f'{em} px: no {name} fits over a small letter')
            pix |= placed(mark, cx, bottom, em)
        out[ch] = (adv, draw(pix, width, em))
    return out


def label(ch):
    return f'U+{ord(ch):04X}' if ch in ' #' or not ch.isprintable() or ch in '\u00a0\u00ad' else ch


def header(em):
    base_row, x_row = metrics(em)
    return [
        f'# Neuronte desktop face at an em of {em} pixel{"s" if em > 1 else ""}, with all of Latin-1: the 96',
        f'# characters of font/ui-{em}.txt, copied unchanged, then U+00A0..U+00FF, as',
        '# pixels. Written for this project. No font was read, and no width was',
        '# copied. U+00A0, the letters with a mark and the spacing marks are made',
        f'# by tools/make-latin1-face.py from this face\'s own letters and the marks',
        '# drawn for this em in font/ui-latin1-marks.txt. The other 38 characters',
        '# are drawn here by hand, from their Unicode names and this face\'s own',
        '# letters; U+00AD, the soft hyphen, is drawn as the hyphen.',
        f'# The baseline is row {base_row} and the x-height row {x_row}; in the drawn cell',
        f'# the baseline is row {glyphs.UI_TOP[em] + base_row} below the pen (UI_TOP {glyphs.UI_TOP[em]}).',
        '# Bold is the same letter struck twice, one pixel apart, by the drawer.',
    ]


def render(lines, glyph_map):
    for ch, (adv, rows) in glyph_map.items():
        lines += [f'{label(ch)} {adv}', *rows]
    return '\n'.join(lines) + '\n'


def build(em, signs):
    face = glyphs.pixel_face(em)
    made = compose(em, face, read_marks())
    if sorted(signs) != sorted(glyphs.LATIN1_SIGNS):
        raise ValueError(f'{em} px: the hand-drawn characters must be exactly the 38 signs')
    latin = {**made, **signs}
    full = {**face, **{chr(c): latin[chr(c)] for c in range(0xA0, 0x100)}}
    return full


def italic_text(em, full):
    base_row, x_row = metrics(em)
    lines = [
        f'# Neuronte italic desktop face at an em of {em} pixels, with all of Latin-1:',
        f'# font/ui-{em}-latin1.txt sheared by tools/make-latin1-face.py with',
        '# tools/make-italic.py\'s rule: rows shear about the baseline by',
        '# (baseline - row) / 4, rounded to nearest with ties away from zero; a',
        '# glyph too wide for its cell is sheared less; no ink pixel is clipped;',
        '# the advance gains the added ink span. Its 96 ASCII characters are',
        f'# font/ui-{em}-italic.txt\'s. No font was read, and no width was copied.',
        f'# The baseline is row {base_row} and the x-height row {x_row}; in the drawn cell',
        f'# the baseline is row {glyphs.UI_TOP[em] + base_row} below the pen (UI_TOP {glyphs.UI_TOP[em]}).',
        '# Bold is the same letter struck twice, one pixel apart, by the drawer.',
    ]
    sheared = {ch: make_italic.shear(rows, adv, base_row, em)[:2] for ch, (adv, rows) in full.items()}
    return render(lines, sheared)


def signs_of(file, em):
    g = glyphs.pixel_face(em, file)
    return {c: g[c] for c in glyphs.LATIN1_SIGNS}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--write', type=int)
    ap.add_argument('--signs')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    if a.write:
        em = a.write
        signs = signs_of(a.signs or path(em), em)
        full = build(em, signs)
        path(em).write_text(render(header(em), full))
        if em in ITALIC_EMS:
            path(em, True).write_text(italic_text(em, full))
        print(f'{em}: wrote {path(em).name}' + (f' and {path(em, True).name}' if em in ITALIC_EMS else ''))
    elif a.check:
        bad = 0
        for em in EMS:
            if not path(em).exists():
                print(f'{em}: no {path(em).name}')
                bad += 1
                continue
            full = build(em, signs_of(path(em), em))
            if path(em).read_text() != render(header(em), full):
                print(f'{em}: {path(em).name} is not what the tool makes from its sources')
                bad += 1
            if em in ITALIC_EMS:
                if not path(em, True).exists() or path(em, True).read_text() != italic_text(em, full):
                    print(f'{em}: {path(em, True).name} is not the shear of the upright face')
                    bad += 1
                it = glyphs.pixel_face(em, path(em, True))
                old = glyphs.pixel_face(em, glyphs.UI_ITALIC[em])
                if any(it[c] != old[c] for c in old):
                    print(f'{em}: the italic ASCII differs from font/ui-{em}-italic.txt')
                    bad += 1
            g = glyphs.pixel_face(em, path(em))
            if any(g[c] != v for c, v in glyphs.pixel_face(em).items()):
                print(f'{em}: the ASCII differs from font/ui-{em}.txt')
                bad += 1
        if bad:
            raise SystemExit(1)
        print(f'Latin-1 faces 1-16 px and italics 3-16 px match their sources')
    else:
        ap.error('--write EM or --check')


if __name__ == '__main__':
    main()
