"""Neuronte video cells. RGB input/output is uint8, row-major, without padding.

TwoInk fits bounded RGB colours by exact least squares for every candidate.
MultiInk uses three cached neural masks, with eight Gray-labelled colours.
No coverage thresholding is performed. See tools/neuronte-video.md.
"""
from pathlib import Path
import ctypes as C
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import glyphs


class NeuralMasks:
    def __init__(self, weights=None, library=None):
        self.lib = C.CDLL(str(library or ROOT / 'build/libneuronte.so'))
        self.lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(C.c_void_p)]
        self.lib.neuronte_close.argtypes = [C.c_void_p]
        self.lib.neuronte_coverage.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_int, C.c_int, C.POINTER(C.c_float)]
        self.handle = C.c_void_p()
        path = Path(weights or ROOT / 'weights/neuronte-split-v4.nrt')
        if self.lib.neuronte_open_file(str(path).encode(), C.byref(self.handle)):
            raise ValueError(f'cannot load {path}')

    def mask(self, cp, width, height, samples=1):
        a = np.empty((height, width), np.float32)
        rc = self.lib.neuronte_coverage(self.handle, cp, width, height, samples, a.ctypes.data_as(C.POINTER(C.c_float)))
        if rc:
            raise ValueError(f'coverage failed: {rc}')
        return a

    def close(self):
        if self.handle:
            self.lib.neuronte_close(self.handle)
            self.handle = C.c_void_p()

    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def octant_characters():
    """All 256 patterns, using Unicode's explicit lattice definitions."""
    out = {bits: cp for cp, bits in glyphs.octants().items()}
    out.update({bits: cp for cp, bits in glyphs.SUBSTITUTES.items()})
    # Remaining patterns encoded by space, halves, quarters and quadrants.
    out.update({0: 0x20, 255: 0x2588, 15: 0x2580, 240: 0x2584,
                85: 0x258c, 170: 0x2590, 192: 0x2582,
                252: 0x2586, 80: 0x2596, 160: 0x2597,
                5: 0x2598, 245: 0x2599, 165: 0x259a,
                95: 0x259b, 175: 0x259c, 10: 0x259d,
                90: 0x259e, 250: 0x259f})
    assert set(out) == set(range(256)), sorted(set(range(256)) - out.keys())
    return out


def exactness(weights=None, library=None):
    weights = weights or ROOT / 'weights/neuronte-video-masks-v0.nrt'
    rows = []
    with NeuralMasks(weights, library) as net:
        for bits, cp in sorted(octant_characters().items()):
            expected = np.array([bits >> k & 1 for k in range(8)]).reshape(4, 2)
            actual = net.mask(cp, 2, 4)
            rows.append(dict(scalar=f'U+{cp:04X}', bits=bits,
                             max_error=float(np.max(np.abs(expected - actual))),
                             exact=bool(np.array_equal(expected, actual))))
    return dict(patterns=256, points=2048, exact=all(x['exact'] for x in rows),
                max_error=max(x['max_error'] for x in rows), results=rows)


def patches(frame, width, height):
    frame = np.asarray(frame)
    if frame.dtype != np.uint8 or frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError('frame must be HxWx3 uint8 RGB')
    h, w = frame.shape[:2]
    if w % width or h % height:
        raise ValueError('frame dimensions must be multiples of cell dimensions')
    return frame.reshape(h // height, height, w // width, width, 3).transpose(0, 2, 1, 3, 4)


def unpatch(p):
    rows, cols, h, w, _ = p.shape
    return p.transpose(0, 2, 1, 3, 4).reshape(rows * h, cols * w, 3)


class MultiInk:
    planes = (0x2590, 0x1cd33, 0x2584)
    row_labels = (0, 1, 3, 2)

    def __init__(self, weights=None, library=None, cell_w=2, cell_h=4):
        if cell_w < 2 or cell_h < 4 or cell_w % 2 or cell_h % 4:
            raise ValueError('multi-ink cells require width divisible by 2, height by 4')
        self.width, self.height = cell_w, cell_h
        weights = weights or ROOT / 'weights/neuronte-video-masks-v0.nrt'
        with NeuralMasks(weights, library) as net:
            masks = np.stack([net.mask(cp, cell_w, cell_h) for cp in self.planes])
        self.mix = np.stack([np.prod(np.stack([masks[b] if k >> b & 1 else 1 - masks[b] for b in range(3)]), axis=0) for k in range(8)])

    def encode(self, rgb):
        p = patches(rgb, self.width, self.height)
        rows, cols = p.shape[:2]
        means = p.reshape(rows, cols, 4, self.height // 4, 2, self.width // 2, 3).mean(axis=(3, 5))
        out = np.empty((rows, cols, 8, 3), np.uint8)
        for y, label in enumerate(self.row_labels):
            out[:, :, label * 2:label * 2 + 2] = np.rint(means[:, :, y]).astype(np.uint8)
        return out

    def decode(self, colours):
        colours = np.asarray(colours)
        if colours.dtype != np.uint8 or colours.ndim != 4 or colours.shape[2:] != (8, 3):
            raise ValueError('colours must be rows x columns x 8 x 3 uint8')
        p = np.einsum('rckd,khw->rchwd', colours.astype(np.float32), self.mix, optimize=True)
        return np.clip(np.rint(unpatch(p)), 0, 255).astype(np.uint8)


def candidates(mode, width, height, weights=None, library=None):
    if mode == 'portable':
        entries = [(' ', 'block', [])] + glyphs.charset('pixel')
        # Ideal binary geometry at pixel centres; no font dependency.
        yy, xx = np.mgrid[:height, :width]
        points = np.stack([(xx.ravel() + .5) / width, (yy.ravel() + .5) * 2 / height], -1)
        masks = np.stack([(glyphs.signed_distance(shape, points, .075) > 0).astype(np.float32) for _, _, shape in entries])
        return np.array([ord(ch) for ch, _, _ in entries], np.uint32), masks
    if mode != 'full': raise ValueError('mode must be portable or full')
    # Read the actual trained scalar lists, rather than current drawing sets.
    paths = ['ascii-v0', 'draw-v2', 'symbol-v0', 'accent-v1', 'pixel-v1', 'braille-v0']
    cps = set()
    for name in paths:
        doc = json.loads((ROOT / f'weights/neuronte-{name}.json').read_text())
        for span in doc['training']['labelled'].split():
            ends = span.split('..')
            low, high = int(ends[0][2:], 16), int(ends[-1][2:], 16)
            cps.update(range(low, high + 1))
    cps = np.array(sorted(cps), np.uint32)
    with NeuralMasks(weights, library) as net:
        masks = np.stack([net.mask(int(cp), width, height).ravel() for cp in cps])
    return cps, masks


class TwoInk:
    def __init__(self, mode='portable', cell_w=8, cell_h=16, weights=None, library=None, margin=0):
        if cell_w < 1 or cell_h < 1 or margin < 0: raise ValueError('invalid cell size or margin')
        self.width, self.height, self.margin = cell_w, cell_h, margin
        self.scalars, self.masks = candidates(mode, cell_w, cell_h, weights, library)
        self.masks = self.masks.astype(np.float64)
        self.previous = None

    def fit(self, rgb):
        p = patches(rgb, self.width, self.height)
        grid = p.shape[:2]
        x = p.reshape(-1, self.width * self.height, 3).astype(np.float64)
        m = self.masks
        # Design matrix [1-m, m]. Each channel's box-constrained quadratic
        # optimum is either interior or on one of the four box edges.
        a = ((1-m)**2).sum(1)[None, :, None]
        b = (m*(1-m)).sum(1)[None, :, None]
        d = (m*m).sum(1)[None, :, None]
        det = a*d-b*b
        ids, colours, losses = [], [], []
        for start in range(0, len(x), 64):
            chunk = x[start:start+64]
            v = np.einsum('kp,bpc->bkc', m, chunk, optimize=True)
            u = chunk.sum(1)[:, None, :] - v
            energy = (chunk*chunk).sum(1)[:, None, :]
            def divide(n, den): return np.divide(n, den, out=np.zeros_like(n), where=den > 1e-12)
            bg, fg = divide(d*u-b*v, det), divide(a*v-b*u, det)
            choices = [(bg, fg, (bg>=0)&(bg<=255)&(fg>=0)&(fg<=255)&(det>1e-12))]
            for bound in (0., 255.):
                choices += [(np.full_like(u,bound), np.clip(divide(v-b*bound,d),0,255), True),
                            (np.clip(divide(u-b*bound,a),0,255), np.full_like(v,bound), True)]
            best = np.full_like(u, np.inf); cb = np.zeros_like(u); cf = np.zeros_like(v)
            for bg, fg, valid in choices:
                loss = np.where(valid, energy+a*bg*bg+2*b*bg*fg+d*fg*fg-2*u*bg-2*v*fg, np.inf)
                take = loss < best
                best = np.where(take,loss,best); cb = np.where(take,bg,cb); cf = np.where(take,fg,cf)
            total = best.sum(2)
            choice = total.argmin(1)
            ix = np.arange(len(chunk))
            if self.previous is not None and self.previous.shape == grid:
                old = self.previous.ravel()[start:start+len(chunk)]
                choice = np.where(total[ix,old] <= total[ix,choice] + self.margin * self.width*self.height*3, old, choice)
            ids.extend(choice); colours.extend(np.stack([cb[ix,choice],cf[ix,choice]],1)); losses.extend(total[ix,choice])
        idx = np.array(ids).reshape(grid)
        self.previous = idx.copy()
        return dict(indices=idx, colours=np.clip(np.rint(colours),0,255).astype(np.uint8).reshape(*grid,2,3),
                    sse=np.maximum(losses,0).reshape(grid))

    def decode(self, cells):
        masks = self.masks[cells['indices']].reshape(*cells['indices'].shape,self.height,self.width,1)
        c = cells['colours'].astype(np.float64)
        pixels = c[:,:,0,None,None,:]*(1-masks)+c[:,:,1,None,None,:]*masks
        return np.clip(np.rint(unpatch(pixels)),0,255).astype(np.uint8)

    def ansi(self, cells, previous=None):
        out = []
        for y,x in np.ndindex(cells['indices'].shape):
            i = cells['indices'][y,x]; c = cells['colours'][y,x]
            if previous is not None and i == previous['indices'][y,x] and np.array_equal(c,previous['colours'][y,x]): continue
            bg,fg = c
            out.append(f'\x1b[{y+1};{x+1}H\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m'+chr(int(self.scalars[i])))
        return ''.join(out)+'\x1b[0m'
