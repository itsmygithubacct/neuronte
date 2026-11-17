"""The letters of neuronte-term-letters-v1, made from the project's strokes.

font/term-letters.txt holds three kinds of line:

    $name PARTS             a named part (a hook, a tail), not a character
    U+XXXX PARTS            a character
    U+XXXX & U+BASE U+MARK  a character composed as train/glyphs.py composes
                            a letter and its marks; the base may be one of
                            this file's letters
    tletNAME U+XXXX ...     a training set and its characters, in the order
                            the group nets take them

PARTS are separated by " | ". A part is a stroke in the syntax of
font/strokes.txt (P, E, F, O, S, with @pen), or a reference to a drawing
that exists, changed by a chain of operations:

    @REF[:op]...            REF is one character, U+XXXX or $name
    @REF[0,2]               only those of its parts, counted from 0

A reference is looked up in this file, then in letters.txt, strokes.txt,
symbols.txt and marks.txt, and last among the composed letters of the
older sets. A character that refers to itself gets the older drawing.

Operations, on the 10 x 20 grid of strokes.txt (cap top 4, x-height 8,
baseline 15, descender 19):

    turn      half a turn about the middle of the x-height band; what then
              hangs under the descender line or stands over the ascender
              line is squeezed back to it
    turncap   half a turn about the middle of the capital band
    mirror    left for right
    flip      top for bottom in the x-height band, squeezed like turn
    flipcap   top for bottom in the capital band
    side      a quarter turn, clockwise, about the middle of the x-height band
    small     a capital made a small capital: onto the baseline at x-height
    super     a modifier letter: SCRIPT of the size, baseline at SUPER_BASE,
              drawn with SCRIPT_PEN
    sub       the same hung low, baseline at SUB_BASE
    lh, rh    the left or right half of the cell, for two letters in one
              cell, drawn with PAIR_PEN
    t1 t2 t3  the three thirds of the cell, for three letters
    m(kx,ky,cx,cy)   scaled about a point
    t(dx,dy)         moved
    pen(r)           every stroke drawn with pen radius r, in grid units

A character with no line of its own whose compatibility decomposition is
<super> or <sub> of one character is that character with super or sub.
The tone bars are made from their names by tone_bar().

A trailing "  # unsure: ..." on a character's line says the shape was drawn
from the Unicode name and what I remember of the chart, without certainty;
the review sheet shows the note beside the drawing.

No font file was opened and no font rasteriser was called to make these.
"""
import math
import os
import re
import unicodedata

import glyphs
import strokes

TERM_LETTERS = os.path.join(strokes.ROOT, "font", "term-letters.txt")
SCRIPT, SUPER_BASE, SUB_BASE, SCRIPT_PEN = 0.7, 9.6, 16.2, 0.62
PAIR, PAIR_LEFT, PAIR_RIGHT, PAIR_PEN = 0.58, 0.6, 5.92, 0.6
THIRD, THIRDS, THIRD_PEN = 0.38, (0.6, 3.86, 7.12), 0.5
SMALL_X = 0.92                  # a small capital keeps this much of the capital's width
ASCENDER, XHEIGHT, BASELINE, DESCENDER = 3.5, 8.0, 15.0, 19.0
REF = re.compile(r"@(U\+[0-9A-F]{4,5}|\$[a-z0-9]+|.)(\[[0-9,]+\])?((?::[a-z0-9]+(?:\([^)]*\))?)*)$")
OP = re.compile(r":([a-z0-9]+)(?:\(([^)]*)\))?")


def _lines():
    """(kind, head, body, note) for each line of the file."""
    with open(TERM_LETTERS, encoding="utf-8") as fh:
        for num, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("# ") or line == "#":
                continue
            note = ""
            if "  # " in line:
                line, _, note = line.partition("  # ")
                line = line.rstrip()
            head, _, body = line.partition(" ")
            if head.startswith("tlet"):
                yield "set", head, body, note
            elif head.startswith("$"):
                yield "part", head, body, note
            elif head.startswith("U+"):
                yield "char", chr(int(head[2:], 16)), body, note
            else:
                raise ValueError(f"{TERM_LETTERS}:{num}: a line starts with tlet..., $name or U+XXXX")


def sets():
    """{set: [code points]} in the file's order."""
    return glyphs.term_letters_sets()


def notes():
    """{char: note} for the characters whose line carries one, and the dotted tone bars."""
    out = {head: note for kind, head, _, note in _lines() if kind == "char" and note}
    for cps in sets().values():
        for c in cps:
            got = _tone(chr(c))
            if got is not None and "DOTTED" in got[1]:
                out.setdefault(chr(c), TONE_NOTE)
    return out


def _source_parts(path):
    """{char: [part text]} of a stroke file, the parts as written."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("# ") or line == "#" or not line.strip():
                continue
            if line.startswith("U+"):
                head, _, rest = line.partition(" ")
                ch = chr(int(head[2:], 16))
            else:
                ch, rest = line[0], line[2:]
            out[ch] = [p.strip() for p in rest.split("|") if p.strip()]
    return out


def _fit(shapes):
    """Squeeze what hangs under the descender line or stands over the ascender line."""
    ys = [y for _, y in glyphs.points(shapes)]
    low, top = max(ys) * 10, min(ys) * 10
    kd = (DESCENDER - BASELINE) / (low - BASELINE) if low > DESCENDER + 1e-9 else 1.0
    ka = (XHEIGHT - ASCENDER) / (XHEIGHT - top) if top < ASCENDER - 1e-9 else 1.0
    if kd == 1.0 and ka == 1.0:
        return shapes

    def f(x, y):
        g = y * 10
        if g > BASELINE:
            g = BASELINE + (g - BASELINE) * kd
        elif g < XHEIGHT:
            g = XHEIGHT - (XHEIGHT - g) * ka
        return x, g / 10
    return glyphs.moved(shapes, f)


def _grid(f):
    """A map of cell units from a map of grid units."""
    def g(x, y):
        a, b = f(x * 10, y * 10)
        return a / 10, b / 10
    return g


def _apply(shapes, name, arg):
    mid = XHEIGHT + BASELINE            # twice the middle of the x-height band
    cap = 4.0 + BASELINE
    mv = lambda f: glyphs.moved(shapes, _grid(f))  # noqa: E731
    if name == "turn":
        return _fit(mv(lambda x, y: (10 - x, mid - y)))
    if name == "turncap":
        return mv(lambda x, y: (10 - x, cap - y))
    if name == "mirror":
        return mv(lambda x, y: (10 - x, y))
    if name == "flip":
        return _fit(mv(lambda x, y: (x, mid - y)))
    if name == "flipcap":
        return mv(lambda x, y: (x, cap - y))
    if name == "side":
        return mv(lambda x, y: (5 - (y - mid / 2), mid / 2 + (x - 5)))
    if name == "small":
        k = (BASELINE - XHEIGHT) / (BASELINE - 4.0)
        return mv(lambda x, y: (5 + (x - 5) * SMALL_X, BASELINE - (BASELINE - y) * k))
    if name in ("super", "sub"):
        base = SUPER_BASE if name == "super" else SUB_BASE
        return glyphs._with_pen(mv(lambda x, y: (5 + (x - 5) * SCRIPT, base - (BASELINE - y) * SCRIPT)),
                                SCRIPT_PEN / 10)
    if name in ("lh", "rh"):
        off = PAIR_LEFT if name == "lh" else PAIR_RIGHT
        return glyphs._with_pen(mv(lambda x, y: (off + (x - 2) * PAIR, y)), PAIR_PEN / 10)
    if name in ("t1", "t2", "t3"):
        off = THIRDS[int(name[1]) - 1]
        return glyphs._with_pen(mv(lambda x, y: (off + (x - 2) * THIRD, y)), THIRD_PEN / 10)
    nums = [float(v) for v in arg.split(",")] if arg else []
    if name == "m" and len(nums) == 4:
        kx, ky, cx, cy = nums
        return mv(lambda x, y: (cx + (x - cx) * kx, cy + (y - cy) * ky))
    if name == "t" and len(nums) == 2:
        return mv(lambda x, y: (x + nums[0], y + nums[1]))
    if name == "pen" and len(nums) == 1:
        return glyphs._with_pen(shapes, nums[0] / 10)
    raise ValueError(f"no operation {name}({arg or ''})")


# Tone bars, from their names: a stem at the right (or the left) and a bar at
# one of five heights; a dotted one has a dot at that height and no bar.
TONE_LEVEL = {"EXTRA-HIGH": 0, "HIGH": 1, "MID": 2, "LOW": 3, "EXTRA-LOW": 4}
TONE_TOP, TONE_STEP, TONE_STEM, TONE_FREE = 4.0, 2.75, 7.6, 2.6
TONE_DOT_X, TONE_DOT = 3.6, 1.1   # a dotted bar's dot and its radius
TONE_NOTE = "unsure: drawn as a stem and a dot at the height of the tone, with no bar between them"


def _tone(ch):
    words = unicodedata.name(ch, "").split()
    if words[:2] != ["MODIFIER", "LETTER"] or words[-2:] != ["TONE", "BAR"] or words[2] not in TONE_LEVEL:
        return None
    rest = words[3:-2]
    return None if set(rest) - {"DOTTED", "LEFT-STEM"} else (TONE_LEVEL[words[2]], rest)


def tone_bar(ch):
    """Shapes for MODIFIER LETTER level [DOTTED] [LEFT-STEM] TONE BAR, or None."""
    got = _tone(ch)
    if got is None:
        return None
    level, rest = got
    y = (TONE_TOP + TONE_STEP * level) / 10
    stem, top, low = TONE_STEM / 10, TONE_TOP / 10, (TONE_TOP + 4 * TONE_STEP) / 10
    out = [("seg", stem, top, stem, low, None)]
    if "DOTTED" in rest:
        out.append(("seg", TONE_DOT_X / 10, y, TONE_DOT_X / 10, y, TONE_DOT / 10))
    else:
        out.append(("seg", stem, y, TONE_FREE / 10, y, None))
    return glyphs.moved(out, lambda px, py: (1 - px, py)) if "LEFT-STEM" in rest else out


class _Maker:
    def __init__(self):
        self.mine, self.named, self.compose = {}, {}, {}
        for kind, head, body, _ in _lines():
            if kind == "set":
                continue
            table = self.named if kind == "part" else self.mine
            if head in table or head in self.compose:
                raise ValueError(f"{TERM_LETTERS}: {head!r} is drawn twice")
            if kind == "char" and body.startswith("& "):
                self.compose[head] = body[2:].split()
            else:
                table[head] = [p.strip() for p in body.split(" | ") if p.strip()]
        self.files = [_source_parts(p) for p in (glyphs.LETTERS, strokes.STROKES, strokes.SYMBOLS, glyphs.MARKS)]
        self.older = None
        self.marks = {ord(c): m for c, m in strokes.parse(glyphs.MARKS).items()}
        self.done, self.busy = {}, set()

    def _older(self, ch):
        if self.older is None:
            self.older = {**glyphs.accents(), **glyphs.terminal_letters(), **glyphs.term_latin()}
            self.older.update({c: g for c, g in glyphs.terminal_symbols().items()})
        if ch not in self.older:
            raise ValueError(f"no drawing for U+{ord(ch):04X} to refer to")
        return [self.older[ch]]

    def parts(self, key, skip_mine=False):
        """[shapes of each part] for a character or a $name."""
        if not skip_mine and (key, False) in self.done:
            return self.done[(key, False)]
        if key.startswith("$") and len(key) > 1:
            texts, where = self.named.get(key), "named"
            if texts is None:
                raise ValueError(f"no part {key}")
        elif not skip_mine and key in self.mine:
            texts, where = self.mine[key], "mine"
        elif not skip_mine and key in self.compose:
            return [self.composed(key)]
        else:
            texts = next((f[key] for f in self.files if key in f), None)
            where = "file"
            if texts is None:
                made = self._auto(key) if not skip_mine else None
                return [made] if made is not None else self._older(key)
        if where != "file":
            if key in self.busy:
                raise ValueError(f"{key!r} refers to itself in a circle")
            self.busy.add(key)
        out = [self.part(t, key) for t in texts]
        if where != "file":
            self.busy.discard(key)
            self.done[(key, False)] = out
        return out

    def part(self, text, owner):
        if not text.startswith("@"):
            return strokes._shapes(text, owner)
        m = REF.match(text)
        if not m:
            raise ValueError(f"bad reference {text!r} for {owner!r}")
        ref, sel, ops = m.groups()
        key = chr(int(ref[2:], 16)) if ref.startswith("U+") else ref
        got = self.parts(key, skip_mine=key == owner)
        if sel:
            got = [got[int(i)] for i in sel[1:-1].split(",")]
        shapes = [s for p in got for s in p]
        for name, arg in OP.findall(ops or ""):
            shapes = _apply(shapes, name, arg)
        return shapes

    def shapes(self, ch):
        return [s for p in self.parts(ch) for s in p]

    def _auto(self, ch):
        if len(ch) != 1:
            return None
        bar = tone_bar(ch)
        if bar is not None:
            return bar
        d = unicodedata.decomposition(ch).split()
        if len(d) == 2 and d[0] in ("<super>", "<sub>"):
            return _apply(self.shapes(chr(int(d[1], 16))), d[0][1:-1], None)
        return None

    def composed(self, ch):
        spec = self.compose[ch]
        greek = spec[-1] == "greek"
        cps = [int(t[2:], 16) for t in (spec[:-1] if greek else spec)]
        letter = chr(cps[0])
        return glyphs.composed(letter, cps[1:], {letter: self.shapes(letter)}, self.marks, greek)


_MADE = None


def letters():
    """{char: shapes} for every character of the file's training sets."""
    global _MADE
    if _MADE is None:
        _MADE = _letters()
    return _MADE


def _letters():
    maker = _Maker()
    out = {}
    for cps in sets().values():
        for c in cps:
            ch = chr(c)
            out[ch] = maker.shapes(ch)
            if not out[ch]:
                raise ValueError(f"U+{c:04X} {unicodedata.name(ch)}: nothing drawn")
    extra = (set(maker.mine) | set(maker.compose)) - set(out)
    if extra:
        raise ValueError("drawn but in no set: " + " ".join(f"U+{ord(c):04X}" for c in sorted(extra)))
    return out


if __name__ == "__main__":
    made = letters()
    print(len(made), "characters in", len(sets()), "sets:",
          ", ".join(f"{n} {len(c)}" for n, c in sets().items()))
    print(len(notes()), "marked unsure")
