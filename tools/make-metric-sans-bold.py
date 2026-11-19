#!/usr/bin/env python3
"""Make the drawn bold pixel faces of Neuronte Sans Metric:
font/metric-sans-EM-bold.txt and font/metric-sans-EM-bold-italic.txt, EM = 9..16,
and their advances, font/metric-sans-EM-bold.advances.txt.

usage: python3 tools/make-metric-sans-bold.py --write EM [EM ...]
       python3 tools/make-metric-sans-bold.py --check

Why: the pixel faces' packed bold is the regular letter struck twice, one
pixel apart, so it is a column wider; Helvetica-Bold is only about 18/1000 em
wider than Helvetica, so at these sizes most bold advances come to the regular
advance's pixels and the strike fills the clear column between letters. These
faces are bold DRAWN to Helvetica-Bold's advances with one clear column. A
caller draws bold text from the -bold file with bold = 0.

Each face is drawn from the same source as the regular metric face,
font/ui-EM-latin1.txt (this project's own drawing), with the rules of
tools/make-metric-sans-face.py, which are imported, not changed:

- The bold advance is round(bold width * EM / 1000), Helvetica-Bold's, from
  font/metric-sans-widths.txt (numbers copied from Adobe's Core 14 AFM files;
  no font file is opened here).
- A base character's bold ink is n columns: the regular AFM ink box's width
  plus the bold width's extra (bold width - width), in pixels, but at most the
  bold advance less its left side bearing and one clear column. The source's
  ink is resampled row by row to n - 1 columns (rowmap(), so a stem stays one
  column), placed at the regular box's left side bearing, and then struck: each
  pixel also inks the pixel to its right, except where that would close a
  one-column gap between two inked pixels of the row (so the counters of m, w,
  M, W, # and the like stay open). Stems become two columns.
  Two kinds of character are not struck but drawn at the full bold ink width
  in one-column strokes: one whose struck body would be a solid bar (its
  body would be one column though its source is wider: ( ) [ ] / and the
  like at the smaller ems), and one whose strike would close a counter
  (© ® ° and the like: fewer counters than in the source drawing). The
  header lists them.
- The letters with marks, U+00A0 and the spacing marks are composed from the
  unstruck bases by tools/make-latin1-face.py's rules and then struck alike.
  A row whose strike would pass the clear column stays unstruck: the marks
  over a narrow letter, and a letter with room for one column of ink. A mark
  that is itself wider than the room keeps no clear column, as in the
  regular face; the header lists those.
- A character drawn by hand in font/metric-sans-bold-fixes.txt for this em
  replaces what the rules made (its advance is still Helvetica-Bold's).
- The italic is the upright bold sheared about the baseline, as the regular
  metric italic is (tools/make-metric-sans-face.py's pure_shear()).
- Rows are not resampled: each face keeps the heights it was drawn with.
- No character is shifted: the ink starts at or right of the pen.

--check rebuilds every face in memory and compares it with the files.

The advances file is a fine advances file for train/pack.py: U+XXXX, then the
"regular" and "bold" advance, both Helvetica-Bold's width in thousandths, and
two zero shifts. The file's packed bold (bold = 1) would strike the bold again;
it is not meant to be used.
"""
import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


face = _load('make_metric_sans_face', 'make-metric-sans-face.py')
latin1, italic, widths_mod, glyphs = face.latin1, face.italic, face.widths_mod, face.glyphs
px, columns, rowmap = face.px, face.columns, face.rowmap

EMS = range(9, 17)
FIXES = ROOT / 'font' / 'metric-sans-bold-fixes.txt'


def path(em, kind=''):
    return ROOT / 'font' / f'metric-sans-{em}-bold{kind}.txt'


def fixes():
    """{em: {char: rows}} from font/metric-sans-bold-fixes.txt: blocks 'EM CHAR' then EM rows."""
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


def strike(rows, adv):
    """Each pixel also inks its right neighbour, unless that closes a one-column gap in the row.
    A row whose strike would pass the clear column (a mark wider than a narrow letter, or a
    letter with room for one column) stays as it was."""
    limit = adv - 1 if adv >= 3 else adv
    out = []
    for r in rows:
        r = r.ljust(adv, '.')
        s = list(r)
        for x in range(1, len(r)):
            if r[x] == '.' and r[x - 1] == '#':
                if x + 1 < len(r) and r[x + 1] == '#':
                    continue  # a one-column gap: keep it open
                s[x] = '#'
        struck = ''.join(s).rstrip('.')
        out.append(struck if len(struck) <= limit else r.rstrip('.'))
    w = max(1, max((len(r) for r in out), default=0))  # a blank keeps one column, as in the regular face
    return [r.ljust(w, '.') for r in out]


def holes(rows):
    """The number of enclosed counters: 8-connected regions of blank pixels that do not reach the edge
    (8-connected, so the blank pixels a diagonal stroke steps around are not counted)."""
    if not rows or not rows[0]:
        return 0
    H, W = len(rows), max(len(r) for r in rows)
    g = [r.ljust(W, '.') for r in rows]
    seen, n = set(), 0
    for y in range(H):
        for x in range(W):
            if g[y][x] != '.' or (y, x) in seen:
                continue
            stack, edge = [(y, x)], False
            seen.add((y, x))
            while stack:
                cy, cx = stack.pop()
                if cy in (0, H - 1) or cx in (0, W - 1):
                    edge = True
                for ny, nx in ((cy + dy, cx + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx):
                    if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == '.' and (ny, nx) not in seen:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            n += not edge
    return n


def padded(rows, adv):
    """rows on a blank border, so that a counter open only at the cell's edge is not counted."""
    w = max(adv, max((len(r) for r in rows), default=0)) + 2
    return ['.' * w] + ['.' + r.ljust(w - 2, '.') + '.' for r in rows] + ['.' * w]


def base(em, rows, box, w, wb, badv, columns_out=None):
    """The unstruck bold drawing of one base character (n - 1 columns, at its side bearing)."""
    cols = columns(rows)
    inked = [i for i, c in enumerate(cols) if '#' in c]
    if not inked:
        return [r[:1] for r in rows] if rows and rows[0] else rows
    n = max(2, px(box[2] - box[0] + (wb - w), em))
    left = max(0, px(box[0], em) if box[0] >= 0 else 0)
    if badv >= 3:
        n = max(2, min(n, badv - 1))
        left = max(0, min(left, badv - 1 - n))
    body = rowmap(rows, inked[0], inked[-1], n if columns_out == 'full' else n - 1)
    return ['.' * left + r for r in body]


def build(em):
    chars, _ = widths_mod.read(ROOT / 'font' / 'metric-sans-widths.txt')
    src = glyphs.pixel_face(em, ROOT / 'font' / f'ui-{em}-latin1.txt')
    unstruck, plain = {}, set()
    for ch in face.BASES:
        w, wb, box, _ = chars[ord(ch)]
        badv = max(1, px(wb, em))
        rows = base(em, src[ch][1], box, w, wb, badv)
        srcw = len([c for c in columns(src[ch][1]) if '#' in c])
        bodyw = len([c for c in columns(rows) if '#' in c])
        if (bodyw == 1 and srcw >= 2) or holes(padded(strike(rows, badv), badv)) < holes(padded(src[ch][1], badv)):
            # a thin shape that the strike would make a bar, or a counter it would close:
            # drawn at the full bold width and not struck
            rows = base(em, src[ch][1], box, w, wb, badv, 'full')
            plain.add(ch)
        unstruck[ch] = (badv, rows)
    made = latin1.compose(em, unstruck, latin1.read_marks())
    full = {**unstruck, **made}
    for ch, (badv, rows) in made.items():
        b0 = latin1.unicodedata.normalize('NFD', ch)[0]
        if b0 in plain or holes(padded(strike(rows, badv), badv)) < holes(padded(rows, badv)):
            plain.add(ch)
    hand = fixes().get(em, {})
    out, wide = {}, []
    for cp in sorted(chars):
        ch = chr(cp)
        w, wb, _, _ = chars[cp]
        badv = max(1, px(wb, em))
        if ch in hand:
            rows = hand[ch]
            if len(rows) != em or any(len(r) > em for r in rows):
                raise ValueError(f'{em} px: the bold fix of U+{cp:04X} is not {em} rows of at most {em}')
        else:
            rows = full[ch][1] if ch in plain else strike(full[ch][1], badv)
        if any(len(r.rstrip('.')) > badv - (1 if badv >= 3 else 0) for r in rows):
            if ch in unstruck and ch not in hand:
                raise ValueError(f'{em} px: bold U+{cp:04X} leaves no clear column in its advance of {badv}')
            wide.append(ch)  # a composed letter whose mark is wider than the room, as in the regular face
        out[ch] = (badv, rows)
    return out, sorted(hand), wide, sorted(plain)


def header(em, hand, wide, plain, italic_face=False):
    base_row, x_row = latin1.metrics(em)
    kind = 'italic ' if italic_face else ''
    lines = [
        f'# Neuronte Sans Metric, drawn bold {kind}pixel face at an em of {em} pixels: the 192',
        '# characters of the desktop faces (printable ASCII, U+2026, U+00A0..U+00FF).',
        f'# Drawn by tools/make-metric-sans-bold.py from font/ui-{em}-latin1.txt, this',
        "# project's own drawing, to Helvetica-Bold's widths in font/metric-sans-widths.txt.",
        "# THE ADVANCES ARE COPIED from Adobe's Core 14 AFM metric files for Helvetica-Bold",
        '# (notice in LICENSES/Adobe-Core14-AFM.txt). No font file was opened. TeX Gyre',
        '# Heros (GUST Font License) was looked at as a reference while drawing, outside',
        '# this repository; nothing was copied or traced from it.',
        "# Rows are as drawn: the heights are this face's own, not Helvetica's.",
        f'# The baseline is row {base_row} and the x-height row {x_row}.',
        '# This IS the bold: draw it with bold = 0. Every letter keeps one clear column.',
        f'# Its advances are in font/metric-sans-{em}-bold.advances.txt.',
    ]
    if italic_face:
        lines.insert(3, "# Then sheared about the baseline (pure_shear()); the advances stay upright's.")
    if hand:
        lines.append('# Drawn by hand in font/metric-sans-bold-fixes.txt: ' + ' '.join(latin1.label(c) for c in hand) + '.')
    if plain:
        lines.append('# Not struck (a thin shape or a counter the strike would fill): ' + ' '.join(latin1.label(c) for c in plain) + '.')
    if wide:
        lines.append('# Marks wider than the room, so no clear column: ' + ' '.join(latin1.label(c) for c in wide) + '.')
    return lines


def texts(em):
    body, hand, wide, plain = build(em)
    chars, _ = widths_mod.read(ROOT / 'font' / 'metric-sans-widths.txt')
    up = latin1.render(header(em, hand, wide, plain), body)
    sh = ['#! neuronte fine advances',
          f'# Neuronte Sans Metric drawn bold at {em} px, from tools/make-metric-sans-bold.py: the',
          "# advance (twice: this face's regular is the bold) and two zero shifts, in thousandths",
          "# of an em. COPIED from Adobe's Core 14 AFM metric files for Helvetica-Bold",
          '# (font/metric-sans-widths.txt; notice in LICENSES/Adobe-Core14-AFM.txt).']
    for ch, (badv, _) in body.items():
        wb = chars[ord(ch)][1]
        if (wb * em + 500) // 1000 != badv:
            raise ValueError(f'{em} px: U+{ord(ch):04X} has no table entry for its pixels')
        sh.append(f'U+{ord(ch):04X} {wb} {wb} 0 0')
    base_row, _ = latin1.metrics(em)
    slanted = {ch: (adv, face.pure_shear(rows, base_row, em)) for ch, (adv, rows) in body.items()}
    return {path(em): up, path(em, '.advances'): '\n'.join(sh) + '\n',
            path(em, '-italic'): latin1.render(header(em, hand, wide, plain, True), slanted)}


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
            if em not in EMS:
                ap.error(f'the drawn bold is for {EMS.start} to {EMS.stop - 1} px')
            for p, t in texts(em).items():
                write(p, t)
            print(f'{em} px bold written')
    if a.check:
        bad = 0
        for em in EMS:
            for p, t in texts(em).items():
                if not p.exists() or p.read_text() != t:
                    print(f'DIFFERS: {p.name}')
                    bad += 1
        print('metric-sans bold faces:', 'all current' if not bad else f'{bad} differ')
        raise SystemExit(1 if bad else 0)
    if not a.write and not a.check:
        ap.error('--write EM or --check')


if __name__ == '__main__':
    main()
