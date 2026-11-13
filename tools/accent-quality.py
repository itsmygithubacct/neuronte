"""Score all accent labels through the public native coverage API.

Teacher ties count as compatible identities, with tie counts retained. Output
includes raw coverage and per-script/per-glyph baseline-relative decisions.
Use an external host-wide lock around the entire command when benchmarking.
"""
import argparse
import ctypes as ct
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'train'))
from decompose import teacher_masks, digest


def script(c):
    return 'latin' if c < 0x370 else 'greek' if c < 0x400 else 'russian'


def metrics(actual, truth, scalars):
    error = np.abs(actual - truth)
    a, t = actual > .5, truth > .5
    intersection = (a & t).sum((1, 2))
    union = (a | t).sum((1, 2))
    iou = np.divide(intersection, union, out=np.ones(len(union)), where=union != 0)
    firm = np.abs(truth - .5) > .1
    wrong = (a != t) & firm
    # Bound memory without changing the full-repertoire nearest search.
    distances = np.stack([np.abs(truth - cell).mean((1, 2)) for cell in actual])
    best = distances.min(1)
    own = np.diag(distances)
    compatible = own <= best + 1e-7
    ties = (np.abs(distances - best[:, None]) <= 1e-7).sum(1)
    glyphs = []
    for i, c in enumerate(scalars):
        glyphs.append({'scalar': c, 'script': script(c), 'mae': float(error[i].mean()),
                       'iou': float(iou[i]), 'firm_wrong': int(wrong[i].sum()),
                       'binary_exact': bool((a[i] == t[i]).all()),
                       'lost': bool(t[i].any() and not (a[i] & t[i]).any()),
                       'nearest_compatible': bool(compatible[i]), 'nearest_ties': int(ties[i]),
                       'nearest_scalar': int(scalars[distances[i].argmin()]),
                       'own_distance': float(own[i]), 'best_distance': float(best[i])})
    groups = {}
    for name in ('all', 'latin', 'greek', 'russian'):
        idx = np.array([i for i, c in enumerate(scalars) if name == 'all' or script(c) == name])
        groups[name] = {'count': len(idx), 'mae': float(error[idx].mean()),
                       'p99': float(np.quantile(error[idx], .99)),
                       'firm_error_fraction': float(wrong[idx].mean()),
                       'firm_wrong': int(wrong[idx].sum()), 'mean_iou': float(iou[idx].mean()),
                       'nearest_compatible': int(compatible[idx].sum()),
                       'ambiguous_nearest': int((ties[idx] > 1).sum()),
                       'binary_exact': sum(glyphs[i]['binary_exact'] for i in idx),
                       'lost': sum(glyphs[i]['lost'] for i in idx)}
    return {'groups': groups, 'glyphs': glyphs}


def gate(current, baseline):
    failures = []
    for name in ('latin', 'greek', 'russian'):
        c, b = current['groups'][name], baseline['groups'][name]
        for key, allowance in (('mae', .0015), ('p99', .02), ('firm_error_fraction', .0005)):
            if c[key] > b[key] + allowance + 1e-9:
                failures.append(f'{name}:{key}')
        if c['mean_iou'] < b['mean_iou'] - .005 - 1e-9:
            failures.append(f'{name}:mean_iou')
    for c, b in zip(current['glyphs'], baseline['glyphs']):
        if c['scalar'] != b['scalar']:
            raise ValueError('baseline scalar order differs')
        prefix = f"U+{c['scalar']:04X}:"
        if c['mae'] > b['mae'] + .01 + 1e-9:
            failures.append(prefix + 'mae')
        if c['iou'] < b['iou'] - .05 - 1e-9:
            failures.append(prefix + 'iou')
        if c['lost'] and not b['lost']:
            failures.append(prefix + 'lost')
        if b['nearest_compatible'] and not c['nearest_compatible']:
            failures.append(prefix + 'nearest')
    return failures


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library', type=Path, required=True)
    p.add_argument('--model', type=Path, required=True)
    p.add_argument('--teacher', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--baseline', type=Path)
    p.add_argument('--sizes', default='8x16,16x32,48x96')
    p.add_argument('--samples', type=int, choices=(0, 1, 2, 3), default=0,
                   help='0 is native automatic sampling; 1 matches the video consumer')
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    metadata = json.loads((a.teacher / 'teacher.json').read_text())
    if digest(a.teacher / 'teacher.npy') != metadata['sha256']:
        raise ValueError('teacher hash mismatch')
    scalars = metadata['identity']['scalars']
    if len(scalars) != 318 or len(set(scalars)) != 318:
        raise ValueError('expected full accent inventory')
    fields = np.load(a.teacher / 'teacher.npy', allow_pickle=False)
    sizes = [tuple(map(int, size.split('x'))) for size in a.sizes.split(',')]
    if not sizes or any(len(s) != 2 or min(s) < 1 for s in sizes) or len(set(sizes)) != len(sizes):
        raise ValueError('invalid geometry inventory')
    lib = ct.CDLL(str(a.library.resolve()))
    lib.neuronte_open_file.argtypes = [ct.c_char_p, ct.POINTER(ct.c_void_p)]
    lib.neuronte_close.argtypes = [ct.c_void_p]
    lib.neuronte_coverage.argtypes = [ct.c_void_p, ct.c_uint32, ct.c_int, ct.c_int, ct.c_int, ct.c_void_p]
    handle = ct.c_void_p()
    if lib.neuronte_open_file(str(a.model.resolve()).encode(), ct.byref(handle)):
        raise ValueError('native model open failed')
    baseline = json.loads(a.baseline.read_text()) if a.baseline else None
    if baseline and baseline['teacher'] != metadata:
        raise ValueError('baseline teacher differs')
    if baseline and (baseline['samples'] != a.samples or baseline.get('complete') is False):
        raise ValueError('baseline sampling differs or evaluation is incomplete')
    result = {'model_sha256': digest(a.model), 'library_sha256': digest(a.library),
              'teacher': metadata, 'samples': a.samples, 'sizes': {}, 'passed': True,
              'requested_sizes': [f'{w}x{h}' for w, h in sizes], 'complete': False,
              'baseline_sha256': digest(a.baseline) if a.baseline else None}
    try:
        for w, h in sizes:
            key = f'{w}x{h}'
            ref = metadata['targets'].get(key)
            if ref:
                if digest(a.teacher / ref['file']) != ref['sha256']:
                    raise ValueError('coverage reference hash mismatch')
                truth = np.load(a.teacher / ref['file'], allow_pickle=False)
            else:
                truth = teacher_masks(fields, w, h)
            coverage = np.empty((len(scalars), h, w), np.float32)
            for i, c in enumerate(scalars):
                if lib.neuronte_coverage(handle, c, w, h, a.samples, coverage[i].ctypes.data):
                    raise ValueError(f'coverage failed for {c}')
            if not np.isfinite(coverage).all() or coverage.min() < 0 or coverage.max() > 1:
                raise ValueError('invalid native coverage')
            path = a.out / f'coverage-{key}.npy'
            np.save(path, coverage, allow_pickle=False)
            row = metrics(coverage, truth, scalars)
            row.update(coverage_sha256=digest(path), calls=len(scalars))
            row['failures'] = gate(row, baseline['sizes'][key]) if baseline else []
            result['passed'] &= not row['failures']
            result['sizes'][key] = row
            (a.out / 'quality.json').write_text(json.dumps(result, indent=2) + '\n')
            print(json.dumps({'size': key, 'groups': row['groups'], 'failure_count': len(row['failures'])}), flush=True)
    finally:
        lib.neuronte_close(handle)
    result['complete'] = True
    (a.out / 'quality.json').write_text(json.dumps(result, indent=2) + '\n')
    # Quality failure is a retained experimental outcome, not a broken run.
    print(json.dumps({'complete': True, 'passed': result['passed']}), flush=True)


if __name__ == '__main__':
    main()
