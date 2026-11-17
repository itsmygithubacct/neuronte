"""The symbols of neuronte-kilix-chrome-v1, from font/kilix-chrome.txt.

That file lists the symbols Kilix prints on its bars, set by set, in
training order. A line with strokes is a drawing. A line without is made
here:

    battery  one upright outline with a cap, filled from the bottom to a
             level, or holding an exclamation or a question mark
    weather  a sun, a cloud in front of it (with clear space cut around the
             cloud so the two stay apart in one colour), and rain, snow or
             a lightning bolt under the cloud

Shapes are glyphs.py's, in cell units; the tables here are in grid units,
10 to a cell width, as the font files are. No font was read.

    sets()      {set: [code points]}, the file's sets and, for each group
                net of a set, the set NAMErI of that group's characters
    primary()   {set: (group nets, [code points])}, the file's own sets
    made()      {char: shapes} for every character in the file
    notes()     {code point: what the symbol means in Kilix}
"""
import math
import os

import strokes
from term_rest import _disc, _ell, _poly, _seg, groups

FILE = os.path.join(strokes.ROOT, "font", "kilix-chrome.txt")
PREFIX = "tchr"


def read(path=FILE):
    """({set: (nets, [code points])}, {code point: shapes or None}, {code point: note})."""
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
                    if part:
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


# The battery: an upright body x 2..8, y 5.8..15.2, a cap on top.

BODY = (2.0, 5.8, 8.0, 15.2)
WALL = 0.5                        # the pen of the outline
LEVELS = {0xF007A: 1, 0xF007B: 2, 0xF007C: 3, 0xF007D: 4, 0xF007E: 5, 0xF007F: 6, 0xF0080: 7, 0xF0081: 8,
          0xF0082: 9, 0xF0079: 10}
MARKS = {0xF0083: "!", 0xF0091: "?"}


def battery(level=0, mark=None):
    """The outline, filled from the bottom to level tenths of its inside, or with a mark in it."""
    x0, y0, x1, y1 = BODY
    out = _seg([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], WALL)
    out += _poly([(3.7, y0 - 1.6), (6.3, y0 - 1.6), (6.3, y0), (3.7, y0)])
    if level:                         # tenths of the inside, between the walls
        top = (y1 - WALL) - (y1 - y0 - 2 * WALL) * level / 10
        out += _poly([(x0, top), (x1, top), (x1, y1), (x0, y1)])
    if mark == "!":
        out += _seg([(5, 7.9), (5, 11.3)], 0.55) + _disc(5, 13.2, 0.7)
    elif mark == "?":
        out += _seg([(3.7, 8.9), (4.1, 7.9), (5, 7.5), (5.9, 7.9), (6.3, 8.9), (5.9, 9.8), (5, 10.5), (5, 11.4)], 0.45)
        out += _disc(5, 13.2, 0.7)
    return out


# Weather.

def _cloud(cx, cy, s, grow=0.0):
    """A cloud about (cx, cy): three lobes on a flat base; grow widens it all round."""
    g = grow
    return (_disc(cx - 1.9 * s, cy + 0.5 * s, 1.5 * s + g, 1.3 * s + g) + _disc(cx - 0.2 * s, cy - 0.5 * s, 2.0 * s + g, 1.9 * s + g) +
            _disc(cx + 1.9 * s, cy + 0.4 * s, 1.6 * s + g, 1.4 * s + g) +
            _poly([(cx - 1.9 * s - g, cy + 0.5 * s), (cx + 1.9 * s + g, cy + 0.5 * s),
                   (cx + 1.9 * s + g, cy + 1.8 * s + g), (cx - 1.9 * s - g, cy + 1.8 * s + g)]))


def _sun(cx, cy, r, angles, reach=1.7):
    out = _disc(cx, cy, r)
    for a in angles:
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        out += _seg([(cx + (r + 0.75) * c, cy + (r + 0.75) * s), (cx + (r + reach) * c, cy + (r + reach) * s)], 0.4)
    return out


def _behind(back, cloud_at):
    """back, then clear space cut around a cloud, then the cloud."""
    return back + [("cut", sh) for sh in _cloud(*cloud_at, grow=0.75)] + _cloud(*cloud_at)


def _rain(xs, y, length=2.2):
    out = []
    for x in xs:
        out += _seg([(x, y), (x - 0.75, y + length)], 0.45)
    return out


BOLT = [(5.9, 11.3), (3.6, 13.9), (4.9, 13.9), (4.0, 16.3), (6.7, 13.0), (5.4, 13.0)]


def weather(cp):
    big = (5.0, 8.4, 1.25)            # the cloud alone in the cell, with room under it
    if cp == 0x1F324:
        return _behind(_sun(4.3, 9.0, 2.1, range(0, 360, 45), 1.6), (6.5, 12.6, 0.72))
    if cp == 0x26C5:
        return _behind(_sun(4.1, 8.3, 1.9, (150, 195, 240, 285, 330), 1.5), (5.7, 12.0, 1.05))
    if cp == 0x1F326:
        return _behind(_sun(4.0, 6.9, 1.7, (150, 195, 240, 285, 330), 1.5), (5.7, 10.3, 1.05)) + _rain((3.8, 6.0, 8.2), 13.2, 2.0)
    if cp == 0x1F327:
        return _cloud(*big) + _rain((3.0, 5.4, 7.8), 11.9)
    if cp == 0x1F328:
        return (_cloud(*big) + _disc(2.6, 12.3, 0.62) + _disc(5.0, 12.3, 0.62) + _disc(7.4, 12.3, 0.62) +
                _disc(3.8, 14.4, 0.62) + _disc(6.2, 14.4, 0.62))
    if cp == 0x26C8:
        return _cloud(*big) + _poly(BOLT) + _rain((2.5,), 11.9, 2.0) + _rain((8.6,), 11.9, 2.0)
    raise ValueError(f"no weather symbol U+{cp:04X}")


def made():
    """{char: shapes} for every character of font/kilix-chrome.txt."""
    _, drawn, _ = read()
    out = {}
    for cp, shapes in drawn.items():
        if shapes is None:
            if cp in LEVELS:
                shapes = battery(level=LEVELS[cp])
            elif cp in MARKS:
                shapes = battery(mark=MARKS[cp])
            else:
                shapes = weather(cp)
        elif cp in LEVELS or cp in MARKS:
            raise ValueError(f"U+{cp:04X} has strokes and a rule")
        out[chr(cp)] = shapes
    return out
