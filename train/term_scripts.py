"""The characters of the term-scripts bundles, from font/term-scripts.txt.

Three standalone bundles to open beside neuronte-split-v9:

    neuronte-term-mathalpha-v1   the styled alphabets (sets tscrm...)
    neuronte-term-syllabics-v1   Canadian syllabics (sets tscrs...)
    neuronte-term-scripts-v1     Armenian, Georgian, Tifinagh, Lisu, Ogham
                                 and Old Italic (sets tscra... and so on)

font/term-scripts.txt has three kinds of line:

    U+XXXX strokes           a drawing, in the syntax of train/strokes.py
    part NAME strokes        a named shape that the code here builds on
    tscrNAME U+XXXX ...      a training set and its characters, in the
                             order the group nets take them

A character that is listed in a set and has no drawing line is made
here by rule, from the project's own strokes:

    monospace letters and digits (U+1D670.., U+1D7F6..) are the ASCII
    strokes of font/strokes.txt as they are: that face is a monospace one;
    sans-serif letters and digits (U+1D5A0.., U+1D7E2..) are the same
    strokes, but for the few the file draws without their slab serifs.

    Canadian syllabics (U+1400..U+167F) are a series' shape, one of the
    seven "part syl-..." lines, turned one of four ways for the vowel,
    with a dot above for a long vowel, a dot at mid height before the
    shape for w (after it in the West Cree forms), and a raised small
    shape for a final: SYLLABIC below, from the Unicode names.

No font file was read to make any of them. glyphs.py lists each set as a
tier and a set of its own; no set made before holds any of these
characters.
"""
import os
import re
import unicodedata

import strokes

FILE = os.path.join(strokes.ROOT, "font", "term-scripts.txt")
PREFIX = "tscr"
_cache = {}


def read(path=FILE):
    """(drawn {char: shapes}, parts {name: shapes}, sets {name: [code points]})."""
    key = (path, os.path.getmtime(path))
    if key in _cache:
        return _cache[key]
    drawn, parts, sets = {}, {}, {}
    with open(path, encoding="utf-8") as fh:
        for num, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if line.startswith("#") or not line.strip():
                continue
            head, _, rest = line.partition(" ")
            where = f"{path}:{num}"
            if head.startswith("U+"):
                ch = chr(int(head[2:], 16))
                if ch in drawn:
                    raise ValueError(f"{where}: {head} is drawn twice")
                drawn[ch] = _shapes(rest, head)
            elif head == "part":
                name, _, rest = rest.partition(" ")
                if name in parts:
                    raise ValueError(f"{where}: part {name} is given twice")
                parts[name] = _shapes(rest, name)
            elif head.startswith(PREFIX):
                cps = rest.split()
                if not cps or any(not c.startswith("U+") for c in cps):
                    raise ValueError(f"{where}: a set line is a name and its U+XXXX")
                sets.setdefault(head, []).extend(int(c[2:], 16) for c in cps)
            else:
                raise ValueError(f"{where}: a line starts with U+XXXX, part or {PREFIX}...")
    for name, cps in sets.items():
        if len(set(cps)) != len(cps):
            raise ValueError(f"{path}: set {name} lists a character twice")
    _cache.clear()
    _cache[key] = (drawn, parts, sets)
    return _cache[key]


def _shapes(text, what):
    out = []
    for part in (p.strip() for p in text.split("|")):
        if part:
            out += strokes._shapes(part, what)
    return out


def sets(path=FILE):
    """{set: [code points]}, in the file's order."""
    return read(path)[2]


# Styled alphabets made from the ASCII strokes: (first code point, first ASCII letter, count).
PLAIN = ((0x1D5A0, "A", 26), (0x1D5BA, "a", 26), (0x1D7E2, "0", 10),      # sans-serif
         (0x1D670, "A", 26), (0x1D68A, "a", 26), (0x1D7F6, "0", 10))      # monospace


def _plain():
    base = strokes.parse(strokes.STROKES)
    return {chr(first + i): base[chr(ord(letter) + i)] for first, letter, n in PLAIN for i in range(n)}


# Canadian syllabics. A syllabic is a consonant's shape turned for its
# vowel. The vowels, p and t are shapes with one axis of symmetry, pointing
# down for e, up for i, right for o and left for a: the part is the e form
# and the others are quarter turns of it. k, c, m and n have a stem or bar
# and a feature at one end: the part is the a form (feature at the lower
# right), o is its mirror image, i is it upside down, e both.
SYL_NAME = re.compile(r"^CANADIAN SYLLABICS (WEST-CREE |Y-CREE )?(P|T|K|C|M|N)?(W)?(E|II|I|OO|O|AA|A)?$")
SYL_PART = {None: "syl-vowel", "P": "syl-p", "T": "syl-t", "K": "syl-k", "C": "syl-c", "M": "syl-m", "N": "syl-n"}
SYL_TURNED = (None, "P", "T")                     # the series whose part is the e form, turned by quarters
SYL_BOX = (2.0, 8.0, 6.6, 15.0)                   # a syllabic's strokes: x0, x1, y0, y1 on the 10 x 20 grid
SYL_SHIFT = 1.15                                  # how far a shape moves aside for a w dot
SYL_NARROW = 0.95                                 # and how much narrower it is beside one
SYL_W_X, SYL_W_Y = 1.0, 10.8                      # the w dot, before the shape; after it at 10 - SYL_W_X
SYL_LONG_Y = 4.3                                  # the dot above for a long vowel
SYL_YCREE_DX = 1.5                                # Y-Cree oo: two dots above, this far each side of the middle
SYL_FINAL = (2.7, 7.3, 4.4, 10.0)                 # a final: the a form, small and raised
SYL_FINAL_NARROW = (1.9, 6.5, 4.4, 10.0)          # a final with a dot after it (kw)
DOT = 0.3                                         # half the length of a dot's stroke, as the full stop of strokes.txt


def _dot(x, y):
    return ("seg", x / 10, (y - DOT) / 10, x / 10, (y + DOT) / 10, None)


def _in_box(shapes, box, turn):
    """A part, drawn on 0..10 x 0..10 (read as 0..1), turned and set in a box of the grid."""
    x0, x1, y0, y1 = box

    def at(x, y):
        u, v = turn(x, y)
        return (x0 + u * (x1 - x0)) / 10, (y0 + v * (y1 - y0)) / 10
    out = []
    for sh in shapes:
        if sh[0] != "seg":
            raise ValueError("a syllabic part is strokes only")
        out.append(("seg", *at(sh[1], sh[2]), *at(sh[3], sh[4]), sh[5]))
    return out


SYL_TURNS = {  # on the unit square, y down
    "turned": {"E": lambda u, v: (u, v), "I": lambda u, v: (u, 1 - v),
               "O": lambda u, v: (v, u), "A": lambda u, v: (1 - v, u)},
    "flipped": {"A": lambda u, v: (u, v), "O": lambda u, v: (1 - u, v),
                "I": lambda u, v: (u, 1 - v), "E": lambda u, v: (1 - u, 1 - v)},
}


def syllabic(ch, parts):
    """The shapes of one syllabic, or None if its name follows no rule here."""
    m = SYL_NAME.match(unicodedata.name(ch, ""))
    if not m or not (m.group(2) or m.group(3) or m.group(4)):
        return None
    dialect, cons, w, vowel = m.groups()
    part = parts[SYL_PART[cons]]
    family = "turned" if cons in SYL_TURNED else "flipped"
    if vowel is None:                              # a final: the consonant alone, or with w
        if cons is None or dialect:
            return None                            # West Cree finals have shapes of their own, drawn in the file
        if cons in SYL_TURNED:
            turn = SYL_TURNS["turned"]["A"]
        else:
            turn = SYL_TURNS["flipped"]["A"]
        if w:
            x0, x1, y0, y1 = SYL_FINAL_NARROW
            return _in_box(part, SYL_FINAL_NARROW, turn) + [_dot(x1 + 1.7, (y0 + y1) / 2)]
        return _in_box(part, SYL_FINAL, turn)
    if dialect == "Y-CREE " and (vowel != "OO" or w):
        return None
    x0, x1, y0, y1 = SYL_BOX
    out = []
    if w:
        after = dialect == "WEST-CREE "
        mid, half = (x0 + x1) / 2, (x1 - x0) / 2 * SYL_NARROW
        mid += -SYL_SHIFT if after else SYL_SHIFT
        x0, x1 = mid - half, mid + half
        out.append(_dot(10 - SYL_W_X if after else SYL_W_X, SYL_W_Y))
    elif dialect == "WEST-CREE ":
        return None
    turn = SYL_TURNS[family][vowel[0]]
    out = _in_box(part, (x0, x1, y0, y1), turn) + out
    mid = (x0 + x1) / 2
    if dialect == "Y-CREE ":
        out += [_dot(mid - SYL_YCREE_DX, SYL_LONG_Y), _dot(mid + SYL_YCREE_DX, SYL_LONG_Y)]
    elif len(vowel) == 2:
        out.append(_dot(mid, SYL_LONG_Y))
    return out


def made(path=FILE):
    """{char: shapes} for every character a set of the file lists."""
    drawn, parts, listed = read(path)
    wanted = {c for cps in listed.values() for c in cps}
    out = {}
    plain = _plain()
    for c in sorted(wanted):
        ch = chr(c)
        if ch in drawn:
            out[ch] = drawn[ch]
        elif ch in plain:
            out[ch] = plain[ch]
        elif 0x1400 <= c <= 0x167F and syllabic(ch, parts) is not None:
            out[ch] = syllabic(ch, parts)
        else:
            raise ValueError(f"U+{c:04X} is listed in {os.path.basename(path)} and has no drawing and no rule")
    extra = sorted(set(drawn) - set(out))
    if extra:
        raise ValueError("drawn and in no set: " + " ".join(f"U+{ord(c):04X}" for c in extra))
    return out


def tier(name, path=FILE):
    """[(char, shapes)] for one set, in the file's order."""
    shapes = made(path)
    return [(chr(c), shapes[chr(c)]) for c in sets(path)[name]]


def bundle_sets(letter, path=FILE):
    """The sets of one bundle: tscrm... the styled alphabets, tscrs... syllabics, and so on."""
    return [name for name in sets(path) if name.startswith(PREFIX + letter)]


# A bundle's characters as one set, to judge a character against every
# other of its bundle. A set named tscrx... is a failed group's characters
# again, to train as two halves: it repeats characters and joins no bundle.
BUNDLES = {"termmathalpha": "m", "termsyllabics": "s", "termscripts": "agtlo"}
AGAIN = PREFIX + "x"


def bundles(path=FILE):
    """{bundle set: [its training sets]} for the bundles that have any."""
    out = {}
    for name, letters in BUNDLES.items():
        mine = [s for s in sets(path) if s[len(PREFIX):len(PREFIX) + 1] in letters and not s.startswith(AGAIN)]
        if mine:
            out[name] = mine
    return out
