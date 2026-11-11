"""Read Neuronte stroke files into shapes.

Each character becomes a list of shapes in cell units, x 0..1 across the
cell and y 0..2 down it:

    ("seg", x0, y0, x1, y1, r)   a pen stroke of radius r, or None for the
                                 default pen
    ("poly", [(x, y), ...])      a filled polygon

File syntax, one character per line, coordinates on a 10 x 20 grid:

    P x,y x,y ...            polyline stroke
    E cx,cy rx,ry a0 a1      elliptical arc stroke, degrees, 0 = east, 90 = down
    F x,y x,y ...            filled polygon
    O cx,cy rx,ry            filled ellipse
    S cx,cy rx,ry a0 a1      filled sector of an ellipse
    P@1.3 ...                any stroke with its own pen radius, in grid units

The character is written first, or as U+XXXX, then a space, then shapes
separated by " | ".

Colour glyphs (font/icons.txt) are written as layers, back to front,
separated by " || ", each starting with a palette entry in braces from
font/palette.txt:

    U+E654 {red} O 5,10 3.9,3.9 || {clear} P@0.6 3.4,8.4 6.6,11.6
"""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STROKES = os.path.join(ROOT, "font", "strokes.txt")
SYMBOLS = os.path.join(ROOT, "font", "symbols.txt")
MASKS = os.path.join(ROOT, "font", "code-masks.txt")
ICONS = os.path.join(ROOT, "font", "icons.txt")
PALETTE = os.path.join(ROOT, "font", "palette.txt")


def _xy(tok):
    x, y = tok.split(",")
    return float(x) / 10, float(y) / 10


def _arc(cx, cy, rx, ry, a0, a1):
    n = max(2, int(abs(a1 - a0) / 10) + 1)
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _shapes(part, ch):
    tok = part.split()
    kind, _, rad = tok[0].partition("@")
    r = float(rad) / 10 if rad else None
    args = tok[1:]
    if kind == "P" and len(args) >= 2:
        pts = [_xy(t) for t in args]
    elif kind in ("E", "S") and len(args) == 4:
        (cx, cy), (rx, ry) = _xy(args[0]), _xy(args[1])
        pts = _arc(cx, cy, rx, ry, float(args[2]), float(args[3]))
        if kind == "S":
            return [("poly", [(cx, cy)] + pts)]
    elif kind == "F" and len(args) >= 3:
        return [("poly", [_xy(t) for t in args])]
    elif kind == "O" and len(args) == 2:
        (cx, cy), (rx, ry) = _xy(args[0]), _xy(args[1])
        return [("poly", _arc(cx, cy, rx, ry, 0, 360)[:-1])]
    else:
        raise ValueError(f"bad shape {part!r} for {ch!r}")
    return [("seg", *pts[i], *pts[i + 1], r) for i in range(len(pts) - 1)]


def parse(path=STROKES):
    glyphs = {}
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
            shapes = []
            for part in (p.strip() for p in rest.split("|")):
                if part:
                    shapes += _shapes(part, ch)
            if ch in glyphs:
                raise ValueError(f"duplicate {ch!r} in {path}")
            glyphs[ch] = shapes
    return glyphs


def palette(path=PALETTE):
    """The palette: {name: (entry, dark, light)}, colours as (r, g, b) in 0..255,
    None for entries 0 (the cell's foreground) and 1 (clear)."""
    out = {}
    with open(path) as fh:
        for raw in fh:
            tok = raw.split()
            if not tok or tok[0].startswith("#"):
                continue
            n, name, cols = int(tok[0]), tok[1], tok[2:]
            if n != len(out) or name in out:
                raise ValueError(f"palette entry {n} {name!r} is out of order or repeated")
            if (n < 2) != (not cols) or (n < 2 and name != ("fg", "clear")[n]) or (cols and len(cols) != 2):
                raise ValueError(f"palette entry {n} {name!r}: 0 is fg and 1 clear, with no colour; "
                                 "the rest have a dark and a light colour")
            rgb = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in cols]
            out[name] = (n, *rgb) if rgb else (n, None, None)
    return out


def parse_layers(path=ICONS, pal=None):
    """Read a file of colour glyphs: {ch: [(entry name, shapes), ...]}, back to front."""
    pal = palette() if pal is None else pal
    glyphs = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("#") or not line.strip():
                continue
            head, _, rest = line.partition(" ")
            ch = chr(int(head[2:], 16))
            layers = []
            for part in (p.strip() for p in rest.split(" || ")):
                if not part.startswith("{") or "}" not in part:
                    raise ValueError(f"layer {part[:20]!r} of U+{ord(ch):04X} does not start with {{entry}}")
                name, _, body = part[1:].partition("}")
                if name not in pal:
                    raise ValueError(f"U+{ord(ch):04X} uses {name!r}, which is not in the palette")
                shapes = []
                for sh in (q.strip() for q in body.split("|")):
                    if sh:
                        shapes += _shapes(sh, ch)
                layers.append((name, shapes))
            if ch in glyphs:
                raise ValueError(f"duplicate U+{ord(ch):04X} in {path}")
            glyphs[ch] = layers
    return glyphs


def masks(path=MASKS):
    with open(path) as fh:
        out = [int(line, 16) for line in fh if line.startswith("0x")]
    if len(out) != 43 or any(not 0 < m < 1 << 21 for m in out):
        raise ValueError("code-masks.txt must hold 43 masks over 21 bits")
    return out


if __name__ == "__main__":
    for path in (STROKES, SYMBOLS):
        g = parse(path)
        print(os.path.basename(path), len(g), "characters, most shapes", max(len(s) for s in g.values()))
    g = parse_layers()
    print("icons.txt", len(g), "characters, most layers", max(len(v) for v in g.values()),
          "palette", len(palette()), "entries")
