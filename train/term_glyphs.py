"""Terminal symbols made as families, for the term-* bundles.

font/term-math.txt holds the shapes drawn once. This module makes the rest
of each family from them and from the trained symbols: a shape turned,
mirrored, flipped, negated with a stroke, stacked over another, filled or
enclosed. Arrows are built in a frame of their own (along the shaft, across
it) and set in the cell pointing right, left, up or down, with the shaft
lengths and heads of the trained arrows U+2190..U+2193.

Shapes are glyphs.py's, in cell units. The helpers here take grid units, 10
to a cell width, as the font files do. No font was read.

    math()     {char: shapes} for the tmath tier (neuronte-term-math-v1)
    FAMILY     {code point: family name}, what train/term_groups.py groups by
"""
import math as m
import os

import strokes

MATH = os.path.join(strokes.ROOT, "font", "term-math.txt")
CY = 9.75          # the maths line
T = {}             # code point -> function making its shapes
FAMILY = {}        # code point -> family
_fam = [None]


def fam(name):
    _fam[0] = name


def d(cp, fn):
    if cp in T:
        raise ValueError(f"U+{cp:04X} is made twice")
    T[cp] = fn
    FAMILY[cp] = _fam[0]


# Shapes from grid units.

def S(text):
    out = []
    for part in text.split("|"):
        if part.strip():
            out += strokes._shapes(part.strip(), "?")
    return out


def P(*pts, r=None):
    rr = None if r is None else r / 10
    return [("seg", pts[i][0] / 10, pts[i][1] / 10, pts[i + 1][0] / 10, pts[i + 1][1] / 10, rr)
            for i in range(len(pts) - 1)]


def F(*pts):
    return [("poly", [(x / 10, y / 10) for x, y in pts])]


def arc(cx, cy, rx, ry, a0, a1, r=None):
    n = max(2, int(abs(a1 - a0) / 10) + 1)
    return P(*[(cx + rx * m.cos(m.radians(a0 + (a1 - a0) * i / n)),
                cy + ry * m.sin(m.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)], r=r)


def ring(cx, cy, rx, ry=None, r=None):
    return arc(cx, cy, rx, rx if ry is None else ry, 0, 360, r)


def disc(cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    return F(*[(cx + rx * m.cos(m.radians(10 * i)), cy + ry * m.sin(m.radians(10 * i))) for i in range(36)])


def dot(x, y, r=None):
    return P((x, y - 0.3), (x, y + 0.3), r=r)


def dots(*at, r=None):
    return [s for x, y in at for s in dot(x, y, r)]


def head_at(x, y, deg, length=2.6, half=40, r=None):
    """An open arrowhead with its tip at (x, y), pointing along deg (0 east, 90 down)."""
    a, b = m.radians(deg + 180 - half), m.radians(deg + 180 + half)
    return P((x + length * m.cos(a), y + length * m.sin(a)), (x, y),
             (x + length * m.cos(b), y + length * m.sin(b)), r=r)


# Shapes moved. f takes and gives grid units.

def mv(shapes, f):
    def g(x, y):
        a, b = f(x * 10, y * 10)
        return a / 10, b / 10
    out = []
    for sh in shapes:
        if sh[0] == "cut":
            out.append(("cut", mv([sh[1]], f)[0]))
        elif sh[0] == "seg":
            out.append(("seg", *g(sh[1], sh[2]), *g(sh[3], sh[4]), sh[5]))
        else:
            out.append(("poly", [g(x, y) for x, y in sh[1]]))
    return out


def mirror(shapes):
    return mv(shapes, lambda x, y: (10 - x, y))


def flip(shapes, about=CY):
    return mv(shapes, lambda x, y: (x, 2 * about - y))


def rot(shapes, deg, cx=5.0, cy=CY):
    c, s = m.cos(m.radians(deg)), m.sin(m.radians(deg))
    return mv(shapes, lambda x, y: (cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c))


def shift(shapes, dx=0.0, dy=0.0):
    return mv(shapes, lambda x, y: (x + dx, y + dy))


def scale(shapes, kx, ky=None, cx=5.0, cy=CY):
    ky = kx if ky is None else ky
    return mv(shapes, lambda x, y: (cx + (x - cx) * kx, cy + (y - cy) * ky))


def pen(shapes, r):
    """The shapes with every stroke drawn at radius r, in grid units."""
    out = []
    for sh in shapes:
        if sh[0] == "cut":
            out.append(("cut", pen([sh[1]], r)[0]))
        elif sh[0] == "seg":
            out.append(sh[:5] + (r / 10,))
        else:
            out.append(sh)
    return out


def extent(shapes):
    """(x0, y0, x1, y1) of the shapes' points, in grid units."""
    pts = []
    for sh in shapes:
        sh = sh[1] if sh[0] == "cut" else sh
        pts += [(sh[1], sh[2]), (sh[3], sh[4])] if sh[0] == "seg" else list(sh[1])
    xs, ys = [p[0] * 10 for p in pts], [p[1] * 10 for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def small(shapes, k, cx, top):
    """The shapes scaled by k, their middle at x = cx and their top at y = top."""
    x0, y0, x1, _ = extent(shapes)
    mid = (x0 + x1) / 2
    return mv(shapes, lambda x, y: (cx + (x - mid) * k, top + (y - y0) * k))


_bases = {}


def G(cp):
    """The shapes of a character: one made here, drawn in font/term-math.txt,
    or trained already (strokes.txt, symbols.txt, the made terminal symbols)."""
    if cp in _made:
        return _made[cp]
    if cp in T:
        _made[cp] = T[cp]()
        return _made[cp]
    if not _bases:
        import glyphs
        _bases.update({ord(c): g for c, g in strokes.parse(strokes.STROKES).items()})
        _bases.update({ord(c): g for c, g in strokes.parse(strokes.SYMBOLS).items()})
        _bases.update({ord(c): g for c, g in glyphs.terminal_symbols().items()})
        for c, g in strokes.parse(MATH).items():
            if ord(c) in _bases:
                raise ValueError(f"U+{ord(c):04X} is drawn in term-math.txt and trained already")
            _bases[ord(c)] = g
    return _bases[cp]


_made = {}


def neg(shapes, x0=6.8, y0=5.4, x1=3.2, y1=14.1, r=None):
    """With the stroke of U+2260 through it."""
    return shapes + P((x0, y0), (x1, y1), r=r)


# Arrows. A kind gives strokes in the arrow's own frame: u along the shaft
# from its middle towards the tip, s across it. h is half the shaft's
# length and w half the head's width: 4 and 3.25 for arrows that lie, 5.25
# and 3 for arrows that stand, as U+2190..U+2193 are drawn. s grows down
# for an arrow that lies and to the right for one that stands.

FRAMES = {"r": (5, CY, 1, 0, 0, 1, 4.0, 3.25), "l": (5, CY, -1, 0, 0, 1, 4.0, 3.25),
          "u": (5, CY, 0, -1, 1, 0, 5.25, 3.0), "d": (5, 9.25, 0, 1, 1, 0, 5.25, 3.0)}


def arrow(way, kind, off=0.0, h=None, w=None, cy=None, **kw):
    ox, oy, ux, uy, sx, sy, fh, fw = FRAMES[way]
    h, w = fh if h is None else h, fw if w is None else w
    oy = oy if cy is None else cy
    out = []
    for tag, pts, r in kind(h, w, **kw):
        g = [(ox + u * ux + (s + off) * sx, oy + u * uy + (s + off) * sy) for u, s in pts]
        out += F(*g) if tag == "F" else P(*g, r=r)
    return out


def _l(*pts, r=None):
    return ("P", list(pts), r)


def _head(at, w, hl=3.0, r=None):
    return _l((at - hl, -w), (at, 0), (at - hl, w), r=r)


def _back(at, w, hl=3.0, r=None):
    return _l((at + hl, -w), (at, 0), (at + hl, w), r=r)


def _arc(cu, cs, rad, a0, a1, r=None):
    n = max(2, int(abs(a1 - a0) / 15) + 1)
    return _l(*[(cu + rad * m.cos(m.radians(a0 + (a1 - a0) * i / n)),
                 cs + rad * m.sin(m.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)], r=r)


def k_plain(h, w, hl=3.0, r=None):
    return [_l((-h, 0), (h, 0), r=r), _head(h, w, hl, r)]


def k_both(h, w, r=None):
    hl, hw = (2.4, 2.4) if w > 3.1 else (3.0, 3.0)   # U+2194 and U+2195
    return [_l((-h, 0), (h, 0), r=r), _head(h, hw, hl, r), _back(-h, hw, hl, r)]


def k_two_headed(h, w):
    return k_plain(h, w) + [_head(h - 2.5, w)]


def k_tail(h, w):
    return [_l((-h + 2.4, 0), (h, 0)), _head(h, w), _l((-h, -0.8 * w), (-h + 2.4, 0), (-h, 0.8 * w))]


def k_from_bar(h, w, base=k_plain):
    return base(h, w) + [_l((-h, -0.85 * w), (-h, 0.85 * w))]


def k_to_bar(h, w):
    return [_l((-h, 0), (h, 0)), _head(h - 0.2, w), _l((h, -w), (h, w))]


def k_loop(h, w):
    return k_plain(h, w) + [_arc(-h + 1.7, -1.5, 1.5, 0, 360)]


def k_harpoon(h, w, side=-1):
    return [_l((-h, 0), (h, 0)), _l((h - 3, side * w), (h, 0))]


def k_dashed(h, w):
    return [_l((-h, 0), (-0.62 * h, 0)), _l((-0.28 * h, 0), (0.1 * h, 0)), _l((0.45 * h, 0), (h, 0)), _head(h, w)]


def k_ticks(h, w, at=(0.0,), half=2.3, base=k_plain, r=None):
    return base(h, w) + [_l((u, -half), (u, half), r=r) for u in at]


def k_open(h, w, both=False):
    tri = [(h - 3, -2.5), (h, 0), (h - 3, 2.5), (h - 3, -2.5)]
    out = [_l((-h + 3 if both else -h, 0), (h - 3, 0)), _l(*tri)]
    if both:
        out.append(_l(*[(-u, s) for u, s in tri]))
    return out


def k_circle(h, w):
    return [_l((-h, 0), (-2.9, 0)), _arc(-1.3, 0, 1.6, 0, 360), _l((0.3, 0), (h, 0)), _head(h, w, 2.6)]


def k_circled_plus(h, w):
    return [_l((-h, 0), (h, 0)), _arc(-1.5, 0, 2.3, 0, 360), _l((-1.5, -2.3), (-1.5, 2.3)), _head(h, 2.6, 2.4)]


def k_wave(h, w, both=False):
    a, b = (-h + 1.9 if both else -h), (h - 1.9 if both else h - 0.9)
    n, waves, amp = 14, (1 if both else 2), (1.5 if both else 1.25)
    pts = [(a + (b - a) * i / n, -amp * m.sin(2 * m.pi * waves * i / n)) for i in range(n + 1)]
    out = [_l(*pts), _l((b, 0), (h, 0)), _head(h, 2.5 if both else w, 2.4 if both else 3.0)]
    if both:
        out += [_l((-h, 0), (a, 0)), _back(-h, 2.5, 2.4)]
    return out


def k_squiggle(h, w):
    """A shaft in sharp teeth, three units to a tooth."""
    pts, u, s = [], -h, 1.4
    while u < h - 3.4:
        pts.append((u, s))
        u, s = u + 1.5, -s
    return [_l(*pts, (h - 2.6, 0), (h, 0)), _head(h, w)]


def k_double(h, w, tip=None, bar=False):
    """Two shafts and an open head, as U+21D2 (lying) and U+21D1 (standing)."""
    lying = w > 3.1
    tip = h if tip is None else tip
    hl, hw, stop = (3.5, 4.25, 1.2) if lying else (4.0, 4.0, 1.5)
    out = [_l((-h, -1.5), (tip - stop, -1.5)), _l((-h, 1.5), (tip - stop, 1.5)), _head(tip, hw, hl)]
    if bar:
        out.append(_l((-h, -3.4), (-h, 3.4)))
    return out


def k_double_both(h, w):
    lying = w > 3.1
    hl, hw, sh, stop = (2.6, 3.15, 1.35, 1.1) if lying else (3.4, 3.4, 1.5, 1.4)
    return [_l((-h + stop, -sh), (h - stop, -sh)), _l((-h + stop, sh), (h - stop, sh)),
            _head(h, hw, hl), _back(-h, hw, hl)]


def k_triple(h, w, tip=None):
    lying = w > 3.1
    tip = h if tip is None else tip
    hl, hw = (4.0, 4.4) if lying else (4.2, 4.2)
    return [_l((-h, 0), (tip, 0)), _l((-h, -2.3), (tip - 2.5, -2.3)), _l((-h, 2.3), (tip - 2.5, 2.3)),
            _head(tip, hw, hl)]


def k_quadruple(h, w, tip=None):
    tip = h if tip is None else tip
    r = 0.5
    return ([_l((-h, s), (tip - 0.9 * abs(s) - 0.7, s), r=r) for s in (-3, -1, 1, 3)] +
            [_head(tip, 4.6, 4.4, r=0.6)])


def _white(h, hl, hw, t):
    return [(h, 0), (h - hl, -hw), (h - hl, -t), (-h, -t), (-h, t), (h - hl, t), (h - hl, hw)]


def _white2(h, hl, hw, t):
    return [(h, 0), (h - hl, -hw), (h - hl, -t), (-h + hl, -t), (-h + hl, -hw), (-h, 0),
            (-h + hl, hw), (-h + hl, t), (h - hl, t), (h - hl, hw)]


def k_white(h, w, fill=False, both=False, wall=False):
    """The outline arrow of U+21E7, or the same filled."""
    lying = w > 3.1
    if lying:
        hh, hl, hw, t = 4.2, (3.3 if both else 3.9), 3.9, 1.6
    else:
        hh, hl, hw, t = 5.0, (3.9 if both else 4.5), 4.0, 1.5
    pts = (_white2 if both else _white)(hh, hl, hw, t)
    out = [("F", pts, None)] if fill else [_l(*pts, pts[0])]
    if wall:
        out.append(_l((-hh, -hw - 0.3), (-hh, hw + 0.3)))
    return out


def diagonal(shapes, way):
    """A drawing that points north east, turned to another corner."""
    if "w" in way:
        shapes = mirror(shapes)
    if "s" in way:
        shapes = flip(shapes, 10.0)
    return shapes


def slant(way, kind, **kw):
    """An arrow drawn pointing right, turned to a corner of the cell."""
    return rot(arrow("r", kind, **kw), {"ne": -45, "se": 45, "sw": 135, "nw": -135}[way])


def circle_arrow(a0, a1, rad=3.3, cy=10.2, head=2.5, full=False):
    """An arc about the cell's middle from a0 round to a1 (degrees, growing
    clockwise on screen), with an arrowhead at a1 pointing on round."""
    out = ring(5, cy, rad) if full else arc(5, cy, rad, rad, a0, a1)
    way = 1 if a1 > a0 else -1
    t = m.radians(a1)
    tip = (5 + rad * m.cos(t) - way * 0.6 * m.sin(t), cy + rad * m.sin(t) + way * 0.6 * m.cos(t))
    if not full:
        out += P((5 + rad * m.cos(t), cy + rad * m.sin(t)), tip)
    return out + head_at(*tip, a1 + way * 90, head)


fam("arrow")
SLASH = lambda: P((5.9, 6.55), (4.1, 12.95))          # noqa: E731  the stroke of an arrow with stroke
for cp, way in ((0x219A, "l"), (0x219B, "r")):
    d(cp, lambda way=way: arrow(way, k_plain) + SLASH())
d(0x21AE, lambda: G(0x2194) + SLASH())
for cp, way in ((0x219C, "l"), (0x219D, "r")):
    d(cp, lambda way=way: arrow(way, k_wave))
d(0x21AD, lambda: arrow("r", k_wave, both=True))
for cp, way in ((0x219E, "l"), (0x219F, "u"), (0x21A0, "r"), (0x21A1, "d")):
    d(cp, lambda way=way: arrow(way, k_two_headed))
for cp, way in ((0x21A2, "l"), (0x21A3, "r")):
    d(cp, lambda way=way: arrow(way, k_tail))
for cp, way in ((0x21A4, "l"), (0x21A5, "u"), (0x21A6, "r"), (0x21A7, "d")):
    d(cp, lambda way=way: arrow(way, k_from_bar))
d(0x21A8, lambda: mv(G(0x2195), lambda x, y: (x, 4.2 + (y - 4.5) * 0.86)) + P((2, 15.7), (8, 15.7)))
for cp, way in ((0x21AB, "l"), (0x21AC, "r")):
    d(cp, lambda way=way: arrow(way, k_loop))
d(0x21AF, lambda: P((6.6, 4), (3.2, 10.2), (6.9, 9.2), (4.4, 15)) + head_at(4.4, 15, 113.3))
# An arrow that turns a corner: the stem, then the tip.
d(0x21B1, lambda: P((2.2, 15), (2.2, 7.5), (9, 7.5)) + head_at(9, 7.5, 0, 2.9, 42))
d(0x21B0, lambda: mirror(G(0x21B1)))
d(0x21B3, lambda: flip(G(0x21B1), 10.0))
d(0x21B2, lambda: mirror(G(0x21B3)))
d(0x21B4, lambda: P((1, 6.2), (7, 6.2), (7, 14.6)) + head_at(7, 14.6, 90, 2.9, 42))
d(0x2B0E, lambda: P((1, 6.6), (7, 6.6), (7, 11.8)) + F((4.4, 11.4), (9.6, 11.4), (7, 15.4)))
d(0x2B0F, lambda: flip(G(0x2B0E), 10.0))
d(0x2B10, lambda: mirror(G(0x2B0E)))
d(0x2B11, lambda: mirror(G(0x2B0F)))
d(0x21B7, lambda: arc(5, 11.8, 3.5, 4.8, 180, 360) + P((8.5, 11.8), (8.5, 12.4)) + head_at(8.5, 12.6, 90, 2.6, 42))
d(0x21B6, lambda: mirror(G(0x21B7)))
d(0x21B8, lambda: P((1, 4.2), (9, 4.2)) + P((8, 15), (2.6, 7.6)) + P((6.6, 7.6), (2.6, 7.6), (2.6, 11.6)))
d(0x21B9, lambda: arrow("l", k_to_bar, off=-2.9, w=2.1, cy=CY) + arrow("r", k_to_bar, off=2.9, w=2.1, cy=CY))
d(0x21BB, lambda: circle_arrow(-30, 250))
d(0x21BA, lambda: mirror(G(0x21BB)))
d(0x27F3, lambda: circle_arrow(25, 335, rad=3.9, cy=CY))
d(0x27F2, lambda: mirror(G(0x27F3)))
d(0x2941, lambda: ring(5, 10.4, 3.3) + head_at(6.2, 7.1, 0, 2.6))
d(0x2940, lambda: mirror(G(0x2941)))
for cp, way, side in ((0x21BC, "l", -1), (0x21BD, "l", 1), (0x21BE, "u", 1), (0x21BF, "u", -1),
                      (0x21C0, "r", -1), (0x21C1, "r", 1), (0x21C2, "d", 1), (0x21C3, "d", -1)):
    d(cp, lambda way=way, side=side: arrow(way, k_harpoon, side=side))
PAIR = dict(w=1.9, hl=2.3)
d(0x21C4, lambda: arrow("r", k_plain, off=-2.6, **PAIR) + arrow("l", k_plain, off=2.6, **PAIR))
d(0x21C6, lambda: arrow("l", k_plain, off=-2.6, **PAIR) + arrow("r", k_plain, off=2.6, **PAIR))
d(0x21C5, lambda: arrow("u", k_plain, off=-2.3, cy=CY, **PAIR) + arrow("d", k_plain, off=2.3, cy=CY, **PAIR))
d(0x21F5, lambda: arrow("d", k_plain, off=-2.3, cy=CY, **PAIR) + arrow("u", k_plain, off=2.3, cy=CY, **PAIR))
for cp, way in ((0x21C7, "l"), (0x21C9, "r")):
    d(cp, lambda way=way: arrow(way, k_plain, off=-2.6, **PAIR) + arrow(way, k_plain, off=2.6, **PAIR))
for cp, way in ((0x21C8, "u"), (0x21CA, "d")):
    d(cp, lambda way=way: arrow(way, k_plain, off=-2.3, **PAIR) + arrow(way, k_plain, off=2.3, **PAIR))
d(0x21F6, lambda: [s for off in (-3.5, 0, 3.5) for s in arrow("r", k_plain, off=off, w=1.4, hl=2.0, r=0.6)])
d(0x21CB, lambda: arrow("l", k_harpoon, off=-1.4, side=-1) + arrow("r", k_harpoon, off=1.4, side=1))
d(0x21CC, lambda: arrow("r", k_harpoon, off=-1.4, side=-1) + arrow("l", k_harpoon, off=1.4, side=1))
fam("arrow-double")
for cp, base in ((0x21CD, 0x21D0), (0x21CE, 0x21D4), (0x21CF, 0x21D2)):
    d(cp, lambda base=base: G(base) + P((6.1, 5.2), (3.9, 14.3)))
d(0x21D5, lambda: arrow("u", k_double_both))
d(0x21D7, lambda: S("P 1,13.25 6.1,6.4 | P 3,14.75 7.6,8.6 | P 2.9,5.7 8.3,5.7 8.3,11.1"))
for cp, way in ((0x21D6, "nw"), (0x21D8, "se"), (0x21D9, "sw")):
    d(cp, lambda way=way: diagonal(G(0x21D7), way))
for cp, way in ((0x21DA, "l"), (0x21DB, "r")):
    d(cp, lambda way=way: arrow(way, k_triple))
for cp, way in ((0x290A, "u"), (0x290B, "d")):
    d(cp, lambda way=way: arrow(way, k_triple, tip=5.75, cy=CY + (0.25 if way == "u" else -0.25)))
for cp, way in ((0x27F0, "u"), (0x27F1, "d")):
    d(cp, lambda way=way: arrow(way, k_quadruple, tip=5.75, cy=CY + (0.25 if way == "u" else -0.25)))
for cp, way in ((0x2906, "l"), (0x2907, "r")):
    d(cp, lambda way=way: arrow(way, k_double, bar=True))
fam("arrow")
for cp, way in ((0x21DC, "l"), (0x21DD, "r")):
    d(cp, lambda way=way: arrow(way, k_squiggle))
d(0x27FF, lambda: arrow("r", k_squiggle, h=5.0))
for cp, way in ((0x21DE, "u"), (0x21DF, "d")):
    d(cp, lambda way=way: arrow(way, k_ticks, at=(-1.1, -3.1), half=2.0))
for cp, way in ((0x21E0, "l"), (0x21E1, "u"), (0x21E2, "r")):
    d(cp, lambda way=way: arrow(way, k_dashed))
for cp, way in ((0x21E4, "l"), (0x21E5, "r")):
    d(cp, lambda way=way: arrow(way, k_to_bar))
fam("arrow-white")
for cp, way in ((0x21E6, "l"), (0x21E8, "r"), (0x21E9, "d")):
    d(cp, lambda way=way: arrow(way, k_white, cy=CY))
d(0x21F0, lambda: arrow("r", k_white, wall=True))
d(0x21F3, lambda: arrow("u", k_white, both=True))
d(0x2B04, lambda: arrow("r", k_white, both=True))
for cp, way in ((0x2B00, "ne"), (0x2B01, "nw"), (0x2B02, "se"), (0x2B03, "sw")):
    d(cp, lambda way=way: slant(way, k_white))
fam("arrow-black")
for cp, way in ((0x2B05, "l"), (0x2B06, "u"), (0x2B07, "d")):
    d(cp, lambda way=way: arrow(way, k_white, fill=True, cy=CY))
for cp, way in ((0x2B08, "ne"), (0x2B09, "nw"), (0x2B0A, "se"), (0x2B0B, "sw")):
    d(cp, lambda way=way: slant(way, k_white, fill=True))
d(0x2B0C, lambda: arrow("r", k_white, fill=True, both=True))
d(0x2B0D, lambda: arrow("u", k_white, fill=True, both=True))
fam("arrow")
d(0x21F1, lambda: P((1.2, 9.6), (1.2, 5), (5.8, 5)) + P((8.6, 15), (3.5, 8)) + P((7.2, 8), (3.5, 8), (3.5, 11.9)))
d(0x21F2, lambda: rot(G(0x21F1), 180, 5, 10))
d(0x21F4, lambda: arrow("r", k_circle))
d(0x27F4, lambda: arrow("r", k_circled_plus))
for cp, way, base, at in ((0x21F7, "l", k_plain, (0.0,)), (0x21F8, "r", k_plain, (0.0,)), (0x21F9, "r", k_both, (0.0,)),
                          (0x21FA, "l", k_plain, (-2.0, 0.4)), (0x21FB, "r", k_plain, (-2.0, 0.4)),
                          (0x21FC, "r", k_both, (-1.2, 1.2))):
    d(cp, lambda way=way, base=base, at=at: arrow(way, k_ticks, at=at, base=base, r=0.5 if at[0] == -1.2 else None))
for cp, way, both in ((0x21FD, "l", False), (0x21FE, "r", False), (0x21FF, "r", True)):
    d(cp, lambda way=way, both=both: arrow(way, k_open, both=both))
# Long arrows run from edge to edge of the cell.
fam("arrow-long")
for cp, way in ((0x27F5, "l"), (0x27F6, "r")):
    d(cp, lambda way=way: arrow(way, k_plain, h=5.0))
d(0x27F7, lambda: arrow("r", k_both, h=5.0))
for cp, way in ((0x27F8, "l"), (0x27F9, "r")):
    d(cp, lambda way=way: arrow(way, k_double, h=5.0))
d(0x27FA, lambda: arrow("r", k_double_both, h=5.0))
for cp, way in ((0x27FB, "l"), (0x27FC, "r")):
    d(cp, lambda way=way: arrow(way, k_from_bar, h=4.8))
for cp, way in ((0x27FD, "l"), (0x27FE, "r")):
    d(cp, lambda way=way: arrow(way, k_double, h=4.8, bar=True))


# Relations. rel() stacks rows down the cell and fits them to it: an
# angle (< > and the curved, square, round and closed ones), bars, tildes,
# and bars that slant with the arm of the angle beside them.

L, R_ = 2.5, 7.5
LEFT = "<≺⊏⊂⊲"
RIGHT = ">≻⊐⊃⊳"
_H = {"-": 0.0, "=": 2.6, "~": 1.8, "∽": 1.8, "≈": 4.4, "≠": 2.6, "≠1": 0.0, "≁": 1.8, "≉": 4.4}
_STROKES = {"-": 1, "=": 2, "~": 1, "∽": 1, "≈": 2, "≠": 2, "≠1": 1, "≁": 1, "≉": 2}


def angle(tok, y0, y1, r=None):
    ym = (y0 + y1) / 2
    i = (LEFT + RIGHT).index(tok) % 5
    if i == 0:
        sh = P((R_, y0), (L, ym), (R_, y1), r=r)
    elif i == 1:   # curved: steep at the open end, flat at the point
        up = [(R_ - (R_ - L) * t, ym - (ym - y0) * (1 - t) ** 2) for t in (0, 0.2, 0.4, 0.6, 0.8, 1)]
        sh = P(*up, *[(x, 2 * ym - y) for x, y in reversed(up[:-1])], r=r)
    elif i == 2:
        sh = P((R_, y0), (L, y0), (L, y1), (R_, y1), r=r)
    elif i == 3:
        sh = P((8, y0), (5.5, y0), r=r) + arc(5.5, ym, 3.5, (y1 - y0) / 2, 270, 90, r) + P((5.5, y1), (8, y1), r=r)
    else:
        sh = P((R_, y0), (L, ym), (R_, y1), (R_, y0), r=r)
    return mirror(sh) if tok in RIGHT else sh


def tilde(yc, r=None, back=False):
    sh = arc(3.75, yc, 1.25, 0.9, 180, 360, r) + arc(6.25, yc, 1.25, 0.9, 180, 0, r)
    return mirror(sh) if back else sh


def rel(*rows, slash=False, dot=None, band=12.5, want=None):
    items = []
    before = 0
    for tok in rows:
        if tok in ("-/", "=/"):
            before += 1 if tok == "-/" else 2
        elif tok in ("/-", "/="):
            items[-1]["after"] += 1 if tok == "/-" else 2
        elif tok in LEFT + RIGHT:
            items.append({"tok": tok, "before": before, "after": 0})
            before = 0
        else:
            items.append({"tok": tok})
    angles = [it for it in items if "after" in it]
    count = sum(1 + it["before"] + it["after"] if "after" in it else _STROKES[it["tok"]] for it in items)

    def total(a, gap, gs):
        return (sum((it["before"] + it["after"]) * gs + a if "after" in it else _H[it["tok"]] for it in items)
                + gap * (len(items) - 1))
    a, gap, gs = 6.4, 2.4, 2.2
    if total(a, gap, gs) > band:
        gap, gs = 2.0, 2.0
        if angles:
            a = max(3.0, (band - total(0, gap, gs)) / len(angles))
    if want is not None:
        a = want
    r = None if count <= 3 and a >= 5.5 else 0.6 if count <= 5 else 0.5
    y = CY - total(a, gap, gs) / 2
    top = y
    out, first = [], None
    for it in items:
        tok = it["tok"]
        if "after" in it:
            y0 = y + it["before"] * gs
            y1, ym = y0 + a, y0 + a / 2
            first = first or (tok, y0, ym, y1)
            out += angle(tok, y0, y1, r)
            for k in range(1, it["before"] + 1):
                bar = P((R_, y0 - k * gs), (L, ym - k * gs), r=r)
                out += mirror(bar) if tok in RIGHT else bar
            for k in range(1, it["after"] + 1):
                bar = P((L, ym + k * gs), (R_, y1 + k * gs), r=r)
                out += mirror(bar) if tok in RIGHT else bar
            y = y1 + it["after"] * gs
        else:
            h = _H[tok]
            if tok in ("-", "≠1"):
                out += P((L, y), (R_, y), r=r)
            elif tok in ("=", "≠"):
                out += P((L, y), (R_, y), r=r) + P((L, y + 2.6), (R_, y + 2.6), r=r)
            elif tok in ("~", "∽", "≁"):
                out += tilde(y + 0.9, r, tok == "∽")
            else:
                out += tilde(y + 0.9, r) + tilde(y + 3.5, r)
            if tok in ("≠", "≠1", "≁", "≉"):
                out += P((6.0, y - 1.7), (4.0, y + h + 1.7), r=r)
            y += h
        y += gap
    bottom = y - gap
    if slash:
        out += P((6.5, top - 0.9), (3.5, bottom + 0.9), r=r)
    if dot == "in":
        tok, y0, ym, y1 = first
        out += dot_(3.8 if tok in RIGHT else 6.2, ym, 0.95)
    elif dot:
        tok, y0, ym, y1 = first
        x = {"above": 5.0, "right": 8.4, "left": 1.6}[dot]
        out += dot_(x, min(top, y0) - (2.1 if dot == "above" else 2.5), 0.95)
    return out


dot_ = dot


def above_eq(mark):
    """An equals sign with a mark over it."""
    return mark + P((2, 10.9), (8, 10.9)) + P((2, 13.6), (8, 13.6))


def star5(cx, cy, rad):
    pts = []
    for k in range(10):
        a = m.radians(-90 + 36 * k)
        rr = rad if k % 2 == 0 else rad * 0.4
        pts.append((cx + rr * m.cos(a), cy + rr * m.sin(a)))
    return F(*pts)


def nint(x, r):
    """A narrow integral sign at x."""
    return P((x, 5.2), (x, 14.8), r=r) + arc(x + 1.0, 5.2, 1.0, 1.2, 180, 330, r) + arc(x - 1.0, 14.8, 1.0, 1.2, 0, 150, r)


INT = 0x222B
CIRC = lambda: ring(5, CY, 3.6)                         # noqa: E731  as U+25CB
SQUARE = lambda: S("P 1.8,6.55 8.2,6.55 8.2,12.95 1.8,12.95 1.8,6.55")   # noqa: E731  as U+25A1
BIG = lambda: ring(5, CY, 4.4, 5.7)                     # noqa: E731  an n-ary operator's circle
ELEM = lambda: S("P 8,5.9 6,5.9 | E 6,9.75 3.6,3.85 270 90 | P 6,13.6 8,13.6")  # noqa: E731  U+2208 less its stroke

fam("logic")
d(0x2204, lambda: G(0x2203) + P((7.6, 2.9), (3.4, 16.1)))
d(0x220A, lambda: scale(G(0x2208), 0.72))
d(0x220B, lambda: mirror(G(0x2208)))
d(0x220C, lambda: mirror(G(0x2209)))
d(0x220D, lambda: mirror(G(0x220A)))
d(0x2210, lambda: flip(G(0x220F), 10.0))
d(0x2213, lambda: flip(G(0xB1), 10.05))
d(0x2214, lambda: P((5, 7.2), (5, 13.6)) + P((1.8, 10.4), (8.2, 10.4)) + dot(5, 4.6))
d(0x2216, lambda: mirror(G(0x2215)))
d(0x221B, lambda: G(0x221A) + pen(small(G(0x33), 0.36, 2.6, 3.4), 0.5))
d(0x221C, lambda: G(0x221A) + pen(small(G(0x34), 0.36, 2.6, 3.4), 0.5))
d(0x2224, lambda: G(0x2223) + P((7.2, 7.8), (2.8, 11.7)))
d(0x2226, lambda: G(0x2225) + P((8.4, 7.6), (1.6, 11.9)))
fam("integral")
d(0x222C, lambda: nint(3.3, 0.7) + nint(6.7, 0.7))
d(0x222D, lambda: nint(2.2, 0.6) + nint(5, 0.6) + nint(7.8, 0.6))
d(0x2A0C, lambda: [s for x in (1.6, 3.9, 6.1, 8.4) for s in nint(x, 0.5)])
d(0x222E, lambda: G(INT) + ring(5, 10, 2.2))
d(0x222F, lambda: G(0x222C) + ring(5, 10, 3.9, 2.2, r=0.6))
d(0x2230, lambda: G(0x222D) + ring(5, 10, 4.5, 2.2, r=0.6))
d(0x2231, lambda: G(INT) + arc(5, 10, 2.5, 2.5, 120, 400) + head_at(6.9, 11.6, 130, 1.9))
d(0x2A11, lambda: G(INT) + mirror(arc(5, 10, 2.5, 2.5, 120, 400) + head_at(6.9, 11.6, 130, 1.9)))
d(0x2232, lambda: G(INT) + ring(5, 10, 2.5) + head_at(7.5, 11.2, 90, 2.3, 45))
d(0x2233, lambda: G(INT) + ring(5, 10, 2.5) + head_at(2.5, 11.2, 90, 2.3, 45))
d(0x2A0D, lambda: G(INT) + P((3, 10), (7, 10)))
d(0x2A0E, lambda: G(INT) + P((3, 8.8), (7, 8.8)) + P((3, 11.2), (7, 11.2)))
d(0x2A0F, lambda: G(INT) + P((7.2, 7.4), (2.8, 12.6)))
d(0x2A10, lambda: G(INT) + arc(5, 10, 2.8, 2.8, 60, 300))
d(0x2A12, lambda: G(INT) + P((3, 8), (7.2, 8), (7.2, 12), (3, 12)))
d(0x2A13, lambda: G(INT) + arc(5, 10, 2.4, 2.4, -90, 90))
d(0x2A14, lambda: G(INT) + arc(5, 10, 2.4, 2.4, 90, 270) + dot(7.6, 10))
d(0x2A15, lambda: G(INT) + ring(5, 12.6, 2.0))
d(0x2A16, lambda: G(INT) + P((3, 8), (7, 8), (7, 12), (3, 12), (3, 8)))
d(0x2A17, lambda: G(INT) + P((2.6, 10.6), (7.4, 10.6)) + head_at(2.6, 10.6, 180, 1.8) + arc(7.4, 9.5, 1.1, 1.1, 90, -90))
d(0x2A18, lambda: G(INT) + P((3.1, 8.1), (6.9, 11.9)) + P((6.9, 8.1), (3.1, 11.9)))
d(0x2A19, lambda: G(INT) + P((2.9, 12.2), (2.9, 10)) + arc(5, 10, 2.1, 2.1, 180, 360) + P((7.1, 10), (7.1, 12.2)))
d(0x2A1A, lambda: G(INT) + P((2.9, 7.8), (2.9, 10)) + arc(5, 10, 2.1, 2.1, 180, 0) + P((7.1, 10), (7.1, 7.8)))
d(0x2A1B, lambda: mv(G(INT), lambda x, y: (x, 5.6 + (y - 4.5) * 0.9)) + P((2.6, 3.4), (7.4, 3.4)))
d(0x2A1C, lambda: mv(G(INT), lambda x, y: (x, 4.5 + (y - 4.5) * 0.9)) + P((2.6, 16.6), (7.4, 16.6)))
fam("dots")
d(0x2234, lambda: dots((5, 6.8), (2.5, 12.4), (7.5, 12.4)))
d(0x2235, lambda: dots((2.5, 7), (7.5, 7), (5, 12.6)))
d(0x2236, lambda: dots((5, 7.2), (5, 12.3)))
d(0x2237, lambda: dots((2.8, 7.2), (7.2, 7.2), (2.8, 12.3), (7.2, 12.3)))
d(0x2238, lambda: P((1.8, 10.8), (8.2, 10.8)) + dot(5, 7.3))
d(0x2239, lambda: P((1.5, CY), (5.5, CY)) + dots((8, 7.2), (8, 12.3)))
d(0x223A, lambda: P((1.8, CY), (8.2, CY)) + dots((2.8, 6.6), (7.2, 6.6), (2.8, 12.9), (7.2, 12.9)))
d(0x223B, lambda: G(0x223C) + dots((5, 6.4), (5, 13.1)))
d(0x22EE, lambda: dots((5, 5.3), (5, CY), (5, 14.2)))
d(0x22EF, lambda: dots((1.8, CY), (5, CY), (8.2, CY)))
d(0x22F0, lambda: dots((2, 13.8), (5, CY), (8, 5.7)))
d(0x22F1, lambda: mirror(G(0x22F0)))
fam("tilde")
d(0x223D, lambda: mirror(G(0x223C)))
d(0x2240, lambda: scale(rot(G(0x223C), 90), 1, 1.3))
d(0x2241, lambda: G(0x223C) + P((6.4, 6.9), (3.6, 12.6)))
d(0x2242, lambda: rel("-", "~"))
d(0x2243, lambda: rel("~", "-"))
d(0x2244, lambda: rel("~", "-", slash=True))
d(0x2245, lambda: rel("~", "="))
d(0x2246, lambda: rel("~", "≠"))
d(0x2247, lambda: rel("~", "=", slash=True))
d(0x2249, lambda: G(0x2248) + P((6.6, 6), (3.4, 14.2)))
d(0x224A, lambda: rel("≈", "-"))
d(0x224B, lambda: rel("~", "~", "~"))
d(0x224C, lambda: rel("∽", "="))
d(0x22CD, lambda: rel("∽", "-"))
d(0x226D, lambda: G(0x224D) + P((6.4, 5.6), (3.6, 13.9)))
d(0x2A6A, lambda: G(0x223C) + dot(5, 6.3, 0.95))
d(0x2A6B, lambda: G(0x223C) + dots((2.5, 13), (7.5, 6.5)))
fam("equals")
EQ = 0x3D
d(0x2250, lambda: shift(G(EQ), 0, 0.9) + dot(5, 5.6))
d(0x2251, lambda: G(EQ) + dots((5, 4.9), (5, 14.6)))
d(0x2252, lambda: G(EQ) + dots((2.4, 4.9), (7.6, 14.6)))
d(0x2253, lambda: G(EQ) + dots((7.6, 4.9), (2.4, 14.6)))
d(0x2254, lambda: dots((2, 7.5), (2, 12)) + P((4.6, 8.3), (8.8, 8.3)) + P((4.6, 11.2), (8.8, 11.2)))
d(0x2255, lambda: mirror(G(0x2254)))
d(0x2256, lambda: P((2, 6.9), (8, 6.9)) + P((2, 12.6), (8, 12.6)) + ring(5, CY, 1.3, r=0.6))
d(0x2257, lambda: above_eq(ring(5, 6.3, 1.6)))
d(0x2258, lambda: above_eq(arc(5, 9, 3, 3.6, 205, 335)))
d(0x2259, lambda: above_eq(P((2.8, 8.2), (5, 4.4), (7.2, 8.2))))
d(0x225A, lambda: above_eq(P((2.8, 4.4), (5, 8.2), (7.2, 4.4))))
d(0x225B, lambda: above_eq(star5(5, 6.1, 2.6)))
d(0x225C, lambda: above_eq(P((5, 3.9), (7.5, 8.2), (2.5, 8.2), (5, 3.9))))
d(0x225D, lambda: above_eq(pen(small(G(0x64), 0.3, 2.2, 4.6) + small(G(0x65), 0.3, 5, 5.95) + small(G(0x66), 0.3, 7.8, 4.6), 0.45)))
d(0x225E, lambda: above_eq(pen(small(G(0x6D), 0.5, 5, 4.8), 0.6)))
d(0x225F, lambda: above_eq(pen(small(G(0x3F), 0.4, 5, 3.9), 0.6)))
d(0x2262, lambda: G(0x2261) + P((6.8, 4.8), (3.2, 14.7)))
d(0x2263, lambda: S("P@0.6 2,5.85 8,5.85 | P@0.6 2,8.45 8,8.45 | P@0.6 2,11.05 8,11.05 | P@0.6 2,13.65 8,13.65"))
fam("order")
LT, GT = 0x3C, 0x3E
for i, (a, b) in enumerate((("<", ">"), (">", "<"))):
    d(0x2266 + i, lambda a=a: rel(a, "="))
    d(0x2268 + i, lambda a=a: rel(a, "≠"))
    d(0x226E + i, lambda i=i: G(LT + 2 * i) + P((6.2, 4.3), (3.8, 15.2)))
    d(0x2270 + i, lambda i=i: G(0x2264 + i) + P((6.3, 3.6), (3.7, 15.4)))
    d(0x2272 + i, lambda a=a: rel(a, "~"))
    d(0x2274 + i, lambda a=a: rel(a, "~", slash=True))
    d(0x2276 + i, lambda a=a, b=b: rel(a, b))
    d(0x2278 + i, lambda a=a, b=b: rel(a, b, slash=True))
    d(0x22D6 + i, lambda i=i: G(LT + 2 * i) + dot(3.6 if i else 6.4, CY))
    d(0x22DA + i, lambda a=a, b=b: rel(a, "-", b))
    d(0x22DC + i, lambda a=a: rel("-", a))
    d(0x22E6 + i, lambda a=a: rel(a, "≁"))
    d(0x2A7D + i, lambda a=a: rel(a, "/-"))
    d(0x2A7F + i, lambda a=a: rel(a, "/-", dot="in"))
    d(0x2A81 + i, lambda a=a: rel(a, "/-", dot="above"))
    d(0x2A83 + i, lambda a=a, i=i: rel(a, "/-", dot="left" if i else "right"))
    d(0x2A85 + i, lambda a=a: rel(a, "≈"))
    d(0x2A87 + i, lambda a=a: rel(a, "≠1"))
    d(0x2A89 + i, lambda a=a: rel(a, "≉"))
    d(0x2A8B + i, lambda a=a, b=b: rel(a, "=", b))
    d(0x2A8D + i, lambda a=a: rel(a, "~", "-"))
    d(0x2A8F + i, lambda a=a, b=b: rel(a, "~", b))
    d(0x2A91 + i, lambda a=a, b=b: rel(a, b, "="))
    d(0x2A93 + i, lambda a=a, b=b: rel(a, "/-", b, "/-"))
    d(0x2A95 + i, lambda a=a: rel("-/", a))
    d(0x2A97 + i, lambda a=a: rel("-/", a, dot="in"))
    d(0x2A99 + i, lambda a=a: rel("=", a))
    d(0x2A9B + i, lambda a=a: rel("=/", a))
    d(0x2A9D + i, lambda a=a: rel("~", a))
    d(0x2A9F + i, lambda a=a: rel("~", a, "="))
    d(0x2AF9 + i, lambda a=a: rel(a, "/="))
d(0x226A, lambda: P((5.6, 5.5), (1.4, CY), (5.6, 14)) + P((9, 5.5), (4.8, CY), (9, 14)))
d(0x226B, lambda: mirror(G(0x226A)))
d(0x22D8, lambda: [s for x in (0, 2.5, 5) for s in P((x + 4.4, 5.5), (x + 0.6, CY), (x + 4.4, 14), r=0.5)])
d(0x22D9, lambda: mirror(G(0x22D8)))
fam("precedes")
for i, a in enumerate(("≺", "≻")):
    d(0x227A + i, lambda a=a: angle(a, 6.2, 13.3))
    d(0x227C + i, lambda a=a: rel(a, "/-"))
    d(0x227E + i, lambda a=a: rel(a, "~"))
    d(0x2280 + i, lambda i=i: G(0x227A + i) + P((6.2, 4.7), (3.8, 14.8)))
    d(0x22DE + i, lambda a=a: rel("-/", a))
    d(0x22E0 + i, lambda a=a: rel(a, "/-", slash=True))
    d(0x22E8 + i, lambda a=a: rel(a, "≁"))
    d(0x2AAF + i, lambda a=a: rel(a, "-"))
    d(0x2AB1 + i, lambda a=a: rel(a, "≠1"))
    d(0x2AB3 + i, lambda a=a: rel(a, "="))
    d(0x2AB5 + i, lambda a=a: rel(a, "≠"))
    d(0x2AB7 + i, lambda a=a: rel(a, "≈"))
    d(0x2AB9 + i, lambda a=a: rel(a, "≉"))
d(0x22B1, lambda: mirror(G(0x22B0)))
fam("subset")
for i in (0, 1):
    d(0x2284 + i, lambda i=i: G(0x2282 + i) + P((6.3, 4.4), (3.7, 15.1)))
    d(0x2288 + i, lambda i=i: G(0x2286 + i) + P((6.3, 3.4), (3.7, 15.6)))
    d(0x228A + i, lambda i=i: rel("⊃" if i else "⊂", "≠1"))
    d(0x228F + i, lambda i=i: angle("⊐" if i else "⊏", 6, 13.5))
    d(0x2291 + i, lambda i=i: rel("⊐" if i else "⊏", "-"))
    d(0x22E2 + i, lambda i=i: rel("⊐" if i else "⊏", "-", slash=True))
    d(0x22E4 + i, lambda i=i: rel("⊐" if i else "⊏", "≠1"))
d(0x228C, lambda: G(0x222A) + P((3.7, 8.4), (6.5, 8.4), r=0.6) + head_at(3.7, 8.4, 180, 1.5, r=0.6))
d(0x228D, lambda: G(0x222A) + dot(5, 9))
d(0x228E, lambda: G(0x222A) + P((5, 6.9), (5, 10.9), r=0.6) + P((3.2, 8.9), (6.8, 8.9), r=0.6))
d(0x2294, lambda: flip(G(0x2293)))
DCAP = "P@0.6 1.5,14.5 1.5,9.3 | E@0.6 5,9.3 3.5,4 180 360 | P@0.6 8.5,9.3 8.5,14.5 | P@0.6 3.8,14.5 3.8,10 | E@0.6 5,10 1.2,1.6 180 360 | P@0.6 6.2,10 6.2,14.5"
d(0x22D2, lambda: S(DCAP))
d(0x22D3, lambda: flip(G(0x22D2)))
DSUB = "P@0.6 8.6,5.6 5.3,5.6 | E@0.6 5.3,9.75 3.8,4.15 270 90 | P@0.6 5.3,13.9 8.6,13.9 | P@0.6 8.6,8.1 6,8.1 | E@0.6 6,9.75 1.6,1.65 270 90 | P@0.6 6,11.4 8.6,11.4"
d(0x22D0, lambda: S(DSUB))
d(0x22D1, lambda: mirror(G(0x22D0)))
d(0x22C1, lambda: flip(G(0x22C0), 10.0))
d(0x22C3, lambda: flip(G(0x22C2), 10.0))
d(0x22CF, lambda: flip(G(0x22CE)))
fam("element")
d(0x22F2, lambda: scale(G(0x2208), 0.8, 1, cx=8) + P((0.3, CY), (3.5, CY)))
d(0x22F3, lambda: G(0x2208) + P((8, 8.1), (8, 11.4)))
d(0x22F4, lambda: scale(G(0x22F3), 0.72))
d(0x22F5, lambda: shift(G(0x2208), 0, 0.9) + dot(5.6, 4.5))
d(0x22F6, lambda: mv(G(0x2208), lambda x, y: (x, 10.9 + (y - CY) * 0.85)) + P((2.4, 5), (8, 5)))
d(0x22F7, lambda: shift(scale(G(0x2208), 0.72), 0, 0.8) + P((3.1, 5.9), (7.2, 5.9)))
d(0x22F8, lambda: mv(G(0x2208), lambda x, y: (x, 8.6 + (y - CY) * 0.85)) + P((2.4, 14.6), (8, 14.6)))
d(0x22F9, lambda: ELEM() + P((2.9, 8.5), (7.5, 8.5)) + P((2.9, 11), (7.5, 11)))
for i in range(5):
    d(0x22FA + i, lambda i=i: mirror(G((0x22F2, 0x22F3, 0x22F4, 0x22F6, 0x22F7)[i])))
fam("circled")
d(0x2295, lambda: CIRC() + P((5, 6.15), (5, 13.35)) + P((1.4, CY), (8.6, CY)))
d(0x2296, lambda: CIRC() + P((1.4, CY), (8.6, CY)))
d(0x2297, lambda: CIRC() + P((2.45, 7.2), (7.55, 12.3)) + P((7.55, 7.2), (2.45, 12.3)))
d(0x2298, lambda: CIRC() + P((7.55, 7.2), (2.45, 12.3)))
d(0x2299, lambda: CIRC() + P((5, CY), (5, CY), r=0.85))
d(0x229A, lambda: CIRC() + ring(5, CY, 1.4, r=0.55))
d(0x229B, lambda: CIRC() + pen(scale(G(0x2217), 0.7), 0.55))
d(0x229C, lambda: CIRC() + P((3.2, 8.6), (6.8, 8.6), r=0.6) + P((3.2, 10.9), (6.8, 10.9), r=0.6))
d(0x229D, lambda: CIRC() + P((3.7, CY), (6.3, CY)))
d(0x229E, lambda: SQUARE() + P((5, 6.55), (5, 12.95)) + P((1.8, CY), (8.2, CY)))
d(0x229F, lambda: SQUARE() + P((1.8, CY), (8.2, CY)))
d(0x22A0, lambda: SQUARE() + P((1.8, 6.55), (8.2, 12.95)) + P((8.2, 6.55), (1.8, 12.95)))
d(0x22A1, lambda: SQUARE() + dot(5, CY))
d(0x2A00, lambda: BIG() + dot(5, CY))
d(0x2A01, lambda: BIG() + P((5, 4.05), (5, 15.45)) + P((0.6, CY), (9.4, CY)))
d(0x2A02, lambda: BIG() + P((1.9, 5.7), (8.1, 13.8)) + P((8.1, 5.7), (1.9, 13.8)))
fam("tack")
d(0x22A3, lambda: mirror(G(0x22A2)))
d(0x22A5, lambda: flip(G(0x22A4)))
for cp, base in ((0x22AC, 0x22A2), (0x22AD, 0x22A8), (0x22AE, 0x22A9), (0x22AF, 0x22AB)):
    d(cp, lambda base=base: G(base) + P((7, 5.6), (4.2, 13.9)))
d(0x27DC, lambda: mirror(G(0x22B8)))
d(0x22B7, lambda: mirror(G(0x22B6)))
fam("triangle")
for i, a in enumerate(("⊲", "⊳")):
    d(0x22B2 + i, lambda a=a: angle(a, 5.9, 13.6))
    d(0x22B4 + i, lambda a=a: rel(a, "-"))
    d(0x22EA + i, lambda i=i: G(0x22B2 + i) + P((6.4, 4.3), (3.6, 15.2)))
    d(0x22EC + i, lambda a=a: rel(a, "-", slash=True))
fam("product")
d(0x22C6, lambda: star5(5, CY, 3.4))
d(0x22C7, lambda: G(0xD7) + P((1.6, CY), (8.4, CY)) + dots((5, 5.6), (5, 13.9)))
d(0x22CA, lambda: mirror(G(0x22C9)))
d(0x22CC, lambda: mirror(G(0x22CB)))
fam("bracket")
for cp in (0x27C5, 0x27E6, 0x27E8, 0x27EA, 0x2983, 0x2987, 0x2997):
    d(cp + 1, lambda cp=cp: mirror(G(cp)))
d(0x29D0, lambda: mirror(G(0x29CF)))
d(0x29D2, lambda: mirror(G(0x29D1)))
d(0x29D5, lambda: mirror(G(0x29D4)))

# The drawn characters take the family of the made ones beside them.
DRAWN_FAMILY = {
    "arrow-white": (0x21EA, 0x21EB, 0x21EC, 0x21ED, 0x21EE, 0x21EF),
    "logic": (0x2200, 0x2201, 0x2203, 0x2205, 0x220E, 0x2215, 0x2217, 0x2218, 0x2219, 0x221D, 0x221F, 0x2220,
              0x2221, 0x2222, 0x2223, 0x2225, 0x22BE, 0x22BF),
    "tilde": (0x223C, 0x223E, 0x223F, 0x224D, 0x224E, 0x224F, 0x226C, 0x2AAE),
    "subset": (0x2293, 0x22C0, 0x22C2, 0x22CE, 0x22D4),
    "tack": (0x22A2, 0x22A4, 0x22A6, 0x22A7, 0x22A8, 0x22A9, 0x22AA, 0x22AB, 0x22B6, 0x22B8, 0x22B9, 0x22BA,
             0x22BB, 0x22BC, 0x22BD, 0x27C2),
    "precedes": (0x22B0,),
    "product": (0x22C4, 0x22C8, 0x22C9, 0x22CB, 0x22D5, 0x29CE, 0x29CF, 0x29D1, 0x29D3, 0x29D4, 0x29EB, 0x29FA,
                0x29FB, 0x2A2F, 0x27E0),
    "element": (0x22FF,),
    "bracket": (0x27C5, 0x27E6, 0x27E8, 0x27EA, 0x2983, 0x2987, 0x2997),
}
for _name, _cps in DRAWN_FAMILY.items():
    for _cp in _cps:
        if _cp in FAMILY:
            raise ValueError(f"U+{_cp:04X} is in two families")
        FAMILY[_cp] = _name


def math():
    """{char: shapes} for the tmath tier: every character drawn in
    font/term-math.txt and every one made here."""
    drawn = {ord(c): g for c, g in strokes.parse(MATH).items()}
    both = set(drawn) & set(T)
    if both:
        raise ValueError("drawn and made: " + " ".join(f"U+{c:04X}" for c in sorted(both)))
    out = {chr(c): g for c, g in drawn.items()}
    out.update({chr(c): G(c) for c in T})
    lost = [c for c in out if ord(c) not in FAMILY]
    if lost:
        raise ValueError("no family: " + " ".join(f"U+{ord(c):04X}" for c in sorted(lost)))
    return out
