"""The characters of neuronte-term-rest-v1, from font/term-rest.txt.

That file lists every character, set by set, in training order. A line
with strokes is a drawing. A line without is made here:

    Hebrew   a letter and a point (dagesh, mapiq, rafe, shin and sin dot,
             holam, hiriq, patah, qamats), or a letter widened to the cell
    faces    a round outline, eyes and a mouth, chosen from the Unicode
             name in FACES; cat faces are the same parts in a head with
             ears; the mouse, cow and monkey have a head of their own
    moons    a ring with the dark part of the phase filled

Shapes are glyphs.py's, in cell units; the tables here are in grid units,
10 to a cell width, as the font files are. No font was read.

    sets()      {set: [code points]}, the file's sets and, for each group
                net of a set, the set NAMErI of that group's characters
    primary()   {set: (group nets, [code points])}, the file's own sets
    made()      {char: shapes} for every character in the file
    notes()     {code point: what is not sure about its drawing}
"""
import math
import os

import strokes

FILE = os.path.join(strokes.ROOT, "font", "term-rest.txt")
PREFIX = "trst"


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


def groups(cps, nets):
    """The runs split_expert.py's contiguous partition cuts."""
    n = len(cps)
    return [cps[n * i // nets:n * (i + 1) // nets] for i in range(nets)]


def sets():
    out = {}
    for name, (nets, cps) in primary().items():
        out[name] = cps
        for i, run in enumerate(groups(cps, nets)):
            out[f"{name}r{i}"] = run
    return out


def notes():
    return read()[2]


# Shapes from grid units.

def _seg(pts, r=None):
    rr = None if r is None else r / 10
    return [("seg", pts[i][0] / 10, pts[i][1] / 10, pts[i + 1][0] / 10, pts[i + 1][1] / 10, rr)
            for i in range(len(pts) - 1)]


def _poly(pts):
    return [("poly", [(x / 10, y / 10) for x, y in pts])]


def _ell(cx, cy, rx, ry, a0=0.0, a1=360.0):
    n = max(4, int(abs(a1 - a0) / 12) + 1)
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _disc(cx, cy, rx, ry=None):
    return _poly(_ell(cx, cy, rx, rx if ry is None else ry)[:-1])


def _map(shapes, f):
    """The shapes with every point (x, y), in cell units, sent to f(x, y)."""
    out = []
    for sh in shapes:
        if sh[0] == "cut":
            out.append(("cut", _map([sh[1]], f)[0]))
        elif sh[0] == "seg":
            (x0, y0), (x1, y1) = f(sh[1], sh[2]), f(sh[3], sh[4])
            out.append(("seg", x0, y0, x1, y1, sh[5]))
        else:
            out.append(("poly", [f(x, y) for x, y in sh[1]]))
    return out


# Hebrew. A point is a filled dot; a bar is a pen stroke.

POINT = 0.72                      # radius of a dagesh, mapiq or shin dot
THIN = 0.55                       # the pen of a rafe, patah or qamats
WIDE = 1.42                       # how far a wide letter is stretched about the cell's middle
WIDE_REACH = 0.385                # the farthest a wide letter's strokes go from the middle, in cell widths
# Where the dagesh or mapiq sits in each letter.
DAGESH = {0xFB30: (0x5D0, 4.75, 13.5), 0xFB31: (0x5D1, 4.4, 10.8), 0xFB32: (0x5D2, 3.4, 10.2),
          0xFB33: (0x5D3, 4.2, 11), 0xFB34: (0x5D4, 5.3, 11.4), 0xFB35: (0x5D5, 3.2, 10.8),
          0xFB36: (0x5D6, 2.8, 11), 0xFB38: (0x5D8, 5.1, 12), 0xFB39: (0x5D9, 2.6, 8.3),
          0xFB3A: (0x5DA, 4.4, 11), 0xFB3B: (0x5DB, 4.6, 10.8), 0xFB3C: (0x5DC, 4.3, 9.7),
          0xFB3E: (0x5DE, 5.3, 11.2), 0xFB40: (0x5E0, 3.8, 10.6), 0xFB41: (0x5E1, 5.1, 10.6),
          0xFB43: (0x5E3, 4.6, 13.2), 0xFB44: (0x5E4, 5.3, 12.7), 0xFB46: (0x5E6, 3.4, 12.4),
          0xFB47: (0x5E7, 5.2, 10.3), 0xFB48: (0x5E8, 4.4, 11), 0xFB49: (0x5E9, 6.55, 10.6),
          0xFB4A: (0x5EA, 5.6, 11)}
SHIN_DOT, SIN_DOT, SHIN_DAGESH = (8, 4.5), (2.2, 4.5), (6.55, 10.6)
RAFE = {0xFB4C: 0x5D1, 0xFB4D: 0x5DB, 0xFB4E: 0x5E4}
WIDENED = {0xFB21: 0x5D0, 0xFB22: 0x5D3, 0xFB23: 0x5D4, 0xFB24: 0x5DB, 0xFB25: 0x5DC, 0xFB26: 0x5DD,
           0xFB27: 0x5E8, 0xFB28: 0x5EA}


def _dot(x, y):
    return _disc(x, y, POINT)


def hebrew(cp, drawn):
    """Shapes for a Hebrew presentation form made from a drawn letter, or None."""
    if cp in DAGESH:
        base, x, y = DAGESH[cp]
        return drawn[base] + _dot(x, y)
    if cp in RAFE:
        return drawn[RAFE[cp]] + _seg([(3, 4.4), (7, 4.4)], THIN)
    if cp in WIDENED:
        letter = drawn[WIDENED[cp]]
        reach = max(abs(x - 0.5) for sh in letter for x in (sh[1], sh[3]))
        k = min(WIDE, WIDE_REACH / reach)  # as wide as the rule says, and no nearer the cell's edge than that
        return _map(letter, lambda x, y: (0.5 + (x - 0.5) * k, y))
    shin, alef, yod, vav = drawn[0x5E9], drawn[0x5D0], drawn[0x5D9], drawn[0x5D5]
    patah = _seg([(3.2, 17.3), (6.8, 17.3)], THIN)
    made = {
        0xFB2A: lambda: shin + _dot(*SHIN_DOT),
        0xFB2B: lambda: shin + _dot(*SIN_DOT),
        0xFB2C: lambda: shin + _dot(*SHIN_DOT) + _dot(*SHIN_DAGESH),
        0xFB2D: lambda: shin + _dot(*SIN_DOT) + _dot(*SHIN_DAGESH),
        0xFB2E: lambda: alef + patah,
        0xFB2F: lambda: alef + _seg([(3.2, 17), (6.8, 17)], THIN) + _seg([(5, 17), (5, 18.7)], THIN),
        0xFB4B: lambda: vav + _dot(4.9, 4.4),
        0xFB1D: lambda: yod + _dot(5, 12.6),
        0xFB1F: lambda: drawn[0x5F2] + patah,
    }
    return made[cp]() if cp in made else None


# Faces. Parts are placed about the middle of the head, x right and y down,
# in grid units; a head of another size scales them.

HEAD = (5.0, 9.75, 4.2)           # the middle of a round face and its radius
RIM, LINE, FINE = 0.6, 0.5, 0.4   # pens: the outline, a mouth or brow, small parts
EYE_X, EYE_Y, EYE_Y_BROW = 1.55, -1.15, -0.8

# code point: (eyes, mouth, brows or None, extras)
FACES = {
    0x1F600: ("dot", "grin", None, ()),
    0x1F601: ("smile", "grin", None, ()),
    0x1F602: ("smile", "open", None, ("tears",)),
    0x1F603: ("dot", "open", None, ()),
    0x1F604: ("smile", "open", None, ()),
    0x1F605: ("smile", "open", None, ("sweat",)),
    0x1F606: ("tight", "open", None, ()),
    0x1F607: ("smile", "smile", None, ("halo",)),
    0x1F608: ("dot", "smile", "angry", ("horns",)),
    0x1F609: ("wink", "smile", None, ()),
    0x1F60A: ("smile", "smile", None, ()),
    0x1F60B: ("smile", "yum", None, ()),
    0x1F60C: ("down", "slight", None, ()),
    0x1F60D: ("heart", "smile", None, ()),
    0x1F60E: ("glasses", "smile", None, ()),
    0x1F60F: ("side", "smirk", None, ()),
    0x1F610: ("dot", "flat", None, ()),
    0x1F611: ("flat", "flat", None, ()),
    0x1F612: ("lid", "frownsmall", None, ()),
    0x1F613: ("dot", "frownsmall", None, ("sweat",)),
    0x1F614: ("down", "frownsmall", "sad", ()),
    0x1F615: ("dot", "slant", None, ()),
    0x1F616: ("tight", "wavy", None, ()),
    0x1F617: ("dot", "kiss", None, ()),
    0x1F618: ("wink", "kiss", None, ("heart",)),
    0x1F619: ("smile", "kiss", None, ()),
    0x1F61A: ("down", "kiss", None, ()),
    0x1F61B: ("dot", "tongue", None, ()),
    0x1F61C: ("wink", "tongue", None, ()),
    0x1F61D: ("tight", "tongue", None, ()),
    0x1F61E: ("down", "frown", None, ()),
    0x1F61F: ("dot", "frown", "sad", ()),
    0x1F620: ("dot", "frown", "angry", ()),
    0x1F621: ("big", "pout", "angry", ()),
    0x1F622: ("dot", "frown", None, ("tear",)),
    0x1F623: ("tight", "frown", None, ()),
    0x1F625: ("dot", "frownsmall", "sad", ("sweatright",)),
    0x1F626: ("dot", "openfrown", None, ()),
    0x1F627: ("dot", "openfrown", "sad", ()),
    0x1F628: ("ring", "openfrown", "sad", ()),
    0x1F629: ("down", "openfrown", "sad", ()),
    0x1F62A: ("down", "flatsmall", None, ("drop",)),
    0x1F62B: ("tight", "openfrown", None, ()),
    0x1F62D: ("down", "round", None, ("streams",)),
    0x1F62E: ("dot", "o", None, ()),
    0x1F62F: ("dot", "osmall", "raised", ()),
    0x1F630: ("dot", "round", None, ("sweat",)),
    0x1F631: ("ring", "scream", None, ("hands",)),
    0x1F632: ("big", "round", "raised", ()),
    0x1F633: ("ring", "flatsmall", None, ()),
    0x1F634: ("down", "o", None, ("zzz",)),
    0x1F635: ("x", "o", None, ()),
    0x1F636: ("dot", "none", None, ()),
    0x1F637: ("dot", "mask", None, ()),
    0x1F643: ("dot", "slight", None, ("upsidedown",)),
}
CATS = {
    0x1F638: ("smile", "grin", None, ()),
    0x1F639: ("smile", "open", None, ("tears",)),
    0x1F63A: ("dot", "open", None, ()),
    0x1F63B: ("heart", "smile", None, ()),
    0x1F63C: ("dot", "smirk", None, ()),
    0x1F63D: ("down", "kiss", None, ()),
    0x1F63E: ("dot", "frown", "angry", ()),
    0x1F63F: ("dot", "frown", None, ("tear",)),
    0x1F640: ("tight", "openfrown", None, ()),
    0x1F431: ("dot", "cat", None, ()),
}
CAT_HEAD = (5.0, 10.9, 3.55)
MOONS = {0x1F311: ("all", 0), 0x1F312: ("left", -0.5), 0x1F313: ("left", 0), 0x1F314: ("left", 0.5),
         0x1F315: ("none", 0), 0x1F316: ("right", 0.5), 0x1F317: ("right", 0), 0x1F318: ("right", -0.5)}
MOON = (5.0, 9.75, 4.2)
HEART = [(0, 0.9), (-0.95, -0.1), (-0.95, -0.6), (-0.5, -0.9), (0, -0.5), (0.5, -0.9), (0.95, -0.6), (0.95, -0.1)]
DROP = [(0, -0.95), (0.55, 0.2), (0.4, 0.75), (0, 0.95), (-0.4, 0.75), (-0.55, 0.2)]


def _eye(kind, side, y):
    """One eye, side -1 the left as seen and 1 the right, about (side * EYE_X, y)."""
    x = side * EYE_X
    if kind == "dot":
        return _disc(x, y, 0.62)
    if kind == "big":
        return _disc(x, y, 0.85)
    if kind == "ring":
        return _seg(_ell(x, y, 0.8, 0.8), 0.38)
    if kind == "smile":
        return _seg(_ell(x, y + 0.35, 0.9, 0.9, 195, 345), LINE)
    if kind == "down":
        return _seg(_ell(x, y - 0.35, 0.9, 0.9, 15, 165), LINE)
    if kind == "tight":
        return _seg([(x - side * 0.75, y - 0.7), (x + side * 0.65, y), (x - side * 0.75, y + 0.7)], FINE)
    if kind == "flat":
        return _seg([(x - 0.85, y), (x + 0.85, y)], LINE)
    if kind == "x":
        return _seg([(x - 0.7, y - 0.7), (x + 0.7, y + 0.7)], FINE) + _seg([(x - 0.7, y + 0.7), (x + 0.7, y - 0.7)], FINE)
    if kind == "heart":
        return _poly([(x + 1.05 * px, y + 1.05 * py) for px, py in HEART])
    if kind == "lid":
        return _seg([(x - 0.85, y - 0.2), (x + 0.85, y - 0.2)], FINE) + _poly(_ell(x, y - 0.1, 0.62, 0.7, 0, 180))
    raise ValueError(f"no eye {kind!r}")


def _eyes(kind, y):
    if kind == "wink":
        return _eye("dot", -1, y) + _eye("smile", 1, y)
    if kind == "side":
        return (_disc(-EYE_X + 0.45, y, 0.62) + _disc(EYE_X + 0.45, y, 0.62) +
                _seg([(-EYE_X - 0.6, y - 1.1), (-EYE_X + 0.9, y - 1.1)], FINE) +
                _seg([(EYE_X - 0.6, y - 1.1), (EYE_X + 0.9, y - 1.1)], FINE))
    if kind == "glasses":
        return (_disc(-1.6, y, 1.25, 0.95) + _disc(1.6, y, 1.25, 0.95) + _seg([(-0.6, y - 0.3), (0.6, y - 0.3)], FINE) +
                _seg([(-2.7, y - 0.3), (-3.9, y - 0.5)], FINE) + _seg([(2.7, y - 0.3), (3.9, y - 0.5)], FINE))
    return _eye(kind, -1, y) + _eye(kind, 1, y)


def _brows(kind):
    if kind == "angry":
        a, b = -2.8, -2.1
    elif kind == "sad":
        a, b = -2.1, -2.8
    elif kind == "raised":
        a = b = -2.75
    else:
        raise ValueError(f"no brows {kind!r}")
    return _seg([(-2.4, a), (-0.8, b)], FINE) + _seg([(2.4, a), (0.8, b)], FINE)


def _mouth(kind):
    if kind == "none":
        return []
    if kind == "smile":
        return _seg(_ell(0, 0.6, 2.15, 1.75, 25, 155), LINE)
    if kind == "slight":
        return _seg(_ell(0, 1.1, 1.5, 0.9, 25, 155), LINE)
    if kind == "frown":
        return _seg(_ell(0, 3.1, 1.9, 1.5, 205, 335), LINE)
    if kind == "frownsmall":
        return _seg(_ell(0, 2.8, 1.3, 0.9, 205, 335), LINE)
    if kind == "pout":
        return _seg(_ell(0, 2.9, 1.1, 1.0, 205, 335), LINE)
    if kind == "flat":
        return _seg([(-1.6, 1.8), (1.6, 1.8)], LINE)
    if kind == "flatsmall":
        return _seg([(-0.9, 1.9), (0.9, 1.9)], LINE)
    if kind == "open":
        return _poly(_ell(0, 0.75, 2.2, 2.0, 0, 180))
    if kind == "grin":
        d = _ell(0, 0.75, 2.2, 2.0, 0, 180)
        return _seg(d + [d[0]], FINE) + _seg([(-1.75, 1.75), (1.75, 1.75)], 0.3)
    if kind == "openfrown":
        return _poly(_ell(0, 2.9, 1.9, 1.7, 180, 360))
    if kind == "o":
        return _seg(_ell(0, 1.9, 0.9, 1.0), FINE)
    if kind == "osmall":
        return _disc(0, 2.0, 0.6)
    if kind == "round":
        return _disc(0, 1.9, 1.15, 1.35)
    if kind == "scream":
        return _disc(0, 1.85, 1.0, 1.5)
    if kind == "kiss":
        return _seg([(-0.2, 1.2), (0.5, 1.55), (-0.2, 1.9), (0.5, 2.25), (-0.2, 2.6)], FINE)
    if kind == "tongue":
        return _seg([(-1.7, 1.2), (1.7, 1.2)], LINE) + _poly(_ell(0, 1.2, 0.9, 1.7, 0, 180))
    if kind == "yum":
        return _mouth("smile") + _poly(_ell(1.15, 1.9, 0.85, 1.25, 0, 180))  # the tongue hangs from the smile
    if kind == "wavy":
        return _seg([(-1.9, 2.0), (-0.95, 1.4), (0, 2.0), (0.95, 1.4), (1.9, 2.0)], LINE)
    if kind == "smirk":
        return _seg([(-1.3, 2.0), (0.5, 2.0), (1.8, 1.0)], LINE)
    if kind == "slant":
        return _seg([(-1.5, 2.3), (1.5, 1.5)], LINE)
    if kind == "mask":
        box = [(-2.2, 0.4), (2.2, 0.4), (2.2, 2.9), (-2.2, 2.9), (-2.2, 0.4)]
        return (_seg(box, FINE) + _seg([(-2.2, 1.65), (2.2, 1.65)], 0.3) +
                _seg([(-2.2, 0.5), (-3.8, -0.3)], FINE) + _seg([(2.2, 0.5), (3.8, -0.3)], FINE))
    if kind == "cat":
        return (_disc(0, 0.9, 0.45) + _seg(_ell(-0.75, 1.5, 0.75, 0.8, 0, 180), FINE) +
                _seg(_ell(0.75, 1.5, 0.75, 0.8, 0, 180), FINE))
    raise ValueError(f"no mouth {kind!r}")


def _inside(extra):
    """An extra part that lies in the face and scales with it."""
    if extra == "tears":
        return (_poly([(-2.75 + 0.8 * x, 0.2 + 0.8 * y) for x, y in DROP]) +
                _poly([(2.75 + 0.8 * x, 0.2 + 0.8 * y) for x, y in DROP]))
    if extra == "tear":
        return _poly([(-1.55 + 0.85 * x, 0.75 + 0.85 * y) for x, y in DROP])
    if extra == "drop":
        return _poly([(1.9 + 0.8 * x, 1.2 + 0.8 * y) for x, y in DROP])
    if extra == "streams":
        return _seg([(-1.9, -0.6), (-1.9, 3.0)], LINE) + _seg([(1.9, -0.6), (1.9, 3.0)], LINE)
    if extra == "heart":
        return _poly([(2.3 + 0.75 * x, 1.9 + 0.75 * y) for x, y in HEART])
    if extra == "hands":
        return _seg([(-2.15, 0.9), (-2.5, 2.6)], LINE) + _seg([(2.15, 0.9), (2.5, 2.6)], LINE)
    return None


def _outside(extra, cx, cy, r):
    """An extra part outside a head at (cx, cy) of radius r, in the cell's own grid units."""
    if extra == "sweat":
        return _poly([(cx - 3.4 + 1.4 * x, cy - r - 1.0 + 1.4 * y) for x, y in DROP])
    if extra == "sweatright":
        return _poly([(cx + 3.4 + 1.4 * x, cy - r - 1.0 + 1.4 * y) for x, y in DROP])
    if extra == "halo":
        return _seg(_ell(cx, cy - r - 1.95, 2.6, 0.8), FINE)
    if extra == "horns":
        return (_poly([(cx - 3.4, cy - 2.6), (cx - 3.7, cy - 5.5), (cx - 1.7, cy - 3.9)]) +
                _poly([(cx + 3.4, cy - 2.6), (cx + 3.7, cy - 5.5), (cx + 1.7, cy - 3.9)]))
    if extra == "zzz":
        return _seg([(cx + 1.1, cy - r - 3.6), (cx + 3.3, cy - r - 3.6), (cx + 1.1, cy - r - 1.5),
                     (cx + 3.3, cy - r - 1.5)], FINE)
    raise ValueError(f"no extra {extra!r}")


def _features(spec, cx, cy, s):
    """Eyes, brows, mouth and the extras inside the face, about (cx, cy) at scale s."""
    eyes, mouth, brows, extras = spec
    parts = _eyes(eyes, EYE_Y_BROW if brows else EYE_Y) + _mouth(mouth)
    if brows:
        parts += _brows(brows)
    for e in extras:
        parts += _inside(e) or []
    flip = -1 if "upsidedown" in extras else 1
    out = []
    for sh in parts:  # parts are in grid units over ten; put them in the cell
        if sh[0] == "seg":
            out.append(("seg", (cx + s * 10 * sh[1]) / 10, (cy + flip * s * 10 * sh[2]) / 10,
                        (cx + s * 10 * sh[3]) / 10, (cy + flip * s * 10 * sh[4]) / 10,
                        None if sh[5] is None else sh[5] * max(s, 0.85)))
        else:
            out.append(("poly", [((cx + s * 10 * x) / 10, (cy + flip * s * 10 * y) / 10) for x, y in sh[1]]))
    return out


def face(spec):
    cx, cy, r = HEAD
    out = _seg(_ell(cx, cy, r, r), RIM) + _features(spec, cx, cy, 1.0)
    for e in spec[3]:
        if e != "upsidedown" and _inside(e) is None:
            out += _outside(e, cx, cy, r)
    return out


def cat(spec):
    cx, cy, r = CAT_HEAD
    ears = (_seg([(cx - 3.25, cy - 1.6), (cx - 3.1, cy - 5.0), (cx - 0.7, cy - 3.3)], RIM) +
            _seg([(cx + 3.25, cy - 1.6), (cx + 3.1, cy - 5.0), (cx + 0.7, cy - 3.3)], RIM))
    return _seg(_ell(cx, cy, r, r), RIM) + ears + _features(spec, cx, cy, r / HEAD[2])


def mouse():
    cx, cy, r = 5.0, 11.3, 3.1
    s = r / HEAD[2]
    out = _seg(_ell(cx, cy, r, r), RIM)
    out += _seg(_ell(2.45, 7.2, 1.6, 1.6), RIM) + _seg(_ell(7.55, 7.2, 1.6, 1.6), RIM)
    out += _features(("dot", "none", None, ()), cx, cy, s)
    out += _disc(cx, cy + 0.9, 0.5)
    for side in (-1, 1):
        out += _seg([(cx + side * 0.9, cy + 1.2), (cx + side * 2.4, cy + 0.8)], 0.3)
        out += _seg([(cx + side * 0.9, cy + 1.5), (cx + side * 2.4, cy + 1.9)], 0.3)
    return out


def cow():
    cx, cy = 5.0, 10.8
    out = _seg(_ell(cx, cy, 3.0, 3.6), RIM)
    for side in (-1, 1):
        out += _seg([(cx + side * 2.2, 7.9), (cx + side * 3.3, 6.4), (cx + side * 2.7, 4.9)], RIM)
        out += _poly([(cx + side * 2.8, 8.9), (cx + side * 4.4, 8.2), (cx + side * 4.5, 9.4), (cx + side * 2.9, 10.1)])
        out += _disc(cx + side * 1.35, 9.6, 0.6)
        out += _disc(cx + side * 0.8, 12.8, 0.38)
    return out + _seg(_ell(cx, 12.8, 2.0, 1.3), 0.45)


def monkey():
    cx, cy, r = 5.0, 10.3, 3.0
    out = _seg(_ell(cx, cy, r, r), RIM)
    for side in (-1, 1):
        out += _seg(_ell(cx + side * 3.3, cy - 0.2, 0.95, 1.0), LINE)
        out += _disc(cx + side * 1.15, cy - 0.8, 0.55)
    return out + _seg(_ell(cx, cy + 1.45, 1.7, 1.15), 0.42) + _seg([(cx - 0.8, cy + 1.6), (cx + 0.8, cy + 1.6)], 0.3)


def moon(dark, bulge):
    """A ring, and the dark part filled: "all", "none", or the "left" or
    "right" of a terminator that is straight (bulge 0), bows toward the
    dark rim (positive: a dark crescent) or away from it (negative: all
    but a lit crescent)."""
    cx, cy, r = MOON
    out = _seg(_ell(cx, cy, r, r), RIM)
    if dark == "none":
        return out
    if dark == "all":
        return out + _disc(cx, cy, r)
    side = -1 if dark == "left" else 1
    rim = [(cx + side * r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 91, 6)]
    edge = [(cx + side * bulge * r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
            for a in range(90, -91, -6)]
    return out + _poly(rim + edge[1:-1])


def made():
    """{char: shapes} for every character of font/term-rest.txt."""
    _, drawn, _ = read()
    letters = {cp: sh for cp, sh in drawn.items() if sh is not None}
    out = {}
    for cp, shapes in drawn.items():
        if shapes is None:
            if cp in FACES:
                shapes = face(FACES[cp])
            elif cp in CATS:
                shapes = cat(CATS[cp])
            elif cp in MOONS:
                shapes = moon(*MOONS[cp])
            elif cp in (0x1F42D, 0x1F42E, 0x1F435):
                shapes = {0x1F42D: mouse, 0x1F42E: cow, 0x1F435: monkey}[cp]()
            else:
                shapes = hebrew(cp, letters)
            if shapes is None:
                raise ValueError(f"U+{cp:04X} has no strokes in font/term-rest.txt and no rule here")
        elif cp in FACES or cp in CATS or cp in MOONS or hebrew(cp, letters) is not None:
            raise ValueError(f"U+{cp:04X} is drawn in font/term-rest.txt and made here")
        out[chr(cp)] = shapes
    return out
