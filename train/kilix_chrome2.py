"""The symbols of neuronte-kilix-chrome-v2, from font/kilix-chrome-2.txt.

Kilix prints most of the symbols on its bars across two cells: the cell of
the symbol and the blank cell after it. That file draws them for that box,
on a grid of 18 by 18 units (one unit is a pixel when the cell is 9 x 18).
A net's design cell is one unit wide and two high, and the engine asks it
for a box W x H as W x 2H and averages each pair of rows; so a box drawing
is put in the cell twice as tall as it is wide, and every stroke is turned
into its outline in the box first (a rectangle for each piece and a round
end at each point), which keeps a lying stroke as thick as a standing one.

A line with strokes is a drawing in box units, in the syntax of
font/strokes.txt, with one addition: a part that starts with "-" is cut
out of everything before it. A line without strokes is made here:

    battery  one upright outline with a cap, filled from the bottom to a
             level, or holding an exclamation or a question mark
    weather  a sun, a cloud in front of it (with clear space cut around the
             cloud so the two stay apart in one colour), and rain, snow or
             a lightning bolt under the cloud
    bell     the one-cell drawing of neuronte-kilix-chrome-v1, unchanged

No font was read.

    sets()      {set: [code points]}, the file's sets and, for each group
                net of a set, the set NAMErI of that group's characters
    primary()   {set: (group nets, [code points])}, the file's own sets
    made()      {char: shapes} for every character in the file, in cell units
    notes()     {code point: what the symbol means in Kilix}
    one_cell()  the code points drawn for one cell
"""
import math
import os

import kilix_chrome
import strokes
from term_rest import groups

FILE = os.path.join(strokes.ROOT, "font", "kilix-chrome-2.txt")
PREFIX = "tchw"
BOX = 18.0                         # units across and down the two-cell box
PEN = 1.0                          # half the width of an outline or a thin stroke: 2 units, 1/9 of the box
ROUND = 20                         # sides of a round end
ONE_CELL = (0x1F56D,)              # carried over from v1: the bell stands beside one-cell marks


def read(path=FILE):
    """({set: (nets, [code points])}, {code point: box shapes or None}, {code point: note}).

    Box shapes are strokes.py's, a tenth of the numbers written, with
    ("cut", shape) for a part that is cut out."""
    sets, drawn, notes, name = {}, {}, {}, None
    with open(path, encoding="utf-8") as fh:
        for num, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if line.startswith("# set "):
                tok = line.split()
                if len(tok) != 4 or not tok[2].startswith(PREFIX) or not tok[3].isdigit() or tok[2] in sets:
                    raise ValueError(f"{path}:{num}: a set line is '# set {PREFIX}NAME NETS', each name once")
                name = tok[2]
                sets[name] = (int(tok[3]), [])
            elif line.startswith("# note "):
                tok = line.split(None, 3)
                if len(tok) != 4 or not tok[2].startswith("U+"):
                    raise ValueError(f"{path}:{num}: a note line is '# note U+XXXX text'")
                notes[int(tok[2][2:], 16)] = tok[3]
            elif line.startswith("#") or not line.strip():
                continue
            elif not line.startswith("U+") or name is None:
                raise ValueError(f"{path}:{num}: a character line is U+XXXX and its strokes, after a set line")
            else:
                head, _, rest = line.partition(" ")
                cp = int(head[2:], 16)
                if cp in drawn:
                    raise ValueError(f"{path}:{num}: U+{cp:04X} is listed twice")
                shapes = []
                for part in (p.strip() for p in rest.split("|")):
                    if part.startswith("-"):
                        shapes += [("cut", s) for s in strokes._shapes(part[1:].strip(), chr(cp))]
                    elif part:
                        shapes += strokes._shapes(part, chr(cp))
                drawn[cp] = shapes or None
                sets[name][1].append(cp)
    for name, (nets, cps) in sets.items():
        if not 1 <= nets <= len(cps):
            raise ValueError(f"{path}: set {name} has {len(cps)} characters for {nets} nets")
    return sets, drawn, notes


def primary():
    return read()[0]


def sets():
    out = {}
    for name, (nets, cps) in primary().items():
        out[name] = cps
        for i, run in enumerate(groups(cps, nets)):
            out[f"{name}r{i}"] = run
    return out


def notes():
    return read()[2]


def one_cell():
    return ONE_CELL


# From the box to the cell.

def _put(x, y):
    """A box point (a tenth of the units written) in the net's cell, 1 wide and 2 high."""
    return (x * 10 / BOX, y * 20 / BOX)


def to_cell(shapes):
    """Box shapes as cell shapes: polygons only, each stroke as its outline in the box."""
    out, ends = [], set()
    for sh in shapes:
        if sh[0] == "cut":
            out += [("cut", s) for s in to_cell([sh[1]])]
        elif sh[0] == "poly":
            out.append(("poly", [_put(x, y) for x, y in sh[1]]))
        else:
            _, x0, y0, x1, y1, r = sh
            r = PEN / 10 if r is None else r
            length = math.hypot(x1 - x0, y1 - y0)
            if length:
                nx, ny = -(y1 - y0) / length * r, (x1 - x0) / length * r
                out.append(("poly", [_put(x0 + nx, y0 + ny), _put(x1 + nx, y1 + ny), _put(x1 - nx, y1 - ny), _put(x0 - nx, y0 - ny)]))
            for cx, cy in ((x0, y0), (x1, y1)):
                if (cx, cy, r) not in ends:          # one round end for a point two pieces share
                    ends.add((cx, cy, r))
                    out.append(("poly", [_put(cx + r * math.cos(2 * math.pi * i / ROUND), cy + r * math.sin(2 * math.pi * i / ROUND))
                                         for i in range(ROUND)]))
    return out


# Shapes made here, in box units.

def _rect(x0, y0, x1, y1):
    return [("poly", [(x0 / 10, y0 / 10), (x1 / 10, y0 / 10), (x1 / 10, y1 / 10), (x0 / 10, y1 / 10)])]


def _poly(pts):
    return [("poly", [(x / 10, y / 10) for x, y in pts])]


def _disc(cx, cy, r, n=40):
    return [("poly", [((cx + r * math.cos(2 * math.pi * i / n)) / 10, (cy + r * math.sin(2 * math.pi * i / n)) / 10) for i in range(n)])]


def _seg(pts, r=PEN):
    return [("seg", pts[i][0] / 10, pts[i][1] / 10, pts[i + 1][0] / 10, pts[i + 1][1] / 10, r / 10) for i in range(len(pts) - 1)]


def _cut(shapes):
    return [("cut", s) for s in shapes]


# The battery: an upright body 10 units wide and 13 high with walls of 2, a
# cap of 4 by 1 on top. The inside is 6 by 9; a level is 0.9 unit.
BODY = (4.0, 3.0, 14.0, 16.0)
WALL = 2.0
LEVELS = {0xF007A: 1, 0xF007B: 2, 0xF007C: 3, 0xF007D: 4, 0xF007E: 5, 0xF007F: 6, 0xF0080: 7, 0xF0081: 8,
          0xF0082: 9, 0xF0079: 10}
MARKS = {0xF0083: "!", 0xF0091: "?"}


def battery(level=0, mark=None):
    """The outline, filled from the bottom to level tenths of its inside, or with a mark in it."""
    x0, y0, x1, y1 = BODY
    out = _rect(x0, y0, x1, y1) + _cut(_rect(x0 + WALL, y0 + WALL, x1 - WALL, y1 - WALL)) + _rect(7, y0 - 1, 11, y0)
    if level:
        top = (y1 - WALL) - (y1 - y0 - 2 * WALL) * level / 10
        out += _rect(x0, top, x1, y1)
    if mark == "!":
        out += _rect(8, 6, 10, 10) + _rect(8, 11, 10, 13)
    elif mark == "?":
        hook = [(9 + 1.25 * math.cos(math.radians(t)), 8.0 + 1.25 * math.sin(math.radians(t))) for t in range(180, 421, 20)]
        out += _seg(hook + [(9, 9.75)], 0.75) + _rect(8, 11.5, 10, 13)
    return out


# Weather.

def _cloud(cx, cy, s=1.0, grow=0.0):
    """A cloud 14 s wide and 10 s high about (cx, cy - s / 2): three lobes on a flat base; grow widens it all round."""
    g = grow
    return (_disc(cx - 3.5 * s, cy + 1.0 * s, 3.5 * s + g) + _disc(cx + 0.5 * s, cy - 1.0 * s, 4.5 * s + g) +
            _disc(cx + 4.0 * s, cy + 1.5 * s, 3.0 * s + g) +
            _rect(cx - 3.5 * s - g, cy + 1.0 * s, cx + 4.0 * s + g, cy + 4.5 * s + g))


def _sun(cx, cy, r, angles, inner, outer, pen=PEN):
    """A disc and rays: each a stroke from inner to outer of the centre, round ended."""
    out = _disc(cx, cy, r)
    for a in angles:
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        out += _seg([(cx + inner * c, cy + inner * s), (cx + outer * c, cy + outer * s)], pen)
    return out


def _behind(back, cloud_at, clear=1.6):
    """back, then clear space cut around a cloud, then the cloud."""
    return back + _cut(_cloud(*cloud_at, grow=clear)) + _cloud(*cloud_at)


def _rain(xs, y, length=2.4, lean=1.3, pen=0.95):
    out = []
    for x in xs:
        out += _seg([(x, y), (x - lean, y + length)], pen)
    return out


HIGH = (9.0, 6.4, 0.8)             # the cloud with room under it for what falls: x 3.4..14.6, y 2..10
STORM = (9.0, 5.85, 0.7)           # a smaller one over the bolt: x 4.1..13.9, y 2..9


def weather(cp):
    if cp == 0x2600:
        return _sun(9, 9, 3.0, range(0, 360, 45), 5.5, 6.5)
    if cp == 0x2601:
        return _cloud(9, 9.5)
    if cp == 0x1F324:
        return _behind(_sun(8.1, 8.1, 2.8, range(0, 360, 45), 5.0, 5.7, 0.9), (12.5, 13.8, 0.55), 1.5)
    if cp == 0x26C5:
        return _behind(_sun(7.35, 8.0, 2.4, (135, 180, 225, 270, 315), 4.7, 4.7, 0.9), (10.65, 11.9, 0.8))
    if cp == 0x1F326:
        return (_behind(_sun(6.8, 6.3, 2.3, (135, 180, 225, 270, 315), 4.0, 4.0, 0.8), (10.9, 8.8, 0.7)) +
                _rain((8.7, 11.9, 15.1), 13.6, 2.0, 1.1, 0.9))
    if cp == 0x1F327:
        return _cloud(*HIGH) + _rain((6.3, 9.8, 13.3), 12.6)
    if cp == 0x1F328:
        return (_cloud(*HIGH) + _disc(5.5, 12.5, 1.1) + _disc(9.0, 12.5, 1.1) + _disc(12.5, 12.5, 1.1) +
                _disc(7.25, 15.2, 1.1) + _disc(10.75, 15.2, 1.1))
    if cp == 0x26C8:
        return (_cloud(*STORM) + _poly([(11.4, 10.4), (6.6, 13.8), (9.0, 13.8), (7.0, 16.5), (12.6, 12.4), (10.2, 12.4)]) +
                _rain((4.3,), 11.6, 2.3, 1.2) + _rain((15.1,), 11.6, 2.3, 1.2))
    raise ValueError(f"no weather symbol U+{cp:04X}")


WEATHER = (0x2600, 0x2601, 0x1F324, 0x26C5, 0x1F326, 0x1F327, 0x1F328, 0x26C8)


def box_shapes():
    """{code point: box shapes} for the two-cell symbols."""
    _, drawn, _ = read()
    out = {}
    for cp, shapes in drawn.items():
        if cp in ONE_CELL:
            if shapes is not None:
                raise ValueError(f"U+{cp:04X} is a one-cell symbol of v1 and has strokes here")
            continue
        if shapes is None:
            if cp in LEVELS:
                shapes = battery(level=LEVELS[cp])
            elif cp in MARKS:
                shapes = battery(mark=MARKS[cp])
            else:
                shapes = weather(cp)
        elif cp in LEVELS or cp in MARKS or cp in WEATHER:
            raise ValueError(f"U+{cp:04X} has strokes and a rule")
        out[cp] = shapes
    return out


def made():
    """{char: shapes}, in cell units, for every character of font/kilix-chrome-2.txt."""
    _, drawn, _ = read()
    boxed = box_shapes()
    first = kilix_chrome.made()
    return {chr(cp): first[chr(cp)] if cp in ONE_CELL else to_cell(boxed[cp]) for cp in drawn}
