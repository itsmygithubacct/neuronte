"""Neuronte Sans Metric in greyscale at 8 to 16 pixels: sets uiEMmsg (upright)
and uiEMmsgi (italic).

The binary pixel faces (uiEMms, font/metric-sans-EM.txt) are exact bitmaps,
so the library draws them with hard edges. These faces are drawn from the
large face's strokes (train/metric_sans.py), hinted for each em so that
their straight stems and bars fall on whole pixels while curves and
diagonals keep greyscale edges. The library draws them at their em with
its usual coverage: two samples per axis below 24 px, each a ramp one
sample wide.

The hinting for an em E, per character, in cell units (x 0..1, y 0..2):

1. Pen. Every stroke is one pixel wide: the pen radius is 0.5 / E, the
   weight of the binary faces, whose stems are one pixel through 16. A
   stroke drawn with its own radius keeps its ratio to the face's pen, but
   is never thinner than one pixel (the small figures, as in the binary face).
2. Across. The ink takes the columns the binary face gives the character,
   left to right: the leftmost and rightmost stroke centres go to the
   centres of the binary face's first and last ink columns, so letters are
   spaced exactly as in the binary face (its clear-column rule included).
   Between knots x is mapped piecewise linearly.
3. Down. The top and bottom stroke centres go to the centres of the binary
   face's first and last ink rows for the character. The face's baseline,
   x-height, cap height, ascender and descender (measured on the binary
   face's H, x, d and p) are knots too where they fall between. Between
   knots y is mapped piecewise linearly.
4. Stems and bars. Each vertical stroke goes to the nearest binary column
   that is inked over at least 60% of the stroke's rows, and each horizontal
   stroke to the nearest binary row inked over 60% of its columns; with
   none, to the nearest whole pixel. A knot that would not keep the map
   increasing is left out. Across, the stems are placed before the extremes,
   which may then meet a stem's column but not pass it (the end of a mark
   folds into the stem, as in the binary face).
5. Italic. The hinted upright is sheared about the centre of the baseline
   row by one column per four rows, the slope of the binary italic faces;
   the slope is reduced where the letter would leave the em, and a letter
   that would start left of the pen moves right, just enough.

No font file is opened. The advances are the binary face's
(font/metric-sans-EM.advances.txt): Helvetica's widths, copied from Adobe's
Core 14 AFM metric files, as for every Neuronte Sans Metric face.
MIT licence; see LICENSE.
"""
import glyphs
import metric_sans

EMS = range(8, 17)
SLOPE = 0.25          # one column per four rows
MIN_STEM = 0.12       # a vertical or horizontal stroke this long (em) or longer is a stem or a bar
EPS = 1e-9
WANT = [chr(c) for c in range(32, 127)] + ["…"] + [chr(c) for c in range(0xA0, 0x100)]


def pen(em):
    return 0.5 / em


def _ink(rows):
    cols = [c for r in rows for c, v in enumerate(r) if v == "#"]
    rws = [i for i, r in enumerate(rows) if "#" in r]
    return (min(cols), max(cols), min(rws), max(rws)) if cols else None


def metrics(em):
    """Cell rows (centres, cell units) of the binary face's baseline, x-height, cap height, ascender, descender."""
    face = glyphs.pixel_face(em, glyphs.UI_METRIC[em])
    top = glyphs.UI_TOP[em]
    c = lambda r: (top + r + 0.5) / em
    H, x, d, p = (_ink(face[ch][1]) for ch in "Hxdp")
    return {"asc": c(d[2]), "cap": c(H[2]), "x": c(x[2]), "base": c(H[3]), "desc": c(p[3])}


def _map(knots):
    """A piecewise-linear map through sorted (src, dst) knots; slope 1 outside."""
    def f(v):
        if v <= knots[0][0]:
            return v + knots[0][1] - knots[0][0]
        if v >= knots[-1][0]:
            return v + knots[-1][1] - knots[-1][0]
        for (a0, b0), (a1, b1) in zip(knots, knots[1:]):
            if a0 <= v <= a1:
                return b0 if a1 - a0 < EPS else b0 + (v - a0) * (b1 - b0) / (a1 - a0)
        raise AssertionError(v)
    return f


def _add(knots, src, dst, equal=False):
    """Insert (src, dst) if the map stays increasing (strictly, unless equal); return whether it was."""
    if any(abs(src - a) < EPS for a, _ in knots):
        return False
    trial = sorted(knots + [(src, dst)])
    if all(b1 - b0 > (-EPS if equal else EPS) for (_, b0), (_, b1) in zip(trial, trial[1:])):
        knots[:] = trial
        return True
    return False


def _snap(v, em):
    return (round(v * em - 0.5) + 0.5) / em


def _strokes(shapes, axis):
    """Strokes that run along one axis for MIN_STEM or more: [(position, lo, hi)] across the other axis.
    axis 0: vertical strokes, position x, extent in y; axis 1: horizontal strokes, position y, extent in x."""
    out = {}
    for sh in shapes:
        if sh[0] != "seg":
            continue
        x0, y0, x1, y1 = sh[1:5]
        pos0, pos1, e0, e1 = (x0, x1, y0, y1) if axis == 0 else (y0, y1, x0, x1)
        if abs(pos0 - pos1) < EPS and abs(e1 - e0) >= MIN_STEM:
            k = round(pos0, 9)
            lo, hi = min(e0, e1), max(e0, e1)
            a, b = out.get(k, (lo, hi))
            out[k] = (min(a, lo), max(b, hi))
    return sorted((k, a, b) for k, (a, b) in out.items())


def _place(knots, strokes, lin, fother, lines, centre, lo_i, hi_i, em):
    """Knots for stems (or bars): each to the nearest binary column (row) between lo_i and hi_i that is inked
    over at least 60% of the stroke's run, else to the nearest whole pixel; strictly increasing."""
    for pos, a, b in strokes:
        want = lin(pos) * em - 0.5
        run = range(max(0, int(round(fother(a)))), int(round(fother(b))) + 1)
        cands = [i for i in range(lo_i, hi_i + 1)
                 if run and sum(lines(i, j) for j in run) >= 0.6 * len(run)]
        order = sorted(cands, key=lambda i: abs(i - want)) or [min(hi_i, max(lo_i, round(want)))]
        for i in order:
            if _add(knots, pos, centre(i)):
                break


def hinted(shapes, rows, em, keys, top_row):
    """The shapes hinted onto the binary drawing `rows` (see the module notes)."""
    box = _ink(rows)
    pts = list(glyphs.points(shapes))
    if box is None or not pts:
        return []
    L, R, T, B = box
    cx = lambda c: (c + 0.5) / em
    cy = lambda r: (top_row + r + 0.5) / em
    ink = lambda c, r: 0 <= r < len(rows) and 0 <= c < len(rows[r]) and rows[r][c] == "#"
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    lo, hi, top, bot = min(xs), max(xs), min(ys), max(ys)

    # down, first pass: extremes and the face's heights
    ky = [(top, cy(T))] if bot - top < EPS else [(top, cy(T)), (bot, cy(B))]
    for name, src in zip(("asc", "cap", "x", "base", "desc"), (k for _, k in metric_sans.knots())):
        if top + EPS < src < bot - EPS:
            _add(ky, src, keys[name])
    fy0 = _map(ky)
    row_of = lambda y: fy0(y) * em - 0.5 - top_row

    # across: stems first, then the extremes, which may meet a stem but not pass it
    if hi - lo < EPS:
        fx = (lambda m: (lambda v: v - lo + m))(_snap((cx(L) + cx(R)) / 2, em))
    else:
        lin = _map([(lo, cx(L)), (hi, cx(R))])
        kx = []
        _place(kx, _strokes(shapes, 0), lin, row_of, lambda c, r: ink(c, r), cx, L, R, em)
        _add(kx, lo, cx(L), equal=True)
        _add(kx, hi, cx(R), equal=True)
        fx = _map(kx or [(lo, cx(L))])
    col_of = lambda x: fx(x) * em - 0.5

    # down, second pass: bars to inked binary rows
    if bot - top < EPS:
        fy = lambda v: v - top + cy(T)
    else:
        bars = [(p, a, b) for p, a, b in _strokes(shapes, 1) if top + EPS < p < bot - EPS]
        _place(ky, bars, fy0, col_of, lambda r, c: ink(c, r), cy, T, B, em)
        fy = _map(ky)

    k = pen(em) / metric_sans.PEN
    out = []
    for sh in glyphs.moved(shapes, lambda x, y: (fx(x), fy(y))):
        if sh[0] == "seg" and sh[5] is not None:
            sh = sh[:5] + (max(sh[5] * k, pen(em)),)
        out.append(sh)
    return out


def sheared(shapes, em, base_y):
    """The italic: shear about base_y, slope reduced to stay in the em, moved right to start at the pen."""
    if not shapes:
        return shapes
    r = pen(em)
    slope = SLOPE
    while True:
        s = glyphs.moved(shapes, lambda x, y, k=slope: (x + (base_y - y) * k, y))
        xs = [x for x, _ in glyphs.points(s)]
        lo, hi = min(xs) - r, max(xs) + r
        move = max(0.0, -lo)
        if hi + move <= 1.0 + EPS or slope <= EPS:
            return glyphs.moved(s, lambda x, y, m=move: (x + m, y)) if move else s
        slope = max(0.0, slope - 1 / (4 * em))


def drawings(em, italic=False):
    """{char: shapes} for the 192 characters of the face at em."""
    if em not in EMS:
        raise ValueError(f"greyscale Metric Sans is drawn at {EMS.start} to {EMS.stop - 1} px, not {em}")
    face = glyphs.pixel_face(em, glyphs.UI_METRIC[em])
    large = metric_sans.drawings()
    keys = metrics(em)
    top_row = glyphs.UI_TOP[em]
    out = {}
    for ch in WANT:
        g = hinted(large[ch][0], face[ch][1], em, keys, top_row)
        out[ch] = sheared(g, em, keys["base"]) if italic else g
    return out


def tier(em, italic=False):
    d = drawings(em, italic)
    return [(c, d[c]) for c in WANT]
