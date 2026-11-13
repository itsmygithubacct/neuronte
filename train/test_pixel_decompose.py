"""Pixel inventory and teacher checks for expert decomposition."""
import unittest
import numpy as np
import decompose
import glyphs


class PixelTests(unittest.TestCase):
    def test_full_inventory_and_exact_budgets(self):
        codes = decompose.inventory('pixel')
        self.assertEqual(len(codes), 327)
        self.assertEqual(codes, sorted(set(codes)))
        for k in (2, 4, 8, 16, 64):
            for mode in ('spatial', 'repertoire'):
                parts = decompose.specs(mode, k, 'pixel')
                self.assertEqual(sum(p['width'] for p in parts), 128)
                if mode == 'repertoire':
                    self.assertEqual([c for p in parts for c in p['scalars']], codes)
                else:
                    self.assertTrue(all(p['scalars'] == codes for p in parts))
        with self.assertRaises(ValueError):
            decompose.specs('spatial', 4, 'pixel', 127)

    def test_mosaic_order_and_missing_halves(self):
        self.assertEqual([glyphs.sextant(cp)[0] for cp in range(0x1fb00, 0x1fb3c)],
                         [i for i in range(1, 63) if i not in (21, 42)])
        # Braille's left-column bit 1 differs from the mosaic top-right bit 1.
        for rows in (3, 4):
            points = np.array([[.25, (r + .5) * 2 / rows] for r in range(rows)] +
                              [[.75, (r + .5) * 2 / rows] for r in range(rows)])
            for bits in range(1 << (2 * rows)):
                got = glyphs.signed_distance(glyphs.lattice(bits, rows), points, glyphs.PEN) > 0
                wanted = [bool(bits & (1 << (2*r+c))) for c in range(2) for r in range(rows)]
                np.testing.assert_array_equal(got, wanted)

    def test_occupancy_alone_is_not_a_shared_distance_input(self):
        # Same occupied top-left tile, same local point, different neighbours.
        # An occupancy-only canonical net cannot equal both targets.
        point = np.array([[.49, .25]])
        for rows in (3, 4):
            isolated = glyphs.signed_distance(glyphs.lattice(1, rows), point, glyphs.PEN)
            joined = glyphs.signed_distance(glyphs.lattice(3, rows), point, glyphs.PEN)
            self.assertAlmostEqual(float(isolated[0]), .01)
            self.assertGreater(float(joined[0]), .2)
            self.assertGreater(float(np.clip(joined/.15,-1,1)[0] - np.clip(isolated/.15,-1,1)[0]), .9)


if __name__ == '__main__':
    unittest.main()
