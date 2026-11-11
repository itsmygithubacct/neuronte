"""Independent invariants for video fitting, stream framing and multi-ink labels."""
import importlib.util
from pathlib import Path
import sys
import unittest
import io
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import neuronte_video as v
spec=importlib.util.spec_from_file_location('cli',ROOT/'tools/neuronte-video.py')
cli=importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)

class Video(unittest.TestCase):
    def test_octant_manifest(self):
        chars=v.octant_characters()
        self.assertEqual(len(set(chars.values())),256)
        self.assertEqual(chars[0xaa],0x2590)
        self.assertEqual(chars[0x3c],0x1cd33)
        self.assertEqual(chars[0xf0],0x2584)

    def test_bounded_fit_against_independent_solver(self):
        from scipy.optimize import lsq_linear
        model=v.TwoInk(cell_w=2,cell_h=4)
        # Fractional masks exercise boundary optima as well as degenerate masks.
        model.masks=np.array([[0]*8,[1]*8,[.1,.2,.4,.9,.3,.8,.6,.7],[0,0,0,0,1,1,1,1]],float)
        model.scalars=np.array([32,0x2588,65,0x2584])
        rng=np.random.default_rng(831)
        image=rng.integers(0,256,(12,4,3),dtype=np.uint8)
        cells=model.fit(image)
        for k,patch in enumerate(v.patches(image,2,4).reshape(-1,8,3)):
            expected=[]
            for mask in model.masks:
                design=np.stack([1-mask,mask],1)
                expected.append(sum(np.square(design@lsq_linear(design,patch[:,c],bounds=(0,255),tol=1e-12).x-patch[:,c]).sum() for c in range(3)))
            self.assertAlmostEqual(cells['sse'].flat[k],min(expected),places=6)

    def test_uniform_and_delta(self):
        model=v.TwoInk(cell_w=2,cell_h=4)
        a=np.full((8,8,3),97,np.uint8)
        cells=model.fit(a)
        np.testing.assert_array_equal(model.decode(cells),a)
        self.assertEqual(model.ansi(cells,cells),'\x1b[0m')
        self.assertTrue(np.all(cells['sse']<1e-6))

    def test_gray_labels_without_neural_assumption(self):
        model=v.MultiInk()
        # Test record layout independently of neural exactness; explicit label
        # masks here are a test fixture, never the production renderer.
        labels=np.array([[0,1],[2,3],[6,7],[4,5]])
        model.mix=np.stack([labels==k for k in range(8)])
        image=np.arange(96,dtype=np.uint8).reshape(8,4,3)
        colours=model.encode(image)
        np.testing.assert_array_equal(model.decode(colours),image)
        np.testing.assert_array_equal(colours[0,0,6],image[2,0])

    def test_neural_blend_partition(self):
        model=v.MultiInk(cell_w=4,cell_h=8)
        np.testing.assert_allclose(model.mix.sum(0),1,atol=2e-7)
        self.assertTrue(np.all(model.mix>=0))
        image=np.full((8,4,3),193,np.uint8)
        np.testing.assert_array_equal(model.decode(model.encode(image)),image)

    def test_frame_read(self):
        class Short(io.BytesIO):
            def read(self,n): return super().read(min(n,3))
        stream=Short(bytes(range(24)))
        self.assertEqual(cli.read_frame(stream,12),bytes(range(12)))
        self.assertEqual(cli.read_frame(stream,12),bytes(range(12,24)))
        self.assertIsNone(cli.read_frame(stream,12))
        with self.assertRaises(ValueError): cli.read_frame(io.BytesIO(b'abc'),4)

    def test_exact_video_asset(self):
        result=v.exactness()
        self.assertEqual(result['points'],2048)
        self.assertTrue(result['exact'])
        image=np.random.default_rng(45).integers(0,256,(32,48,3),dtype=np.uint8)
        renderer=v.MultiInk()
        np.testing.assert_array_equal(renderer.decode(renderer.encode(image)),image)

    def test_bad_inputs(self):
        with self.assertRaises(ValueError): v.MultiInk(cell_w=3)
        with self.assertRaises(ValueError): v.patches(np.zeros((4,3,3),np.uint8),2,4)

if __name__=='__main__': unittest.main()
