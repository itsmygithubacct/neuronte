"""Neuronte Sans Metric above 16 pixels: the strokes of the large desktop face
(font/ui-large.txt, font/ui-large-latin1-signs.txt and the Latin-1 letters
train/glyphs.py composes from them), redrawn to Helvetica's proportions.

The proportions are numbers only, copied from Adobe's Core 14 AFM metric files
into font/metric-sans-widths.txt (tools/make-metric-sans-widths.py): each
character's advance and ink box, and the font's cap height, x-height and
descender. No font file is opened here. TeX Gyre Heros was looked at, outside
this repository, as a reference while these rules were chosen; nothing is
read from it.

The rules, in order:
1. Heights. One piecewise-linear map of y for every character, the baseline
   fixed: the stroke centres of the x-height, the cap height and the
   descender move to where a stroke of this pen has its ink edge at the AFM's
   XHeight, CapHeight and Descender. Ascenders stay at the top of the
   cell's ink band (their ink 0.75 em above the baseline, Helvetica's
   0.718: the band allows no more, and taking them down to the cap height
   would flatten the hooks of f and the like). Above the ascender and below
   the descender y moves without scaling.
2. Widths. Each base character (ASCII, U+2026 and the 38 drawn signs) is moved
   and scaled across so that its ink, stroke centres plus the pen radius,
   spans the AFM box's left..right. The pen is not scaled: stems keep the
   face's weight (3/32 em; the AFM's stem is 88/1000). A character whose ink
   is one stem across is moved, not scaled.
3. The Latin-1 letters with marks are composed from the new base letters and
   font/marks.txt by glyphs.large_latin1()'s rules, with the new x-height and
   cap height.
4. A drawing whose ink would start left of the pen (the AFM box starts left
   of 0, e.g. j and /) is moved right until it starts at 0, and its regular
   shift (advance table version 8) is minus that amount, so it is drawn where
   the AFM puts it. Ink must end inside the em and stay in the cell's band.
"""
import os

import glyphs
import strokes

ROOT = strokes.ROOT
WIDTHS = os.path.join(ROOT, "font", "metric-sans-widths.txt")
PEN = glyphs.PENS["uilarge"]
BASE = glyphs.LARGE_BASELINE
OLD = {"desc": 1.55, "base": BASE, "x": glyphs.LARGE_XHEIGHT, "cap": glyphs.LARGE_CAP, "asc": 0.65}
BAND = glyphs.LARGE_INK
BOLD_REF_EM = 16  # the em at which a bold shift centres the one-pixel strike


def widths():
    """{scalar: (width, bold width, (llx, lly, urx, ury), name)}, {metric: (regular, bold)}."""
    chars, metrics = {}, {}
    for line in open(WIDTHS, encoding="utf-8"):
        t = line.split()
        if line.startswith("M "):
            metrics[t[1]] = (int(t[2]), int(t[3]))
        elif line.startswith("U+"):
            chars[int(t[0][2:], 16)] = (int(t[1]), int(t[2]), tuple(int(v) for v in t[3:7]), t[7])
    return chars, metrics


def knots():
    _, m = widths()
    new = {"desc": BASE - m["Descender"][0] / 1000 - PEN, "base": BASE,
           "x": BASE - m["XHeight"][0] / 1000 + PEN, "cap": BASE - m["CapHeight"][0] / 1000 + PEN,
           "asc": BAND[0] + PEN}
    order = ["asc", "cap", "x", "base", "desc"]
    return [(OLD[k], new[k]) for k in order]


def map_y(y, ks=None):
    ks = ks or knots()
    if y <= ks[0][0]:
        return y + ks[0][1] - ks[0][0]
    if y >= ks[-1][0]:
        return y + ks[-1][1] - ks[-1][0]
    for (a0, b0), (a1, b1) in zip(ks, ks[1:]):
        if a0 <= y <= a1:
            return b0 + (y - a0) * (b1 - b0) / (a1 - a0)
    raise AssertionError(y)


def ink_x(shapes):
    xs = [x for x, _ in glyphs.points(shapes)]
    return (min(xs), max(xs)) if xs else None


def fit_x(shapes, box):
    """Move and scale across so the ink spans the box's left..right (em)."""
    span = ink_x(shapes)
    if span is None:
        return shapes
    lo, hi = span
    left, right = box[0] / 1000 + PEN, box[2] / 1000 - PEN
    if hi - lo < 1e-6 or right - left < 1e-6:
        c = (box[0] + box[2]) / 2000
        m = (lo + hi) / 2
        return glyphs.moved(shapes, lambda x, y: (x - m + c, y))
    k = (right - left) / (hi - lo)
    return glyphs.moved(shapes, lambda x, y: (left + (x - lo) * k, y))


def bases():
    """{char: shapes}: ASCII, U+2026 and the 38 signs, heights mapped and widths fitted."""
    chars, _ = widths()
    ks = knots()
    src = dict(strokes.parse(glyphs.UI_LARGE))
    src.update(glyphs.large_signs())
    out = {}
    for ch, shapes in src.items():
        if ord(ch) not in chars:
            raise ValueError(f"U+{ord(ch):04X} has no AFM width")
        mapped = glyphs.moved(shapes, lambda x, y: (x, map_y(y, ks)))
        out[ch] = fit_x(mapped, chars[ord(ch)][2])
    return out


def composed(base):
    """glyphs.large_latin1()'s letters with marks, from these base letters."""
    g = glyphs
    ks = dict(zip(["asc", "cap", "x", "base", "desc"], [b for _, b in knots()]))
    xh, cap = ks["x"], ks["cap"]
    marks = {ord(c): m for c, m in strokes.parse(g.MARKS).items()}
    out = {" ": base[" "]}
    import unicodedata
    for c in range(0xA1, 0x100):
        ch = chr(c)
        nfd = unicodedata.normalize("NFD", ch)
        if c in g.SPACING:
            letter, mark = None, g.SPACING[c]
        elif len(nfd) == 2 and nfd[0] in base and ord(nfd[1]) in marks:
            letter, mark = nfd[0], ord(nfd[1])
        else:
            continue
        shapes = [] if letter is None else base[letter]
        k = g.LARGE_MARK
        if mark in g.ABOVE:
            if letter in g.DOTLESS:
                shapes = [sh for sh in shapes if max(y for _, y in g.points([sh])) > xh - 0.01]
            capital = letter is not None and letter.isupper()
            xs = [x for x, _ in g.points(shapes)] or [0.0]
            cx = (min(xs) + max(xs)) / 2
            if capital:
                f = (BASE - g.LARGE_SHORT_TOP) / (BASE - cap)
                shapes = g.moved(shapes, lambda x, y, f=f: (x, BASE - (BASE - y) * f))
                low = max(y for _, y in g.points(marks[mark]))
                top = g.LARGE_SHORT_TOP - g.LARGE_CAP_GAP
                fy = lambda y, low=low, top=top: top - (low - y) * k * g.LARGE_CAP_FLAT
            else:
                fy = lambda y: xh - (g.XHEIGHT - y) * k
        elif mark in g.BELOW:
            cx = 0.0 if letter is None else g.bottom_x(shapes)
            fy = lambda y: BASE + (y - g.BASELINE) * k
        else:
            continue
        if letter is None:  # a spacing mark: in the middle of its own AFM box
            chars, _ = widths()
            b = chars[c][2]
            cx = (b[0] + b[2]) / 2000
        drawn = g.moved(marks[mark], lambda x, y, cx=cx, fy=fy: (cx + (x - 0.5) * k, fy(y)))
        # a mark above that would leave the band keeps its gap to the letter
        # and is made shorter, about its lowest point, until it fits
        ys = [y for _, y in g.points(drawn)]
        top, low = min(ys), max(ys)
        if top - PEN < BAND[0]:
            if low - top < 1e-6:
                raise ValueError(f"U+{c:04X}: a flat mark above the band")
            f = (low - (BAND[0] + PEN)) / (low - top)
            drawn = g.moved(drawn, lambda x, y, f=f, low=low: (x, low - (low - y) * f))
        out[ch] = shapes + drawn
    return out


def drawings():
    """{char: (shapes, regular shift, bold shift)} for all 192 characters, shifts in thousandths."""
    chars, _ = widths()
    base = bases()
    allg = dict(base)
    allg.update(composed(base))
    if sorted(map(ord, allg)) != sorted(chars):
        raise ValueError("the drawings and the widths file differ")
    out = {}
    for ch, shapes in allg.items():
        w, wb, _, _ = chars[ord(ch)]
        span = ink_x(shapes)
        shift = 0
        if span is not None:
            d = max(0.0, PEN - span[0])
            if d > 0:
                shapes = glyphs.moved(shapes, lambda x, y, d=d: (x + d, y))
                shift = -round(d * 1000)
            if span[1] + d + PEN > 1.0 + 1e-9:
                raise ValueError(f"U+{ord(ch):04X}: ink past the em")
            ys = [y for _, y in glyphs.points(shapes)]
            if min(ys) - PEN < BAND[0] - 1e-9 or max(ys) + PEN > BAND[1] + 1e-9:
                raise ValueError(f"U+{ord(ch):04X}: ink outside the band {BAND}")
        bold = shift + round(max(0, (wb - w) - 1000 / BOLD_REF_EM) / 2)
        out[ch] = (shapes, shift, max(-500, min(500, bold)))
    return out


def tier():
    d = drawings()
    return [(c, d[c][0]) for c in sorted(d)]


def advances():
    """[(scalar, regular, bold, regular shift, bold shift)], thousandths, for the version 8 table."""
    chars, _ = widths()
    d = drawings()
    return [(cp, chars[cp][0], chars[cp][1], d[chr(cp)][1], d[chr(cp)][2]) for cp in sorted(chars)]


ADVANCES = os.path.join(ROOT, "font", "metric-sans-advances.txt")


def advances_text():
    """The fine advances file of the large and scaled face (train/pack.py)."""
    lines = ["#! neuronte fine advances",
             "# Neuronte Sans Metric above 16 px (the large and the scaled face), from",
             "# train/metric_sans.py: regular and bold advance, regular and bold shift",
             "# (+ is right), in thousandths of an em. The advances are COPIED from Adobe's",
             "# Core 14 AFM metric files for Helvetica (font/metric-sans-widths.txt; notice",
             "# in LICENSES/Adobe-Core14-AFM.txt). The shifts are this face's own."]
    lines += [f"U+{cp:04X} {r} {b} {rs} {bs}" for cp, r, b, rs, bs in advances()]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys
    text = advances_text()
    if sys.argv[1:] == ["--check"]:
        same = os.path.exists(ADVANCES) and open(ADVANCES, encoding="utf-8").read() == text
        print("metric-sans-advances.txt:", "current" if same else "DIFFERS")
        raise SystemExit(0 if same else 1)
    if sys.argv[1:] != ["--write"]:
        raise SystemExit("usage: python3 train/metric_sans.py --write | --check")
    open(ADVANCES + ".tmp", "w", encoding="utf-8").write(text)
    os.replace(ADVANCES + ".tmp", ADVANCES)
    print("wrote", ADVANCES)
