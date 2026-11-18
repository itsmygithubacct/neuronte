#!/usr/bin/env python3
"""Make the pixel faces of Neuronte Sans Metric: font/metric-sans-EM.txt
(EM = 1..16) and font/metric-sans-EM-italic.txt (EM = 3..16).

usage: python3 tools/make-metric-sans-face.py --write EM [EM ...]
       python3 tools/make-metric-sans-face.py --check

Each face is redrawn from the desktop face of the same em,
font/ui-EM-latin1.txt, to the proportions in font/metric-sans-widths.txt
(numbers copied from Adobe's Core 14 AFM metric files; no font file is
opened here):

- A base character (printable ASCII, U+2026 and the 38 signs drawn by hand
  in the Latin-1 face) keeps its rows. Its ink columns are resampled to
  round((right - left) * EM / 1000) columns of the AFM ink box (at least 1),
  row by row: each run of ink in a row is mapped, its first and last column
  each to the nearest new column, so a stem stays one column and a bar
  grows or shrinks; where a diagonal's pixels in neighbouring rows would no
  longer touch, the columns between are inked, half in each row (see
  rowmap()). The ink is placed round(left * EM / 1000) columns right of the
  pen. Where that leaves no clear column inside the advance (an advance of
  2 pixels or more), the ink is first made narrower and then moved left
  until one column is clear, so that neighbouring letters never touch.
- The letters with marks, U+00A0 and the spacing marks are composed from
  these characters and font/ui-latin1-marks.txt by tools/make-latin1-face.py's
  rules, unchanged.
- Every advance is round(width * EM / 1000), a half going up: Helvetica's.
- Rows are not resampled: each face keeps the heights it was drawn with
  (baseline, x-height, cap height and the rows of the marks).
- A character whose AFM box starts left of the pen is drawn from column 0,
  and the face's version 8 table moves it left by the missing columns (its
  regular shift, below). Ink never passes the em.
- Last, any character drawn by hand in font/metric-sans-fixes.txt for this em
  replaces what the rules made (its advance is still Helvetica's); the file
  header lists them.

The italic face is the upright face sheared by tools/make-italic.py's rule,
with the upright advance: Helvetica-Oblique's widths are Helvetica's.

Bold, as in every desktop face, is the letter struck twice, one pixel apart.
The bold advance is round(bold width * EM / 1000); the bold shift centres the
wider strike in it: half of (bold advance - advance - 1) pixels, rounded down.

--check rebuilds every face in memory and compares it with the files.

Each face's advance table is written to font/metric-sans-EM.advances.txt, a
fine advances file for train/pack.py: U+XXXX, then the regular and bold
advance and the regular and bold shift, all in thousandths of an em. The
advances are Helvetica's widths, exactly, except where a width comes to less
than one pixel at this em (51 characters at 1 px, 4 at 2 px): those take the
least thousandths that come to one pixel, ceil(500 / EM). A shift of s pixels
is round(s * 1000 / EM), which the library rounds back to s at this em.
"""
import argparse
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import glyphs  # noqa: E402


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


latin1 = _load('make_latin1_face', 'make-latin1-face.py')
italic = _load('make_italic', 'make-italic.py')
widths_mod = _load('make_metric_sans_widths', 'make-metric-sans-widths.py')

EMS = range(1, 17)
ITALIC_EMS = range(3, 17)
FIXES = ROOT / 'font' / 'metric-sans-fixes.txt'
BASES = [chr(c) for c in range(0x20, 0x7F)] + ['…'] + list(glyphs.LATIN1_SIGNS)


def path(em, kind=''):
    return ROOT / 'font' / f'metric-sans-{em}{kind}.txt'


def px(v, em):
    """v thousandths of an em in whole pixels, the nearest, a half going up."""
    return (v * em + 500) // 1000


def columns(rows):
    w = len(rows[0]) if rows else 0
    return [''.join(r[x] for r in rows) for x in range(w)]


def from_columns(cols, em):
    return [''.join(c[y] for c in cols) for y in range(em)] if cols else ['' for _ in range(em)]




def rowmap(rows, lo, hi, n):
    """The ink between columns lo..hi of rows mapped onto n columns from 0.
    Column x goes to round((x - lo) * (n - 1) / (hi - lo)), counted from the
    nearer side so that a symmetric drawing stays symmetric (all to 0 when
    either span is one column); a run of ink in a row stays one run from the
    image of its first column to the image of its last. Two pixels of
    neighbouring rows that touched (also at a corner) still touch: where
    their images lie further apart, the upper row's run is drawn on toward
    the lower one."""
    span = hi - lo

    def g(t):
        return int(t * (n - 1) / span + 0.5)

    def f(x):  # mirrored about the middle, so a symmetric drawing stays symmetric
        if span == 0 or n == 1:
            return 0
        t = x - lo
        return g(t) if 2 * t <= span else n - 1 - g(span - t)

    em = len(rows)
    out = [set() for _ in range(em)]
    for y, r in enumerate(rows):
        x = lo
        while x <= hi:
            if r[x] == '#':
                a = x
                while x + 1 <= hi and r[x + 1] == '#':
                    x += 1
                out[y].update(range(f(a), f(x) + 1))
            x += 1
    for y in range(em - 1):
        for x in range(lo, hi + 1):
            if rows[y][x] != '#':
                continue
            for x2 in (x - 1, x, x + 1):
                if lo <= x2 <= hi and rows[y + 1][x2] == '#':
                    a, b = f(x), f(x2)
                    if abs(a - b) > 1:
                        step = 1 if b > a else -1
                        gap = list(range(a + step, b, step))
                        half = len(gap) // 2
                        out[y].update(gap[:half])
                        out[y + 1].update(gap[half:])
    return [''.join('#' if c in out[y] else '.' for c in range(n)) for y in range(em)]


def fixes():
    """{em: {char: rows}} from font/metric-sans-fixes.txt: blocks 'EM CHAR' then EM rows."""
    out, cur = {}, None
    if not FIXES.exists():
        return out
    for num, raw in enumerate(FIXES.read_text().splitlines(), 1):
        if raw.startswith('# ') or not raw.strip():
            continue
        if ' ' in raw:
            em, _, name = raw.partition(' ')
            ch = chr(int(name[2:], 16)) if name.startswith('U+') else name
            cur = []
            out.setdefault(int(em), {})[ch] = cur
        elif cur is None or set(raw) - set('.#'):
            raise ValueError(f'{FIXES}:{num}: a row is . and #, after an "EM CHAR" line')
        else:
            cur.append(raw)
    return out


def redraw(em, rows, box, adv):
    """(rows, regular shift in pixels) of one base character."""
    cols = columns(rows)
    inked = [i for i, c in enumerate(cols) if '#' in c]
    if not inked:
        return [r[:1] for r in rows] if rows and rows[0] else rows, 0
    n = max(1, px(box[2] - box[0], em))
    left = px(box[0], em) if box[0] >= 0 else -px(-box[0], em)
    shift = min(0, left)
    left = max(0, left)
    n = min(n, em - left)
    if adv >= 2:  # one clear column in the advance, so neighbours never touch
        n = max(1, min(n, adv - 1))
        left = max(0, min(left, adv - 1 - n))
    body = rowmap(rows, inked[0], inked[-1], n)
    return ['.' * left + r for r in body], shift


def build(em):
    chars, _ = widths_mod.read(ROOT / 'font' / 'metric-sans-widths.txt')
    src = glyphs.pixel_face(em, ROOT / 'font' / f'ui-{em}-latin1.txt')
    face, shifts = {}, {}
    for ch in BASES:
        w, wb, box, _ = chars[ord(ch)]
        rows, sh = redraw(em, src[ch][1], box, max(1, px(w, em)))
        face[ch] = (max(1, px(w, em)), rows)
        if sh:
            shifts[ch] = sh
    made = latin1.compose(em, face, latin1.read_marks())
    full = {**face, **made}
    hand = fixes().get(em, {})
    for ch, rows in hand.items():
        if len(rows) != em or any(len(r) > em for r in rows):
            raise ValueError(f'{em} px: the fix of U+{ord(ch):04X} is not {em} rows of at most {em}')
        full[ch] = (full[ch][0], rows)
    out = {}
    for cp in sorted(chars):
        ch = chr(cp)
        w, wb, box, _ = chars[cp]
        adv, rows = full[ch]
        adv = max(1, px(w, em))
        bold = max(1, px(wb, em))
        reg = shifts.get(ch, 0)
        if ch not in face and ch not in hand:  # composed: the base letter's shift
            base = latin1.unicodedata.normalize('NFD', ch)[0]
            reg = shifts.get(base, 0)
        out[ch] = (adv, rows, reg, reg + max(0, bold - adv - 1) // 2, bold)
    return out, sorted(hand)


def header(em, hand, italic_face=False):
    base_row, x_row = latin1.metrics(em)
    kind = 'italic ' if italic_face else ''
    lines = [
        f'# Neuronte Sans Metric, {kind}pixel face at an em of {em} pixel{"s" if em > 1 else ""}: the 192',
        '# characters of the desktop faces (printable ASCII, U+2026, U+00A0..U+00FF).',
        f'# Redrawn by tools/make-metric-sans-face.py from font/ui-{em}-latin1.txt, this',
        "# project's own drawing, to the widths and ink boxes in font/metric-sans-widths.txt.",
        "# THE ADVANCES ARE COPIED from Adobe's Core 14 AFM metric files for Helvetica",
        '# (notice in LICENSES/Adobe-Core14-AFM.txt). No font file was opened. TeX Gyre',
        '# Heros (GUST Font License) was looked at as a reference while drawing, outside',
        '# this repository; nothing was copied or traced from it.',
        '# Rows are as drawn: the heights are this face\'s own, not Helvetica\'s.',
        f'# The baseline is row {base_row} and the x-height row {x_row}; in the drawn cell',
        f'# the baseline is row {glyphs.UI_TOP[em] + base_row} below the pen (UI_TOP {glyphs.UI_TOP[em]}).',
        '# Bold is the same letter struck twice, one pixel apart, by the drawer;',
        f'# its advances and shifts are in font/metric-sans-{em}.advances.txt.',
    ]
    if italic_face:
        lines.insert(3, "# Then sheared by tools/make-italic.py's rule; the advances stay upright's.")
    if hand:
        lines.append('# Drawn by hand in font/metric-sans-fixes.txt: ' + ' '.join(latin1.label(c) for c in hand) + '.')
    return lines


def texts(em):
    face, hand = build(em)
    body = {ch: (adv, rows) for ch, (adv, rows, _, _, _) in face.items()}
    up = latin1.render(header(em, hand), body)
    chars, _ = widths_mod.read(ROOT / 'font' / 'metric-sans-widths.txt')
    least = -(-500 // em)  # the fewest thousandths that come to one pixel
    sh = ['#! neuronte fine advances',
          f'# Neuronte Sans Metric at {em} px, from tools/make-metric-sans-face.py: regular and',
          '# bold advance, regular and bold shift (+ is right), in thousandths of an em.',
          "# The advances are COPIED from Adobe's Core 14 AFM metric files for Helvetica",
          '# (font/metric-sans-widths.txt; notice in LICENSES/Adobe-Core14-AFM.txt),',
          f'# except that none is less than {least}, one pixel at this em.']
    for ch, (adv, _, r, b, ba) in face.items():
        w, wb, _, _ = chars[ord(ch)]
        m, mb = max(w, least), max(wb, least)
        sm, sb = round(r * 1000 / em), round(b * 1000 / em)
        if (m * em + 500) // 1000 != adv or (mb * em + 500) // 1000 != ba or abs(sm) > 500 or abs(sb) > 500:
            raise ValueError(f'{em} px: U+{ord(ch):04X} has no table entry for its pixels')
        sh.append(f'U+{ord(ch):04X} {m} {mb} {sm} {sb}')
    out = {path(em): up, path(em, '.advances'): '\n'.join(sh) + '\n'}
    if em in ITALIC_EMS:
        base_row, _ = latin1.metrics(em)
        slanted = {ch: (adv, italic.shear(rows, adv, base_row, em)[1]) for ch, (adv, rows) in body.items()}
        out[path(em, '-italic')] = latin1.render(header(em, hand, True), slanted)
    return out


def write(p, text):
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(text)
    tmp.replace(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--write', type=int, nargs='+')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    if a.write:
        for em in a.write:
            for p, t in texts(em).items():
                write(p, t)
            print(f'{em} px written')
    if a.check:
        bad = 0
        for em in EMS:
            for p, t in texts(em).items():
                if not p.exists() or p.read_text() != t:
                    print(f'DIFFERS: {p.name}')
                    bad += 1
        print('metric-sans faces:', 'all current' if not bad else f'{bad} differ')
        raise SystemExit(1 if bad else 0)
    if not a.write and not a.check:
        ap.error('--write EM or --check')


if __name__ == '__main__':
    main()
