"""The characters of the neuronte-wide bundles: wide characters drawn for a box of two cells.

A terminal gives a wide character two cells. These drawings fill that box,
which is square: 18 x 18 units here (one unit a pixel when the cell is
9 x 18). A net's design cell is one unit wide and two high, and the engine
asks it for a box W x H as the cell W x 2H and averages each pair of rows
(the contract of neuronte-kilix-chrome-v2), so a box drawing is put in the
cell twice as tall as it is wide by kilix_chrome2.to_cell, which first
turns every stroke into its outline in the box.

The drawings are made in code, in box units, x right and y down:

    wide_forms.py   the 103 fullwidth forms, from the project's one-cell
                    drawings of the same characters at text size
    wide_symbols.py the signs, the enclosed forms, the emoticons and the
                    transport and map symbols
    wide_pict.py    Miscellaneous Symbols and Pictographs
    wide_supp.py    Supplemental Symbols and Pictographs and Extended-A

Each module has DRAWN {code point: box shapes} and NOTES {code point: what
is not sure}. No font file was opened or rasterised; each drawing is made
from the character's Unicode name and this project's own drawings.

    bundles()       {bundle: [set names]}
    primary()       {set: (group nets, [code points])}
    sets()          the sets and, for each group net of a set, the set NAMErI
    made()          {char: shapes} in cell units, for every character
    box_shapes()    {code point: shapes} in box units
    notes()         {code point: note}
"""
import math

import kilix_chrome2
from term_rest import groups

PREFIX = "twd"
BOX = 18.0
PEN = 2.0                          # the width of an outline or a thin stroke, in units

# The bundles, their set prefixes and characters a group net.
BUNDLES = {
    "neuronte-wide-forms-v1": ("twdf", 10, "wide_forms"),
    "neuronte-wide-symbols-v1": ("twds", 6, "wide_symbols"),
    "neuronte-wide-pictographs-v1": ("twdp", 6, "wide_pict"),
    "neuronte-wide-supplement-v1": ("twdu", 6, "wide_supp"),
}
TEACHER = {"neuronte-wide-forms-v1": "wideforms", "neuronte-wide-symbols-v1": "widesymbols",
           "neuronte-wide-pictographs-v1": "widepict", "neuronte-wide-supplement-v1": "widesupp"}
SET_MAX = 60                       # characters in one training set at most


# ---------------------------------------------------------------- shapes in box units

def L(*pts, w=PEN):
    """A polyline stroke w units wide, round ended."""
    return [("seg", pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], w / 2) for i in range(len(pts) - 1)]


def _pts(cx, cy, rx, ry, a0, a1, step=None):
    span = a1 - a0
    n = max(3, int(abs(span) / (step or max(8.0, 60.0 / max(1.0, max(rx, ry))))) + 1)
    return [(cx + rx * math.cos(math.radians(a0 + span * i / n)), cy + ry * math.sin(math.radians(a0 + span * i / n)))
            for i in range(n + 1)]


def A(cx, cy, rx, ry, a0, a1, w=PEN):
    """An elliptical arc stroke, degrees, 0 east, 90 down."""
    return L(*_pts(cx, cy, rx, ry, a0, a1), w=w)


def C(cx, cy, r, w=PEN, ry=None):
    """A ring: a circle (or ellipse) outline w wide, r to the middle of the pen."""
    return A(cx, cy, r, r if ry is None else ry, 0, 360, w)


def D(cx, cy, rx, ry=None):
    """A filled disc or ellipse."""
    return [("poly", _pts(cx, cy, rx, rx if ry is None else ry, 0, 360)[:-1])]


def S(cx, cy, rx, ry, a0, a1):
    """A filled sector."""
    return [("poly", [(cx, cy)] + _pts(cx, cy, rx, ry, a0, a1))]


def F(*pts):
    return [("poly", list(pts))]


def R(x0, y0, x1, y1):
    return [("poly", [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])]


def RR(x0, y0, x1, y1, r):
    """A filled rectangle with round corners of radius r."""
    pts = []
    for cx, cy, a in ((x1 - r, y0 + r, 270), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        pts += _pts(cx, cy, r, r, a, a + 90, 15)
    return [("poly", pts)]


def B(x0, y0, x1, y1, w=PEN):
    """A rectangle outline w wide, its outer edge at the given corners: four bars."""
    return R(x0, y0, x1, y0 + w) + R(x0, y1 - w, x1, y1) + R(x0, y0, x0 + w, y1) + R(x1 - w, y0, x1, y1)


def RB(x0, y0, x1, y1, r, w=PEN):
    """A rounded rectangle outline, its outer edge at the corners given."""
    h = w / 2
    a, b, c, d = x0 + h, y0 + h, x1 - h, y1 - h
    rr = max(r - h, 0.01)
    return (L((a + rr, b), (c - rr, b), w=w) + L((a + rr, d), (c - rr, d), w=w) + L((a, b + rr), (a, d - rr), w=w) +
            L((c, b + rr), (c, d - rr), w=w) + A(c - rr, b + rr, rr, rr, 270, 360, w) + A(c - rr, d - rr, rr, rr, 0, 90, w) +
            A(a + rr, d - rr, rr, rr, 90, 180, w) + A(a + rr, b + rr, rr, rr, 180, 270, w))


def K(shapes):
    """Cut the shapes out of everything before them."""
    out = []
    for s in shapes:
        out.append(s if s[0] == "cut" else ("cut", s))
    return out


def P(*pts):
    """A filled polygon from a flat list of numbers."""
    return F(*[(pts[i], pts[i + 1]) for i in range(0, len(pts), 2)])


def star(cx, cy, r, inner=0.42, n=5, rot=-90.0):
    return F(*[(cx + r * (1 if i % 2 == 0 else inner) * math.cos(math.radians(rot + i * 180.0 / n)),
                cy + r * (1 if i % 2 == 0 else inner) * math.sin(math.radians(rot + i * 180.0 / n))) for i in range(2 * n)])


def heart(cx, cy, s):
    """A filled heart about s units wide, its middle at (cx, cy)."""
    k = s / 2.0
    return (D(cx - 0.5 * k, cy - 0.3 * k, 0.52 * k) + D(cx + 0.5 * k, cy - 0.3 * k, 0.52 * k) +
            F((cx - 0.98 * k, cy - 0.18 * k), (cx + 0.98 * k, cy - 0.18 * k), (cx, cy + 0.95 * k)))


def drop(cx, cy, h):
    """A filled drop h units tall, its round end down, its middle at (cx, cy)."""
    r = 0.33 * h
    by = cy + h / 2 - r
    return D(cx, by, r) + F((cx - r * 0.94, by - r * 0.33), (cx, cy - h / 2), (cx + r * 0.94, by - r * 0.33))


def move(shapes, dx=0.0, dy=0.0, s=1.0, rot=0.0, mx=False, my=False, cx=9.0, cy=9.0, sy=None):
    """Shapes scaled by s (sy across y if given) and turned rot degrees about (cx, cy), mirrored, then moved."""
    c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    syy = s if sy is None else sy

    def f(x, y):
        x, y = (x - cx) * s, (y - cy) * syy
        if mx:
            x = -x
        if my:
            y = -y
        return (cx + x * c - y * sn + dx, cy + x * sn + y * c + dy)
    k = math.sqrt(abs(s * syy))
    out = []
    for sh in shapes:
        if sh[0] == "cut":
            out.append(("cut", move([sh[1]], dx, dy, s, rot, mx, my, cx, cy, sy)[0]))
        elif sh[0] == "seg":
            (x0, y0), (x1, y1) = f(sh[1], sh[2]), f(sh[3], sh[4])
            out.append(("seg", x0, y0, x1, y1, sh[5] * k))
        else:
            out.append(("poly", [f(x, y) for x, y in sh[1]]))
    return out


def from_cell(shapes, k, ox, oy, pen=0.075, pen_scale=None):
    """One-cell shapes (cell units, x 0..1, y 0..2) in the box: x k + ox, y k + oy.

    A stroke's radius is scaled by pen_scale (k when not given); None is the default pen."""
    ps = k if pen_scale is None else pen_scale
    out = []
    for sh in shapes:
        if sh[0] == "cut":
            out.append(("cut", from_cell([sh[1]], k, ox, oy, pen, pen_scale)[0]))
        elif sh[0] == "seg":
            r = pen if sh[5] is None else sh[5]
            out.append(("seg", sh[1] * k + ox, sh[2] * k + oy, sh[3] * k + ox, sh[4] * k + oy, r * ps))
        else:
            out.append(("poly", [(x * k + ox, y * k + oy) for x, y in sh[1]]))
    return out


_ASCII = None


def ascii_shapes():
    global _ASCII
    if _ASCII is None:
        import strokes
        _ASCII = strokes.parse(strokes.STROKES)
    return _ASCII


def text(s, cx, cy, h, w=None, gap=0.15, pen=None):
    """The ASCII string s from font/strokes.txt, capitals h units tall, centred on (cx, cy).

    Each letter takes 0.6 + gap cell widths; pen is the stroke width in units (default in scale)."""
    g = ascii_shapes()
    k = h / 1.1                    # strokes.txt: capitals 1.1 cell widths tall, y 0.4..1.5
    adv = (0.6 + gap) * k
    if w is not None:              # squeeze across to fit w units
        k_x = min(1.0, w / (adv * len(s) - gap * k)) if s else 1.0
    else:
        k_x = 1.0
    total = (adv * len(s) - gap * k) * k_x
    out = []
    for i, ch in enumerate(s):
        ox = cx - total / 2 + i * adv * k_x - 0.2 * k * k_x
        oy = cy - 0.95 * k
        r = None if pen is None else pen / 2
        for sh in g[ch]:
            if sh[0] == "seg":
                rr = r if r is not None else (sh[5] if sh[5] is not None else 0.075) * k
                out.append(("seg", sh[1] * k * k_x + ox, sh[2] * k + oy, sh[3] * k * k_x + ox, sh[4] * k + oy, rr))
            elif sh[0] == "poly":
                out.append(("poly", [(x * k * k_x + ox, y * k + oy) for x, y in sh[1]]))
            else:
                raise ValueError("a cut in strokes.txt")
    return out


# ---------------------------------------------------------------- sets

def _modules():
    import importlib
    return {b: importlib.import_module(m) for b, (_, _, m) in BUNDLES.items()}


_CACHE = {}


def box_shapes():
    """{code point: shapes in box units} over all bundles."""
    if "box" not in _CACHE:
        out = {}
        for b, mod in _modules().items():
            for cp, sh in mod.drawn().items():
                if cp in out:
                    raise ValueError(f"U+{cp:04X} is drawn twice")
                out[cp] = sh
        _CACHE["box"] = out
    return _CACHE["box"]


def bundle_of():
    out = {}
    for b, mod in _modules().items():
        for cp in mod.drawn():
            out[cp] = b
    return out


def primary():
    """{set: (group nets, [code points])}: each bundle's characters in code point order, cut into sets."""
    if "primary" in _CACHE:
        return _CACHE["primary"]
    out = {}
    for b, mod in _modules().items():
        prefix, per, _ = BUNDLES[b]
        cps = sorted(mod.cps() if hasattr(mod, "cps") else mod.drawn())
        runs = mod.set_runs() if hasattr(mod, "set_runs") else None
        if runs is None:
            n = max(1, math.ceil(len(cps) / SET_MAX))
            runs = groups(cps, n)
        for i, run in enumerate(r for r in runs if r):
            out[f"{prefix}{i}"] = (max(1, math.ceil(len(run) / per)), list(run))
    _CACHE["primary"] = out
    return out


def bundles():
    out = {b: [] for b in BUNDLES}
    for name in primary():
        for b, (prefix, _, _) in BUNDLES.items():
            if name.startswith(prefix) and name[len(prefix):].isdigit():
                out[b].append(name)
    return out


def sets():
    out = {}
    for name, (nets, cps) in primary().items():
        out[name] = cps
        for i, run in enumerate(groups(cps, nets)):
            out[f"{name}r{i}"] = run
    return out


def notes():
    out = {}
    for mod in _modules().values():
        out.update(getattr(mod, "NOTES", {}))
    return out


def made():
    """{char: shapes} in cell units for every drawn character."""
    if "made" not in _CACHE:
        _CACHE["made"] = {chr(cp): kilix_chrome2.to_cell([_tenth(s) for s in sh]) for cp, sh in box_shapes().items()}
    return _CACHE["made"]


def _tenth(sh):
    """Box units to the tenths kilix_chrome2.to_cell takes (it reads strokes.py's numbers, a tenth of those written)."""
    if sh[0] == "cut":
        return ("cut", _tenth(sh[1]))
    if sh[0] == "seg":
        return ("seg", sh[1] / 10, sh[2] / 10, sh[3] / 10, sh[4] / 10, sh[5] / 10)
    return ("poly", [(x / 10, y / 10) for x, y in sh[1]])


def tier(name):
    m = made()
    return [(chr(c), m[chr(c)]) for c in sets()[name]]


COMMON = ["train/wide.py", "train/wide_parts.py", "train/kilix_chrome2.py", "train/term_rest.py", "font/strokes.txt"]
EXTRA = {"neuronte-wide-forms-v1": ["font/symbols.txt", "font/letters.txt", "font/marks.txt", "font/term-sym.txt",
                                    "font/term-sym-partition.json", "train/term_glyphs.py"],
         "neuronte-wide-symbols-v1": ["font/term-rest.txt"]}


def sources(tiers):
    """The files the given tiers are made from."""
    files = list(COMMON)
    for b, (prefix, _, _) in BUNDLES.items():
        if any(t.startswith(prefix) or t == TEACHER[b] for t in tiers):
            for f in ["train/" + BUNDLES[b][2] + ".py"] + EXTRA.get(b, []):
                if f not in files:
                    files.append(f)
    return files
