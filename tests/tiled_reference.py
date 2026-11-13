"""An independent float64 evaluation of a tiled (version 6) distance net.

It reads the neuronte-tiled-weights JSON, not the packed file, and shares
no code with src/neuronte.c or train/pack.py. Every sample of the whole
cell, at (i + 0.5) / (W * S) across and (j + 0.5) / (H * S) * 2 down,
belongs to the tile whose edges hold it (left edge inclusive). Its place
inside that tile, 0 to 1 across and 0 to 2 down, is what the tile's net
sees. The net's code comes from the bits b = scalar - first, modulo 2^32:
"place" gives base | (b & mask), "extract" gives base plus the bits of b
under mask, packed to the low end. A sample's coverage is
clamp(0.5 + f * tau * (tile width in cells) * W * S), and each pixel is
the mean of its S x S samples.
"""
import math

import numpy as np


def normal(s):
    return 0xFFFD if s > 0x10FFFF or 0xD800 <= s <= 0xDFFF else s


def _value(tok):
    if isinstance(tok, int):
        return tok
    return int(tok[2:], 16)


class Distance:
    """A version 1 distance net from its JSON document."""

    def __init__(self, doc):
        self.L = {k: (np.asarray(v["weight"], np.float32).astype(np.float64).reshape(v["rows"], v["cols"]),
                      np.asarray(v["bias"], np.float32).astype(np.float64)) for k, v in doc["layers"].items()}
        self.tau = float(np.float32(doc["shape"]["tau"]))
        self.masks = [int(m, 16) for m in doc["shape"]["parity_masks"]]

    def code(self, c):
        bits = [(c >> i) & 1 for i in range(21)] + [bin(c & m).count("1") & 1 for m in self.masks]
        return np.where(np.array(bits) == 1, 1.0, -1.0)

    def field(self, c, x, y):
        """Raw outputs at the points (x[i], y[i]) for the code c."""
        f = [2 * x - 1, y - 1]
        for k in range(6):
            w = 2 * math.pi * 2 ** k
            f += [np.sin(w * x), np.sin(w * y), np.cos(w * x), np.cos(w * y)]
        p = np.stack(f, -1)
        inp = np.concatenate([p, np.broadcast_to(self.code(c), (p.shape[0], 64))], 1)
        h = inp
        for name in ("l1", "l2", "l3"):
            w, b = self.L[name]
            h = np.maximum(h @ w.T + b, 0)
        w, b = self.L["out"]
        return (h @ w.T + b)[:, 0]


class Tiled:
    colour = False

    def __init__(self, doc):
        self.first = _value(doc["first"])
        self.xe = [float(np.float32(e)) for e in doc["columns"]]
        self.ye = [float(np.float32(e)) for e in doc["rows"]]
        self.nets = [Distance(d) for d in doc["nets"]]
        self.tiles = [(t["net"], _value(t["mask"]), _value(t["base"]), t["code"] == "extract")
                      for t in doc["tiles"]]

    def code(self, s, tile):
        _, mask, base, extract = tile
        b = (s - self.first) % (1 << 32)
        if not extract:
            return base | (b & mask)
        v, bit = 0, 0
        for i in range(32):
            if mask >> i & 1:
                v |= (b >> i & 1) << bit
                bit += 1
        return base + v

    def coverage(self, s, cw, ch, ss):
        s = normal(s)
        sw, sh = cw * ss, ch * ss
        cols, rows = len(self.xe) - 1, len(self.ye) - 1
        x = (np.arange(sw) + 0.5) / sw
        y = (np.arange(sh) + 0.5) / sh * 2
        col = np.minimum(np.searchsorted(self.xe, x, side="right") - 1, cols - 1)
        row = np.minimum(np.searchsorted(self.ye, y, side="right") - 1, rows - 1)
        xe, ye = np.asarray(self.xe), np.asarray(self.ye)
        lx = (x - xe[col]) / (xe[col + 1] - xe[col])
        ly = (y - ye[row]) / (ye[row + 1] - ye[row]) * 2
        out = np.full((sh, sw), np.nan)
        for k, tile in enumerate(self.tiles):
            r, c = divmod(k, cols)
            jx, jy = np.nonzero(col == c)[0], np.nonzero(row == r)[0]
            if not len(jx) or not len(jy):
                continue
            net = self.nets[tile[0]]
            yy, xx = np.meshgrid(ly[jy], lx[jx], indexing="ij")
            f = net.field(self.code(s, tile), xx.ravel(), yy.ravel()).reshape(len(jy), len(jx))
            slope = net.tau * (xe[c + 1] - xe[c]) * cw * ss
            out[np.ix_(jy, jx)] = np.clip(0.5 + f * slope, 0, 1)
        assert not np.isnan(out).any()
        return out.reshape(ch, ss, cw, ss).mean((1, 3))
