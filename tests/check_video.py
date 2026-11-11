"""Independent invariants for video fitting, stream framing and multi-ink labels."""
import importlib.util
from pathlib import Path
import sys
import unittest
import io
import subprocess
import json
import tempfile
import struct
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
        model.ink_indices=None  # exercise the independent fixture, not cached neural indices
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

    def test_proposal_fit(self):
        model=v.TwoInk(cell_w=2,cell_h=4)
        image=np.random.default_rng(22).integers(0,256,(8,4,3),dtype=np.uint8)
        exhaustive=model.fit(image)
        restricted=model.fit(image,exhaustive['indices'][:,:,None])
        np.testing.assert_allclose(restricted['sse'],exhaustive['sse'],atol=1e-7)
        np.testing.assert_array_equal(restricted['colours'],exhaustive['colours'])
        with self.assertRaises(ValueError):model.fit(image,np.full((2,2,1),-1))

    def test_binary_fast_path_matches_neural_blend(self):
        image=np.random.default_rng(87).integers(0,256,(64,96,3),dtype=np.uint8)
        for width,height in [(2,4),(4,8),(8,16)]:
            model=v.MultiInk(cell_w=width,cell_h=height)
            colours=model.encode(image)
            fast=model.decode(colours)
            model.ink_indices=None
            np.testing.assert_array_equal(fast,model.decode(colours))
        fractional=v.MultiInk(ROOT/'weights/neuronte-split-v4.nrt')
        self.assertIsNone(fractional.ink_indices)

    def test_helper_numpy_reference(self):
        from neuronte_video_helpers import Helper
        for kind,n in [('speed',24),('quality',51)]:
            path=ROOT/f'weights/neuronte-video-{kind}-v0.json'
            model=Helper(path,kind);doc=json.loads(path.read_text())
            x=np.random.default_rng(15).random((7,n)).astype(np.float32)
            reference=x.astype(float)
            for i,layer in enumerate(doc['layers']):
                reference=reference@np.array(layer['weight']).T+np.array(layer['bias'])
                if i==0:reference=np.maximum(reference,0)
            np.testing.assert_allclose(model(x),reference,atol=2e-4,rtol=1e-5)

    def test_temporal_guard_rejects_bad_retention(self):
        from neuronte_video_helpers import quality_cells,ssim
        model=v.TwoInk('full')
        yy,xx=np.mgrid[:32,:32]
        old=np.repeat((((xx//4)%2)*255)[:,:,None],3,2).astype(np.uint8)
        new=np.repeat((((yy//4)%2)*255)[:,:,None],3,2).astype(np.uint8)
        prior=model.fit(old);model.previous=None;best=model.fit(new)
        keep_all=lambda x:np.tile([0,1],(len(x),1))
        result=quality_cells(model,keep_all,new,old,prior,best)
        self.assertGreaterEqual(ssim(new,model.decode(result)),ssim(new,model.decode(best))-.001)

    def test_cli_exact_and_partial_stream(self):
        raw=np.random.default_rng(15).integers(0,256,(8,4,3),dtype=np.uint8).tobytes()
        cmd=[sys.executable,str(ROOT/'tools/neuronte-video.py'),'--width','4','--height','8','--level','multi','--cell','2x4','--require-exact']
        good=subprocess.run(cmd,input=raw,capture_output=True)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(good.stdout,raw)
        bad=subprocess.run(cmd,input=raw[:-1],capture_output=True)
        self.assertEqual(bad.returncode,2)
        self.assertIn(b'truncated frame',bad.stderr)

    def test_full_mode_rejects_colour_even_one_layer(self):
        import pack
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'colour-bundle.nrt'
            data,_=pack.bundle([str(ROOT/'weights/neuronte-flame-v0.json'),str(ROOT/'weights/neuronte-ascii-v0.json')])
            path.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'monochrome'):v.TwoInk('full',weights=path)
            # Valid one-layer constant-red colour net: layers()==1 is NOT
            # sufficient to establish a monochrome foreground mask.
            h=r=8
            header=struct.pack('<8s5If6I43I',b'NEURONTE',3,6,64,h,3,1.,1,32,5,r,0,14,*([1]*43))
            palette=np.zeros((32,3),np.uint8);palette[2]=[255,0,0]
            trunk=np.zeros(2*h*h+94*h+1,dtype='<f4');trunk[-1]=1
            head=np.zeros(r*70+5,dtype='<f4');head[-5:]=[-1,1,-1,-1,-1]
            colour=header+palette.tobytes()*2+trunk.tobytes()+head.tobytes()
            bundle=struct.pack('<8s5II3I',b'NEURONTE',2,1,1,0,0,len(colour),32,32,0)+colour
            path.write_bytes(bundle)
            with v.NeuralMasks(path) as net:np.testing.assert_array_equal(net.mask(32,2,4),np.ones((4,2)))
            with self.assertRaisesRegex(ValueError,'monochrome'):v.TwoInk('full',weights=path)

    def test_cli_exact_flag_scope(self):
        cmd=[sys.executable,str(ROOT/'tools/neuronte-video.py'),'--width','8','--height','16','--mode','full','--require-exact']
        result=subprocess.run(cmd,input=bytes(384),capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertEqual(result.stdout,b'')
        self.assertIn(b'requires --level multi',result.stderr)
        result=subprocess.run(cmd+['--level','multi','--weights',str(ROOT/'weights/neuronte-split-v4.nrt')],input=bytes(384),capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertIn(b'exactness failed',result.stderr)

    def test_runtime_helper_policy_required_before_frames(self):
        doc=json.loads((ROOT/'weights/neuronte-video-speed-v0.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'helper.json'
            for policy in ['missing',None,[],3]:
                model=dict(doc)
                if policy=='missing':model.pop('inference')
                else:model['inference']=policy
                path.write_text(json.dumps(model))
                cmd=[sys.executable,str(ROOT/'tools/neuronte-video.py'),'--width','8','--height','16','--mode','full','--helper','speed','--helper-model',str(path)]
                result=subprocess.run(cmd,input=b'',capture_output=True)
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertIn(b'inference policy',result.stderr)
                self.assertNotIn(b'Traceback',result.stderr)

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
