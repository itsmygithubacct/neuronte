"""Neuronte's character sets and the target fields the net learns.

A glyph is a list of shapes in cell units, x 0..1 across the cell and y
0..2 down it, applied in order to an empty field:

    ("seg", x0, y0, x1, y1, r)   add a pen stroke of radius r (None: the default pen)
    ("poly", [(x, y), ...])      add a filled polygon
    ("cut", shape)               take a shape away

Tiers:

    ascii    U+0020..U+007E, from font/strokes.txt.
    box      box drawing U+2500..U+257F, made here from the Unicode names.
    block    block elements U+2580..U+259F, from the names, and the
             shades U+2591..U+2593 as dither patterns.
    braille  U+2800..U+28FF, made here from the dot bits.
    symbol   the symbols in font/symbols.txt and five asterisks made here.
    accent   Latin-1 letters U+00C0..U+00FF, Latin Extended-A
             U+0100..U+017F and the spacing marks, made here from an
             ASCII letter and the marks in font/marks.txt, by the Unicode
             decomposition, or taken from font/letters.txt.

Sets, each a list of tiers: ascii; draw (box, block, braille); symbol;
accent; and full (ascii, draw and symbol), the set the shipped full
weights were trained on.

field() gives the target: the signed distance to the ink edge, positive
inside, divided by tau and clamped to -1..1, at grid nodes 1/n cell width
apart. Lines and blocks that meet the cell edge run on past it, so
neighbouring cells join.

python3 train/glyphs.py lists the full set and checks it.
"""
import math
import os
import sys
import unicodedata

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import strokes  # noqa: E402

PAD = 0.25                  # how far edge lines and blocks run past the cell
LIGHT, HEAVY = 0.06, 0.12   # half widths of box lines, in cell widths
DOUBLE = 0.19               # offset of each line of a double line from its centre line
CX, CY = 0.5, 1.0           # where box lines meet
BRAILLE_R = 0.11            # Braille dot radius; the dots sit on a lattice 0.5 apart
CENTRE = 0.975              # the maths line, where the asterisks sit
FAR = -10.0                 # the field of an empty glyph


def rect(x0, y0, x1, y1):
    return ("poly", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


# Box drawing: lines from the centre to each side.

SIDES = ("up", "right", "down", "left")
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
ACROSS = {"up": ("left", "right"), "down": ("left", "right"),
          "left": ("up", "down"), "right": ("up", "down")}
KIND = {"LIGHT": 1, "SINGLE": 1, "HEAVY": 2, "DOUBLE": 3}
REACH = {0: 0.0, 1: LIGHT, 2: HEAVY, 3: DOUBLE + LIGHT}  # half width across each kind
DIRS = {"UP": ("up",), "DOWN": ("down",), "LEFT": ("left",), "RIGHT": ("right",),
        "VERTICAL": ("up", "down"), "HORIZONTAL": ("left", "right")}


def _side(side, half, reach):
    """A bar of half width `half` from the far edge to `reach` past the centre."""
    if side == "left":
        return rect(-PAD, CY - half, CX + reach, CY + half)
    if side == "right":
        return rect(CX - reach, CY - half, 1 + PAD, CY + half)
    if side == "up":
        return rect(CX - half, -PAD, CX + half, CY + reach)
    return rect(CX - half, CY - reach, CX + half, 2 + PAD)


def junction(arms):
    """Shapes for arms {side: 1 light, 2 heavy, 3 double} meeting at the centre.

    A line runs past the centre to the far side of the arms across it.
    Where there are none, it runs on into an opposite arm at least as
    heavy, so the two leave no seam. A double line is a wide bar with a
    channel cut along it; channels of doubles that meet join, and single
    lines are added after the cut, so they cross a double.
    """
    outer, channel, single = [], [], []
    inner = DOUBLE - LIGHT
    for side, kind in arms.items():
        across = [arms.get(s, 0) for s in ACROSS[side]]
        reach = max(REACH[k] for k in across)
        opp = arms.get(OPPOSITE[side], 0)
        if kind == 3:
            outer.append(_side(side, DOUBLE + LIGHT, max(reach, DOUBLE + LIGHT if opp == 3 else 0)))
            channel.append(_side(side, inner, inner if 3 in across else max(reach, inner if opp == 3 else 0)))
        else:
            half = REACH[kind]
            single.append(_side(side, half, max(reach, half if REACH[opp] >= half else 0)))
    return outer + [("cut", c) for c in channel] + single


def arms_of(words):
    """Arms from a name such as LIGHT DOWN AND RIGHT, DOWN LIGHT AND RIGHT
    HEAVY or LIGHT LEFT AND HEAVY RIGHT. A weight word either follows its
    directions or leads them."""
    arms, pending, lead = {}, [], None

    def give(dirs, kind):
        for d in dirs:
            if d in arms:
                raise ValueError(f"{d} given twice in {' '.join(words)}")
            arms[d] = kind

    for w in words:
        if w in KIND:
            if pending and lead is None:  # DOWN LIGHT: the weight follows
                give(pending, KIND[w])
            else:                         # LIGHT DOWN: the weight leads
                if pending:
                    give(pending, lead)
                lead = KIND[w]
            pending = []
        elif w in DIRS:
            pending += DIRS[w]
        elif w != "AND":
            raise ValueError(f"unknown word {w} in {' '.join(words)}")
    if pending:
        if lead is None:
            raise ValueError(f"no weight for {pending} in {' '.join(words)}")
        give(pending, lead)
    return arms


def dashes(vertical, n, half):
    """n dashes, each 0.6 of its period and centred in it, so a row of
    cells keeps the rhythm."""
    length = 2.0 if vertical else 1.0
    period = length / n
    out = []
    for k in range(n):
        a, b = (k + 0.2) * period, (k + 0.8) * period
        out.append(rect(CX - half, a, CX + half, b) if vertical else rect(a, CY - half, b, CY + half))
    return out


def arc(v, h):
    """A quarter circle of radius 0.5 joining the v (up/down) arm to the
    h (left/right) arm, with straight runs past the cell edge."""
    sx, sy = (1 if h == "RIGHT" else -1), (1 if v == "DOWN" else -1)
    r = 0.5
    cx, cy = CX + r * sx, CY + r * sy
    a0 = math.atan2(0, -r * sx)
    a1 = math.atan2(-r * sy, 0)
    if a1 - a0 > math.pi:
        a1 -= 2 * math.pi
    elif a0 - a1 > math.pi:
        a1 += 2 * math.pi
    pts = [(CX, CY + sy * (1 + PAD))]
    pts += [(cx + r * math.cos(a0 + (a1 - a0) * i / 9), cy + r * math.sin(a0 + (a1 - a0) * i / 9))
            for i in range(10)]
    pts.append((CX + sx * (0.5 + PAD), CY))
    return [("seg", *pts[i], *pts[i + 1], LIGHT) for i in range(len(pts) - 1)]


def diagonal(x0, y0, x1, y1):
    e = 0.15
    dx, dy = x1 - x0, y1 - y0
    return [("seg", x0 - e * dx, y0 - e * dy, x1 + e * dx, y1 + e * dy, LIGHT)]


def box(ch):
    words = unicodedata.name(ch).split()
    assert words[:2] == ["BOX", "DRAWINGS"], ch
    words = words[2:]
    if "DASH" in words:
        n = {"DOUBLE": 2, "TRIPLE": 3, "QUADRUPLE": 4}[words[1]]
        return dashes(words[-1] == "VERTICAL", n, REACH[KIND[words[0]]])
    if "ARC" in words:
        return arc(words[2], words[4])
    if "DIAGONAL" in words:
        if words[-1] == "CROSS":
            return diagonal(1, 0, 0, 2) + diagonal(0, 0, 1, 2)
        if words[2:4] == ["UPPER", "RIGHT"]:
            return diagonal(1, 0, 0, 2)
        return diagonal(0, 0, 1, 2)
    return junction(arms_of(words))


# Block elements.

NUM = {"ONE": 1, "THREE": 3, "FIVE": 5, "SEVEN": 7}
DEN = {"EIGHTH": 8, "EIGHTHS": 8, "QUARTER": 4, "QUARTERS": 4}


def block(ch):
    name = unicodedata.name(ch)
    words = name.split()
    if name == "FULL BLOCK":
        return [rect(-PAD, -PAD, 1 + PAD, 2 + PAD)]
    if words[0] == "QUADRANT":
        quads = {tuple(part.split()) for part in " ".join(words[1:]).split(" AND ")}
        out = []
        for v, h in quads:
            x0, x1 = (-PAD, CX) if h == "LEFT" else (CX, 1 + PAD)
            y0, y1 = (-PAD, CY) if v == "UPPER" else (CY, 2 + PAD)
            # run into a neighbour that is also ink, so the union has no seam
            if (v, "RIGHT") in quads and h == "LEFT":
                x1 = CX + PAD
            if (v, "LEFT") in quads and h == "RIGHT":
                x0 = CX - PAD
            if ("LOWER", h) in quads and v == "UPPER":
                y1 = CY + PAD
            if ("UPPER", h) in quads and v == "LOWER":
                y0 = CY - PAD
            out.append(rect(x0, y0, x1, y1))
        return out
    assert words[-1] == "BLOCK", name
    frac = 0.5 if words[1] == "HALF" else NUM[words[1]] / DEN[words[2]]
    return [{"UPPER": rect(-PAD, -PAD, 1 + PAD, 2 * frac),
             "LOWER": rect(-PAD, 2 - 2 * frac, 1 + PAD, 2 + PAD),
             "LEFT": rect(-PAD, -PAD, frac, 2 + PAD),
             "RIGHT": rect(1 - frac, -PAD, 1 + PAD, 2 + PAD)}[words[0]]]


def shade(ch):
    """Light, medium and dark shade: squares a quarter cell width across
    on a lattice that tiles across cells, 25, 50 and 75 percent ink."""
    q = 0.25
    level = {0x2591: 1, 0x2592: 2, 0x2593: 3}[ord(ch)]

    def square(x0, y0):
        x1, y1 = x0 + q, y0 + q
        # a square on the cell edge runs past it, so neighbours join
        return rect(-PAD if x0 <= 0 else x0, -PAD if y0 <= 0 else y0,
                    1 + PAD if x1 >= 1 else x1, 2 + PAD if y1 >= 2 else y1)

    if level == 2:
        return [square(i * q, j * q) for i in range(4) for j in range(8) if (i + j) % 2 == 0]
    holes = [rect(0.125 + 0.5 * i, 0.125 + 0.5 * j, 0.375 + 0.5 * i, 0.375 + 0.5 * j)
             for i in range(2) for j in range(4)]
    if level == 1:
        return holes
    return [rect(-PAD, -PAD, 1 + PAD, 2 + PAD)] + [("cut", h) for h in holes]


SHADES = (0x2591, 0x2592, 0x2593)


# Braille: bit k raises dot k + 1. Dots 1-3 and 7 are the left column,
# 4-6 and 8 the right, top to bottom.

DOTS = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (0, 3), (1, 3)]


def braille(bits):
    out = []
    for k, (c, r) in enumerate(DOTS):
        if bits >> k & 1:
            x, y = 0.25 + 0.5 * c, 0.25 + 0.5 * r
            out.append(("seg", x, y, x, y, BRAILLE_R))
    return out


# Asterisks.

def teardrop(ang, length, tip):
    """A spoke from the centre, sharp at the centre and round at the tip."""
    a = math.radians(ang)
    cx, cy = 0.5 + length * math.cos(a), CENTRE + length * math.sin(a)
    b = math.acos(tip / length)
    a0, a1 = a + math.pi + b, a + 3 * math.pi - b
    arc_pts = [(cx + tip * math.cos(a0 + (a1 - a0) * i / 16), cy + tip * math.sin(a0 + (a1 - a0) * i / 16))
               for i in range(17)]
    return ("poly", [(0.5, CENTRE)] + arc_pts)


def spokes(n, length, tip, start=-90.0):
    hub = ("seg", 0.5, CENTRE, 0.5, CENTRE, tip * 0.8)
    return [teardrop(start + 360.0 * k / n, length, tip) for k in range(n)] + [hub]


def star(points, outer, inner):
    pts = []
    for k in range(2 * points):
        a = math.radians(-90 + 180.0 * k / points)
        r = outer if k % 2 == 0 else inner
        pts.append((0.5 + r * math.cos(a), CENTRE + r * math.sin(a)))
    return [("poly", pts)]


def asterisks():
    return {
        "✢": spokes(4, 0.28, 0.1),
        "✳": [("seg", 0.5, CENTRE, 0.5 + 0.33 * math.cos(math.radians(45 * k)),
                    CENTRE + 0.33 * math.sin(math.radians(45 * k)), 0.06) for k in range(8)],
        "✶": star(6, 0.42, 0.42 / math.sqrt(3)),
        "✻": spokes(6, 0.295, 0.085),
        "✽": spokes(8, 0.3, 0.08),
    }


# Composed letters.
LETTERS = os.path.join(strokes.ROOT, "font", "letters.txt")
MARKS = os.path.join(strokes.ROOT, "font", "marks.txt")
ABOVE = {0x300, 0x301, 0x302, 0x303, 0x304, 0x306, 0x307, 0x308, 0x30A, 0x30B, 0x30C, 0x312}
BELOW = {0x326, 0x327, 0x328}
RAISE = 0.23           # how far marks above move up for a capital
SHORT_TOP = 0.58       # where a capital, or an ascender, under a mark now starts
BASELINE, XHEIGHT = 1.5, 0.8
# Marks drawn differently on some letters, as fonts commonly do.
CARON_BESIDE = {"d": 0.89, "l": 0.72, "t": 0.66, "L": 0.45}   # caron as a comma beside the stem, at x
COMMA_BELOW = set("GKLNRknlr")                                # cedilla as a comma below
TURNED_COMMA = {"g"}                                          # cedilla as a turned comma above
DOTLESS = {"i": "\u0131", "j": "\u0237"}
# The spacing marks, alone in the cell, and the mark each one is.
SPACING = {0xA8: 0x308, 0xAF: 0x304, 0xB4: 0x301, 0xB8: 0x327, 0x2C6: 0x302, 0x2C7: 0x30C,
           0x2D8: 0x306, 0x2D9: 0x307, 0x2DA: 0x30A, 0x2DB: 0x328, 0x2DC: 0x303, 0x2DD: 0x30B}
CENTRE_X = {"\u0131": 0.5, "\u0237": 0.65, "J": 0.6, "l": 0.5}  # where marks above centre


def points(shapes):
    for sh in shapes:
        sh = sh[1] if sh[0] == "cut" else sh
        if sh[0] == "seg":
            yield sh[1], sh[2]
            yield sh[3], sh[4]
        else:
            yield from sh[1]


def moved(shapes, f):
    """The shapes with every point (x, y) sent to f(x, y)."""
    out = []
    for sh in shapes:
        if sh[0] == "cut":
            out.append(("cut", moved([sh[1]], f)[0]))
        elif sh[0] == "seg":
            (x0, y0), (x1, y1) = f(sh[1], sh[2]), f(sh[3], sh[4])
            out.append(("seg", x0, y0, x1, y1, sh[5]))
        else:
            out.append(("poly", [f(x, y) for x, y in sh[1]]))
    return out


def shortened(shapes, capital):
    """Room for a mark above: a capital is scaled down onto the baseline
    from SHORT_TOP; a lowercase letter's ascender is squeezed into
    SHORT_TOP..x-height and the rest left alone."""
    top = min((y for _, y in points(shapes)), default=SHORT_TOP)
    if top >= SHORT_TOP:
        return shapes
    if capital:
        k = (BASELINE - SHORT_TOP) / (BASELINE - top)
        return moved(shapes, lambda x, y: (x, BASELINE - (BASELINE - y) * k))
    k = (XHEIGHT - SHORT_TOP) / (XHEIGHT - top)
    return moved(shapes, lambda x, y: (x, XHEIGHT - (XHEIGHT - y) * k if y < XHEIGHT else y))


def bottom_x(shapes, right=False):
    """Where a mark below hangs: the middle of the lowest points, or the
    rightmost of them."""
    pts = list(points(shapes))
    low = max(y for _, y in pts)
    xs = [x for x, y in pts if y > low - 0.005]
    return max(xs) if right else (min(xs) + max(xs)) / 2


def accents():
    """{char: shapes} for the accent tier."""
    base = strokes.parse(strokes.STROKES)
    letters = strokes.parse(LETTERS)
    base.update(letters)
    marks = {ord(c): m for c, m in strokes.parse(MARKS).items()}
    out = dict(letters)
    del out["\u0237"]  # dotless j is a base, not in the set: it is Latin Extended-B
    wanted = [c for c in range(0xC0, 0x180) if c != 0xD7] + sorted(SPACING)
    for c in wanted:
        ch = chr(c)
        if ch in out:
            continue
        nfd = unicodedata.normalize("NFD", ch)
        if c in SPACING:
            letter, mark = None, SPACING[c]
        elif len(nfd) == 2 and nfd[0] in base and ord(nfd[1]) in marks:
            letter, mark = nfd[0], ord(nfd[1])
        else:
            raise ValueError(f"U+{c:04X} {unicodedata.name(ch)}: no rule; draw it in letters.txt")
        capital = letter is not None and letter.isupper()
        if letter in CARON_BESIDE and mark == 0x30C:
            mark, at = 0x315, CARON_BESIDE[letter]
        elif letter in COMMA_BELOW and mark == 0x327:
            mark = 0x326
        elif letter in TURNED_COMMA and mark == 0x327:
            mark = 0x312
        if letter in DOTLESS and mark in ABOVE:
            letter = DOTLESS[letter]
        shapes = [] if letter is None else base[letter]
        if mark in ABOVE:
            shapes = shortened(shapes, capital)
            if letter is None:
                at = 0.5
            elif letter in CENTRE_X:
                at = CENTRE_X[letter]
            else:
                xs = [x for x, _ in points(shapes)]
                at = (min(xs) + max(xs)) / 2
            dy = -RAISE if capital else 0.0
        elif mark in BELOW:
            at = 0.5 if letter is None else bottom_x(shapes, right=mark == 0x328)
            dy = 0.0
        else:
            dy = 0.0  # beside the stem, at the x chosen above
        dx = at - 0.5
        out[ch] = shapes + moved(marks[mark], lambda x, y: (x + dx, y + dy))
    return out


SETS = {
    "ascii": ["ascii"],
    "draw": ["box", "block", "braille"],
    "symbol": ["symbol"],
    "accent": ["accent"],
    "full": ["ascii", "box", "block", "braille", "symbol"],
}


def tier(name):
    """[(char, shapes)] for one tier, in code point order."""
    if name == "ascii":
        g = strokes.parse(strokes.STROKES)
        if sorted(g) != [chr(c) for c in range(32, 127)]:
            raise ValueError("strokes.txt must hold exactly U+0020..U+007E")
        return [(c, g[c]) for c in sorted(g)]
    if name == "box":
        return [(chr(c), box(chr(c))) for c in range(0x2500, 0x2580)]
    if name == "block":
        return [(chr(c), shade(chr(c)) if c in SHADES else block(chr(c))) for c in range(0x2580, 0x25A0)]
    if name == "braille":
        return [(chr(c), braille(c - 0x2800)) for c in range(0x2800, 0x2900)]
    if name == "symbol":
        sym = strokes.parse(strokes.SYMBOLS)
        made = asterisks()
        if set(sym) & set(made):
            raise ValueError("symbols.txt draws an asterisk glyphs.py makes")
        sym.update(made)
        return [(c, sym[c]) for c in sorted(sym)]
    if name == "accent":
        acc = accents()
        return [(c, acc[c]) for c in sorted(acc)]
    raise ValueError(f"no tier {name!r}")


def charset(name):
    """[(char, tier, shapes)] for the set, in a fixed order."""
    if name not in SETS:
        raise ValueError(f"no set {name!r}; sets are {', '.join(SETS)}")
    out = [(c, t, g) for t in SETS[name] for c, g in tier(t)]
    seen = [c for c, _, _ in out]
    if len(set(seen)) != len(seen):
        raise ValueError("a character is in two tiers")
    return out


def _seg_sd(s, P, pen):
    x0, y0, x1, y1, r = s[1:]
    a = np.array([x0, y0])
    ab = np.array([x1 - x0, y1 - y0])
    t = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    return (pen if r is None else r) - np.hypot(*(P - a - t[:, None] * ab).T)


def _poly_sd(pts, P):
    A = np.asarray(pts, np.float64)
    B = np.roll(A, -1, 0)
    e = B - A
    w = P[:, None, :] - A[None]
    t = np.clip((w * e).sum(-1) / np.maximum((e * e).sum(-1), 1e-12), 0, 1)
    d = np.hypot(*(w - t[..., None] * e).transpose(2, 0, 1)).min(1)
    px, py = P[:, :1], P[:, 1:]
    ay, by = A[None, :, 1], B[None, :, 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        xcross = A[None, :, 0] + (py - ay) * (B[None, :, 0] - A[None, :, 0]) / (by - ay)
    inside = (((ay > py) != (by > py)) & (px < xcross)).sum(1) % 2 == 1
    return np.where(inside, d, -d)


def _shape_sd(s, P, pen):
    return _seg_sd(s, P, pen) if s[0] == "seg" else _poly_sd(s[1], P)


def signed_distance(shapes, P, pen):
    """Signed distance to the ink edge at points P (M, 2), positive inside."""
    out = np.full(len(P), FAR)
    for s in shapes:
        if s[0] == "cut":
            out = np.minimum(out, -_shape_sd(s[1], P, pen))
        else:
            out = np.maximum(out, _shape_sd(s, P, pen))
    return out


def nodes(n):
    ys, xs = np.mgrid[0:2 * n + 1, 0:n + 1] / n
    return np.stack([xs.ravel(), ys.ravel()], 1)


def field(shapes, n, pen, tau):
    """The clamped field at the nodes, shape (2n + 1, n + 1)."""
    sd = signed_distance(shapes, nodes(n), pen)
    return np.clip(sd / tau, -1, 1).reshape(2 * n + 1, n + 1)


def sources(name):
    """The files the set is made from, for the weights' record."""
    tiers = SETS[name]
    files = ["font/strokes.txt"] if "ascii" in tiers or "accent" in tiers else []
    if "symbol" in tiers:
        files.append("font/symbols.txt")
    if "accent" in tiers:
        files += ["font/letters.txt", "font/marks.txt"]
    return files + ["train/strokes.py", "train/glyphs.py"]


if __name__ == "__main__":
    full = charset("full")
    junctions = {}
    for ch, t, shapes in full:
        if t == "box":
            words = unicodedata.name(ch).split()[2:]
            if not ({"DASH", "ARC", "DIAGONAL"} & set(words)):
                key = tuple(sorted(arms_of(words).items()))
                if key in junctions:
                    raise SystemExit(f"U+{ord(ch):04X} and U+{ord(junctions[key]):04X} have the same arms")
                junctions[key] = ch
    counts = {}
    for _, t, _ in full:
        counts[t] = counts.get(t, 0) + 1
    print(len(full), "characters:", ", ".join(f"{k} {v}" for k, v in counts.items()),
          f"({len(junctions)} distinct box junctions)")
    for name in SETS:
        print(f"  {name}: {len(charset(name))}")
