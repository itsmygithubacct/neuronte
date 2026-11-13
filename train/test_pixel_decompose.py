"""Pixel inventory and teacher checks for expert decomposition."""
import unittest
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
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

    def test_explicit_semantic_groups_and_selected_restart(self):
        codes = decompose.inventory('pixel')
        mosaic = glyphs.mosaics()
        groups = [dict(name='pixel-block', width=2, scalars=sorted(ord(c) for c,t,_ in glyphs.charset('pixel') if t=='block')),
                  dict(name='pixel-sextant', width=2, scalars=sorted(c for c,(_,n) in mosaic.items() if n==3)),
                  dict(name='pixel-octant', width=4, scalars=sorted(c for c,(_,n) in mosaic.items() if n==4))]
        doc=dict(schema='neuronte.decomposition-spec/v1',expert='pixel',groups=groups)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); specification=root/'spec.json'; specification.write_text(json.dumps(doc))
            specs=decompose.explicit_specs(specification,'pixel','repertoire',3,8)
            self.assertEqual([len(p['scalars']) for p in specs],[29,60,238])
            with self.assertRaises(ValueError):decompose.explicit_specs(specification,'pixel','spatial',3,8)
            dirs=[root/'full',root/'resume']
            for directory in dirs:
                directory.mkdir(); yy,xx=np.mgrid[0:9,0:5]/4
                np.save(directory/'teacher.npy',np.repeat((xx-.5)[None],len(codes),axis=0).astype(np.float16))
                (directory/'teacher.json').write_text(json.dumps(dict(sha256=decompose.digest(directory/'teacher.npy'),identity=dict(expert='pixel',scalars=codes,grid=4,sources={},pen=.075))))
            args=argparse.Namespace(directory=dirs[0],expert='pixel',width_budget=8,mode='repertoire',parts=3,
                seeds='0,1',start=0,batch_models=4,steps=4,device='cpu',unlabelled=0.,compile=False,resume=False,
                log_every=1,checkpoint_every=2,stop_after=None,specification=specification,model_indices='0,1,3,4')
            with contextlib.redirect_stdout(io.StringIO()):
                decompose.train(args)
                resumed=copy.copy(args);resumed.directory=dirs[1];resumed.stop_after=2;decompose.train(resumed)
                resumed.stop_after=None;resumed.resume=True;decompose.train(resumed)
            files=list(dirs[0].glob('pixel-*-s*.json'));self.assertEqual(len(files),4)
            for path in files:self.assertEqual(path.read_bytes(),(dirs[1]/path.name).read_bytes())
            mixed=copy.copy(args);mixed.model_indices='0,2'
            with self.assertRaisesRegex(ValueError,'single width'):decompose.train(mixed)
            groups[1]['scalars'][0]=groups[0]['scalars'][0];specification.write_text(json.dumps(doc))
            with self.assertRaises(ValueError):decompose.explicit_specs(specification,'pixel','repertoire',3,8)

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
