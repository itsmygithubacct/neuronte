"""Check every accent glyph's native cold/warm draw against coverage.

Run under the target host's benchmark lock. This checks API/cache composition,
not teacher quality: a poor model can pass this check and fail accent-quality.
"""
import argparse
import ctypes as ct
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library', type=Path, required=True)
    p.add_argument('--package', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--sizes', default='1x2,3x5,7x13,8x16,16x32,23x47,24x48,25x49,33x61,48x96')
    p.add_argument('--samples', default='0,1,3', help='comma-separated sample counts; 0 is automatic')
    a = p.parse_args()
    try:
        sample_counts = [int(x) for x in a.samples.split(',')]
        if len(set(sample_counts)) != len(sample_counts) or any(x not in range(9) for x in sample_counts):
            raise ValueError()
    except ValueError:
        p.error('samples must be distinct integers from 0 through 8')
    package = json.loads((a.package / 'package.json').read_text())
    model = a.package / package['file']
    assert hashlib.sha256(model.read_bytes()).hexdigest() == package['sha256']
    lib = ct.CDLL(str(a.library.resolve()))
    lib.neuronte_open_file.argtypes = [ct.c_char_p, ct.POINTER(ct.c_void_p)]
    lib.neuronte_close.argtypes = [ct.c_void_p]
    lib.neuronte_route.argtypes = [ct.c_void_p, ct.c_uint32]
    lib.neuronte_set_samples.argtypes = [ct.c_void_p, ct.c_int]
    lib.neuronte_coverage.argtypes = [ct.c_void_p, ct.c_uint32, ct.c_int, ct.c_int, ct.c_int, ct.c_void_p]
    lib.neuronte_draw_scalar.argtypes = [ct.c_void_p, ct.c_void_p] + [ct.c_int] * 7 + [ct.c_uint32] * 2
    rows = []
    for size in a.sizes.split(','):
        w, h = map(int, size.split('x'))
        for samples in sample_counts:
            handle = ct.c_void_p()
            assert lib.neuronte_open_file(str(model.resolve()).encode(), ct.byref(handle)) == 0
            expected = []
            digest = hashlib.sha256()
            try:
                assert lib.neuronte_set_samples(handle, samples) == 0
                for scalar, route in zip(package['corpus'], package['routes']):
                    assert lib.neuronte_route(handle, scalar) == route
                    coverage = np.empty((h, w), np.float32)
                    assert lib.neuronte_coverage(handle, scalar, w, h, samples, coverage.ctypes.data) == 0
                    assert np.isfinite(coverage).all() and coverage.min() >= 0 and coverage.max() <= 1
                    alpha = (coverage * np.float32(255) + np.float32(.5)).astype(np.uint32)
                    pixels = np.where(coverage > 0, (alpha << 24) | 0xffffff, 0).astype(np.uint32)
                    expected.append(pixels)
                    digest.update(coverage.tobytes())
                # The first full repertoire starts with an empty draw cache;
                # the second full repertoire reuses all 318 complete glyphs.
                for phase in ('cold', 'warm'):
                    for scalar, pixels in zip(package['corpus'], expected):
                        drawn = np.zeros((h, w), np.uint32)
                        assert lib.neuronte_draw_scalar(handle, drawn.ctypes.data, w, w, h,
                                                       0, 0, w, h, scalar, 0xffffffff) == 0
                        np.testing.assert_array_equal(drawn, pixels,
                                                      err_msg=f'{phase} U+{scalar:04X} {size} S{samples}')
            finally:
                lib.neuronte_close(handle)
            row = {'size': size, 'samples': samples, 'glyphs': len(expected),
                   'coverage_calls': len(expected), 'cold_draw_calls': len(expected),
                   'warm_draw_calls': len(expected), 'coverage_sha256': digest.hexdigest()}
            rows.append(row)
            print(json.dumps(row), flush=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({'passed': True, 'model_sha256': package['sha256'],
                                'library_sha256': hashlib.sha256(a.library.read_bytes()).hexdigest(),
                                'checks': rows}, indent=2) + '\n')


if __name__ == '__main__':
    main()
