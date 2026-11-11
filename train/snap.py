"""Straight edges of a colour glyph, and the warp that snaps them to pixels.

The probe reads the drawings, not the net. It is the pack-time probe:
160 samples per cell width, an edge must run for 0.08 cell widths, and a
crossing may drift by at most 1e-6 cell widths from one row to the next.
Curves and diagonals fail that test and are not stored.

Positions are design-cell widths. x is 0 at the left and 1 at the right.
y is 0 at the top and 2 at the bottom. The warp is separable, one
piecewise-linear map for x and one for y. On a 1:2 cell the y scale is
the cell width and the y extent is twice that.
"""
import math

import numpy as np

import glyphs

N = 160          # probe samples per cell width
MIN_LEN = 0.08   # an edge must run this far, in cell widths, to be stored
STRAIGHT = 1e-6  # how far, in cell widths, a crossing may drift and stay one edge
PEN = 0.075


def _edges_1d(sd):
    """Straight edges along the last axis of a field (rows, cols): [(pos, rising)].

    pos is in cell widths. rising means ink starts there, moving along the
    axis. An edge counts only where the zero crossing stays at one position
    for MIN_LEN or more of consecutive rows."""
    m = sd > 0
    rise = ~m[:, :-1] & m[:, 1:]
    fall = m[:, :-1] & ~m[:, 1:]
    out = []
    for trans, rising in ((rise, True), (fall, False)):
        rows, cols = np.nonzero(trans)
        a, b = sd[rows, cols], sd[rows, cols + 1]
        x = (cols + np.clip(a / np.where(a == b, 1e-12, a - b), 0, 1)) / N
        order = np.lexsort((rows, cols))
        rows, x = rows[order], x[order]
        i = 0
        while i < len(x):
            j = i + 1
            while j < len(x) and abs(x[j] - x[j - 1]) < STRAIGHT and rows[j] == rows[j - 1] + 1:
                j += 1
            if (j - i) / N >= MIN_LEN:
                out.append((float(x[i]), rising))
            i = j
    out.sort()
    merged = []
    for pos, rising in out:
        if merged and abs(pos - merged[-1][0]) < 1e-6 and merged[-1][1] == rising:
            continue
        merged.append((pos, rising))
    return merged


def probe(layers):
    """Edges of each layer, back to front: [(xs, ys)], each a list of (pos, rising)."""
    P = glyphs.nodes(N)
    out = []
    for _, shapes in layers:
        sd = glyphs.signed_distance(shapes, P, PEN).reshape(2 * N + 1, N + 1)
        out.append((_edges_1d(sd), _edges_1d(sd.T)))
    return out


def _round(v, centre):
    """Nearest whole pixel. A value on n + 0.5 moves toward centre."""
    f = math.floor(v)
    if v - f == 0.5:
        return f if v > centre else f + 1
    return math.floor(v + 0.5)


def knots(edge_lists, scale, extent):
    """Warp knots (original px, snapped px) for one axis.

    edge_lists is one list of (pos, rising) per layer, in cell widths.
    scale is pixels per cell width. extent is the axis length in pixels.
    A rising edge followed immediately by a falling edge is a stem: its
    width rounds half down, stays at least 1, and keeps its centre. The
    tie for that left edge uses extent/2 - width/2, so a symmetric stem
    stays symmetric. Any other edge rounds on its own, ties toward
    extent/2. Knots closer than half a pixel in the original are one
    edge. The rest stay at least one pixel apart, and a knot on or past
    extent is dropped."""
    pairs = []
    for edges in edge_lists:
        edges = sorted(edges)
        i = 0
        while i < len(edges):
            p = edges[i][0] * scale
            if edges[i][1] and i + 1 < len(edges) and not edges[i + 1][1]:
                q = edges[i + 1][0] * scale
                w = max(1, math.ceil(q - p - 0.5))
                c = (p + q) / 2
                left = _round(c - w / 2, extent / 2 - w / 2)
                pairs += [(p, left), (q, left + w)]
                i += 2
            else:
                pairs.append((p, _round(p, extent / 2)))
                i += 1
    pairs.sort()
    out = [(0.0, 0.0)]
    for p, t in pairs:
        lp, lt = out[-1]
        if p - lp < 0.5 or p >= extent:
            continue
        t = max(t, lt + 1)
        if t >= extent:
            break
        out.append((p, float(t)))
    out.append((float(extent), float(extent)))
    return out


def axis_knots(layers, axis, cell_w, cell_h):
    """Knots for axis 0 (x) or 1 (y) of one glyph's probed layers."""
    if axis == 0:
        return knots([xs for xs, _ in layers], cell_w, cell_w)
    return knots([ys for _, ys in layers], cell_h / 2, cell_h)


def sample_positions(n_px, ss, kn, scale):
    """Sample positions in cell widths for the pixel samples along one axis.

    kn is None when the axis is not snapped. Otherwise it is the knots
    from knots(), and a sample at output pixel u is mapped back through
    them before dividing by scale."""
    u = (np.arange(n_px * ss) + 0.5) / ss
    if kn is None:
        return u / scale
    p, t = np.array(kn, dtype=np.float64).T
    return np.interp(u, t, p) / scale
