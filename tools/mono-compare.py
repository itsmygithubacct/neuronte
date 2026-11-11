"""Compare packed mono networks against the same current source targets.

The default measures the baseline's labelled scalars. --include-new also
measures new labels, recording each tier separately. Counts and per-glyph
deltas remain in the report so a mean cannot hide individual regressions.
"""
import argparse
import ctypes as ct
import hashlib
import json
import math
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
    p.add_argument('--samples', type=int, choices=(0,1,2), default=2,
                   help='samples per axis; 0 exercises the production automatic choice')
    p.add_argument('--minimum-iou', type=float,
                   help='require both new seeds to pass every tier at 16 and 48 px')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    try:
        widths = tuple(int(w) for w in a.sizes.split(','))
    except ValueError:
        p.error('--sizes must be comma separated positive integers')
    if not widths or any(w <= 0 for w in widths) or len(set(widths)) != len(widths):
        p.error('--sizes must be distinct positive integers')
    if a.minimum_iou is not None:
        if not math.isfinite(a.minimum_iou) or not 0 <= a.minimum_iou <= 1:
            p.error('--minimum-iou must be finite and in [0, 1]')
        if not {16,48} <= set(widths):
            p.error('--minimum-iou requires both 16 and 48 in --sizes')
    lib = ct.CDLL(str(Path(a.library).resolve()))
    P, I, U = ct.c_void_p, ct.c_int, ct.c_uint32
    lib.neuronte_open_file.argtypes = [ct.c_char_p, ct.POINTER(P)]
    lib.neuronte_close.argtypes = [P]
    lib.neuronte_coverage.argtypes = [P, U, I, I, I, P]
    inputs = {'old': a.baseline, 'new': a.candidate, 'seed1': a.other_seed}
    documents = {name: json.loads(Path(path).read_text()) for name, path in inputs.items()}
    images = {name: pack.pack(path) for name, path in inputs.items()}
    known = pack.scalars(a.baseline)[1]
    chars = [(c, tier, sh) for c, tier, sh in glyphs.charset(a.set)
             if a.include_new or ord(c) in known]
    points = {w: sample_points(w) for w in widths}
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
                        assert lib.neuronte_coverage(h, ord(c), w, 2*w, a.samples, cov.ctypes.data) == 0
                        row[name] = counts(truth, cov > .5)
                    row['delta'] = row['new']['iou'] - row['old']['iou']
                    rows[str(w)].append(row)
        finally:
            for h in handles.values():
                lib.neuronte_close(h)
    sizes = {}
    passed = True
    for w, rs in rows.items():
        sizes[w] = {name+'_mean': float(np.mean([r[name]['iou'] for r in rs]))
                    for name in inputs}
        sizes[w]['regressions'] = [r for r in rs if r['delta'] < -1e-12]
        sizes[w]['glyphs'] = rs
        common = [r for r in rs if r['baseline_trained']]
        sizes[w]['common_labels'] = {'count': len(common),
            **{name+'_mean': float(np.mean([r[name]['iou'] for r in common])) for name in inputs},
            'regressions': [r for r in common if r['delta'] < -1e-12]}
        groups = {tier: [r for r in rs if r['tier'] == tier] for tier in sorted({r['tier'] for r in rs})}
        for name, lo, hi in (('greek',0x370,0x3ff), ('russian',0x400,0x4ff), ('latin',0,0x36f)):
            group = [r for r in rs if r['tier'] == 'accent' and lo <= int(r['scalar'][2:],16) <= hi]
            if group:
                groups[name] = group
        tiers = {}
        for name, group in groups.items():
            tiers[name] = {'count': len(group)}
            for seed in ('new','seed1'):
                tiers[name][seed] = {'mean': float(np.mean([r[seed]['iou'] for r in group])),
                    'minimum': min(r[seed]['iou'] for r in group),
                    'lost': sum(r[seed]['target_ink'] > 0 and r[seed]['intersection'] == 0 for r in group)}
                if a.minimum_iou is not None and int(w) in (16,48):
                    passed &= tiers[name][seed]['mean'] >= a.minimum_iou and tiers[name][seed]['lost'] == 0
        sizes[w]['tiers'] = tiers
    report = {'characters': len(chars), 'samples': a.samples, 'target_grid': 256,
              'target_samples': 8, 'set': a.set, 'include_new': a.include_new,
              'minimum_iou': a.minimum_iou, 'passed': bool(passed),
              'target': {'grid':256, 'pen_radius':.075, 'tau':.15,
                         'field_storage':'float16', 'subpixels_per_axis':8,
                         'coverage_cutoff':.5},
              'models': {name: {'shape': {k: v for k,v in d['shape'].items() if k != 'parity_masks'},
                                'training_target': {k: d['training'].get(k) for k in ('grid','pen_radius')}}
                         for name,d in documents.items()},
              'library_sha256': hashlib.sha256(Path(a.library).read_bytes()).hexdigest(),
              'sources_sha256': {f: hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
                                 for f in glyphs.sources(a.set)},
              'weights_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in images.items()},
              'sizes': sizes}
    Path(a.out).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({w: {k: v for k, v in r.items() if k not in ('glyphs', 'regressions','common_labels')}
                     | {'regressed_glyphs': len(r['regressions'])} for w, r in sizes.items()}, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
