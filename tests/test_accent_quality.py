"""Quality gates must retain teacher aliases and expose small-script failures."""
import copy
import importlib.util
from pathlib import Path
import unittest

import numpy as np

spec = importlib.util.spec_from_file_location('quality', Path(__file__).resolve().parents[1] / 'tools/accent-quality.py')
q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q)


class QualityTests(unittest.TestCase):
    def test_ties_and_lost_glyphs(self):
        truth = np.array([[[0., 1.]], [[0., 1.]], [[1., 0.]]], np.float32)
        scalars = [0xC0, 0x391, 0x410]
        exact = q.metrics(truth, truth, scalars)
        self.assertEqual(exact['groups']['all']['nearest_compatible'], 3)
        self.assertEqual(exact['groups']['all']['ambiguous_nearest'], 2)
        self.assertEqual(q.gate(exact, exact), [])
        broken = truth.copy()
        broken[2] = 0
        measured = q.metrics(broken, truth, scalars)
        failed = q.gate(measured, exact)
        self.assertIn('U+0410:lost', failed)
        self.assertIn('russian:mean_iou', failed)
        self.assertEqual(measured['groups']['latin'], exact['groups']['latin'])

    def test_script_gate_without_aggregate_change(self):
        truth = np.array([[[0., 1.]], [[0., 1.]], [[1., 0.]]], np.float32)
        exact = q.metrics(truth, truth, [0xC0, 0x391, 0x410])
        changed = copy.deepcopy(exact)
        changed['groups']['greek']['mae'] += .0016
        self.assertEqual(q.gate(changed, exact), ['greek:mae'])
        changed['glyphs'][0]['scalar'] += 1
        with self.assertRaises(ValueError):
            q.gate(changed, exact)


if __name__ == '__main__':
    unittest.main()
