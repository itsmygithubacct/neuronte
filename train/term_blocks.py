"""The drawings of neuronte-term-blocks-v1, made by rule from font/term-blocks.txt.

Four blocks, each a generator over a few parts:

  Yijing hexagrams U+4DC0..U+4DFF      six lines, whole or broken, one to
                                       each sixth of the cell
  Tai Xuan Jing U+1D300..U+1D356       one, two or four lines, each whole,
                                       broken once or broken twice
  Domino tiles U+1F030..U+1F093        a frame, a bar across the middle and
                                       two fields of pips; lying and standing
  Playing cards U+1F0A0..U+1F0DF       a frame, a rank above and a suit below

Every drawing fills one cell, 1 wide and 2 tall, as every Neuronte glyph
does. Unicode shows the dominoes and the cards as wide pictures; here a
standing tile is the cell, and a lying tile is the cell cut down the
middle: two tall fields side by side, each showing its face upright with
pips stretched to tall ovals (a face turned a quarter turn, three pips
across, does not fit half a cell). The parts of a drawing keep to their
own piece of the cell (a sixth, a quarter or a half of its height, or half
of its width), so a tiled net can draw each piece alone: see TILE_GRID.

No font is read. The hexagram table, the digrams and the suits are in
font/term-blocks.txt; the ranks of the cards are the letters and digits of
font/strokes.txt, made small.
MIT licence; see LICENSE.
"""
import math
import os

import strokes

FILE = os.path.join(strokes.ROOT, "font", "term-blocks.txt")

# Lines of the hexagrams and the Tai Xuan Jing figures.
LINE_X = (0.125, 0.875)                    # a whole line, across the cell
ONCE = ((0.125, 0.375), (0.625, 0.875))    # broken once: two pieces
TWICE = ((0.125, 0.275), (0.425, 0.575), (0.725, 0.875))  # broken twice: three
HEX_ROW, HEX_BAR = 1 / 3, 1 / 6            # a hexagram line: the upper half of its sixth
TET_ROW, TET_BAR = 0.5, 0.25               # a tetragram line: the middle half of its quarter

# Dominoes and cards.
FRAME = (0.1, 0.1, 0.9, 1.9)               # the centre line of the frame
FRAME_PEN = 0.05
PIP = 0.095                                # a pip's radius on a standing tile
PIP_X, PIP_Y = 0.22, 0.26                  # from a field's centre to its outer pips
FIELD_Y = (0.55, 1.45)                     # the centres of a standing tile's fields
LYING_X = (0.30, 0.70)                     # the centres of a lying tile's fields
LYING_STEP = (0.08, 0.52)                  # across and down, from a field's centre
LYING_PIP = (0.05, 0.22)                   # a lying tile's pip: half as wide, and tall
FACES = {0: (), 1: ((0, 0),), 2: ((-1, -1), (1, 1)), 3: ((-1, -1), (0, 0), (1, 1)),
         4: ((-1, -1), (1, -1), (-1, 1), (1, 1)), 5: ((-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)),
         6: ((-1, -1), (-1, 0), (-1, 1), (1, -1), (1, 0), (1, 1))}   # (column, row) of each pip
BACK_INNER = (0.26, 0.32, 0.74, 1.68)      # the second frame of a tile's back
CARD_BACK = (0.22, 0.24, 0.78, 1.76)       # the filled panel of a card's back
RANKS = "A23456789TJCQK"                   # T is 10; C is the knight
RANK_PEN = 0.055
RANK_TOP, RANK_K = 0.22, 0.6               # a rank: font/strokes.txt's capital, this much smaller
SUIT_AT, SUIT_K = (0.5, 1.46), 0.8         # a suit: its centre and its size
SUITS = ("spade", "heart", "diamond", "club")
OUTLINED = {"heart": 0.56, "diamond": 0.56}   # drawn in outline: the hollow, as a part of the shape
STAR = (0.5, 1.0, 0.36, 0.15)              # a joker's star: centre, outer and inner radius
STAR_HOLLOW = 0.5


def _rect(x0, y0, x1, y1):
    return ("poly", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def _outline(box, pen=FRAME_PEN):
    x0, y0, x1, y1 = box
    c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [("seg", *c[i], *c[(i + 1) % 4], pen) for i in range(4)]


def _oval(cx, cy, rx, ry, n=36):
    return ("poly", [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n))
                     for i in range(n)])


def _move(shapes, f):
    out = []
    for sh in shapes:
        if sh[0] == "cut":
            out.append(("cut", _move([sh[1]], f)[0]))
        elif sh[0] == "seg":
            out.append(("seg", *f(sh[1], sh[2]), *f(sh[3], sh[4]), sh[5]))
        else:
            out.append(("poly", [f(x, y) for x, y in sh[1]]))
    return out


def read(path=FILE):
    """(sets, trigrams, hexagrams, digrams, parts) from font/term-blocks.txt."""
    sets, trigrams, hexagrams, digrams, parts = {}, {}, [], {}, {}
    with open(path, encoding="utf-8") as fh:
        for num, raw in enumerate(fh, 1):
            tok = raw.split("#")[0].split()
            if not tok:
                continue
            where = f"{path}:{num}"
            if tok[0] == "set":
                cps = sets.setdefault(tok[1], [])
                for t in tok[2:]:
                    lo, _, hi = t.partition("..")
                    cps.extend(range(int(lo[2:], 16), int((hi or lo)[2:], 16) + 1))
            elif tok[0] == "trigram":
                trigrams[tok[1]] = tuple(int(c) for c in tok[2])
            elif tok[0] == "hexagrams":
                hexagrams += [tuple(t.split("/")) for t in tok[1:]]
            elif tok[0] == "digram":
                digrams[int(tok[1][2:], 16)] = (int(tok[2]), int(tok[3]))
            elif tok[0] == "part":
                shapes = []
                for piece in " ".join(tok[2:]).split("|"):
                    shapes += strokes._shapes(piece.strip(), tok[1])
                parts[tok[1]] = shapes
            else:
                raise ValueError(f"{where}: {tok[0]!r} is not set, trigram, hexagrams, digram or part")
    seen = [c for cps in sets.values() for c in cps]
    if len(set(seen)) != len(seen):
        raise ValueError(f"{path}: a character is in two sets")
    if any(not name.startswith("tblk") for name in sets):
        raise ValueError(f"{path}: a set is named tblk...")
    return sets, trigrams, hexagrams, digrams, parts


def sets():
    """{set: [code points]}, in the file's order."""
    return read()[0]


def _line(kind, y0, y1):
    """One line of a figure: 0 whole, 1 broken once, 2 broken twice."""
    spans = (LINE_X,) if kind == 0 else ONCE if kind == 1 else TWICE
    return [_rect(x0, y0, x1, y1) for x0, x1 in spans]


def hexagram_lines(n, trigrams, hexagrams):
    """The six lines of hexagram n (0 for U+4DC0), top first: 1 whole, 0 broken."""
    upper, lower = hexagrams[n]
    bottom_up = trigrams[lower] + trigrams[upper]
    return bottom_up[::-1]


def hexagram(lines):
    out = []
    for r, whole in enumerate(lines):
        out += _line(0 if whole else 1, r * HEX_ROW, r * HEX_ROW + HEX_BAR)
    return out


def tetragram_lines(n):
    """The four lines of tetragram n (0 for U+1D306), top first: n counted in
    threes, the top line the highest digit."""
    return tuple(n // 3 ** (3 - r) % 3 for r in range(4))


def tetragram(kinds):
    out = []
    for r, kind in enumerate(kinds):
        y = r * TET_ROW + (TET_ROW - TET_BAR) / 2
        out += _line(kind, y, y + TET_BAR)
    return out


def figure(kinds):
    """One or two lines (the monogram, a digram) about the middle of the cell,
    at the tetragram's size and spacing."""
    top = 1.0 - (len(kinds) * TET_ROW) / 2 + (TET_ROW - TET_BAR) / 2
    out = []
    for r, kind in enumerate(kinds):
        out += _line(kind, top + r * TET_ROW, top + r * TET_ROW + TET_BAR)
    return out


def domino(a, b, lying):
    """A tile with a pips in its first field and b in its second; a = None is
    the back. A standing tile's first field is the upper one, a lying tile's
    the left one."""
    out = _outline(FRAME)
    if a is None:
        return out + _outline(BACK_INNER)
    x0, y0, x1, y1 = FRAME
    if lying:
        out.append(("seg", 0.5, y0, 0.5, y1, FRAME_PEN))
    else:
        out.append(("seg", x0, 1.0, x1, 1.0, FRAME_PEN))
    for field, count in enumerate((a, b)):
        for col, row in FACES[count]:
            if lying:   # each tall field shows its face upright and stretched; a face turned would not fit
                out.append(_oval(LYING_X[field] + LYING_STEP[0] * col, 1.0 + LYING_STEP[1] * row, *LYING_PIP))
            else:
                out.append(_oval(0.5 + PIP_X * col, FIELD_Y[field] + PIP_Y * row, PIP, PIP))
    return out


def _centre(shapes):
    pts = []
    for sh in shapes:
        pts += sh[1] if sh[0] == "poly" else [(sh[1], sh[2]), (sh[3], sh[4])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def suit(name, parts):
    cx, cy = _centre(parts[name])
    put = lambda k: _move(parts[name], lambda x, y: (SUIT_AT[0] + (x - cx) * k, SUIT_AT[1] + (y - cy) * k))  # noqa: E731
    out = put(SUIT_K)
    if name in OUTLINED:
        out += [("cut", sh) for sh in put(SUIT_K * OUTLINED[name])]
    return out


def rank(ch, letters):
    def small(c, cx, kx):
        out = _move(letters[c], lambda x, y: (cx + (x - 0.5) * kx, RANK_TOP + (y - 0.4) * RANK_K))
        return [sh[:5] + (RANK_PEN,) if sh[0] == "seg" else sh for sh in out]
    if ch == "T":
        return small("1", 0.33, RANK_K * 0.6) + small("0", 0.66, RANK_K * 0.6)
    return small(ch, 0.5, RANK_K)


def _star(hollow):
    cx, cy, outer, inner = STAR
    def pts(k):  # noqa: E306
        return [(cx + k * (outer if i % 2 == 0 else inner) * math.cos(math.radians(-90 + 36 * i)),
                 cy + k * (outer if i % 2 == 0 else inner) * math.sin(math.radians(-90 + 36 * i))) for i in range(10)]
    return [("poly", pts(1.0))] + ([("cut", ("poly", pts(STAR_HOLLOW)))] if hollow else [])


def card(cp, parts, letters):
    """U+1F0A0 + 16 * suit + rank: rank 0 the back (spades' row only), 1..14
    ace to king with the knight at 12, 15 a joker (black in the diamonds'
    row, white in the clubs')."""
    row, r = divmod(cp - 0x1F0A0, 16)
    out = _outline(FRAME)
    if r == 0:
        return out + [_rect(*CARD_BACK)]
    if r == 15:
        return out + _star(hollow=row == 3)
    return out + rank(RANKS[r - 1], letters) + suit(SUITS[row], parts)


def drawings():
    """{char: shapes} for every character of font/term-blocks.txt."""
    sets_, trigrams, hexagrams, digrams, parts = read()
    letters = strokes.parse(strokes.STROKES)
    if len(hexagrams) != 64 or len(set(hexagram_lines(n, trigrams, hexagrams) for n in range(64))) != 64:
        raise ValueError("term-blocks.txt must list 64 different hexagrams")
    out = {}
    for name, cps in sets_.items():
        for cp in cps:
            if name == "tblkhex":
                g = hexagram(hexagram_lines(cp - 0x4DC0, trigrams, hexagrams))
            elif name == "tblktet":
                g = tetragram(tetragram_lines(cp - 0x1D306))
            elif name == "tblkdig":
                g = figure((2,) if cp == 0x1D300 else digrams[cp])
            elif name in ("tblkdomh", "tblkdomv"):
                n = cp - (0x1F030 if name == "tblkdomh" else 0x1F062)
                g = domino(None if n == 0 else (n - 1) // 7, None if n == 0 else (n - 1) % 7, name == "tblkdomh")
            elif name == "tblkcard":
                g = card(cp, parts, letters)
            else:
                raise ValueError(f"no rule for the set {name}")
            out[chr(cp)] = g
    return out


# How a tiled net cuts each set: (columns, rows) of equal tiles. Every part
# of a drawing lies inside one tile, or is cut by a tile edge along a
# straight line (the frame, the bar across a tile, a joker's star).
TILE_GRID = {"tblkhex": (1, 6), "tblktet": (1, 4), "tblkdomh": (2, 1), "tblkdomv": (1, 2), "tblkcard": (1, 2)}


def check():
    """The rules the generators rest on, checked against Unicode's names."""
    import unicodedata
    sets_, trigrams, hexagrams, digrams, _ = read()
    lines = [hexagram_lines(n, trigrams, hexagrams) for n in range(64)]
    # King Wen pairs: each hexagram and the next are one turned over, or, where that changes nothing, its opposite.
    for k in range(0, 64, 2):
        a, b = lines[k], lines[k + 1]
        if b != (a[::-1] if a[::-1] != a else tuple(1 - x for x in a)):
            raise SystemExit(f"hexagrams {k + 1} and {k + 2} are not a King Wen pair")
    names = {"heaven": "HEAVEN", "earth": "EARTH", "thunder": "THUNDER", "water": "WATER", "mountain": "MOUNTAIN",
             "wind": "WIND", "fire": "FIRE", "lake": "LAKE"}
    doubled = {0x4DC0: "heaven", 0x4DC1: "earth", 0x4DDC: "water", 0x4DDD: "fire", 0x4DF2: "thunder",
               0x4DF3: "mountain", 0x4DF8: "wind", 0x4DF9: "lake"}
    for cp, tri in doubled.items():   # the eight doubled trigrams are named after their trigram
        if names[tri] not in unicodedata.name(chr(cp)) or hexagrams[cp - 0x4DC0] != (tri, tri):
            raise SystemExit(f"U+{cp:04X} is not the doubled trigram {tri}")
    if len({tetragram_lines(n) for n in range(81)}) != 81 or tetragram_lines(0) != (0, 0, 0, 0):
        raise SystemExit("the tetragrams are not the 81 stacks of four lines")
    for cp in sets_["tblkdomh"][1:] + sets_["tblkdomv"][1:]:
        n = cp - (0x1F031 if cp < 0x1F062 else 0x1F063)
        want = f"DOMINO TILE {'HORIZONTAL' if cp < 0x1F062 else 'VERTICAL'}-{n // 7:02d}-{n % 7:02d}"
        if unicodedata.name(chr(cp)) != want:
            raise SystemExit(f"U+{cp:04X} is not {want}")
    words = ("ACE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN", "JACK", "KNIGHT", "QUEEN", "KING")
    for cp in sets_["tblkcard"]:
        row, r = divmod(cp - 0x1F0A0, 16)
        name = unicodedata.name(chr(cp))
        want = ("PLAYING CARD BACK" if r == 0 else f"PLAYING CARD {('', '', 'BLACK', 'WHITE')[row]} JOKER" if r == 15
                else f"PLAYING CARD {words[r - 1]} OF {SUITS[row].upper()}S")
        if name != want:
            raise SystemExit(f"U+{cp:04X} is {name}, not {want}")
    made = drawings()
    count = sum(len(v) for v in sets_.values())
    if len(made) != count:
        raise SystemExit("a character has no drawing")
    print(f"term_blocks: {count} characters in {len(sets_)} sets; hexagram pairs, doubled trigrams, tetragram "
          "count, domino and card names agree with Unicode's names")


if __name__ == "__main__":
    check()
