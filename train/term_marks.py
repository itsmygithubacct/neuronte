"""The characters of neuronte-term-marks-v1, from font/term-marks.txt.

That file lists every character, set by set, in training order. A line
with strokes is a drawing. A line without is made here:

    marks       the mark of font/marks.txt, which the accented letters use,
                drawn alone where it falls on a lowercase letter; the grave
                and acute tone marks and the koronis are the grave, the
                acute and the psili (Unicode gives them as equivalents)
    letters     U+0363 to U+036F, the medieval letters written over a
                letter: strokes.txt's lowercase letter made small, its
                x-height band put in the band of the marks above
    modifiers   U+1DB4 to U+1DB7: term-letters' esh, t with palatal hook,
                barred u and upsilon, raised as its other modifier letters;
                the two that run from ascender to descender are made small
                to the same band, y 0.18..0.93
    Lao         U+0EBC: term-rest's lo made small and put under the line
    blanks      the spaces, the grapheme joiner and the annotation characters
    hyphen      the soft hyphen, drawn as the hyphen
    signs       neuronte-wide-symbols-v1's drawing, its square box put in the
                cell's width on the maths line

Shapes are glyphs.py's, in cell units. No font was read.

    read()      ({set: (nets, [code points])}, {code point: shapes or None}, {code point: note})
    sets()      {set: [code points]}, the file's sets and, for each group
                net of a set, the set NAMErI of that group's characters
    primary()   {set: (group nets, [code points])}
    made()      {char: shapes} for every character in the file
    notes()     {code point: what is not sure about its drawing}
    blanks()    the code points drawn with no ink
"""
import os

import strokes
import term_rest
from term_rest import groups

FILE = os.path.join(strokes.ROOT, "font", "term-marks.txt")
PREFIX = "tmk"

ALIAS = {0x340: 0x300, 0x341: 0x301, 0x343: 0x313}
LETTERS_ABOVE = dict(zip(range(0x363, 0x370), "aeioucdhmrtvx"))
LETTER_K = 0.343            # x-height band 0.8..1.5 to the marks' band 0.32..0.56
LETTER_TOP = 0.32
LETTER_PEN = 0.045
MODIFIERS = {0x1DB4: 0x283, 0x1DB5: 0x1AB, 0x1DB6: 0x289, 0x1DB7: 0x28A}
MODIFIER_TALL, MODIFIER_SPAN, MODIFIER_TOP, MODIFIER_PEN = 1.0, 0.75, 0.18, 0.055
LAO_LO, LAO_BELOW_K, LAO_BELOW_TOP, LAO_PEN = 0xEA5, 0.36, 1.56, 0.045
BLANKS = frozenset([0x34F, *range(0x2000, 0x200B), 0x202F, 0x205F, 0xFFF9, 0xFFFA, 0xFFFB])
SOFT_HYPHEN = 0xAD
SIGNS = frozenset([0x25FD, 0x25FE, 0x2614, 0x2615, *range(0x2648, 0x2654), 0x267F, 0x2693, 0x26A1])
SIGN_K = 0.92 / 18          # the 18-unit box to 0.92 of the cell's width
SIGN_MIN_PEN = 0.05
SIGN_CY = 0.975             # glyphs.CENTRE, the maths line, where the asterisks sit


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


def blanks():
    return BLANKS


def _sign(shapes):
    """A wide sign's box shapes (18 x 18 units, x right, y down) in one cell, its centre at SIGN_CY."""
    cy = SIGN_CY
    f = lambda x, y: (0.5 + (x - 9.0) * SIGN_K, cy + (y - 9.0) * SIGN_K)  # noqa: E731
    out = []
    for sh in shapes:
        if sh[0] == "seg":
            (x0, y0), (x1, y1) = f(sh[1], sh[2]), f(sh[3], sh[4])
            r = None if sh[5] is None else max(sh[5] * SIGN_K, SIGN_MIN_PEN)
            out.append(("seg", x0, y0, x1, y1, r))
        elif sh[0] == "poly":
            out.append(("poly", [f(x, y) for x, y in sh[1]]))
        elif sh[0] == "cut":
            out.append(("cut", _sign([sh[1]])[0]))
        else:
            raise ValueError(f"a wide sign has a shape of kind {sh[0]}")
    return out


def made():
    """{char: shapes} for every character of font/term-marks.txt."""
    import glyphs   # here, not at the top: glyphs.py imports this module to register its sets
    _, drawn, _ = read()
    marks = strokes.parse(os.path.join(strokes.ROOT, "font", "marks.txt"))
    small = strokes.parse(strokes.STROKES)
    letters = None
    out = {}
    for cp, shapes in drawn.items():
        rule = None
        if cp in BLANKS:
            rule = []
        elif cp == SOFT_HYPHEN:
            rule = small["-"]
        elif cp in LETTERS_ABOVE:
            src = small[LETTERS_ABOVE[cp]]
            rule = glyphs._with_pen(glyphs.moved(src, lambda x, y: (0.5 + (x - 0.5) * LETTER_K,
                                                                     LETTER_TOP + (y - 0.8) * LETTER_K)), LETTER_PEN)
        elif cp in MODIFIERS:
            import term_letters
            if letters is None:
                letters = {c: s for c, _, s in glyphs.charset("termletters")}
            src = letters[chr(MODIFIERS[cp])]
            ys = [y for _, y in glyphs.points(src)]
            if max(ys) - min(ys) > MODIFIER_TALL:
                # a letter from ascender to descender: made small to the band of the raised x-height letters
                k = MODIFIER_SPAN / (max(ys) - min(ys))
                top = min(ys)
                rule = glyphs._with_pen(glyphs.moved(src, lambda x, y: (0.5 + (x - 0.5) * k,
                                                                         MODIFIER_TOP + (y - top) * k)), MODIFIER_PEN)
            else:
                rule = term_letters._apply(src, "super", None)
        elif cp == 0xEBC:
            lo = term_rest.made()[chr(LAO_LO)]
            rule = glyphs._with_pen(glyphs.moved(lo, lambda x, y: (0.5 + (x - 0.5) * LAO_BELOW_K,
                                                                    LAO_BELOW_TOP + (y - 0.73) * LAO_BELOW_K)), LAO_PEN)
        elif cp in SIGNS:
            import wide_symbols
            rule = _sign(wide_symbols.DRAWN[cp])
        elif chr(ALIAS.get(cp, cp)) in marks:
            rule = marks[chr(ALIAS.get(cp, cp))]
        if shapes is None:
            if rule is None:
                raise ValueError(f"U+{cp:04X} has no strokes in font/term-marks.txt and no rule here")
            shapes = rule
        elif rule is not None and cp not in (0x315, 0x31B):
            raise ValueError(f"U+{cp:04X} is drawn in font/term-marks.txt and made here")
        out[chr(cp)] = shapes
    return out
