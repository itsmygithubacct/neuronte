"""The fullwidth forms of Halfwidth and Fullwidth Forms, for neuronte-wide-forms-v1.

Each is the project's own one-cell drawing of the same character, at text
size, centred in the box of two cells: the cell's x 0..1 goes to box units
4.5..13.5 and its y 0..2 to 0..18, so a fullwidth letter is as tall as the
letter beside it in the terminal and its strokes as thick. The sources:

    U+FF01..U+FF5E   U+0021..U+007E, font/strokes.txt
    U+FFE0..U+FFE5   the cent, pound, not, macron, broken bar and yen signs
                     of split-v9 (the tsymbol tier; the macron from the accent tier)
    U+FFE6           the won sign of neuronte-term-symbol-v1 (the tsym tiers)
    U+FF5F, U+FF60   the white parentheses: the ASCII parenthesis drawn twice,
                     the second a little inside and shorter, joined at the ends
"""
import wide

K, OX, OY = 9.0, 4.5, 0.0
SOURCE = {0xFFE0: 0xA2, 0xFFE1: 0xA3, 0xFFE2: 0xAC, 0xFFE3: 0xAF, 0xFFE4: 0xA6, 0xFFE5: 0xA5, 0xFFE6: 0x20A9}
NOTES = {
    0xFF5F: "white parenthesis: drawn as two nested parentheses joined at the ends; the shape is from the name",
    0xFF60: "white parenthesis: drawn as two nested parentheses joined at the ends; the shape is from the name",
}

_DRAWN = None


def cps():
    return list(range(0xFF01, 0xFF61)) + list(range(0xFFE0, 0xFFE7))


def set_runs():
    """One training set of all 103, cut into 11 group nets."""
    return [cps()]


def _one_cell():
    import glyphs
    want = set(SOURCE.values())
    found = {}
    for name in ("tsymbol", "accent", "tsym12", "tsym10", "tsym8"):
        for ch, sh in glyphs.tier(name):
            if ord(ch) in want and ord(ch) not in found:
                found[ord(ch)] = sh
    missing = want - set(found)
    if missing:
        raise ValueError("no one-cell drawing of " + " ".join(f"U+{c:04X}" for c in sorted(missing)))
    return found


def _white(open_left):
    import glyphs
    g = wide.ascii_shapes()["(" if open_left else ")"]
    # the inner stroke: the same parenthesis 0.22 cell widths further in, 0.8 as tall about its middle
    inner = glyphs.moved(g, lambda x, y: (x + (0.22 if open_left else -0.22), 0.95 + (y - 0.95) * 0.8))
    pts =[(s[1], s[2]) for s in g] + [(g[-1][3], g[-1][4])]
    ipts = [(s[1], s[2]) for s in inner] + [(inner[-1][3], inner[-1][4])]
    top = sorted(pts, key=lambda p: p[1])[0], sorted(ipts, key=lambda p: p[1])[0]
    bot = sorted(pts, key=lambda p: -p[1])[0], sorted(ipts, key=lambda p: -p[1])[0]
    ends = [("seg", top[0][0], top[0][1], top[1][0], top[1][1], None), ("seg", bot[0][0], bot[0][1], bot[1][0], bot[1][1], None)]
    return g + inner + ends


def drawn():
    global _DRAWN
    if _DRAWN is None:
        g = wide.ascii_shapes()
        out = {}
        for cp in range(0xFF01, 0xFF5F):
            out[cp] = wide.from_cell(g[chr(cp - 0xFF01 + 0x21)], K, OX, OY)
        out[0xFF5F] = wide.from_cell(_white(True), K, OX, OY)
        out[0xFF60] = wide.from_cell(_white(False), K, OX, OY)
        one = _one_cell()
        for cp, src in SOURCE.items():
            out[cp] = wide.from_cell(one[src], K, OX, OY)
        _DRAWN = out
    return _DRAWN
