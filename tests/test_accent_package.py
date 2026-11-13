"""Check appended accent members leave original fallback semantics intact."""
import ctypes as ct
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'train'), str(ROOT / 'tests')]
import decompose as d
import pack
import strokes


def fixture(width, seed, labelled):
    rng = np.random.default_rng(seed)
    return {'format': 'neuronte-weights', 'version': 1,
            'shape': {'position_octaves': 6, 'code_bits': 64, 'hidden_layers': 3,
                      'hidden_width': width, 'tau': .15,
                      'parity_masks': [hex(m) for m in strokes.masks()]},
            'training': {'set': 'accent-test', 'labelled': labelled},
            'layers': {name: {'rows': rows, 'cols': cols,
                             'weight': rng.normal(0, .1, rows * cols).tolist(),
                             'bias': rng.normal(0, .1, rows).tolist()}
                       for name, rows, cols in pack.layers(width)}}

spec = importlib.util.spec_from_file_location('accent_pack', ROOT / 'tools/pack-accent-experiment.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PackageTests(unittest.TestCase):
    def test_preserved_experts_and_unknown_routes(self):
        lib = ct.CDLL(str(ROOT / 'build/libneuronte.so'))
        lib.neuronte_open_file.argtypes = [ct.c_char_p, ct.POINTER(ct.c_void_p)]
        lib.neuronte_close.argtypes = [ct.c_void_p]
        lib.neuronte_route.argtypes = [ct.c_void_p, ct.c_uint32]
        lib.neuronte_coverage.argtypes = [ct.c_void_p, ct.c_uint32, ct.c_int, ct.c_int, ct.c_int, ct.c_void_p]
        baseline = ct.c_void_p()
        self.assertEqual(lib.neuronte_open_file(str(ROOT / 'weights/neuronte-split-v5.nrt').encode(), ct.byref(baseline)), 0)
        accent = set(pack.scalars(ROOT / 'weights/neuronte-accent-v2.json')[1])
        known = set().union(*(pack.scalars(ROOT / 'weights' / ('neuronte-' + n + '.json'))[1] for n in p.ORIGINALS))
        unknown = [c for c in range(0, 0x110000, 101) if c not in known and not 0xd800 <= c <= 0xdfff]
        try:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for mode, parts in (('spatial', 4), ('repertoire', 4), ('repertoire', 3)):
                    destination = root / f'{mode}{parts}'
                    members = d.specs(mode, parts, 'accent', 16)
                    for s in members:
                        doc = fixture(s['width'], s['index'], labelled=' '.join(f'U+{c:04X}' for c in s['scalars']))
                        doc['shape']['tau'] = .15 / (s['region'][1] - s['region'][0])
                        doc['training'].update(steps=1, unlabelled_weight=1.)
                        doc['training']['experiment'] = {**s, 'seed': 0, 'identity': {
                            'teacher': {'identity': {'scalars': sorted(accent)}},
                            'steps': 1, 'unlabelled_weight': 1., 'trainer_sha256': 'test-fixture'}}
                        (root / (s['name'] + '-s0.json')).write_text(json.dumps(doc))
                    report = p.build(root, destination, mode, parts, 0, 16)
                    handle = ct.c_void_p()
                    self.assertEqual(lib.neuronte_open_file(str(destination / report['file']).encode(), ct.byref(handle)), 0)
                    try:
                        for scalar, expected in zip(report['corpus'], report['routes']):
                            self.assertEqual(lib.neuronte_route(handle, scalar), expected)
                        for scalar in sorted(known - accent) + unknown:
                            self.assertEqual(lib.neuronte_route(handle, scalar), lib.neuronte_route(baseline, scalar))
                        # Every unaffected label and a spread of gate-selected misses.
                        for scalar in sorted(known - accent) + unknown[::97]:
                            old, new = np.empty((2, 1), np.float32), np.empty((2, 1), np.float32)
                            self.assertEqual(lib.neuronte_coverage(baseline, scalar, 1, 2, 0, old.ctypes.data), 0)
                            self.assertEqual(lib.neuronte_coverage(handle, scalar, 1, 2, 0, new.ctypes.data), 0)
                            np.testing.assert_array_equal(old, new)
                    finally:
                        lib.neuronte_close(handle)
                    source = root / (members[-1]['name'] + '-s0.json')
                    changed = json.loads(source.read_text())
                    changed['training']['unlabelled_weight'] = 0.
                    source.write_text(json.dumps(changed))
                    with self.assertRaisesRegex(ValueError, 'differs from its identity'):
                        p.build(root, destination, mode, parts, 0, 16)
                    changed['training']['experiment']['identity']['unlabelled_weight'] = 0.
                    source.write_text(json.dumps(changed))
                    with self.assertRaisesRegex(ValueError, 'different training recipes'):
                        p.build(root, destination, mode, parts, 0, 16)
        finally:
            lib.neuronte_close(baseline)


if __name__ == '__main__':
    unittest.main()
