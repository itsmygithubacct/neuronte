"""Read font/strokes.txt into line segments.

Each character becomes a list of (x0, y0, x1, y1) segments in cell units:
x runs 0..1 across the cell and y runs 0..2 down it. Arcs are cut into
pieces of at most 10 degrees.
"""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STROKES = os.path.join(ROOT, "font", "strokes.txt")
MASKS = os.path.join(ROOT, "font", "code-masks.txt")


def _points(part, ch):
    tok = part.split()
    if tok[0] == "P":
        pts = [tuple(float(v) / 10 for v in t.split(",")) for t in tok[1:]]
        if len(pts) < 2:
            raise ValueError(f"polyline with one point for {ch!r}")
        return pts
    if tok[0] == "E" and len(tok) == 5:
        cx, cy = (float(v) / 10 for v in tok[1].split(","))
        rx, ry = (float(v) / 10 for v in tok[2].split(","))
        a0, a1 = float(tok[3]), float(tok[4])
        n = max(2, int(abs(a1 - a0) / 10) + 1)
        return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    raise ValueError(f"bad stroke {part!r} for {ch!r}")


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
            segs = []
            for part in (p.strip() for p in rest.split("|")):
                if part:
                    pts = _points(part, ch)
                    segs += [(*pts[i], *pts[i + 1]) for i in range(len(pts) - 1)]
            if ch in glyphs:
                raise ValueError(f"duplicate {ch!r}")
            glyphs[ch] = segs
    return glyphs


def masks(path=MASKS):
    with open(path) as fh:
        out = [int(line, 16) for line in fh if line.startswith("0x")]
    if len(out) != 43 or any(not 0 < m < 1 << 21 for m in out):
        raise ValueError("code-masks.txt must hold 43 masks over 21 bits")
    return out


if __name__ == "__main__":
    g = parse()
    missing = [chr(c) for c in range(32, 127) if chr(c) not in g]
    print(len(g), "characters, missing", missing, ", most segments", max(len(s) for s in g.values()))
