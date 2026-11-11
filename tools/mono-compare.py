"""Compare packed mono networks against the same current source targets.

The default measures the baseline's labelled scalars. --include-new also
measures new labels, recording each tier separately. Counts and per-glyph
deltas remain in the report so a mean cannot hide individual regressions.
"""
import argparse
import ctypes as ct
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'train'), str(ROOT / 'tests')]
import glyphs
import pack
from check_icon_quality import interpolate, sample_points, counts


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library', required=True)
    p.add_argument('--baseline', required=True)
    p.add_argument('--candidate', required=True)
    p.add_argument('--other-seed', required=True)
    p.add_argument('--set', choices=('accent', 'full'), default='accent')
    p.add_argument('--include-new', action='store_true')
    p.add_argument('--sizes', default='8,16,48')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    lib = ct.CDLL(str(Path(a.library).resolve()))
    P, I, U = ct.c_void_p, ct.c_int, ct.c_uint32
    lib.neuronte_open_file.argtypes = [ct.c_char_p, ct.POINTER(P)]
    lib.neuronte_close.argtypes = [P]
    lib.neuronte_coverage.argtypes = [P, U, I, I, I, P]
    inputs = {'old': a.baseline, 'new': a.candidate, 'seed1': a.other_seed}
    images = {name: pack.pack(path) for name, path in inputs.items()}
    known = pack.scalars(a.baseline)[1]
    chars = [(c, tier, sh) for c, tier, sh in glyphs.charset(a.set)
             if a.include_new or ord(c) in known]
    points = {int(w): sample_points(int(w)) for w in a.sizes.split(',')}
    rows = {str(w): [] for w in points}
    with tempfile.TemporaryDirectory(prefix='neuronte-compare-') as temp:
        handles = {}
        try:
            for name, data in images.items():
                path = Path(temp) / (name + '.nrt')
                path.write_bytes(data)
                h = P()
                assert lib.neuronte_open_file(str(path).encode(), ct.byref(h)) == 0
                handles[name] = h
            for c, tier, shape in chars:
                field = glyphs.field(shape, 256, .075, .15).astype(np.float16).astype(np.float32)
                for w in points:
                    values = interpolate(field, points[w], 256)
                    truth = (values > 0).reshape(2*w, 8, w, 8).mean((1, 3)) > .5
                    row = {'scalar': f'U+{ord(c):04X}', 'tier': tier,
                           'baseline_trained': ord(c) in known}
                    for name, h in handles.items():
                        cov = np.zeros((2*w, w), np.float32)
                        assert lib.neuronte_coverage(h, ord(c), w, 2*w, 2, cov.ctypes.data) == 0
                        row[name] = counts(truth, cov > .5)
                    row['delta'] = row['new']['iou'] - row['old']['iou']
                    rows[str(w)].append(row)
        finally:
            for h in handles.values():
                lib.neuronte_close(h)
    sizes = {}
    for w, rs in rows.items():
        sizes[w] = {name+'_mean': float(np.mean([r[name]['iou'] for r in rs]))
                    for name in inputs}
        sizes[w]['regressions'] = [r for r in rs if r['delta'] < -1e-12]
        sizes[w]['glyphs'] = rs
    report = {'characters': len(chars), 'samples': 2, 'target_grid': 256,
              'target_samples': 8, 'set': a.set, 'include_new': a.include_new,
              'sources_sha256': {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
                                 for f in glyphs.sources(a.set)},
              'weights_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in images.items()},
              'sizes': sizes}
    Path(a.out).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({w: {k: v for k, v in r.items() if k not in ('glyphs', 'regressions')}
                     | {'regressed_glyphs': len(r['regressions'])} for w, r in sizes.items()}, indent=2))


if __name__ == '__main__':
    main()
