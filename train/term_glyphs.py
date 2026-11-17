"""Terminal symbols made as families, for the term-* bundles.

font/term-math.txt and font/term-sym.txt hold the shapes drawn once. This
module makes the rest
of each family from them and from the trained symbols: a shape turned,
mirrored, flipped, negated with a stroke, stacked over another, filled or
enclosed. Arrows are built in a frame of their own (along the shaft, across
it) and set in the cell pointing right, left, up or down, with the shaft
lengths and heads of the trained arrows U+2190..U+2193.

Shapes are glyphs.py's, in cell units. The helpers here take grid units, 10
to a cell width, as the font files do. No font was read.

    math()     {char: shapes} for the tmath tier (neuronte-term-math-v1)
    sym()      {char: shapes} for the tsym tier (neuronte-term-symbol-v1)
    FAMILY     {code point: family name}, what tools/term-partition.py groups by
"""
import math as m
import os

import strokes

MATH = os.path.join(strokes.ROOT, "font", "term-math.txt")
SYMBOL = os.path.join(strokes.ROOT, "font", "term-sym.txt")
DING = os.path.join(strokes.ROOT, "font", "term-ding.txt")
DRAWN = {"math": MATH, "sym": SYMBOL, "ding": DING}
CY = 9.75          # the maths line
T = {}             # code point -> function making its shapes
FAMILY = {}        # code point -> family
TIER = {}          # code point made here -> tier
_fam = [None]
_tier = ["math"]


def tier(name):
    _tier[0] = name


def fam(name):
    _fam[0] = name


def d(cp, fn):
    if cp in T:
        raise ValueError(f"U+{cp:04X} is made twice")
    T[cp] = fn
    FAMILY[cp] = _fam[0]
    TIER[cp] = _tier[0]


def drawn_families(path):
    """{code point: family} from a drawing file's "# family NAME" lines."""
    out, name = {}, None
    with open(path) as fh:
        for line in fh:
            if line.startswith("# family "):
                name = line.split()[2]
            elif line.startswith("U+"):
                out[int(line.split()[0][2:], 16)] = name
    return out


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
        _bases.update({ord(c): g for c, g in strokes.parse(glyphs.LETTERS).items()})
        for path in DRAWN.values():
            for c, g in strokes.parse(path).items():
                if ord(c) in _bases:
                    raise ValueError(f"U+{ord(c):04X} is drawn in {os.path.basename(path)} and elsewhere")
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


# Batch 2: punctuation, currency, letterlike symbols, number forms, technical
# symbols and geometric shapes. font/term-sym.txt holds the shapes drawn
# by hand; here are the forms a transform gives.

tier("sym")
FAMILY.update(drawn_families(SYMBOL))


def shear(shapes, k=0.15, about=15.0):
    """Slanted to the right, the line y = about staying where it is."""
    return mv(shapes, lambda x, y: (x + (about - y) * k, y))


def script(shapes, k=0.55, top=3.6, src=4.0, cx=5.0):
    """Scaled by k about x = 5, the line y = src going to y = top: the
    superscripts and subscripts of the trained digits."""
    return mv(shapes, lambda x, y: (cx + (x - 5) * k, top + (y - src) * k))


def squeeze(shapes, x0, x1):
    """The shapes with their width fitted to x0..x1."""
    a, _, b, _ = extent(shapes)
    return mv(shapes, lambda x, y: (x0 + (x - a) * (x1 - x0) / (b - a), y))


def cut(shapes):
    return [("cut", sh) for sh in shapes]


def regular(n, cx, cy, rad, start=-90.0):
    return [(cx + rad * m.cos(m.radians(start + 360 * i / n)), cy + rad * m.sin(m.radians(start + 360 * i / n)))
            for i in range(n)]


def outline(pts, r=None):
    return P(*pts, pts[0], r=r)


def sector(cx, cy, rad, a0, a1):
    n = max(2, int(abs(a1 - a0) / 10) + 1)
    return F((cx, cy), *[(cx + rad * m.cos(m.radians(a0 + (a1 - a0) * i / n)),
                          cy + rad * m.sin(m.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)])


def half_disc(cx, cy, rad, a0):
    """Half a disc, the half that starts at a0 and runs on half a turn."""
    return F(*[(cx + rad * m.cos(m.radians(a0 + 10 * i)), cy + rad * m.sin(m.radians(a0 + 10 * i))) for i in range(19)])


def A(ch):
    return G(ord(ch))


SQ0, SQ1, SQT, SQB = 1.8, 8.2, 6.55, 12.95       # the square of U+25A1
QUAD = lambda: G(0x2395)                          # noqa: E731
TRI = [(5, 5.8), (8.4, 13.6), (1.6, 13.6)]        # the triangle of U+25B3
DIA = [(5, 5.5), (9, 9.75), (5, 14), (1, 9.75)]   # the diamond of U+25C7

fam("punct")
d(0x2011, lambda: G(0x2010))
d(0x201B, lambda: mirror(G(0x2019)))
d(0x201F, lambda: mirror(G(0x201D)))
d(0x2024, lambda: A("."))
d(0x2025, lambda: dots((3, 14.6), (7, 14.6)))
d(0x2027, lambda: dot(5, 10.5))
d(0x2033, lambda: shift(G(0x2032), -1.3) + shift(G(0x2032), 1.3))
d(0x2034, lambda: pen([s for dx in (-2.4, 0, 2.4) for s in shift(G(0x2032), dx)], 0.6))
d(0x2057, lambda: pen([s for dx in (-3.3, -1.1, 1.1, 3.3) for s in shift(G(0x2032), dx)], 0.5))
d(0x2035, lambda: mirror(G(0x2032)))
d(0x2036, lambda: mirror(G(0x2033)))
d(0x2037, lambda: mirror(G(0x2034)))
d(0x203C, lambda: shift(A("!"), -2.5) + shift(A("!"), 2.5))
d(0x203D, lambda: A("?") + P((5, 4.2), (5, 9.2)))
d(0x2E18, lambda: rot(G(0x203D), 180, 5, 10.5))
d(0x2047, lambda: pen(shift(scale(A("?"), 0.6, 1), -2.2) + shift(scale(A("?"), 0.6, 1), 2.2), 0.6))
d(0x2048, lambda: pen(shift(scale(A("?"), 0.6, 1), -1.7), 0.65) + shift(A("!"), 2.6))
d(0x2049, lambda: shift(A("!"), -2.6) + pen(shift(scale(A("?"), 0.6, 1), 1.7), 0.65))
d(0x2042, lambda: pen([s for x, y in ((5, 6.4), (2.6, 12.6), (7.4, 12.6))
                       for s in shift(scale(A("*"), 0.45, cy=9), x - 5, y - 9)], 0.5))
d(0x2051, lambda: pen(shift(scale(A("*"), 0.55, cy=9), 0, -2.6) + shift(scale(A("*"), 0.55, cy=9), 0, 3.9), 0.55))
d(0x204E, lambda: shift(scale(A("*"), 0.8, cy=9), 0, 5))
d(0x2045, lambda: A("[") + P((4, 10), (6.4, 10)))
d(0x2046, lambda: mirror(G(0x2045)))
d(0x204B, lambda: mirror(G(0xB6)))
d(0x204C, lambda: F(*[(4.6 + 2.6 * m.cos(m.radians(90 + 10 * i)), CY + 2.6 * m.sin(m.radians(90 + 10 * i)))
                      for i in range(19)], (7.8, CY - 2.6), (7.8, CY + 2.6)))
d(0x204D, lambda: mirror(G(0x204C)))
d(0x204F, lambda: mirror(A(";")))
d(0x2055, lambda: [s for k in range(8) for s in P((5 + 1.5 * m.cos(m.radians(45 * k)), CY + 1.5 * m.sin(m.radians(45 * k))),
                                                 (5 + 3.6 * m.cos(m.radians(45 * k)), CY + 3.6 * m.sin(m.radians(45 * k))), r=0.55)]
  + disc(5, CY, 1.0))
d(0x2056, lambda: dots((3, 6.6), (3, 12.9), (7, CY)))
d(0x2058, lambda: dots((5, 6.4), (2.4, CY), (7.6, CY), (5, 13.1)))
d(0x205A, lambda: dots((5, 6), (5, 13.5)))
d(0x205B, lambda: dots((5, 4.6), (1.8, CY), (8.2, CY), (5, 14.9), r=0.95))
d(0x205C, lambda: P((5, 5.5), (5, 14)) + P((1.5, CY), (8.5, CY)) + dots((2.8, 7.2), (7.2, 7.2), (2.8, 12.3), (7.2, 12.3)))
d(0x205D, lambda: dots((5, 5.6), (5, 10.1), (5, 14.6)))
d(0x205E, lambda: dots((5, 4.2), (5, 7.9), (5, 11.6), (5, 15.3)))
d(0x2E1F, lambda: shift(A("~"), 0, -1) + dot(5, 13.2))
d(0x2E23, lambda: mirror(G(0x2E22)))
d(0x2E25, lambda: mirror(G(0x2E24)))
d(0x2E2E, lambda: mirror(A("?")))

# Superscripts and subscripts, as the trained digits are: 0.55 of the size,
# tops at y 3.6 and 10.4. A small letter without an ascender is 0.6 of its
# size, as the ordinals are.
fam("small")
SUP = {0x2071: "i", 0x207A: "+", 0x207B: "−", 0x207C: "=", 0x207D: "(", 0x207E: ")", 0x207F: "n"}
SUB = {0x208A: "+", 0x208B: "−", 0x208C: "=", 0x208D: "(", 0x208E: ")", 0x2090: "a", 0x2091: "e", 0x2092: "o",
       0x2093: "x", 0x2094: "ə", 0x2095: "h", 0x2096: "k", 0x2097: "l", 0x2098: "m", 0x2099: "n", 0x209A: "p",
       0x209B: "s", 0x209C: "t"}


def _script(ch, top):
    if ch == "ə":
        base = rot(A("e"), 180, 5, 11.5)
    else:
        base = A(ch)
    if ch in "aeoxmnsə":                 # x-height letters: 8..15
        return script(base, 0.6, top + (0.4 if top < 9 else 1.9), 8.0)
    if ch == "p":
        return script(base, 0.55, top + 1.2, 8.0)
    if ch in "+=−":                     # signs keep to the middle of the digits
        return script(base, 0.6, top + 3.0, 9.5)
    return script(base, 0.55, top, 3.5 if ch in "hklt()" else 4.0)


for _cp, _ch in SUP.items():
    d(_cp, lambda ch=_ch: _script(ch, 3.6))
for _cp, _ch in SUB.items():
    d(_cp, lambda ch=_ch: _script(ch, 10.4))
d(0x23E8, lambda: pen(script(A("1"), 0.5, 9.5, 4.0, 2.9) + script(A("0"), 0.5, 9.5, 4.0, 7.1), 0.65))


def over(a, b, r=0.6):
    """a over a slash over b: the care-of signs."""
    return pen(small(a, 0.52, 2.7, 4.2) + small(b, 0.52, 7.3, 15 - 0.52 * (extent(b)[3] - extent(b)[1])), r) + \
        P((8, 4.5), (2, 14.5), r=r)


d(0x2100, lambda: over(A("a"), A("c")))
d(0x2101, lambda: over(A("a"), A("s")))
d(0x2105, lambda: over(A("c"), A("o")))
d(0x2106, lambda: over(A("c"), A("u")))
d(0x2103, lambda: ring(1.9, 5.2, 1.2, r=0.6) + S("E 6.3,9.5 2.6,5.5 40 320"))
d(0x2109, lambda: ring(1.9, 5.2, 1.2, r=0.6) + S("P 8.8,4 4.6,4 4.6,15 | P 4.6,9.5 7.8,9.5"))
d(0x2120, lambda: pen(small(A("S"), 0.39, 2.3, 4.2), 0.6) + S("P 5,8.5 5,4.2 7.1,7 9.2,4.2 9.2,8.5"))
d(0x2121, lambda: S("P@0.55 0.6,7 3.2,7 | P@0.55 1.9,7 1.9,12.5 | P@0.55 6,7 4,7 4,12.5 6,12.5 | P@0.55 4,9.75 5.6,9.75 | "
                    "P@0.55 7.2,7 7.2,12.5 9.4,12.5"))
d(0x213B, lambda: S("P@0.55 3,7 0.8,7 0.8,12.5 | P@0.55 0.8,9.75 2.6,9.75 | P@0.55 3.6,12.5 4.9,7 6.2,12.5 | "
                    "P@0.55 4.1,10.8 5.7,10.8 | P@0.55 6.9,7 9.3,12.5 | P@0.55 9.3,7 6.9,12.5"))
d(0x20A8, lambda: pen(squeeze(A("R"), 0.8, 5.2), 0.65) + pen(small(A("s"), 0.62, 7.5, 10.6), 0.65))

fam("currency")
d(0x20A1, lambda: A("C") + P((5.6, 3), (3.4, 16), r=0.6) + P((7.2, 3), (5, 16), r=0.6))
d(0x20A2, lambda: A("C") + S("P@0.6 4.6,9 4.6,13 | E@0.6 6.2,10.6 1.6,1.6 180 300"))
d(0x20A3, lambda: A("F") + P((0.8, 12.2), (5, 12.2)))
d(0x20A5, lambda: A("m") + P((7.2, 6), (2.8, 17)))
d(0x20A6, lambda: A("N") + P((0.8, 8.3), (9.2, 8.3), r=0.6) + P((0.8, 10.7), (9.2, 10.7), r=0.6))
d(0x20A9, lambda: A("W") + P((0.8, 9.2), (9.2, 9.2)))
d(0x20AB, lambda: A("d") + P((5.6, 5.4), (9.6, 5.4)) + P((2.5, 17.3), (8, 17.3)))
d(0x20AD, lambda: A("K") + P((0.6, 9.6), (6.2, 9.6)))
d(0x20AE, lambda: A("T") + P((3, 9.4), (7, 7.6)) + P((3, 11.9), (7, 10.1)))
d(0x20B1, lambda: A("P") + P((0.8, 6), (9.2, 6), r=0.55) + P((0.8, 8), (9.2, 8), r=0.55))
d(0x20B2, lambda: A("G") + P((5.2, 2.6), (5.2, 16.4)))
d(0x20B5, lambda: A("C") + P((5.2, 2.8), (5.2, 16.2)))

# Letters turned, mirrored, slanted or struck through.
fam("letter")
d(0x2107, lambda: mirror(A("3")))
d(0x210E, lambda: shear(A("h")))
d(0x210F, lambda: shear(A("h")) + P((1.2, 6.6), (5.6, 5.2)))
d(0x2114, lambda: S("P 2.6,3.5 2.6,15 | P 5.4,3.5 5.4,15 | E 7.2,11.8 1.8,3.2 0 360 | P 1,6.2 7,6.2"))
d(0x2117, lambda: S("E 5,9.5 4,4 0 360 | P 3.9,12 3.9,7 5.4,7 | E 5.4,8.25 1.25,1.25 270 450 | P 5.4,9.5 3.9,9.5"))
d(0x211E, lambda: A("R") + P((5.2, 14.6), (8.8, 11.4)))
d(0x211F, lambda: A("R") + P((7.4, 3), (3.4, 16)))
d(0x2123, lambda: A("V") + P((4.6, 11), (9, 7.6)))
d(0x2126, lambda: G(0x3A9))
d(0x2127, lambda: flip(G(0x3A9), 9.5))
d(0x2129, lambda: rot(G(0x3B9), 180, 5, 11.5))
d(0x212A, lambda: A("K"))
d(0x2132, lambda: rot(A("F"), 180, 5, 9.5))
d(0x2139, lambda: pen(shear(A("i")), 0.95))
d(0x213A, lambda: scale(rot(A("Q"), -90, 5, 9.5), 0.85, cy=9.5))
d(0x2141, lambda: rot(A("G"), 180, 5, 9.5))
d(0x2142, lambda: rot(A("L"), 180, 5, 9.5))
d(0x2143, lambda: mirror(A("L")))
d(0x2144, lambda: rot(A("Y"), 180, 5, 9.5))
d(0x214B, lambda: rot(A("&"), 180, 5, 9.5))
d(0x214E, lambda: rot(A("f"), 180, 5, 11.5))
d(0x2183, lambda: mirror(A("C")))
d(0x2184, lambda: mirror(A("c")))
d(0x2422, lambda: A("b") + P((0.6, 7.4), (4.6, 5)))
d(0x2373, lambda: G(0x3B9))
d(0x2374, lambda: G(0x3C1))
d(0x2375, lambda: G(0x3C9))
d(0x237A, lambda: G(0x3B1))
d(0x2376, lambda: G(0x3B1) + P((2, 17.3), (8.5, 17.3)))
d(0x2377, lambda: shift(G(0x220A), 0, -0.6) + P((2.4, 14.6), (7.6, 14.6)))
d(0x2378, lambda: G(0x3B9) + P((2.5, 17.3), (8, 17.3)))
d(0x2379, lambda: G(0x3C9) + P((1.5, 17.3), (8.5, 17.3)))

fam("double")
d(0x2102, lambda: A("C") + P((3.7, 5.6), (3.7, 13.4), r=0.55))
d(0x211A, lambda: A("Q") + P((3.7, 5.6), (3.7, 13.4), r=0.55))
d(0x2145, lambda: shear(S("P@0.55 1.8,4 1.8,15 3.6,15 3.6,4 1.8,4 | P@0.55 3.6,4 4,4 | E@0.55 4,9.5 4.2,5.5 270 450 | P@0.55 4,15 3.6,15"), 0.12))
d(0x2146, lambda: shear(S("P@0.55 8.2,3.5 8.2,15 6.5,15 6.5,3.5 8.2,3.5 | E@0.55 4.2,11.5 2.5,3.5 0 360"), 0.12))
d(0x2147, lambda: shear(pen(A("e"), 0.55) + P((3.7, 9), (3.7, 14), r=0.55), 0.12))
d(0x2148, lambda: shear(S("P@0.55 4.2,8 5.9,8 5.9,15 4.2,15 4.2,8 | P@0.55 4.2,4.9 5.9,4.9"), 0.12))
d(0x2149, lambda: shear(S("P@0.55 5.2,8 6.9,8 6.9,16.5 | P@0.55 5.2,8 5.2,16.5 | E@0.55 4.4,16.5 2.5,2.5 0 140 | "
                          "P@0.55 5.2,4.9 6.9,4.9"), 0.12))

# Fractions, laid out as the trained quarter and three quarters are.
fam("fraction")


def frac(num, den):
    out = script(A(num), 0.5, 4.0, 4.0, 2.4) if num else []
    out += P((8, 4.5), (2, 14.5))
    if len(den) == 1:
        out += script(A(den), 0.5, 9.5, 4.0, 7.1)
    elif den:
        out += pen(squeeze(script(A(den[0]), 0.5, 9.5, 4.0, 5), 4.6, 5.9) + squeeze(script(A(den[1]), 0.5, 9.5, 4.0, 5), 7, 9.4), 0.5)
        return pen(out[:-len(squeeze(A(den[0]), 0, 1) + squeeze(A(den[1]), 0, 1))], 0.65) + out[-len(squeeze(A(den[0]), 0, 1) + squeeze(A(den[1]), 0, 1)):]
    return pen(out, 0.65)


for _cp, _nd in {0x2150: "17", 0x2151: "19", 0x2153: "13", 0x2154: "23", 0x2155: "15", 0x2156: "25", 0x2157: "35",
                 0x2158: "45", 0x2159: "16", 0x215A: "56", 0x215B: "18", 0x215C: "38", 0x215D: "58", 0x215E: "78",
                 0x2189: "03"}.items():
    d(_cp, lambda nd=_nd: frac(nd[0], nd[1]))
d(0x2152, lambda: frac("1", "10"))
d(0x215F, lambda: frac("1", ""))

# Roman numerals: the letters, narrowed to stand together; ones as stems
# between a bar above and a bar below.
fam("roman")


def stems(xs, x0, x1):
    return P((x0, 4), (x1, 4)) + P((x0, 15), (x1, 15)) + [s for x in xs for s in P((x, 4), (x, 15))]


def istems(xs):
    return [s for x in xs for s in P((x, 8), (x, 15)) + dot(x, 5)]


d(0x2160, lambda: A("I"))
d(0x2161, lambda: stems((3.4, 6.6), 1.6, 8.4))
d(0x2162, lambda: pen(stems((2.4, 5, 7.6), 1, 9), 0.65))
d(0x2163, lambda: pen(stems((2,), 0.9, 3.1) + squeeze(A("V"), 4, 9.2), 0.65))
d(0x2164, lambda: A("V"))
d(0x2165, lambda: pen(squeeze(A("V"), 0.8, 6) + stems((8,), 6.9, 9.1), 0.65))
d(0x2166, lambda: pen(squeeze(A("V"), 0.6, 4.2) + stems((5.8, 8.2), 4.9, 9.1), 0.55))
d(0x2167, lambda: pen(squeeze(A("V"), 0.5, 3.5) + stems((4.9, 6.9, 8.9), 4.3, 9.5), 0.5))
d(0x2168, lambda: pen(stems((1.9,), 0.8, 3) + squeeze(A("X"), 4, 9.2), 0.65))
d(0x2169, lambda: A("X"))
d(0x216A, lambda: pen(squeeze(A("X"), 0.8, 5.8) + stems((7.9,), 6.8, 9), 0.65))
d(0x216B, lambda: pen(squeeze(A("X"), 0.6, 4.4) + stems((6, 8.4), 5.1, 9.3), 0.55))
d(0x216C, lambda: A("L"))
d(0x216D, lambda: A("C"))
d(0x216E, lambda: A("D"))
d(0x216F, lambda: A("M"))
d(0x2170, lambda: A("i"))
d(0x2171, lambda: istems((2.5, 7.5)))
d(0x2172, lambda: pen(istems((2.4, 5, 7.6)), 0.65))
d(0x2173, lambda: pen(istems((2,)) + squeeze(A("v"), 3.8, 9), 0.65))
d(0x2174, lambda: A("v"))
d(0x2175, lambda: pen(squeeze(A("v"), 1, 6.2) + istems((8,)), 0.65))
d(0x2176, lambda: pen(squeeze(A("v"), 0.8, 4.6) + istems((6.2, 8.4)), 0.6))
d(0x2177, lambda: pen(squeeze(A("v"), 0.6, 3.8) + istems((5.2, 7, 8.8)), 0.5))
d(0x2178, lambda: pen(istems((1.8,)) + squeeze(A("x"), 3.6, 9), 0.65))
d(0x2179, lambda: A("x"))
d(0x217A, lambda: pen(squeeze(A("x"), 1, 6.2) + istems((8,)), 0.65))
d(0x217B, lambda: pen(squeeze(A("x"), 0.8, 4.6) + istems((6.2, 8.4)), 0.6))
d(0x217C, lambda: A("l"))
d(0x217D, lambda: A("c"))
d(0x217E, lambda: A("d"))
d(0x217F, lambda: A("m"))
d(0x2180, lambda: S("P 5,4 5,15 | E 5,9.5 4,5.5 0 360"))
d(0x2181, lambda: A("D") + S("E 2,9.5 3,3.2 270 450"))
d(0x2182, lambda: S("P@0.55 5,4 5,15 | E@0.55 5,9.5 4,5.5 0 360 | E@0.55 5,9.5 2.2,3.2 0 360"))

fam("tech")
d(0x2300, lambda: ring(5, CY, 3.4) + P((8.6, 5.4), (1.4, 14.1)))
d(0x2307, lambda: P(*[(5 + 1.5 * m.sin(2 * m.pi * 3 * i / 30), 3.5 + 13 * i / 30) for i in range(31)]))
d(0x2309, lambda: mirror(G(0x2308)))
d(0x230B, lambda: mirror(G(0x230A)))
d(0x230D, lambda: mirror(G(0x230C)))
d(0x230F, lambda: mirror(G(0x230E)))
d(0x231D, lambda: mirror(G(0x231C)))
d(0x231F, lambda: mirror(G(0x231E)))
d(0x2310, lambda: mirror(G(0xAC)))
d(0x2319, lambda: flip(G(0x2310), 10.3))
d(0x2314, lambda: arc(5, 14.5, 7.8, 7.8, 244, 296) + P((1.58, 7.49), (5, 14.5), (8.42, 7.49)))
d(0x232B, lambda: mirror(G(0x2326)))
d(0x232C, lambda: outline(regular(6, 5, CY, 4.4), r=0.6) +
  [s for k in (0, 2, 4) for s in P(*[(5 + 2.9 * m.cos(m.radians(-90 + 60 * (k + j))), CY + 2.9 * m.sin(m.radians(-90 + 60 * (k + j))))
                                     for j in (0, 1)], r=0.5)])
d(0x23E3, lambda: outline(regular(6, 5, CY, 4.4), r=0.6) + ring(5, CY, 2.2, r=0.55))
d(0x2388, lambda: ring(5, CY, 2.7, r=0.55) +
  [s for k in range(8) for s in P((5 + 1.1 * m.cos(m.radians(45 * k)), CY + 1.1 * m.sin(m.radians(45 * k))),
                                  (5 + 4.4 * m.cos(m.radians(45 * k)), CY + 4.4 * m.sin(m.radians(45 * k))), r=0.5)])
d(0xFFFC, lambda: [s for a, b in (((1, 4), (9, 4)), ((9, 4), (9, 15.5)), ((9, 15.5), (1, 15.5)), ((1, 15.5), (1, 4)))
                   for t in (0.0, 0.4, 0.8)
                   for s in P((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t),
                              (a[0] + (b[0] - a[0]) * (t + 0.2), a[1] + (b[1] - a[1]) * (t + 0.2)), r=0.5)] +
  pen(squeeze(scale(A("O"), 1, 0.4, cy=9.75), 2, 3.8) + squeeze(scale(A("B"), 1, 0.4, cy=9.75), 4.3, 5.9) +
      squeeze(scale(A("J"), 1, 0.4, cy=9.75), 6.4, 8), 0.45))
d(0xFFFD, lambda: F((5, 3.5), (9.7, CY), (5, 16), (0.3, CY)) + cut(pen(scale(A("?"), 0.62, cy=9.5), 0.6)))

fam("piece")
d(0x239D, lambda: flip(G(0x239B), 10.0))
d(0x239E, lambda: mirror(G(0x239B)))
d(0x239F, lambda: mirror(G(0x239C)))
d(0x23A0, lambda: mirror(G(0x239D)))
d(0x23A3, lambda: flip(G(0x23A1), 10.0))
d(0x23A4, lambda: mirror(G(0x23A1)))
d(0x23A5, lambda: mirror(G(0x23A2)))
d(0x23A6, lambda: mirror(G(0x23A3)))
d(0x23A9, lambda: flip(G(0x23A7), 10.0))
d(0x23AB, lambda: mirror(G(0x23A7)))
d(0x23AC, lambda: mirror(G(0x23A8)))
d(0x23AD, lambda: mirror(G(0x23A9)))
d(0x23AE, lambda: G(0x23AA))

# APL: the quad, the circle and the tacks with a sign inside or beside.
fam("apl")
TILDE = lambda y=CY: S(f"E 3,{y} 2,1.3 180 360 | E 7,{y} 2,1.3 180 0")     # noqa: E731
DIAERESIS = lambda y=4.8: dots((3.4, y), (6.6, y))                         # noqa: E731
d(0x2338, lambda: QUAD() + P((3.4, 8.4), (6.6, 8.4), r=0.6) + P((3.4, 11.1), (6.6, 11.1), r=0.6))
d(0x2339, lambda: QUAD() + P((3.4, CY), (6.6, CY), r=0.6) + dots((5, 7.3), (5, 12.2), r=0.6))
d(0x233A, lambda: QUAD() + outline([(5, 6.2), (7.2, CY), (5, 13.3), (2.8, CY)], r=0.6))
d(0x233B, lambda: QUAD() + ring(5, CY, 1.4, r=0.6))
d(0x233C, lambda: QUAD() + ring(5, CY, 2.4, r=0.6))
d(0x233D, lambda: ring(5, CY, 3.4) + P((5, 4), (5, 15.5)))
d(0x233E, lambda: ring(5, CY, 3.4) + ring(5, CY, 1.2, r=0.55))
d(0x2340, lambda: mirror(G(0x233F)))
d(0x2341, lambda: QUAD() + P((8.2, 4.5), (1.8, 15), r=0.6))
d(0x2342, lambda: QUAD() + P((1.8, 4.5), (8.2, 15), r=0.6))
d(0x2343, lambda: QUAD() + P((6.6, 7), (3.4, CY), (6.6, 12.5), r=0.6))
d(0x2344, lambda: mirror(G(0x2343)))
d(0x2345, lambda: G(0x2190) + P((6.2, 5.5), (6.2, 14)))
d(0x2346, lambda: mirror(G(0x2345)))
d(0x2347, lambda: QUAD() + S("P@0.6 3.2,9.75 6.8,9.75 | P@0.6 4.8,8 3.2,9.75 4.8,11.5"))
d(0x2348, lambda: mirror(G(0x2347)))
d(0x2349, lambda: ring(5, CY, 3.4) + P((1.6, 5.4), (8.4, 14.1)))
d(0x234B, lambda: S("P 2,14 5,5.5 8,14 2,14 | P 5,3.8 5,15.8"))
d(0x2352, lambda: flip(G(0x234B), 9.8))
d(0x234C, lambda: QUAD() + P((3.2, 7.5), (5, 12), (6.8, 7.5), r=0.6))
d(0x2353, lambda: QUAD() + P((3.2, 12), (5, 7.5), (6.8, 12), r=0.6))
d(0x234D, lambda: QUAD() + outline([(5, 6.9), (7.2, 12.3), (2.8, 12.3)], r=0.6))
d(0x2354, lambda: QUAD() + outline([(5, 12.6), (7.2, 7.2), (2.8, 7.2)], r=0.6))
d(0x234F, lambda: G(0x2191) + P((2, 11.2), (8, 11.2)))
d(0x2356, lambda: G(0x2193) + P((2, 7.6), (8, 7.6)))
d(0x2350, lambda: QUAD() + S("P@0.6 5,7 5,12.6 | P@0.6 3.3,8.7 5,7 6.7,8.7"))
d(0x2357, lambda: QUAD() + S("P@0.6 5,6.9 5,12.5 | P@0.6 3.3,10.8 5,12.5 6.7,10.8"))
d(0x235E, lambda: QUAD() + P((5, 6.6), (5, 9.8)))
d(0x235F, lambda: ring(5, CY, 3.6) + star5(5, CY, 2.6))
d(0x2360, lambda: QUAD() + dots((5, 7.6), (5, 12)))
d(0x2361, lambda: S("P 2,7.5 8,7.5 | P 5,7.5 5,15") + DIAERESIS(4.6))
d(0x2362, lambda: S("P 2,7.5 8,7.5 5,15 2,7.5") + DIAERESIS(4.6))
d(0x2363, lambda: shift(scale(A("*"), 0.8, cy=9), 0, 2.4) + DIAERESIS(4.8))
d(0x2364, lambda: ring(5, 11.6, 2.0) + DIAERESIS(5.8))
d(0x2365, lambda: ring(5, 11.4, 3.2) + DIAERESIS(4.8))
d(0x2367, lambda: G(0x2282) + P((5.4, 4), (5.4, 15.5)))
d(0x2368, lambda: A("~") + DIAERESIS(6))
d(0x2369, lambda: S("P 2,7.5 8,11.2 2,15") + DIAERESIS(4.8))
d(0x236B, lambda: S("P 2,5 8,5 5,15 2,5") + TILDE(9.4))
d(0x236C, lambda: S("E 5,9.75 3,5 0 360") + TILDE(CY))
d(0x236D, lambda: P((5, 4.5), (5, 15)) + TILDE(CY))
d(0x236E, lambda: shift(A(";"), 0, -2) + P((2.5, 17.5), (7.5, 17.5)))
d(0x236F, lambda: QUAD() + S("P@0.55 3.4,8.5 6.6,8.5 | P@0.55 3.4,11 6.6,11 | P@0.55 6,6.8 4,12.7"))
d(0x2370, lambda: QUAD() + pen(scale(A("?"), 0.6, cy=9.5), 0.6))
d(0x2371, lambda: S("P 2,5.5 5,14 8,5.5") + TILDE(9.2))
d(0x2372, lambda: S("P 2,14 5,5.5 8,14") + TILDE(10.3))

fam("enclosed")
for _i in range(9):
    d(0x2460 + _i, lambda i=_i: ring(5, CY, 4.3, 4.9, r=0.6) + pen(script(A(str(i + 1)), 0.52, 6.9, 4.0), 0.6))
d(0x2469, lambda: ring(5, CY, 4.3, 4.9, r=0.55) +
  pen(squeeze(script(A("1"), 0.5, 7, 4.0), 2.3, 3.9) + squeeze(script(A("0"), 0.5, 7, 4.0), 4.9, 7.5), 0.55))

fam("shape")
SQ = lambda r=None: outline([(SQ0, SQT), (SQ1, SQT), (SQ1, SQB), (SQ0, SQB)], r)     # noqa: E731
RING = lambda: ring(5, CY, 3.6)                                                  # noqa: E731


def hatch(kind, n=2, r=0.45):
    out = []
    for i in range(1, n + 1):
        t = i / (n + 1)
        if kind == "h":
            out += P((SQ0, SQT + (SQB - SQT) * t), (SQ1, SQT + (SQB - SQT) * t), r=r)
        elif kind == "v":
            out += P((SQ0 + (SQ1 - SQ0) * t, SQT), (SQ0 + (SQ1 - SQ0) * t, SQB), r=r)
    if kind in ("\\", "/"):
        for i in range(1, 2 * n):                # diagonals at 45 degrees across the square
            t = i / n
            a = (SQ0 + 6.4 * min(t, 1), SQT + 6.4 * max(0, t - 1))
            b = (SQ0 + 6.4 * max(0, t - 1), SQT + 6.4 * min(t, 1))
            seg = P(a, b, r=r)                    # runs "/"
            out += seg if kind == "/" else mirror(seg)
    return out


d(0x25A2, lambda: [s for cx, cy, a in ((3.2, 7.95, 180), (6.8, 7.95, 270), (6.8, 11.55, 0), (3.2, 11.55, 90))
                   for s in arc(cx, cy, 1.4, 1.4, a, a + 90)] +
  P((3.2, SQT), (6.8, SQT)) + P((SQ1, 7.95), (SQ1, 11.55)) + P((6.8, SQB), (3.2, SQB)) + P((SQ0, 11.55), (SQ0, 7.95)))
d(0x25A4, lambda: SQ(0.6) + hatch("h"))
d(0x25A5, lambda: SQ(0.6) + hatch("v"))
d(0x25A6, lambda: SQ(0.6) + hatch("h") + hatch("v"))
d(0x25A7, lambda: SQ(0.6) + hatch("\\"))
d(0x25A8, lambda: SQ(0.6) + hatch("/"))
d(0x25A9, lambda: SQ(0.6) + hatch("\\") + hatch("/"))
d(0x25BD, lambda: flip(G(0x25B3), 9.7))
d(0x25BF, lambda: flip(G(0x25B5), 10.45))
d(0x25C1, lambda: mirror(G(0x25B7)))
d(0x25C3, lambda: mirror(G(0x25B9)))
d(0x25C5, lambda: mirror(G(0x25BB)))
d(0x25CC, lambda: [s for k in range(8) for s in dot(5 + 3.7 * m.cos(m.radians(45 * k)), CY + 3.7 * m.sin(m.radians(45 * k)), 0.8)])
d(0x25CD, lambda: RING() + [s for x in (3.4, 5, 6.6)
                            for s in P((x, CY - m.sqrt(3.6 ** 2 - (x - 5) ** 2)), (x, CY + m.sqrt(3.6 ** 2 - (x - 5) ** 2)), r=0.4)])
d(0x25CE, lambda: RING() + ring(5, CY, 2.0, r=0.6))
for _i in range(4):
    d(0x25DC + _i, lambda i=_i: arc(5, CY, 3.6, 3.6, 180 + 90 * i, 270 + 90 * i))
d(0x25E0, lambda: arc(5, CY, 3.6, 3.6, 180, 360))
d(0x25E1, lambda: arc(5, CY, 3.6, 3.6, 0, 180))
d(0x25EB, lambda: SQ() + P((5, SQT), (5, SQB)))
d(0x25EC, lambda: G(0x25B3) + dot(5, 11.4))
d(0x25F0, lambda: SQ() + P((5, SQT), (5, CY), (SQ0, CY)))
d(0x25F1, lambda: flip(G(0x25F0)))
d(0x25F2, lambda: mirror(G(0x25F1)))
d(0x25F3, lambda: mirror(G(0x25F0)))
d(0x25F4, lambda: RING() + P((5, CY - 3.6), (5, CY), (1.4, CY)))
d(0x25F5, lambda: flip(G(0x25F4)))
d(0x25F6, lambda: mirror(G(0x25F5)))
d(0x25F7, lambda: mirror(G(0x25F4)))
d(0x25F9, lambda: mirror(G(0x25F8)))
d(0x25FA, lambda: flip(G(0x25F8)))
d(0x25FF, lambda: mirror(G(0x25FA)))
d(0x2B1A, lambda: [s for a, b in (((SQ0, SQT), (SQ1, SQT)), ((SQ1, SQT), (SQ1, SQB)), ((SQ1, SQB), (SQ0, SQB)), ((SQ0, SQB), (SQ0, SQT)))
                   for t in (0.0, 0.4, 0.8)
                   for s in P((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t),
                              (a[0] + (b[0] - a[0]) * (t + 0.2), a[1] + (b[1] - a[1]) * (t + 0.2)), r=0.55)])
d(0x2B20, lambda: outline(regular(5, 5, 10.1, 4.0)))
d(0x2B21, lambda: outline(regular(6, 5, CY, 4.2)))

# Shapes filled or half filled: the outline, then the black part.
fam("shape-black")
d(0x25A3, lambda: SQ() + F((3.6, 8.35), (6.4, 8.35), (6.4, 11.15), (3.6, 11.15)))
d(0x25C4, lambda: mirror(G(0x25BA)))
d(0x25D2, lambda: RING() + half_disc(5, CY, 3.6, 0))
d(0x25D3, lambda: RING() + half_disc(5, CY, 3.6, 180))
d(0x25D4, lambda: RING() + sector(5, CY, 3.6, 270, 360))
d(0x25D5, lambda: RING() + sector(5, CY, 3.6, 270, 540))
d(0x25D6, lambda: half_disc(4.9, CY, 4.0, 90))
d(0x25D7, lambda: half_disc(5.1, CY, 4.0, 270))
BLOCK = lambda y0=5.55, y1=13.95: F((0.8, y0), (9.2, y0), (9.2, y1), (0.8, y1))     # noqa: E731
d(0x25D8, lambda: BLOCK() + cut(disc(5, CY, 1.8)))
d(0x25D9, lambda: BLOCK() + cut(ring(5, CY, 2.7, r=0.6)))
d(0x25DA, lambda: BLOCK(5.55, CY) + cut(arc(5, CY, 2.7, 2.7, 180, 360, r=0.6)))
d(0x25DB, lambda: BLOCK(CY, 13.95) + cut(arc(5, CY, 2.7, 2.7, 0, 180, r=0.6)))
d(0x25E3, lambda: mirror(G(0x25E2)))
d(0x25E4, lambda: flip(G(0x25E3)))
d(0x25E5, lambda: mirror(G(0x25E4)))
d(0x25E7, lambda: SQ() + F((SQ0, SQT), (5, SQT), (5, SQB), (SQ0, SQB)))
d(0x25E8, lambda: mirror(G(0x25E7)))
d(0x25E9, lambda: SQ() + F((SQ0, SQT), (SQ1, SQT), (SQ0, SQB)))
d(0x25EA, lambda: rot(G(0x25E9), 180))
d(0x2B12, lambda: SQ() + F((SQ0, SQT), (SQ1, SQT), (SQ1, CY), (SQ0, CY)))
d(0x2B13, lambda: flip(G(0x2B12)))
d(0x2B14, lambda: mirror(G(0x25E9)))
d(0x2B15, lambda: rot(G(0x2B14), 180))
d(0x25ED, lambda: G(0x25B3) + F((5, 5.8), (5, 13.6), (1.6, 13.6)))
d(0x25EE, lambda: mirror(G(0x25ED)))
d(0x2B16, lambda: outline(DIA) + F(DIA[0], DIA[2], DIA[3]))
d(0x2B17, lambda: mirror(G(0x2B16)))
d(0x2B18, lambda: outline(DIA) + F(DIA[3], DIA[0], DIA[1]))
d(0x2B19, lambda: flip(G(0x2B18)))
d(0x2B1F, lambda: F(*regular(5, 5, 10.1, 4.4)))
d(0x2B22, lambda: F(*regular(6, 5, CY, 4.6)))
d(0x2B23, lambda: F(*regular(6, 5, CY, 4.6, 0)))


# Batch 3: Miscellaneous Symbols and Dingbats. font/term-ding.txt holds the
# pictures drawn by hand, the white (outlined) one of each pair; here are the
# black ones, the turned ones, and the families a rule gives: lines, dice,
# suits, crosses, stars, florettes, shadowed shapes, circled digits, arrows.

tier("ding")
FAMILY.update(drawn_families(DING))


def fill(shapes, tol=0.004):
    """The shapes with every closed run of strokes filled."""
    out, run = [], []

    def close():
        if len(run) > 2 and abs(run[0][1] - run[-1][3]) < tol and abs(run[0][2] - run[-1][4]) < tol:
            out.append(("poly", [(s[1], s[2]) for s in run]))
        else:
            out.extend(run)
        run.clear()

    for sh in shapes:
        if sh[0] == "seg" and (not run or (abs(run[-1][3] - sh[1]) < tol and abs(run[-1][4] - sh[2]) < tol)):
            run.append(sh)
            continue
        close()
        if sh[0] == "seg":
            run.append(sh)
        else:
            out.append(sh)
    close()
    return out


def glyphs_():
    import glyphs
    return glyphs


def at(rad, deg, cx=5.0, cy=CY):
    return (cx + rad * m.cos(m.radians(deg)), cy + rad * m.sin(m.radians(deg)))


def rays(n, r0, r1, r=None, start=0.0):
    return [s for k in range(n) for s in P(at(r0, start + 360 * k / n), at(r1, start + 360 * k / n), r=r)]


def star(n, big, little, twist=0.0, start=-90.0):
    """The corners of an n-pointed star; twist turns the inner corners."""
    return [at(big if k % 2 == 0 else little, start + 180 * k / n + (twist if k % 2 else 0)) for k in range(2 * n)]


def shadow(pts, dx=0.8, dy=0.8, r=0.4):
    """A white shape with a black copy behind it, moved by (dx, dy)."""
    return F(*[(x + dx, y + dy) for x, y in pts]) + cut(F(*pts)) + outline(pts, r)


def around(shapes, n, start=0.0):
    return [s for k in range(n) for s in rot(shapes, start + 360 * k / n)]


fam("sky")
d(0x2600, lambda: disc(5, CY, 2.2) + rays(8, 3.3, 4.5, 0.45))
d(0x263C, lambda: ring(5, CY, 2.1, r=0.55) + rays(8, 3.4, 4.6, 0.45))
d(0x2609, lambda: ring(5, CY, 3.4) + disc(5, CY, 0.9))
d(0x260B, lambda: flip(G(0x260A)))
d(0x263D, lambda: mirror(G(0x263E)))
d(0x269B, lambda: around(ring(5, CY, 4.4, 1.6, r=0.45), 3) + disc(5, CY, 0.8))

fam("sign")
d(0x2622, lambda: sector(5, CY, 4.4, 180, 240) + sector(5, CY, 4.4, 300, 360) + sector(5, CY, 4.4, 60, 120) +
  cut(disc(5, CY, 1.6)) + disc(5, CY, 0.8))
d(0x2623, lambda: [s for a in (270, 30, 150) for s in ring(*at(2.2, a), 2.0, r=0.5)] + disc(5, CY, 0.7))
d(0x2629, lambda: P((5, 5.2), (5, 14.3), r=0.6) + P((0.9, CY), (9.1, CY), r=0.6) +
  [s for x in (2.3, 7.7) for y in (6.9, 12.6) for s in P((x, y - 1), (x, y + 1), r=0.35) + P((x - 1, y), (x + 1, y), r=0.35)])
d(0x262E, lambda: ring(5, CY, 4.0, r=0.6) + P((5, 5.75), (5, 13.75), r=0.6) + P((5, CY), at(4, 135), r=0.6) +
  P((5, CY), at(4, 45), r=0.6))
d(0x262F, lambda: half_disc(5, CY, 4, 90) + disc(5, CY - 2, 2) + cut(disc(5, CY + 2, 2)) + cut(disc(5, CY - 2, 0.65)) +
  disc(5, CY + 2, 0.65) + ring(5, CY, 4.0, r=0.5))
d(0x2638, lambda: ring(5, CY, 3.3, r=0.55) + rays(8, 0, 4.6, 0.4) + disc(5, CY, 0.9))
d(0x2639, lambda: ring(5, CY, 4.0, r=0.55) + disc(3.6, 8.4, 0.6) + disc(6.4, 8.4, 0.6) + arc(5, 12.9, 2, 1.6, 200, 340, r=0.5))
d(0x263A, lambda: ring(5, CY, 4.0, r=0.55) + disc(3.6, 8.4, 0.6) + disc(6.4, 8.4, 0.6) + arc(5, 10.4, 2, 1.6, 20, 160, r=0.5))
d(0x263B, lambda: disc(5, CY, 4.4) + cut(disc(3.6, 8.4, 0.7) + disc(6.4, 8.4, 0.7) + arc(5, 10.4, 2, 1.6, 20, 160, r=0.5)))
d(0x267E, lambda: ring(5, CY, 4.2, r=0.5) + pen(scale(G(0x221E), 0.62), 0.5))
d(0x2699, lambda: ring(5, CY, 2.4, r=0.85) + rays(8, 3.2, 4.3, 0.75))
d(0x269F, lambda: mirror(G(0x269E)))

fam("line")
_ROW = lambda y, whole, r=0.9: (P((1.2, y), (8.8, y), r=r) if whole                 # noqa: E731
                                else P((1.2, y), (3.3, y), r=r) + P((6.7, y), (8.8, y), r=r))
_rows = lambda ys, bits: [s for y, b in zip(ys, bits) for s in _ROW(y, b == "1")]   # noqa: E731
for _cp, _bits in ((0x2631, "011"), (0x2632, "101"), (0x2633, "001"), (0x2634, "110"), (0x2635, "010"),
                   (0x2636, "100"), (0x2637, "000")):
    d(_cp, lambda b=_bits: _rows((6.4, 9.75, 13.1), b))
d(0x268A, lambda: _rows((9.75,), "1"))
d(0x268B, lambda: _rows((9.75,), "0"))
for _cp, _bits in ((0x268C, "11"), (0x268D, "01"), (0x268E, "10"), (0x268F, "00")):
    d(_cp, lambda b=_bits: _rows((8.0, 11.5), b))
d(0x2758, lambda: P((5, 4), (5, 15.5), r=0.45))
d(0x2759, lambda: P((5, 4), (5, 15.5), r=0.9))
d(0x275A, lambda: P((5, 4.4), (5, 15.1), r=1.5))

fam("game")
_PIP = {1: "e", 2: "ai", 3: "aei", 4: "acgi", 5: "acegi", 6: "acdfgi"}
for _n in range(1, 7):
    d(0x267F + _n, lambda n=_n: outline([(1.3, 6.05), (8.7, 6.05), (8.7, 13.45), (1.3, 13.45)], 0.4) +
      [s for c in _PIP[n] for s in disc(3.0 + 2.0 * ((ord(c) - 97) % 3), 7.75 + 2.0 * ((ord(c) - 97) // 3), 0.9)])
d(0x2686, lambda: ring(5, CY, 4.0, r=0.55) + disc(6.7, CY, 0.9))
d(0x2687, lambda: ring(5, CY, 4.0, r=0.55) + disc(6.7, CY, 0.9) + disc(3.3, CY, 0.9))
d(0x2688, lambda: disc(5, CY, 4.4) + cut(disc(6.7, CY, 1.0)))
d(0x2689, lambda: disc(5, CY, 4.4) + cut(disc(6.7, CY, 1.0) + disc(3.3, CY, 1.0)))
_MAN = lambda y, r=0.5: arc(5, y, 4, 2.1, 0, 180, r=r) + P((1, y - 1.8), (1, y), r=r) + P((9, y - 1.8), (9, y), r=r)   # noqa: E731
d(0x26C0, lambda: ring(5, 9.2, 4, 2.1, r=0.5) + _MAN(11))
d(0x26C1, lambda: ring(5, 7.6, 4, 2.1, r=0.5) + _MAN(9.4) + _MAN(11.2) + _MAN(13))
d(0x26C2, lambda: disc(5, 11, 4.4, 2.5) + F((0.6, 9.2), (9.4, 9.2), (9.4, 11), (0.6, 11)) + disc(5, 9.2, 4.4, 2.5) +
  cut(arc(5, 9.2, 4.4, 2.5, 0, 180, r=0.3)))
d(0x26C3, lambda: disc(5, 13, 4.4, 2.5) + F((0.6, 7.6), (9.4, 7.6), (9.4, 13), (0.6, 13)) + disc(5, 7.6, 4.4, 2.5) +
  cut(arc(5, 7.6, 4.4, 2.5, 0, 180, r=0.3) + arc(5, 10.3, 4.4, 2.5, 0, 180, r=0.3)))
HEART = lambda: G(0x2661)                                                           # noqa: E731
_SPADE = lambda: scale(flip(HEART(), about=10.0), 1, 0.85, cy=5.8)                 # noqa: E731
_STEM = lambda: P((5, 11.4), (5, 15.2), r=0.5) + P((3.4, 15.2), (6.6, 15.2), r=0.5)   # noqa: E731
d(0x2664, lambda: _SPADE() + _STEM())
d(0x2660, lambda: fill(_SPADE()) + _STEM())
d(0x2665, lambda: fill(HEART()))
d(0x2666, lambda: fill(G(0x2662)))
d(0x2663, lambda: fill(G(0x2667)))

fam("object-black")
d(0x260E, lambda: fill(G(0x260F)) + cut(disc(5, 12.5, 1.0)))
d(0x2617, lambda: fill(G(0x2616)))
d(0x261B, lambda: fill(G(0x261E)))
d(0x261A, lambda: mirror(G(0x261B)))
for _i in range(6):
    d(0x265A + _i, lambda i=_i: fill(G(0x2654 + i)))
d(0x2712, lambda: fill(G(0x2711)) + cut(P((5, 15.4), (5, 10.6), r=0.3) + disc(5, 9.4, 0.8)))

fam("object")
d(0x261C, lambda: mirror(G(0x261E)))
d(0x261D, lambda: rot(G(0x261E), -90))
d(0x261F, lambda: rot(G(0x261E), 90))
d(0x2703, lambda: flip(G(0x2701)))
d(0x270E, lambda: rot(G(0x270F), 45))
d(0x2710, lambda: rot(G(0x270F), -45))

fam("recycle")
_TRI3 = lambda: regular(3, 5, 10.6, 4.6)                                            # noqa: E731


def _chase(r, length):
    pts = _TRI3()
    out = outline(pts, r)
    for i in range(3):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 3]
        out += head_at(x0 + (x1 - x0) * 0.58, y0 + (y1 - y0) * 0.58, m.degrees(m.atan2(y1 - y0, x1 - x0)), length, 42, r)
    return out


d(0x2672, lambda: _chase(0.5, 1.7))
for _i in range(1, 8):
    d(0x2672 + _i, lambda i=_i: outline(regular(3, 5, 10.9, 5.3), 0.4) + pen(script(A(str(i)), 0.45, 8.4, 4.0), 0.45))
d(0x267A, lambda: outline(_TRI3(), 0.45))
d(0x267B, lambda: _chase(0.95, 2.0))
d(0x267C, lambda: disc(5, CY, 4.6) + cut(shift(scale(_chase(0.45, 1.6), 0.66, cy=10.6), 0, -0.5)))
d(0x267D, lambda: ring(5, CY, 4.3, r=0.45) + shift(scale(_chase(0.45, 1.6), 0.66, cy=10.6), 0, -0.5))

fam("gender")
_g = lambda *parts: pen([s for p in parts for s in p], 0.55)                        # noqa: E731
_NE = lambda x, y, n=2.2: P((x, y), (x + n, y - n * 1.25)) + P((x + n - 2, y - n * 1.25), (x + n, y - n * 1.25), (x + n, y - n * 1.25 + 2))   # noqa: E731
d(0x26A2, lambda: _g(ring(3.8, 7.2, 2.3), ring(6.2, 7.2, 2.3), P((5, 9.2), (5, 15.2)), P((3, 12.6), (7, 12.6))))
d(0x26A3, lambda: _g(shift(scale(G(0x2642), 0.82), -1.1, 0.6), shift(scale(G(0x2642), 0.82), 1.0, -0.6)))
d(0x26A4, lambda: _g(ring(3.8, 8.4, 2.3), P((3.8, 10.7), (3.8, 15.4)), P((2.2, 13.4), (5.4, 13.4)), ring(6.2, 9.8, 2.3),
                     _NE(7.7, 8.1, 1.6)))
d(0x26A5, lambda: _g(ring(5, 9.4, 2.6), P((5, 12), (5, 15.6)), P((3.4, 13.8), (6.6, 13.8)), _NE(6.8, 7.5, 2.0)))
d(0x26A6, lambda: G(0x2642) + P((5.4, 5.6), (8.9, 9.4), r=0.6))
d(0x26A7, lambda: _g(G(0x26A5), mirror(_NE(6.8, 7.5, 2.0)), P((1.3, 7.3), (3.1, 5.5))))
d(0x26A8, lambda: _g(ring(5, 11.8, 2.6), P((5, 9.2), (5, 4.2)), P((3.4, 5.8), (5, 4.2), (6.6, 5.8)), P((3.4, 7.6), (6.6, 7.6))))
d(0x26A9, lambda: _g(ring(3.6, CY, 2.6), P((6.2, CY), (9.2, CY)), P((7.8, 8.2), (9.2, CY), (7.8, 11.3)), P((7, 8.2), (7, 11.3))))
d(0x26AC, lambda: ring(5, CY, 2.0, r=0.55))
d(0x26AD, lambda: _g(ring(3.6, CY, 2.6), ring(6.4, CY, 2.6)))
d(0x26AE, lambda: _g(ring(2.7, CY, 1.9), ring(7.3, CY, 1.9), P((5, 5.5), (5, 14))))
d(0x26AF, lambda: _g(ring(2.5, CY, 1.8), ring(7.5, CY, 1.8), P((4.3, CY), (5.7, CY))))
d(0x26B2, lambda: ring(5, 7.6, 2.8) + P((5, 10.4), (5, 15.4)))

fam("cross")
_PLUS = lambda arm, half: [(5 + sx * a, CY + sy * b) for sx, sy, a, b in (       # noqa: E731
    (-1, -1, half, arm), (1, -1, half, arm), (1, -1, half, half), (1, -1, arm, half), (1, 1, arm, half), (1, 1, half, half),
    (1, 1, half, arm), (-1, 1, half, arm), (-1, 1, half, half), (-1, 1, arm, half), (-1, -1, arm, half), (-1, -1, half, half))]
_LATIN = [(3.9, 4), (6.1, 4), (6.1, 6.6), (8.4, 6.6), (8.4, 8.8), (6.1, 8.8), (6.1, 15.5), (3.9, 15.5), (3.9, 8.8),
          (1.6, 8.8), (1.6, 6.6), (3.9, 6.6)]
_arms = lambda r0, r1, r: rays(4, r0, r1, r)                                        # noqa: E731
d(0x2719, lambda: outline(_PLUS(4.0, 1.5), 0.45))
d(0x271A, lambda: F(*_PLUS(4.3, 1.4)))
d(0x271B, lambda: _arms(1.5, 4.2, 0.6))
d(0x271C, lambda: _arms(2.3, 3.9, 1.1))
d(0x271D, lambda: P((5, 4), (5, 15.5), r=0.6) + P((2, 7.6), (8, 7.6), r=0.6))
d(0x271E, lambda: shadow([(x - 0.4, y - 0.3) for x, y in _LATIN], 0.9, 0.7, 0.4))
d(0x271F, lambda: outline(_LATIN, 0.45))
d(0x2720, lambda: around(F((5, CY - 0.4), (2.9, CY - 4.5), (5, CY - 3.6), (7.1, CY - 4.5)), 4))

fam("star")
_balls = lambda n, r, b, start=-90.0: rays(n, 0, 2.8, r, start) + [s for k in range(n) for s in disc(*at(3.5, start + 360 * k / n), b)]   # noqa: E731
_petals = lambda n, dist, rad, start=-90.0: [at(dist, start + 360 * k / n) + (rad,) for k in range(n)]   # noqa: E731
d(0x2721, lambda: outline(regular(3, 5, CY, 4.5), 0.5) + outline(regular(3, 5, CY, 4.5, 90), 0.5))
d(0x2723, lambda: _balls(4, 0.4, 1.0))
d(0x2724, lambda: _balls(4, 0.75, 1.35))
d(0x2725, lambda: rays(4, 0, 3.0, 0.45, -90) + around(disc(5, CY - 3.9, 0.8) + disc(4.0, CY - 2.9, 0.8) + disc(6.0, CY - 2.9, 0.8), 4))
d(0x2726, lambda: F(*star(4, 4.7, 1.5)))
d(0x2727, lambda: outline(star(4, 4.7, 1.5), 0.5))
d(0x2729, lambda: outline(star(5, 4.9, 2.0), 0.35) + outline(star(5, 2.9, 1.2), 0.35))
d(0x272A, lambda: disc(5, CY, 4.6) + cut(F(*star(5, 4.0, 1.65))))
d(0x272B, lambda: F(*star(5, 4.9, 2.0)) + cut(disc(5, CY + 0.1, 1.05)))
d(0x272C, lambda: outline(star(5, 4.8, 1.95), 0.45) + disc(5, CY + 0.1, 1.1))
d(0x272D, lambda: F(*star(5, 3.3, 1.35)) + outline(star(5, 4.9, 2.0), 0.3))
d(0x272E, lambda: F(*star(5, 2.9, 1.2)) + outline(star(5, 4.8, 2.0), 0.6))
d(0x272F, lambda: F(*star(5, 4.8, 1.5, twist=24)))
d(0x2730, lambda: shadow([(x - 0.4, y - 0.4) for x, y in star(5, 4.3, 1.75)], 0.9, 0.9, 0.4))
d(0x2731, lambda: rays(6, 0, 3.6, 1.0, -90))
d(0x2732, lambda: rays(6, 1.6, 4.2, 0.7, -90))
d(0x2734, lambda: F(*star(8, 4.7, 2.6)))
d(0x2735, lambda: F(*star(8, 4.7, 2.2, twist=16)))
d(0x2737, lambda: F(*regular(4, 5, CY, 4.3, 0)) + F(*regular(4, 5, CY, 4.3, 45)))
d(0x2738, lambda: F(*regular(4, 5, CY, 4.9, 0)) + F(*regular(4, 5, CY, 4.9, 45)) + cut(disc(5, CY, 0.9)))
d(0x2739, lambda: F(*star(12, 4.7, 3.2)))
d(0x273A, lambda: rays(16, 0.9, 4.5, 0.3, -90))
d(0x273C, lambda: glyphs_().spokes(8, 0.43, 0.075)[:-1] + cut(disc(5, CY, 1.2)))
d(0x273E, lambda: [s for k, (x, y, r) in enumerate(_petals(6, 3.0, 1.5)) for s in (disc(x, y, r) if k % 2 == 0 else ring(x, y, r - 0.35, r=0.35))] +
  disc(5, CY, 0.9))
d(0x273F, lambda: [s for x, y, r in _petals(5, 2.8, 1.8) for s in disc(x, y, r)] + cut(disc(5, CY, 1.0)))
d(0x2740, lambda: [s for x, y, r in _petals(5, 2.8, 1.5) for s in ring(x, y, r, r=0.4)] + ring(5, CY, 0.9, r=0.4))
d(0x2741, lambda: [s for x, y, r in _petals(8, 3.3, 1.2) for s in disc(x, y, r)] + ring(5, CY, 1.3, r=0.4))
d(0x2742, lambda: disc(5, CY, 4.7) + cut(F(*star(8, 4.0, 2.0))) + disc(5, CY, 0.9))
d(0x2743, lambda: glyphs_().spokes(5, 0.44, 0.13, -54.0))
_snow = lambda r, barb, r1=4.4: rays(6, 0, r1, r, -90) + around(P((5 - barb, CY - 3.0 - barb), (5, CY - 3.0), (5 + barb, CY - 3.0 - barb), r=r), 6)   # noqa: E731
d(0x2744, lambda: _snow(0.4, 1.1))
d(0x2745, lambda: rays(6, 0, 3.1, 0.5, -90) + [s for k in range(6) for s in disc(*at(3.8, -90 + 60 * k), 0.95)])
d(0x2746, lambda: _snow(0.8, 1.5, 4.0))
_diag = lambda r: rays(4, 1.9, 3.4, r, 45)                                          # noqa: E731
d(0x2747, lambda: F(*star(4, 4.8, 0.9)) + _diag(0.4))
d(0x2748, lambda: F(*star(4, 4.8, 1.6)) + _diag(0.75))
d(0x2749, lambda: _balls(6, 0.4, 0.85))
d(0x274A, lambda: glyphs_().spokes(8, 0.42, 0.07, -67.5))
d(0x274B, lambda: glyphs_().spokes(8, 0.45, 0.105, -67.5))

fam("ornament")
_SQ3 = [(1.4, 6.4), (7.6, 6.4), (7.6, 12.6), (1.4, 12.6)]
d(0x274D, lambda: disc(5.8, 10.6, 3.8) + cut(disc(4.6, 9.4, 3.8)) + ring(4.6, 9.4, 3.8, r=0.4))
d(0x274F, lambda: shadow(_SQ3, 1.3, 1.3))
d(0x2750, lambda: shadow([(x, y + 0.9) for x, y in _SQ3], 1.3, -1.3))
d(0x2751, lambda: outline(_SQ3, 0.4) + P((8.3, 7.4), (8.3, 13.3), (2.4, 13.3), r=0.7))
d(0x2752, lambda: outline([(x, y + 0.9) for x, y in _SQ3], 0.4) + P((2.4, 6.6), (8.3, 6.6), (8.3, 12.5), r=0.7))
d(0x2756, lambda: F(*DIA) + cut(P((3.4, 8.15), (6.6, 11.35), r=0.5) + P((6.6, 8.15), (3.4, 11.35), r=0.5)))
_COMMA = lambda cx, cy, k=1.0: disc(cx, cy, 1.5 * k) + F((cx + 1.5 * k, cy), (cx - 1.4 * k, cy + 4.6 * k), (cx + 0.2 * k, cy + 1.0 * k))   # noqa: E731
_TURNED = lambda cx, cy, k=1.0: disc(cx, cy, 1.5 * k) + F((cx - 1.5 * k, cy), (cx + 1.4 * k, cy - 4.6 * k), (cx - 0.2 * k, cy - 1.0 * k))   # noqa: E731
d(0x275B, lambda: _TURNED(5, 9.6))
d(0x275C, lambda: _COMMA(5, 6.0))
d(0x275D, lambda: _TURNED(2.9, 9.2, 0.85) + _TURNED(7.1, 9.2, 0.85))
d(0x275E, lambda: _COMMA(2.9, 6.2, 0.85) + _COMMA(7.1, 6.2, 0.85))
d(0x2762, lambda: F((3.5, 4), (6.5, 4), (5.5, 11.4), (4.5, 11.4)) + disc(5, 14.1, 1.3))
d(0x2763, lambda: shift(scale(fill(HEART()), 0.8, 0.8, 5, 10), 0, -2.2) + disc(5, 14.3, 1.2))
d(0x2764, lambda: scale(fill(HEART()), 1.17, 1.12, 5, 10))
d(0x2765, lambda: rot(fill(HEART()), -90, 5, 10))
d(0x2767, lambda: rot(G(0x2766), -90, 5, 10))
d(0x2619, lambda: mirror(G(0x2767)))
d(0x2768, lambda: arc(7.6, 10, 3.6, 6.4, 120, 240, r=0.85))
d(0x2769, lambda: mirror(G(0x2768)))
d(0x276A, lambda: arc(10.4, 10, 6.2, 6.6, 145, 215, r=0.85))
d(0x276B, lambda: mirror(G(0x276A)))
d(0x276C, lambda: P((6.4, 3.8), (3.6, 10), (6.4, 16.2), r=0.85))
d(0x276D, lambda: mirror(G(0x276C)))
d(0x276E, lambda: P((6.4, 5.6), (3.4, 9.75), (6.4, 13.9), r=1.2))
d(0x2770, lambda: P((6.9, 3.8), (3.1, 10), (6.9, 16.2), r=1.3))
d(0x2771, lambda: mirror(G(0x2770)))
d(0x2772, lambda: P((6.4, 3.6), (4, 5.6), (4, 14.4), (6.4, 16.4), r=0.5))
d(0x2773, lambda: mirror(G(0x2772)))
d(0x2774, lambda: pen(A("{"), 0.9))
d(0x2775, lambda: pen(A("}"), 0.9))

fam("digit")
_num = lambda i, r: (pen(script(A(str(i)), 0.52, 6.9, 4.0), r) if i < 10 else                                # noqa: E731
                     pen(squeeze(script(A("1"), 0.5, 7, 4.0), 2.3, 3.9) + squeeze(script(A("0"), 0.5, 7, 4.0), 4.9, 7.5), r))
for _i in range(1, 11):
    d(0x2775 + _i, lambda i=_i: disc(5, CY, 4.5, 5.0) + cut(_num(i, 0.55)))
    d(0x277F + _i, lambda i=_i: ring(5, CY, 4.3, 4.9, r=0.5) + _num(i, 0.5))
    d(0x2789 + _i, lambda i=_i: G(0x2775 + i))

fam("arrow")
_BA = lambda x0, x1, sh, hl, hh, notch=0.0: ([(x0, CY - sh), (x1 - hl, CY - sh), (x1 - hl, CY - hh), (x1, CY),      # noqa: E731
                                              (x1 - hl, CY + hh), (x1 - hl, CY + sh), (x0, CY + sh)] +
                                             ([(x0 + notch, CY)] if notch else []))
_tilt = lambda pts, k: [(x + (y - CY) * k, y) for x, y in pts]                      # noqa: E731
_HEAD = lambda x=6.0, hh=2.15: F((9.4, CY), (x, CY - hh), (x, CY + hh))             # noqa: E731
d(0x2794, lambda: P((1.2, CY), (6, CY), r=1.0) + F((9.5, CY), (5.4, CY - 4.2), (5.4, CY + 4.2)))
d(0x2799, lambda: P((1.2, CY), (8, CY), r=1.0) + P((5.2, 6.4), (8.6, CY), (5.2, 13.1), r=1.0))
d(0x2798, lambda: rot(G(0x2799), 45))
d(0x279A, lambda: rot(G(0x2799), -45))
d(0x279D, lambda: P((1, CY), (6, CY), r=0.5) + _HEAD())
d(0x279E, lambda: P((1.3, CY), (5.6, CY), r=0.95) + _HEAD(5.6, 2.95))
d(0x279F, lambda: P((1, CY), (2.0, CY), r=0.5) + P((3.8, CY), (4.8, CY), r=0.5) + _HEAD())
d(0x27A0, lambda: P((1.3, CY), (1.7, CY), r=0.95) + P((4.0, CY), (4.4, CY), r=0.95) + _HEAD(5.6, 2.95))
d(0x27A1, lambda: F(*_BA(0.8, 9.4, 1.3, 4.0, 3.6)))
d(0x27A3, lambda: flip(G(0x27A2)))
d(0x27A6, lambda: flip(G(0x27A5)))
d(0x27A7, lambda: F(*_BA(1.8, 8.6, 2.3, 3.4, 4.3)))
d(0x27A8, lambda: F(*_BA(0.8, 9.4, 1.7, 4.4, 4.2, notch=1.8)))
_WA = lambda: _BA(1.0, 8.4, 1.5, 3.6, 3.5)                                          # noqa: E731
d(0x27A9, lambda: shadow(_WA(), 1.0, 0.0))
d(0x27AA, lambda: shadow([(x + 1.0, y) for x, y in _WA()], -1.0, 0.0))
d(0x27AB, lambda: shadow(_tilt(_WA(), 0.22), 0.8, 0.8))
d(0x27AC, lambda: shadow(_tilt(_WA(), -0.22), 0.8, 0.8))
d(0x27AD, lambda: shadow(_WA(), 0.9, 1.0, 0.6))
d(0x27AE, lambda: shadow([(x, y + 0.6) for x, y in _WA()], 0.9, -1.0, 0.6))
d(0x27AF, lambda: shadow(_BA(1.0, 8.4, 1.5, 3.6, 3.5, notch=1.6), 0.9, 1.0))
d(0x27B1, lambda: shadow([(x, y + 0.6) for x, y in _BA(1.0, 8.4, 1.5, 3.6, 3.5, notch=1.6)], 0.9, -1.0))
d(0x27B2, lambda: disc(5, CY, 4.7) + cut(F(*_BA(2.0, 8.6, 1.0, 3.0, 2.7))))
_FEATHER = lambda r, w: (P((2.6, CY), (6.4, CY), r=r) + _HEAD(6.0, w) +             # noqa: E731
                         F((0.6, CY - w), (2.2, CY - w), (4.2, CY), (2.2, CY + w), (0.6, CY + w), (2.6, CY)))
d(0x27B5, lambda: _FEATHER(0.5, 2.2))
d(0x27B4, lambda: rot(G(0x27B5), 45))
d(0x27B6, lambda: rot(G(0x27B5), -45))
d(0x27B8, lambda: _FEATHER(0.95, 3.1))
d(0x27B7, lambda: rot(G(0x27B8), 45))
d(0x27B9, lambda: rot(G(0x27B8), -45))
d(0x27BD, lambda: F((0.8, 6.5), (3.8, CY), (0.8, 13.0)) + P((2.4, CY), (5.8, CY), r=0.95) + _HEAD(5.6, 3.1))


def made(name):
    """{char: shapes} for a tier: every character drawn in its file and every
    one made here for it."""
    drawn = {ord(c): g for c, g in strokes.parse(DRAWN[name]).items()}
    mine = [c for c in T if TIER[c] == name]
    both = set(drawn) & set(T)
    if both:
        raise ValueError("drawn and made: " + " ".join(f"U+{c:04X}" for c in sorted(both)))
    out = {chr(c): g for c, g in drawn.items()}
    out.update({chr(c): G(c) for c in mine})
    lost = [c for c in out if FAMILY.get(ord(c)) is None]
    if lost:
        raise ValueError("no family: " + " ".join(f"U+{ord(c):04X}" for c in sorted(lost)))
    return out


def math():
    """{char: shapes} for the tmath tier."""
    return made("math")


def sym():
    """{char: shapes} for the tsym tier."""
    return made("sym")


def ding():
    """{char: shapes} for the tding tier."""
    return made("ding")
