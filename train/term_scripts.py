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

No font file was read to make any of them. glyphs.py lists each set as a
tier and a set of its own; no set made before holds any of these
characters.
"""
import os

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
