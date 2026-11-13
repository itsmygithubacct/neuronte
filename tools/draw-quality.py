"""Measure box-drawing coverage quality through the native library.

usage: python3 tools/draw-quality.py TEACHER_DIR OUT_DIR [--lib build/libneuronte.so]
           [--sizes 8x16,16x32,48x96] [--samples 0] (--bundle FILE.nrt | MEMBER.json...)

TEACHER_DIR is made by `train/draw_split.py prepare`. With --bundle every
scalar is drawn by neuronte_coverage() on that file, which routes it.
Otherwise each MEMBER.json is packed to a standalone .nrt in OUT_DIR and a
glyph is assembled from every member trained on its scalar: a repertoire
member draws its scalars whole, a spatial member (training.experiment.region)
draws its region with the full cell's samples per axis. Spatial assembly
needs the region edges to fall on pixel edges; other sizes are refused.

Teacher coverage is the fraction of 8 x 8 samples per pixel inside the ink,
read bilinearly from the FP16 teacher grid as the trainer reads it.
Per size and glyph: binary exactness (coverage > 1/2), firm wrong pixels
(teacher at least 0.1 from 1/2), MAE, IoU, nearest identity, the error on
the cell's outer rows/columns (where neighbouring cells join), the error of
the summed coverage across eight cross-sections (stroke thickness in
pixels: edge, quarter and three-quarter rows and columns) and the MAE in the
junction region around the centre. Seams: for every pair of glyphs whose
arms meet across a shared cell edge with the same weight (light, heavy,
double; arcs count as light), the largest difference between the first
glyph's last column (row) and the second's first, the step a line takes
where two cells join. GEOMETRY in --sizes expands to odd, anisotropic and
sampling-boundary (23/24/25 px wide) cells. Coverage arrays can be kept.
MIT licence; see LICENSE.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'train'))
import decompose  # noqa: E402
import pack  # noqa: E402


GEOMETRY = ('3x6,4x8,5x10,6x12,7x13,7x15,9x18,10x20,11x23,12x24,13x27,15x31,17x35,20x40,'
            '23x46,23x47,24x47,24x48,25x49,25x50,31x63,33x61,40x80,64x128,16x48,16x24,12x30,30x40')


def arms(scalar):
    """{side: weight} where the glyph's strokes cross the cell edge: 1 light, 2 heavy, 3 double."""
    import unicodedata
    import glyphs
    if not 0x2500 <= scalar <= 0x257F:
        return {}
    words = unicodedata.name(chr(scalar)).split()[2:]
    if 'DASH' in words or 'DIAGONAL' in words:
        return {}
    if 'ARC' in words:
        return {words[2].lower(): 1, words[4].lower(): 1}
    return glyphs.arms_of(words)


def seams(n, scalars):
    """Largest edge-profile step between arm-matched neighbours, per weight and direction."""
    out = {}
    index = {s: i for i, s in enumerate(scalars)}
    arm = {s: arms(s) for s in scalars}
    for first, second, axis in (('right', 'left', 'h'), ('down', 'up', 'v')):
        for kind in (1, 2, 3):
            a = [index[s] for s in scalars if arm[s].get(first) == kind]
            b = [index[s] for s in scalars if arm[s].get(second) == kind]
            if not a or not b:
                continue
            pa = n[a][:, :, -1] if axis == 'h' else n[a][:, -1, :]
            pb = n[b][:, :, 0] if axis == 'h' else n[b][:, 0, :]
            step = np.abs(pa[:, None]-pb[None]).max(-1)
            i, j = np.unravel_index(step.argmax(), step.shape)
            out[f'{axis}{kind}'] = {'max': float(step.max()), 'mean': float(step.mean()), 'pairs': int(step.size),
                                    'worst': [f'U+{scalars[a[i]]:04X}', f'U+{scalars[b[j]]:04X}']}
    return out


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Lib:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.c = ctypes.CDLL(str(self.path))
        self.c.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
        self.c.neuronte_close.argtypes = [ctypes.c_void_p]
        self.c.neuronte_route.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        self.c.neuronte_coverage.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int,
                                             ctypes.c_int, ctypes.POINTER(ctypes.c_float)]

    def open(self, path):
        h = ctypes.c_void_p()
        rc = self.c.neuronte_open_file(str(path).encode(), ctypes.byref(h))
        if rc != 0:
            raise SystemExit(f'{path}: neuronte_open_file returned {rc}')
        return h

    def coverage(self, h, scalar, w, hh, samples):
        out = np.zeros(w*hh, np.float32)
        rc = self.c.neuronte_coverage(h, scalar, w, hh, samples, out.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
        if rc != 0:
            raise SystemExit(f'coverage U+{scalar:04X} {w}x{hh}: {rc}')
        return out.reshape(hh, w)


def auto_samples(w):
    return 2 if w < 24 else 1


def members_of(paths, out_dir, lib):
    out = []
    for path in paths:
        doc = json.loads(Path(path).read_text())
        exp = doc['training'].get('experiment', {})
        nrt = out_dir/'packed'/(Path(path).stem+'.nrt')
        nrt.parent.mkdir(parents=True, exist_ok=True)
        image = pack.pack(str(path))
        nrt.write_bytes(image)
        out.append({'json': str(Path(path).resolve()), 'json_sha256': digest(Path(path).read_bytes()),
                    'nrt': str(nrt), 'nrt_sha256': digest(image), 'width': doc['shape']['hidden_width'],
                    'region': exp.get('region', [0., 1., 0., 2.]), 'scalars': sorted(pack.scalars(str(path))[1]),
                    'handle': lib.open(nrt)})
    return out


def render(lib, members, bundle, scalar, w, h, samples):
    s = samples or auto_samples(w)
    if bundle is not None:
        return lib.coverage(bundle, scalar, w, h, samples)
    cov = np.full((h, w), np.nan, np.float32)
    for m in members:
        if scalar not in m['scalars']:
            continue
        x0, x1, y0, y1 = m['region']
        px = [x0*w, x1*w]
        py = [y0/2*h, y1/2*h]
        if any(abs(v-round(v)) > 1e-9 for v in px+py):
            raise SystemExit(f'region {m["region"]} does not fall on pixel edges at {w}x{h}')
        px, py = [int(round(v)) for v in px], [int(round(v)) for v in py]
        cov[py[0]:py[1], px[0]:px[1]] = lib.coverage(m['handle'], scalar, px[1]-px[0], py[1]-py[0], s)
    if np.isnan(cov).any():
        raise SystemExit(f'U+{scalar:04X}: members do not cover the cell')
    return cov


def sections(w, h):
    cols = sorted({0, w//4, w-1-w//4, w-1})
    rows = sorted({0, h//4, h-1-h//4, h-1})
    return cols, rows


def metrics(t, n, scalars):
    g, h, w = t.shape
    err = np.abs(n-t)
    ti, ni = t > .5, n > .5
    wrong = ti != ni
    firm = wrong & (np.abs(t-.5) >= .1)
    union = (ti | ni).sum((1, 2))
    iou = np.where(union > 0, (ti & ni).sum((1, 2))/np.maximum(union, 1), 1.)
    tf, nf = t.reshape(g, -1).astype(np.float64), n.reshape(g, -1).astype(np.float64)
    dist = np.abs(nf[:, None]-tf[None]).sum(-1)
    twin = np.abs(tf[:, None]-tf[None]).sum(-1) < .5
    nearest = dist.argmin(1)
    near_ok = twin[np.arange(g), nearest]
    edge = np.zeros((h, w), bool)
    edge[0], edge[-1], edge[:, 0], edge[:, -1] = True, True, True, True
    cols, rows = sections(w, h)
    thick = np.concatenate([n[:, :, cols].sum(1)-t[:, :, cols].sum(1), n[:, rows, :].sum(2)-t[:, rows, :].sum(2)], 1)
    jy = slice(h//4, h-h//4)
    jx = slice(w//4, w-w//4)
    per = []
    for i, s in enumerate(scalars):
        per.append({'scalar': f'U+{s:04X}', 'exact': bool(not wrong[i].any()), 'wrong': int(wrong[i].sum()),
                     'firm_wrong': int(firm[i].sum()), 'mae': float(err[i].mean()), 'max_error': float(err[i].max()),
                     'iou': float(iou[i]), 'nearest_ok': bool(near_ok[i]),
                     'nearest': f'U+{scalars[nearest[i]]:04X}',
                     'edge_mae': float(err[i][edge].mean()), 'edge_max': float(err[i][edge].max()),
                     'edge_firm_wrong': int((firm[i] & edge).sum()),
                     'thickness_max_px': float(np.abs(thick[i]).max()),
                     'junction_mae': float(err[i][jy, jx].mean())})
    return {'glyphs': len(scalars), 'exact': int((~wrong.any((1, 2))).sum()), 'wrong_pixels': int(wrong.sum()),
            'firm_exact': int((~firm.any((1, 2))).sum()), 'firm_wrong_pixels': int(firm.sum()),
            'firm_fraction': float(firm.mean()), 'nearest_ok': int(near_ok.sum()),
            'mae': float(err.mean()), 'p99': float(np.quantile(err, .99)), 'max_error': float(err.max()),
            'iou_mean': float(iou.mean()), 'iou_min': float(iou.min()),
            'edge_mae': float(err[:, edge].mean()), 'edge_firm_wrong': int((firm & edge).sum()),
            'thickness_max_px': float(np.abs(thick).max()), 'thickness_mean_px': float(np.abs(thick).mean()),
            'junction_mae': float(err[:, jy, jx].mean()),
            'seams': seams(n, scalars), 'teacher_seams': seams(t, scalars),
            'seam_max': max(v['max'] for v in seams(n, scalars).values()),
            'worst_mae': sorted(per, key=lambda r: -r['mae'])[:5], 'per_glyph': per}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('teacher', type=Path)
    p.add_argument('out', type=Path)
    p.add_argument('members', nargs='*')
    p.add_argument('--bundle', type=Path)
    p.add_argument('--lib', default=str(ROOT/'build'/'libneuronte.so'))
    p.add_argument('--sizes', default='8x16,16x32,48x96')
    p.add_argument('--samples', type=int, default=0)
    p.add_argument('--keep', action='store_true', help='write coverage arrays (npz) per size')
    a = p.parse_args()
    if bool(a.members) == bool(a.bundle):
        p.error('give member JSON files or --bundle, not both')
    meta = json.loads((a.teacher/'teacher.json').read_text())
    if digest((a.teacher/'teacher.npy').read_bytes()) != meta['sha256']:
        raise SystemExit('teacher SHA256 differs')
    fields = np.load(a.teacher/'teacher.npy', allow_pickle=False)
    scalars = meta['identity']['scalars']
    lib = Lib(a.lib)
    a.out.mkdir(parents=True, exist_ok=True)
    members, bundle = [], None
    if a.bundle:
        bundle = lib.open(a.bundle)
    else:
        members = members_of(a.members, a.out, lib)
    result = {'schema': 'neuronte.draw-quality/v1', 'teacher_sha256': meta['sha256'],
              'library': str(lib.path), 'library_sha256': digest(lib.path.read_bytes()), 'samples': a.samples,
              'bundle': None if bundle is None else {'path': str(a.bundle.resolve()), 'sha256': digest(a.bundle.read_bytes())},
              'members': [{k: v for k, v in m.items() if k not in ('handle', 'scalars')} | {'scalars': len(m['scalars'])}
                          for m in members], 'sizes': {}}
    for size in a.sizes.replace('GEOMETRY', GEOMETRY).split(','):
        w, h = map(int, size.split('x'))
        t = decompose.teacher_masks(fields, w, h)
        n = np.stack([render(lib, members, bundle, s, w, h, a.samples) for s in scalars])
        r = metrics(t, n, scalars)
        r['coverage_sha256'] = digest(np.ascontiguousarray(n, '<f4').tobytes())
        r['teacher_sha256'] = digest(np.ascontiguousarray(t, '<f4').tobytes())
        r['samples_per_axis'] = a.samples or auto_samples(w)
        result['sizes'][size] = r
        if a.keep:
            np.savez_compressed(a.out/f'coverage-{size}.npz', net=n, teacher=t)
        print(f"{size}: exact {r['exact']} firm_exact {r['firm_exact']} firm_px {r['firm_wrong_pixels']} "
              f"nearest {r['nearest_ok']}/{len(scalars)} mae {r['mae']:.6f} p99 {r['p99']:.4f} "
              f"edge_firm {r['edge_firm_wrong']} seam {r['seam_max']:.4f} thick {r['thickness_max_px']:.3f}px junction {r['junction_mae']:.5f}",
              flush=True)
    (a.out/'quality.json').write_text(json.dumps(result, indent=1)+'\n')


if __name__ == '__main__':
    main()
