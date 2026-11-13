"""Independent invariants for video fitting, stream framing and multi-ink labels."""
import importlib.util
from pathlib import Path
import sys
import unittest
import io
import subprocess
import json
import os
import tempfile
import struct
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import neuronte_video as v
spec=importlib.util.spec_from_file_location('cli',ROOT/'tools/neuronte-video.py')
cli=importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)

class Video(unittest.TestCase):
    def test_full_mode_accepts_ascii_tiles_and_preserves_other_glyphs(self):
        for w,h in ((5,11),(8,16)):
            original_cps,original=v.candidates('full',w,h,ROOT/'weights/neuronte-split-v5.nrt')
            for design in ('groups','spatial'):
                full=ROOT/f'weights/neuronte-split-ascii-{design}-v1.nrt'
                cps,masks=v.candidates('full',w,h,full)
                np.testing.assert_array_equal(cps,original_cps)
                ascii_rows=(cps>=32)&(cps<=126)
                self.assertEqual(int(ascii_rows.sum()),95)
                np.testing.assert_array_equal(masks[~ascii_rows],original[~ascii_rows])
                with v.NeuralMasks(ROOT/f'weights/neuronte-ascii-{design}-v1.nrt') as net:
                    direct=np.stack([net.mask(int(cp),w,h).ravel() for cp in cps[ascii_rows]])
                np.testing.assert_array_equal(masks[ascii_rows],direct)
                self.assertFalse(np.array_equal(masks[ascii_rows],original[ascii_rows]))
        fitted=v.TwoInk('full',w,h,full)
        np.testing.assert_array_equal(fitted.masks,masks.astype(np.float64))

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

    def test_native_rgb_composition_matches_independent_blend_and_odd_edges(self):
        rng = np.random.default_rng(71)
        for width, height in ((1,1), (1,9), (7,1), (17,13), (945,531)):
            image = rng.integers(0,256,(height,width,3),dtype=np.uint8)
            model = v.MultiInk()
            self.assertIsNotNone(model.native_rgb24)
            output = np.empty_like(image)
            self.assertIs(model.render_rgb24(image, output), output)
            model.ink_indices = None  # evaluate the learned continuous blend independently
            padded = np.pad(image,((0,-height%4),(0,-width%2),(0,0)),mode='edge')
            np.testing.assert_array_equal(output, model.decode(model.encode(padded))[:height,:width])
        # A different learned binary selection must change the pixels. Keep
        # mix and indices consistent while exchanging the first two inks.
        for exchange in (1, 2, 4):
            model = v.MultiInk()
            model.ink_indices = model.ink_indices ^ exchange
            model.mix = model.mix[np.arange(8) ^ exchange]
            rendered = model.render_rgb24(image)
            self.assertFalse(np.array_equal(rendered, image))
            model.ink_indices = None
            np.testing.assert_array_equal(rendered, model.decode(model.encode(padded))[:height,:width])

    def test_rgb_fallback_fractional_models_and_output_ownership(self):
        image = np.arange(17*13*3,dtype=np.uint8).reshape(13,17,3)
        for model in (v.MultiInk(), v.MultiInk(ROOT/'weights/neuronte-split-v4.nrt')):
            native = model.render_rgb24(image)
            model.native_rgb24 = None
            np.testing.assert_array_equal(native, model.render_rgb24(image))
            with self.assertRaisesRegex(ValueError,'overlap'):model.render_rgb24(image,image)
            with self.assertRaises(ValueError):model.render_rgb24(image,np.empty((1,1,3),np.uint8))
            output=np.empty_like(image);output.flags.writeable=False
            with self.assertRaises(ValueError):model.render_rgb24(image,output)
        model=v.MultiInk()
        np.testing.assert_array_equal(model.render_rgb24(image[:,::-1]), image[:,::-1])

    def test_planar_rendering_matches_packed_for_learned_exchanged_and_fractional_maps(self):
        rng = np.random.default_rng(1113)
        def planes_of(image):  # FFmpeg gbrp order
            return np.ascontiguousarray(image.transpose(2, 0, 1)[[1, 2, 0]])
        for width, height in ((1,1), (1,9), (7,1), (15,5), (16,4), (17,13), (945,531)):
            image = rng.integers(0,256,(height,width,3),dtype=np.uint8)
            planes = planes_of(image)
            model = v.MultiInk()
            self.assertIsNotNone(model.native_planes)
            self.assertEqual(model.natural_input_format(), 'gbrp')
            packed = model.render_rgb24(image)
            output = np.empty_like(image)
            self.assertIs(model.render_gbrp(planes, output), output)
            np.testing.assert_array_equal(output, packed)
            native, model.native_planes = model.native_planes, None    # numpy packing, then the packed path
            self.assertEqual(model.natural_input_format(), 'rgb24')
            np.testing.assert_array_equal(model.render_gbrp(planes), packed)
            model.native_planes = native
            # A strided view of the planes is accepted and gives the same pixels.
            wide = np.zeros((3, height, width + 3), np.uint8); wide[:, :, :width] = planes
            np.testing.assert_array_equal(model.render_gbrp(wide[:, :, :width]), packed)
        for exchange in (1, 2, 4, 3, 7):
            model = v.MultiInk()
            model.ink_indices = model.ink_indices ^ exchange
            model.mix = model.mix[np.arange(8) ^ exchange]
            rendered = model.render_gbrp(planes)
            self.assertFalse(np.array_equal(rendered, image))
            np.testing.assert_array_equal(rendered, model.render_rgb24(image))
            model.ink_indices = None   # the learned continuous blend, independently
            padded = np.pad(image,((0,-height%4),(0,-width%2),(0,0)),mode='edge')
            np.testing.assert_array_equal(rendered, model.decode(model.encode(padded))[:height,:width])
        fractional = v.MultiInk(ROOT/'weights/neuronte-split-v4.nrt')
        self.assertIsNone(fractional.ink_indices)
        self.assertEqual(fractional.natural_input_format(), 'rgb24')
        small = image[:13, :17]
        np.testing.assert_array_equal(fractional.render_gbrp(planes_of(small)), fractional.render_rgb24(small))
        model = v.MultiInk()
        with self.assertRaisesRegex(ValueError, 'overlap'):
            buffer = np.zeros(3*13*17*2, np.uint8)
            model.render_gbrp(buffer[:3*13*17].reshape(3,13,17), buffer[3*13*17-1:-1].reshape(13,17,3))
        for bad in (np.zeros((2,4,4),np.uint8), np.zeros((3,4,4),np.uint16), np.zeros((3,0,4),np.uint8)):
            with self.assertRaises(ValueError): model.render_gbrp(bad)
        with self.assertRaises(ValueError): model.render_gbrp(planes_of(small), np.empty((13,17,4),np.uint8))
        frozen = np.empty((13,17,3),np.uint8); frozen.flags.writeable = False
        with self.assertRaises(ValueError): model.render_gbrp(planes_of(small), frozen)

    def test_installed_ffmpeg_writes_the_same_samples_as_planes_and_packed(self):
        """The player decodes gbrp for speed; it must equal FFmpeg's rgb24 bytes.

        Checked here on the installed FFmpeg, at its normal SIMD level and with
        forced plain-C and SSE2 code paths, with noise that clips every channel.
        """
        import platform
        sources = ['nullsrc=s=320x180:r=30,format=yuv420p,geq=lum=random(1)*255:cb=random(2)*255:cr=random(3)*255',
                   'testsrc2=s=1280x720:r=30,format=yuv420p', 'smptehdbars=s=640x360:r=30,format=yuv420p10le']
        levels = [[]] + ([['-cpuflags', '0'], ['-cpuflags', 'sse2']] if platform.machine() in ('x86_64', 'AMD64') else [['-cpuflags', '0']])
        for source in sources:
            for width, height, chroma in ((945, 531, 'left'), (161, 91, 'center'), (17, 13, None)):
                outputs = {}
                for fmt in v.DECODED_FORMATS:
                    command = v.decoder_command(source, width, height, 30, lavfi=True, chroma=chroma, pix_fmt=fmt)
                    command[-1:-1] = ['-frames:v', '2']
                    for level in levels:
                        outputs[fmt, tuple(level)] = subprocess.check_output(command[:1] + level + command[1:])
                # Each comparison is within one SIMD level: FFmpeg's levels need
                # not agree with each other, and player and reference share one.
                for level in levels:
                    packed = np.frombuffer(outputs['rgb24', tuple(level)], np.uint8).reshape(2, height, width, 3)
                    g, b, r = np.frombuffer(outputs['gbrp', tuple(level)], np.uint8).reshape(2, 3, height, width).transpose(1, 0, 2, 3)
                    with self.subTest(source=source[:24], size=(width, height), level=level):
                        same = np.stack([r, g, b], -1) == packed
                        self.assertTrue(same.all(), f'{int((~same).sum())} samples differ')
        with self.assertRaises(ValueError): v.decoder_command('input.mp4', 945, 531, 30, pix_fmt='yuv420p')

    def test_reusable_rgb_reader_handles_fragmentation_eof_and_truncation(self):
        class Short(io.BytesIO):
            def readinto(self, buf):return super().readinto(buf[:5])
        reader=v.RGBFrameReader(2,2)
        stream=Short(bytes(range(24)))
        first=reader.read(stream)
        self.assertEqual(first.tobytes(),bytes(range(12)))
        self.assertIs(first,reader.read(stream))
        self.assertEqual(first.tobytes(),bytes(range(12,24)))
        self.assertIsNone(reader.read(stream))
        with self.assertRaisesRegex(ValueError,'truncated'):reader.read(Short(b'abc'))
        planar=v.RGBFrameReader(2,2,planar=True)
        frame=planar.read(Short(bytes(range(12))))
        self.assertEqual(frame.shape,(3,2,2))
        self.assertEqual(frame[1].tobytes(),bytes(range(4,8)))   # the second plane is B in gbrp order

    def test_decoder_builder_keeps_thread_options_on_their_input_and_output(self):
        command=v.decoder_command('input.mp4',945,531,30,start=2.25,chroma='left',decoder_threads=4)
        pos=command.index('-i')
        self.assertIn('-threads:v',command[:pos])
        self.assertEqual(command[command.index('-threads:v')+1],'4')
        self.assertEqual(command[command.index('-threads:v',pos)+1],'1')
        self.assertIn('in_chroma_loc=left',command[command.index('-vf')+1])
        for options in ({'start':float('nan')},{'chroma':'unknown'},{'decoder_threads':-1}):
            with self.assertRaises(ValueError):v.decoder_command('input.mp4',945,531,30,**options)
        outputs=[]
        for decoder,encoder in ((0,0),(0,1),(2,1)):
            command=v.decoder_command('testsrc2=size=64x36:rate=24:duration=0.2',17,13,24,
                                      lavfi=True,decoder_threads=decoder,output_threads=encoder)
            outputs.append(subprocess.check_output(command))
        self.assertEqual(len(outputs[0]),5*17*13*3)
        self.assertEqual(outputs[0],outputs[1])
        self.assertEqual(outputs[0],outputs[2])

    def test_player_decoder_reuses_storage_across_fragmented_frames(self):
        import time
        spec=importlib.util.spec_from_file_location('neuronte_play',ROOT/'tools/neuronte-play.py')
        play=importlib.util.module_from_spec(spec);spec.loader.exec_module(play)
        code='import os,time\nfor part in (b"abc",b"def",b"ghi",b"jkl"):\n os.write(1,part);time.sleep(.03)\n'
        decoder=play.Decoder([sys.executable,'-c',code])
        try:
            frames=[];buffers=[];deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                frame=decoder.read(6,.01)
                if frame is None:break
                if frame:
                    frames.append(bytes(frame));buffers.append(frame.obj)
            self.assertEqual(frames,[b'abcdef',b'ghijkl'])
            self.assertIs(buffers[0],buffers[1])
            self.assertIsNotNone(decoder.child.poll())
        finally:
            decoder.close()

    def test_player_decoder_rejects_a_truncated_successful_stream(self):
        import time
        spec=importlib.util.spec_from_file_location('neuronte_play',ROOT/'tools/neuronte-play.py')
        play=importlib.util.module_from_spec(spec);spec.loader.exec_module(play)
        decoder=play.Decoder([sys.executable,'-c','import os;os.write(1,b"abc")'])
        try:
            deadline=time.monotonic()+5
            with self.assertRaisesRegex(ValueError,'truncated RGB frame'):
                while time.monotonic()<deadline:
                    if decoder.read(6,.01) is None:break
        finally:
            decoder.close()

    def test_in_process_decoder_yields_to_playback_controls(self):
        class Library:
            def __init__(self): self.waits=[]
            def neuronte_media_next(self,handle,frame,wait):
                self.waits.append(wait)
                return v.MediaDecoder.AGAIN if len(self.waits)==1 else v.MediaDecoder.END
            def neuronte_media_close(self,handle): pass
        library=Library()
        stream=v.MediaStream(library,1,2,2,False)
        spec=importlib.util.spec_from_file_location('neuronte_play',ROOT/'tools/neuronte-play.py')
        play=importlib.util.module_from_spec(spec);spec.loader.exec_module(play)
        source=play.LibraryFrames(stream)
        try:
            self.assertEqual(source.read(12,.025),b'')
            self.assertEqual(library.waits,[25])
            self.assertIsNone(source.read(12,0))
            self.assertEqual(library.waits,[25,0])
            self.assertEqual(source.failure(),'')
        finally: source.close()

    def test_helper_numpy_reference(self):
        from neuronte_video_helpers import Helper
        for version,kind,n in [(ver,kind,n) for ver in ('v0','v1') for kind,n in [('speed',24),('quality',51)]]:
            path=ROOT/f'weights/neuronte-video-{kind}-{version}.json'
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
        doc=json.loads((ROOT/'weights/neuronte-video-speed-v1.json').read_text())
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

    def test_helpers_are_bound_to_their_bundle(self):
        from neuronte_video_helpers import Helper
        sums=dict(reversed(line.split('  ')) for line in (ROOT/'weights/SHA256SUMS').read_text().splitlines())
        for version,bundle,scalars in [('v0','split-v4',1061),('v1','split-v5',1176)]:
            for kind in ['speed','quality']:
                doc=Helper(ROOT/f'weights/neuronte-video-{kind}-{version}.json',kind,runtime=True).doc
                self.assertEqual(doc['scalar_manifest'],bundle)
                self.assertEqual(doc['scalar_bundle_sha256'],sums[f'neuronte-{bundle}.nrt'])
            self.assertEqual(len(json.loads((ROOT/f'weights/neuronte-video-speed-{version}.json').read_text())['layers'][1]['bias']),scalars)
        cmd=[sys.executable,str(ROOT/'tools/neuronte-video.py'),'--width','8','--height','16','--mode','full','--helper','speed']
        old=['--helper-model',str(ROOT/'weights/neuronte-video-speed-v0.json')]
        frame=bytes(384)
        # Without --weights the v1 helper runs on its own bundle, split-v5,
        # not the default split-v6 (whose SHA256 it would refuse).
        self.assertEqual(subprocess.run(cmd,input=frame,capture_output=True).returncode,0)
        # The v0 helper is refused with split-v5 and still runs with split-v4.
        result=subprocess.run(cmd+old,input=frame,capture_output=True)
        self.assertEqual(result.returncode,2);self.assertIn(b'differ from the selected bundle',result.stderr)
        self.assertEqual(subprocess.run(cmd+old+['--weights',str(ROOT/'weights/neuronte-split-v4.nrt')],input=frame,capture_output=True).returncode,0)
        result=subprocess.run(cmd+['--weights',str(ROOT/'weights/neuronte-split-v4.nrt')],input=frame,capture_output=True)
        self.assertEqual(result.returncode,2);self.assertIn(b'differ from the selected bundle',result.stderr)
        # A helper whose output layer does not match its bundle is refused.
        with tempfile.TemporaryDirectory() as temp:
            doc=json.loads((ROOT/'weights/neuronte-video-speed-v0.json').read_text());doc['scalar_manifest']='split-v5'
            path=Path(temp)/'helper.json';path.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,'invalid video helper layer'):Helper(path,'speed')

    def test_full_mode_draws_braille_with_split_v6(self):
        # split-v6 is split-v5 with only its Braille expert replaced, so every
        # other candidate is unchanged and every Braille candidate is the
        # tiled braille-v1 net's own mask.
        self.assertEqual(v.DEFAULT_BUNDLE,ROOT/'weights/neuronte-split-v6.nrt')
        self.assertEqual(v.HELPER_BUNDLE,ROOT/'weights/neuronte-split-v5.nrt')
        self.assertEqual(v.cell_bundle(),v.DEFAULT_BUNDLE)
        self.assertEqual(v.cell_bundle(helper=True),v.HELPER_BUNDLE)
        self.assertEqual(v.cell_bundle('x.nrt',True),Path('x.nrt'))
        for w,h in [(8,16),(5,11),(24,48)]:
            cps,new=v.candidates('full',w,h)
            old_cps,old=v.candidates('full',w,h,v.HELPER_BUNDLE)
            np.testing.assert_array_equal(cps,old_cps)
            braille=(cps>=0x2800)&(cps<=0x28ff)
            self.assertEqual(int(braille.sum()),256)
            np.testing.assert_array_equal(new[~braille],old[~braille])
            with v.NeuralMasks(ROOT/'weights/neuronte-braille-v1.nrt') as net:
                alone=np.stack([net.mask(int(cp),w,h).ravel() for cp in cps[braille]])
            np.testing.assert_array_equal(new[braille],alone)
            self.assertFalse(np.array_equal(new[braille],old[braille]))
        two=v.TwoInk('full',8,16)
        np.testing.assert_array_equal(two.masks,v.candidates('full',8,16)[1].astype(np.float64))

    def player(self,*args,keys=(),source=None,grid=True,timeout=60):
        """Run the player off a terminal; keys are (seconds to wait, bytes) written to its key pipe."""
        import shutil,time
        if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):self.skipTest('ffmpeg is not installed')
        cmd=[sys.executable,str(ROOT/'tools/neuronte-play.py'),source or 'color=c=red:size=32x48:rate=10[a];color=c=blue:size=32x48:rate=10[b];[a][b]hstack']
        cmd+=([] if source else ['--lavfi'])+(['--cols','6','--rows','3'] if grid else [])+['--no-status',*args]
        env=dict(os.environ,COLUMNS='80',LINES='24');env.pop('KITTY_WINDOW_ID',None)
        r,w=os.pipe()
        with tempfile.TemporaryFile() as picture:   # a file, so the player never waits on us while we wait to press keys
            child=subprocess.Popen(cmd+['--input-fd',str(r)],stdout=picture,stderr=subprocess.PIPE,env=env,pass_fds=[r]);os.close(r)
            try:
                for wait,key in keys:
                    time.sleep(wait)
                    if child.poll() is None:os.write(w,key)
                _,err=child.communicate(timeout=timeout)
            finally:
                os.close(w)
                if child.poll() is None:child.kill();child.wait()
            picture.seek(0);out=picture.read()
        return child.returncode,out,err

    def test_player_drains_noisy_decoder_and_reports_its_last_error(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            fake=Path(temp)/'ffmpeg'
            # More than a pipe can hold, both before a picture and after stdout
            # closes. Diagnostics must not prevent either playback or EOF.
            fake.write_text('#!/usr/bin/env python3\nimport os,sys\n'
                'for _ in range(256): os.write(2,b"decoder diagnostic\\n"*256)\n'
                'os.write(1,bytes(12*12*3))\nos.close(1)\n'
                'for _ in range(256): os.write(2,b"late diagnostic\\n"*256)\n'
                'os.write(2,b"last decoder error\\n")\nsys.exit(int(os.environ["DECODER_STATUS"]))\n')
            fake.chmod(0o755)
            for status in (0,7):
                with self.subTest(status=status),patch.dict(os.environ,PATH=temp+os.pathsep+os.environ['PATH'],DECODER_STATUS=str(status)):
                    code,out,err=self.player('--no-audio',timeout=5)
                    self.assertEqual(code,1 if status else 0,err)
                    self.assertEqual(len(self.pixel_frames(out)),1)
                    self.assertLess(len(err),70000)  # only a bounded diagnostic tail
                    if status:self.assertIn(b'last decoder error',err)

    def test_player_can_quit_while_a_decoder_holds_a_partial_frame(self):
        from unittest.mock import patch
        import time
        with tempfile.TemporaryDirectory() as temp:
            fake=Path(temp)/'ffmpeg'
            fake.write_text('#!/usr/bin/env python3\nimport os,time\nos.write(1,bytes(100))\ntime.sleep(30)\n')
            fake.chmod(0o755)
            with patch.dict(os.environ,PATH=temp+os.pathsep+os.environ['PATH']):
                began=time.monotonic()
                code,out,err=self.player('--no-audio',keys=[(.8,b'q')],timeout=2)
            self.assertEqual(code,0,err)
            self.assertLess(time.monotonic()-began,2.5)
            self.assertEqual(self.pixel_frames(out),[])

    def test_bad_player_log_keeps_terminal_attributes(self):
        import fcntl,termios
        with tempfile.TemporaryDirectory() as temp:
            master,slave=os.openpty();before=termios.tcgetattr(slave)
            def terminal_owner():
                os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
            cmd=[sys.executable,str(ROOT/'tools/neuronte-play.py'),'color=size=32x32:rate=30',
                 '--lavfi','--no-audio','--log',str(Path(temp)/'missing'/'frames.jsonl')]
            child=None
            try:
                child=subprocess.Popen(cmd,stdin=slave,stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=terminal_owner)
                out,err=child.communicate(timeout=10)
                self.assertEqual(child.returncode,2,err)
                self.assertIn(b'No such file or directory',err)
                self.assertEqual(out,b'')
                self.assertEqual(termios.tcgetattr(slave),before)
            finally:
                if child and child.poll() is None:child.kill();child.wait()
                termios.tcsetattr(slave,termios.TCSANOW,before)
                os.close(master);os.close(slave)

    def test_player_waits_for_slow_frames_including_a_pause(self):
        with tempfile.TemporaryDirectory() as temp:
            log=Path(temp)/'frames.jsonl'
            code,out,err=self.player('--fps','.5','--frames','3','--log',str(log),
                                     keys=[(.8,b' '),(.6,b' ')],timeout=10)
            self.assertEqual(code,0,err)
            rows=[json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([r['pts'] for r in rows],[0,2,4])
            self.assertEqual(len(self.pixel_frames(out)),3)
            self.assertGreater(rows[1]['shown']-rows[0]['shown'],2.4)
            self.assertGreater(rows[2]['shown']-rows[1]['shown'],1.8)
            self.assertGreater(min(r['late_ms'] for r in rows),-10)

    def test_player_busy_terminal_still_waits_for_slow_frames(self):
        with tempfile.TemporaryDirectory() as temp:
            stats=Path(temp)/'stats.json'
            code,out,err=self.player('--fps','.5','--frames','5','--transport','shm','--stats',str(stats),timeout=12)
            self.assertEqual(code,0,err)
            summary=json.loads(stats.read_text())
            self.assertEqual(summary['shown'],3)
            self.assertEqual(summary['skipped_terminal_busy'],2)
            self.assertGreaterEqual(summary['seconds'],7.9)

    def test_cancelled_picture_keeps_the_last_displayed_image(self):
        import base64,re
        spec=importlib.util.spec_from_file_location('neuronte_play',ROOT/'tools/neuronte-play.py')
        play=importlib.util.module_from_spec(spec);spec.loader.exec_module(play)
        presenter=play.Presenter(io.BytesIO(),'shm')
        picture=np.zeros((4,2,3),np.uint8)
        def image_name(payload):
            return '/dev/shm/'+base64.b64decode(re.search(rb',t=s;([^\x1b]+)',payload)[1]).decode()
        try:
            first=presenter.frame(picture,1,1,1,1);presenter.sent()
            shown=presenter.current;os.unlink(image_name(first))  # terminal consumed it
            cancelled=presenter.frame(picture,1,1,1,1)
            presenter.discard()
            self.assertFalse(os.path.exists(image_name(cancelled)))
            self.assertEqual(presenter.current,shown)
            next_frame=presenter.frame(picture,1,1,1,1)
            self.assertIn(f'a=d,d=I,i={shown},'.encode(),next_frame)
            presenter.sent();os.unlink(image_name(next_frame))
        finally:presenter.close(drain=0)

    def pixel_frames(self,out):
        import re,base64,zlib
        frames=[];parts=[];header=None
        for packet in re.findall(rb'\x1b_G(.*?)\x1b\\',out,re.S):
            control,data=packet.split(b';',1)
            fields=dict(item.split(b'=',1) for item in control.split(b','))
            if fields.get(b'a')==b'T':header=fields;parts=[]
            elif b'a' in fields:continue
            if header is None:continue
            parts.append(data)
            if fields.get(b'm',b'0')==b'0':
                pixels=zlib.decompress(base64.standard_b64decode(b''.join(parts)))
                frames.append((header,pixels));header=None
        return frames

    def test_player_pixel_size_preserves_every_sample_and_odd_edges(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'pixels.ppm';stats=Path(temp)/'stats.json'
            for (w,h),layout in [((945,531),'auto'),((945,531),'rgb24'),((1,1),'auto'),((3,5),'gbrp'),((3,5),'rgb24')]:
                with self.subTest(size=(w,h),layout=layout):
                    # Independent RGB samples expose averaging, enlargement,
                    # colour reordering and loss of the partial edge cells.
                    pixels=np.random.default_rng(91).integers(0,256,(h,w,3),dtype=np.uint8)
                    source.write_bytes(f'P6\n{w} {h}\n255\n'.encode()+pixels.tobytes())
                    code,out,err=self.player('--pixel-size',f'{w}x{h}','--frames','1','--stats',str(stats),
                                             '--decoded-format',layout,source=str(source),grid=False)
                    self.assertEqual(code,0,err)
                    frames=self.pixel_frames(out);self.assertEqual(len(frames),1)
                    header,actual=frames[0]
                    self.assertEqual((header[b's'],header[b'v']),(str(w).encode(),str(h).encode()))
                    self.assertNotIn(b'c',header);self.assertNotIn(b'r',header)
                    self.assertEqual(actual,pixels.tobytes())
                    summary=json.loads(stats.read_text())
                    self.assertEqual(summary['decoded_size'],[w,h]);self.assertEqual(summary['image_size'],[w,h])
                    # The default takes planes, packed by the native compositor.
                    self.assertEqual(summary['decoded_format'],'gbrp' if layout=='auto' else layout)

    def test_player_planar_and_packed_decoding_present_identical_scaled_video(self):
        with tempfile.TemporaryDirectory() as temp:
            stats=Path(temp)/'stats.json';pictures=[]
            source='testsrc2=size=640x360:rate=30'
            for layout in ('gbrp','rgb24'):
                code,out,err=self.player('--lavfi','--pixel-size','161x91','--frames','4','--untimed','--decoded-format',layout,
                                         '--stats',str(stats),source=source,grid=False)
                self.assertEqual(code,0,err)
                self.assertEqual(json.loads(stats.read_text())['decoded_format'],layout)
                pictures.append([pixels for _,pixels in self.pixel_frames(out)])
            self.assertEqual(len(pictures[0]),4)
            self.assertEqual(pictures[0],pictures[1])
            reference=subprocess.check_output(v.decoder_command(source,161,91,30,lavfi=True)[:-1]+['-frames:v','4','-'])
            self.assertEqual(b''.join(pictures[0]),reference)
            code,out,err=self.player('--decoded-format','gbrp')
            self.assertEqual(code,2);self.assertIn(b'--decoded-format requires --pixel-size',err)

    def test_player_pixel_size_rejects_ambiguous_geometry(self):
        for size,extra in [('0x531',[]),('945x-1',[]),('945',[]),('945x531',['--cols','4']),
                           ('945x531',['--rows','4']),('945x531',['--mode','cells'])]:
            with self.subTest(size=size,extra=extra):
                code,out,err=self.player('--pixel-size',size,*extra,grid=False)
                self.assertEqual(code,2);self.assertIn(b'--pixel-size',err);self.assertNotIn(b'Traceback',err)
                self.assertEqual(out,b'')

    def test_player_preserves_the_sources_chroma_location(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'left.mkv'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=96x64:rate=1',
                            '-frames:v','1','-c:v','libx264','-qp','0','-preset','ultrafast','-colorspace','bt709',
                            '-x264-params','chromaloc=0',str(source)],check=True)
            reference=subprocess.check_output(['ffmpeg','-v','error','-i',str(source),
                '-vf','scale=17:13:flags=lanczos+accurate_rnd+full_chroma_int+full_chroma_inp:in_chroma_loc=left',
                '-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'])
            code,out,err=self.player('--pixel-size','17x13','--fps','1','--frames','1',source=str(source),grid=False)
            self.assertEqual(code,0,err)
            frames=self.pixel_frames(out);self.assertEqual(len(frames),1)
            self.assertEqual(frames[0][1],reference)

    def test_player_pixel_size_survives_a_paused_seek(self):
        with tempfile.TemporaryDirectory() as temp:
            clip=self.sound_clip(temp);stats=Path(temp)/'stats.json'
            code,out,err=self.player('--pixel-size','17x13','--no-audio','--stats',str(stats),source=clip,grid=False,
                                     keys=[(1.5,b' '),(.2,b'\x1b[C'),(.4,b'q')])
            self.assertEqual(code,0,err)
            frames=self.pixel_frames(out);self.assertGreater(len(frames),2)
            # Paused seeking presents one additional picture outside the main
            # loop. It must take the same pad/draw/crop path as normal playback.
            summary=json.loads(stats.read_text());self.assertEqual(summary['seeks'],1)
            self.assertEqual(len(frames),summary['shown']+1)
            for header,pixels in frames:
                self.assertEqual((header[b's'],header[b'v']),(b'17',b'13'))
                self.assertNotIn(b'c',header);self.assertNotIn(b'r',header)
                self.assertEqual(len(pixels),17*13*3)

    def test_player_untimed_does_not_wait_for_or_drop_source_frames(self):
        import time
        with tempfile.TemporaryDirectory() as temp:
            stats=Path(temp)/'stats.json'
            begin=time.monotonic()
            code,out,err=self.player('--untimed','--frames','5','--fps','.5','--stats',str(stats))
            self.assertEqual(code,0,err)
            self.assertLess(time.monotonic()-begin,5)  # normal playback needs eight seconds
            self.assertEqual(len(self.pixel_frames(out)),5)
            summary=json.loads(stats.read_text())
            self.assertEqual(summary['dropped'],0);self.assertFalse(summary['sound'])

    def test_player_pixels_and_cells(self):
        import re,base64,zlib
        code,out,err=self.player('--frames','3')
        self.assertEqual(code,0,err);self.assertIn(b'3 frames shown',err)
        # Every picture is complete under a new id before the one before it is deleted,
        # all inside one synchronized update: the terminal is never left with no picture.
        updates=re.findall(rb'\x1b\[\?2026h(.*?)\x1b\[\?2026l',out,re.S)
        ids=[]
        for n,update in enumerate(updates[:3]):
            sent=re.findall(rb'\x1b_Ga=T,f=24,s=48,v=48,i=(\d+),p=1,c=6,r=3,z=-1,C=1,q=2,o=z,m=0;([^\x1b]*)\x1b\\',update)
            self.assertEqual(len(sent),1);ids.append(sent[0][0])
            deleted=re.findall(rb'\x1b_Ga=d,d=I,i=(\d+),q=2;',update)
            self.assertEqual(deleted,[ids[n-1]] if n else [])
            if deleted:self.assertLess(update.index(b'a=T'),update.index(b'a=d'))
        self.assertEqual(len(ids),3);self.assertNotEqual(ids[0],ids[1]);self.assertEqual(ids[0],ids[2])
        # Red on the left and blue on the right must come back that way round.
        image=np.frombuffer(zlib.decompress(base64.standard_b64decode(sent[0][1])),np.uint8).reshape(48,48,3).astype(int)
        self.assertLessEqual(int(np.abs(image[:,:24]-[255,0,0]).max()),8)
        self.assertLessEqual(int(np.abs(image[:,24:]-[0,0,255]).max()),8)
        self.assertTrue(out.startswith(b'\x1b[?1049h'));self.assertTrue(out.endswith(b'\x1b[?25h\x1b[?1049l'))
        for i in set(ids):self.assertIn(b'a=d,d=I,i='+i+b',q=2;',out[out.rindex(b'\x1b[?2026l',0,len(out)-8)-400:])
        code,out,err=self.player('--frames','2','--mode','cells')
        self.assertEqual(code,0,err)
        self.assertNotIn(b'\x1b_G'+b'a=T',out)
        self.assertEqual(out.count(b'\x1b[48;2;'),18);self.assertIn(b'\x1b[11;38H',out)   # 6 x 3 cells, centred in 80 x 24, sent once
        code,out,err=self.player(source='nosuchsource=1')
        self.assertEqual(code,2);self.assertNotIn(b'Traceback',err)

    def test_player_shared_memory_backpressure(self):
        import glob
        before=set(glob.glob('/dev/shm/neuronte-play-*'))
        code,out,err=self.player('--frames','8','--transport','shm')
        self.assertEqual(code,0,err)
        # Nothing reads the objects here, so three are written, the rest are skipped, and all are removed at exit.
        self.assertEqual(out.count(b',t=s;'),3);self.assertIn(b'5 skipped for a busy terminal',err)
        self.assertEqual(set(glob.glob('/dev/shm/neuronte-play-*')),before)

    def test_untimed_player_keeps_every_frame_when_the_consumer_stalls(self):
        import base64,re,select,time
        with tempfile.TemporaryDirectory() as temp:
            stats=Path(temp)/'stats.json'
            cmd=[sys.executable,str(ROOT/'tools/neuronte-play.py'),'testsrc2=size=32x24:rate=30',
                 '--lavfi','--no-audio','--pixel-size','17x13','--frames','8','--transport','shm',
                 '--no-status','--untimed','--stats',str(stats)]
            with subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE) as child:
                data=b'';paths=[];frames=[];stalled=False;deadline=time.monotonic()+10
                try:
                    while time.monotonic()<deadline and len(frames)<8:
                        if select.select([child.stdout],[],[],.1)[0]:
                            chunk=os.read(child.stdout.fileno(),4096)
                            if not chunk:break
                            data+=chunk
                        while True:
                            match=re.search(rb',t=s;([^\x1b]+)\x1b\\',data)
                            if match is None:break
                            paths.append(Path('/dev/shm')/base64.b64decode(match[1]).decode())
                            data=data[match.end():]
                        if not stalled and len(paths)==3:
                            time.sleep(.15)  # all slots occupied: frame four must remain pending
                            self.assertIsNone(child.poll(),'player skipped the remaining frames')
                            stalled=True
                        if stalled:
                            while paths:
                                path=paths.pop(0);frames.append(path.read_bytes());path.unlink()
                    _,err=child.communicate(timeout=3)
                    self.assertEqual(child.returncode,0,err)
                    self.assertTrue(stalled)
                    self.assertEqual(len(frames),8)
                    self.assertTrue(all(len(frame)==17*13*3 for frame in frames))
                    summary=json.loads(stats.read_text())
                    self.assertEqual((summary['source_frames'],summary['shown'],summary['skipped_terminal_busy']),
                                     (8,8,0))
                finally:
                    if child.poll() is None:child.kill();child.wait()
                    for path in Path('/dev/shm').glob(f'neuronte-play-{child.pid}-*'):path.unlink(missing_ok=True)

    def test_untimed_player_can_quit_while_the_consumer_is_blocked(self):
        import time
        began=time.monotonic()
        code,out,err=self.player('--untimed','--frames','8','--transport','shm',
                                 '--no-audio',keys=[(1.,b'q')],timeout=3)
        self.assertEqual(code,0,err)
        self.assertLess(time.monotonic()-began,3)
        self.assertEqual(out.count(b',t=s;'),3)
        self.assertIn(b'0 skipped for a busy terminal',err)

    def test_player_waits_for_the_terminal_to_take_the_final_shared_frame(self):
        import base64,re,select,time
        cmd=[sys.executable,str(ROOT/'tools/neuronte-play.py'),'color=c=red:size=32x48:rate=10',
             '--lavfi','--no-audio','--pixel-size','17x13','--frames','1','--transport','shm','--no-status']
        with subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE) as child:
            data=b'';deadline=time.monotonic()+10;path=None
            try:
                while time.monotonic()<deadline:
                    if select.select([child.stdout],[],[],.1)[0]:
                        data+=os.read(child.stdout.fileno(),4096)
                        match=re.search(rb',t=s;([^\x1b]+)\x1b\\',data)
                        if match:
                            path=Path('/dev/shm')/base64.b64decode(match[1]).decode();break
                    if child.poll() is not None:break
                self.assertIsNotNone(path,'no shared frame')
                time.sleep(.04)  # terminal scheduling delay after the player flushes
                self.assertEqual(path.stat().st_size,17*13*3)
                path.unlink()  # actual consumer acknowledgment
                _,err=child.communicate(timeout=3)
                self.assertEqual(child.returncode,0,err)
            finally:
                if child.poll() is None:child.kill();child.wait()
                if path:path.unlink(missing_ok=True)

    def test_player_sound_seek_and_pause(self):
        import shutil
        if not (shutil.which('kilix-mpv') or shutil.which('mpv')):self.skipTest('mpv is not installed')
        with tempfile.TemporaryDirectory() as temp:
            clip=str(Path(temp)/'clip.mkv');log=Path(temp)/'log.jsonl'
            made=subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','testsrc2=size=64x48:rate=20','-f','lavfi','-i','sine=frequency=440',
                                 '-t','30','-c:v','mpeg4','-g','10','-c:a','pcm_s16le',clip],capture_output=True)
            if made.returncode:self.skipTest('ffmpeg cannot make the clip')
            code,out,err=self.player('--audio-output','null','--log',str(log),source=clip,
                                     keys=[(1.5,b'\x1b[C'),(1.2,b' '),(1.0,b' '),(1.0,b'\x1b[D'),(1.2,b'\x1b[A'),(.8,b'q')])
            self.assertEqual(code,0,err);self.assertIn(b'sound on',err)
            rows=[json.loads(line) for line in log.read_text().splitlines()]
            jumps=[round(b['pts']-a['pts']) for a,b in zip(rows,rows[1:]) if abs(b['pts']-a['pts'])>1]
            self.assertEqual(jumps[:2],[5,-5]);self.assertGreaterEqual(jumps[2],15)   # +5 s, -5 s, then +60 s held to the end
            shown=[r for r in rows if 'late_ms' in r]
            # The picture follows the sound's position: after each seek it is shown within three frames of it.
            self.assertLess(float(np.median([abs(r['late_ms']) for r in shown])),150)
            # The second of pause shows no frames: about 1 s of file time is missing from the wall time.
            self.assertGreater(max(b['wall']-a['wall'] for a,b in zip(shown,shown[1:])),.8)
            # and the sound was held too: the picture resumes where it stopped, with no file time skipped.
            self.assertEqual([round(b['pts']-a['pts'],2) for a,b in zip(shown,shown[1:]) if .5<b['pts']-a['pts']<3],[])

    def sound_clip(self,temp,rate=30):
        import shutil
        if not (shutil.which('kilix-mpv') or shutil.which('mpv')):self.skipTest('mpv is not installed')
        clip=str(Path(temp)/'clip.mkv')
        made=subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i',f'testsrc2=size=64x48:rate={rate}','-f','lavfi','-i','sine=frequency=440',
                             '-t','30','-c:v','mpeg4','-g','10','-c:a','pcm_s16le',clip],capture_output=True)
        if made.returncode:self.skipTest('ffmpeg cannot make the clip')
        return clip

    def test_player_keeps_even_time_by_the_sound(self):
        with tempfile.TemporaryDirectory() as temp:
            clip=self.sound_clip(temp);log=Path(temp)/'log.jsonl'
            code,out,err=self.player('--audio-output','null','--log',str(log),'--frames','100',source=clip)
            self.assertEqual(code,0,err);self.assertIn(b'sound on',err)
            rows=[json.loads(line) for line in log.read_text().splitlines()]
            # The sound waits for the first picture, so nothing is late or dropped at the start.
            self.assertEqual([r['n'] for r in rows[:30] if r.get('dropped')],[])
            self.assertLess(abs(rows[0]['late_ms']),40)
            # mpv reports its position in steps of about 50 ms; pictures must still come one period apart.
            shown=[r['shown'] for r in rows if 'shown' in r]
            gaps=np.diff(shown[5:])*1e3
            self.assertGreater(len(gaps),80)
            self.assertGreater(float(np.mean(np.abs(gaps-1000/30)<12)),.8,np.round(gaps[:40],1).tolist())
            # and the picture stays with the sound over the whole run
            late=np.array([r['late_ms'] for r in rows if 'late_ms' in r])
            self.assertLess(float(np.percentile(np.abs(late),95)),25,np.round(late[:40],1).tolist())

    FAKE_SOUND=r"""#!/usr/bin/env python3
# Stands in for mpv: a position that runs at SPEED and is reported in 50 ms steps.
import json,os,socket,sys,time
path=next(a.split('=',1)[1] for a in sys.argv if a.startswith('--input-ipc-server='))
speed=float(os.environ['FAKE_SPEED']);base=time.monotonic();at=float(next(a.split('=',1)[1] for a in sys.argv if a.startswith('--start=')));paused=False
server=socket.socket(socket.AF_UNIX);server.bind(path);server.listen(1);c,_=server.accept();buffer=b''
while True:
    data=c.recv(4096)
    if not data:break
    buffer+=data
    while b'\n' in buffer:
        line,buffer=buffer.split(b'\n',1);q=json.loads(line);cmd=q['command'];value=None
        true=at if paused else at+speed*(time.monotonic()-base)
        if cmd[0]=='seek':at=float(cmd[1]);base=time.monotonic()
        elif cmd[0]=='set_property' and cmd[1]=='pause':at=true;base=time.monotonic();paused=bool(cmd[2])
        elif cmd[-1]=='time-pos':value=int(true/.05)*.05
        elif cmd[-1]=='true-pos':value=true
        elif cmd[-1]=='seeking':value=False
        c.sendall(json.dumps(dict(request_id=q['request_id'],error='success',data=value)).encode()+b'\n')
        if cmd[0]=='quit':sys.exit(0)
"""

    def fake_sound(self,temp,speed,start=3.):
        import importlib.util
        fake=Path(temp)/'fake-mpv';fake.write_text(self.FAKE_SOUND);fake.chmod(0o755)
        spec=importlib.util.spec_from_file_location('neuronte_play',ROOT/'tools/neuronte-play.py');play=importlib.util.module_from_spec(spec);spec.loader.exec_module(play)
        old=os.environ.get('FAKE_SPEED');os.environ['FAKE_SPEED']=str(speed)
        try:sound=play.Sound(str(fake),'unused',start,False,None,0.)
        finally:
            if old is None:del os.environ['FAKE_SPEED']
            else:os.environ['FAKE_SPEED']=old
        self.addCleanup(sound.close)
        return sound

    def test_sound_clock_is_steady_and_follows_a_sound_that_runs_fast(self):
        import time
        with tempfile.TemporaryDirectory() as temp:
            sound=self.fake_sound(temp,1.02)
            seen=[];end=time.perf_counter()+4
            while time.perf_counter()<end:
                seen.append((time.perf_counter(),sound.time()));time.sleep(.005)
            steps=np.diff([t for _,t in seen])/np.diff([w for w,_ in seen])
            # between checks the clock runs with the wall clock: no 50 ms stairs
            self.assertLess(float(np.percentile(np.abs(steps-1),90)),.2)
            self.assertGreater(float(np.mean(np.diff([t for _,t in seen])>0)),.95)
            # and it has followed the sound, which gained 80 ms on the wall clock in that time
            self.assertLess(abs(sound.time()-sound.ask('get_property','true-pos')),.045)

    def test_sound_clock_lands_on_a_seek_and_holds_while_paused(self):
        import time
        with tempfile.TemporaryDirectory() as temp:
            sound=self.fake_sound(temp,1.)
            for _ in range(5):sound.time();time.sleep(.03)
            sound.seek(40.)
            self.assertLess(abs(sound.time()-40.),.08)
            sound.pause(True);held=sound.time();time.sleep(.3)
            self.assertEqual(sound.time(),held)
            sound.pause(False);time.sleep(.2)
            self.assertLess(abs(sound.time()-held-.2),.05)

    def test_a_killed_player_takes_its_sound_and_decoder_with_it(self):
        # The ffmpeg command is a second child; the in-process decoder dies with the player.
        for decoder,children in [('ffmpeg',2)]+([('libav',1)] if (ROOT/'build/libneuronte-media.so').exists() else []):
            with self.subTest(decoder=decoder):self.killed_player(decoder,children)

    def killed_player(self,decoder,children):
        import signal,time
        with tempfile.TemporaryDirectory() as temp:
            clip=self.sound_clip(temp)
            cmd=[sys.executable,str(ROOT/'tools/neuronte-play.py'),clip,'--cols','6','--rows','3','--no-status','--audio-output','null','--loop','--decoder',decoder]
            r,w=os.pipe()
            with tempfile.TemporaryFile() as picture:
                env=dict(os.environ,COLUMNS='80',LINES='24');env.pop('KITTY_WINDOW_ID',None)   # inline pictures, so the file grows while it plays
                child=subprocess.Popen(cmd+['--input-fd',str(r)],stdout=picture,stderr=subprocess.DEVNULL,env=env,pass_fds=[r]);os.close(r)
                started=[]
                try:
                    end=time.time()+20
                    while time.time()<end and (len(started)<children or os.fstat(picture.fileno()).st_size<4096):   # playing
                        time.sleep(.05)
                        try:started=[int(x) for x in Path(f'/proc/{child.pid}/task/{child.pid}/children').read_text().split()]
                        except OSError:started=[]
                    self.assertEqual(len(started),children)
                    child.send_signal(signal.SIGKILL);child.wait(timeout=5)   # no chance to tidy up
                    end=time.time()+5
                    def alive(pid):
                        try:return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
                        except OSError:return False
                    while time.time()<end and any(alive(pid) for pid in started):time.sleep(.05)
                    self.assertEqual([pid for pid in started if alive(pid)],[])
                finally:
                    os.close(w)
                    if child.poll() is None:child.kill()
                    for pid in started:
                        try:os.kill(pid,signal.SIGKILL)
                        except OSError:pass

    @unittest.skipUnless(sys.platform.startswith('linux'), 'needs Linux parent-death signals')
    def test_child_dies_if_player_exits_before_child_setup(self):
        import select,signal,time
        ready_r,ready_w=os.pipe();go_r,go_w=os.pipe()
        script=r'''
import importlib.util,os,subprocess,sys
sys.path.insert(0,sys.argv[1])
spec=importlib.util.spec_from_file_location('play',sys.argv[1]+'/neuronte-play.py')
play=importlib.util.module_from_spec(spec);spec.loader.exec_module(play)
def wait_before_setup():
    os.write(int(sys.argv[2]),str(os.getpid()).encode()+b'\n')
    os.read(int(sys.argv[3]),1)
    play.with_us()
subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],preexec_fn=wait_before_setup)
'''
        parent=subprocess.Popen([sys.executable,'-c',script,str(ROOT/'tools'),str(ready_w),str(go_r)],
                                pass_fds=[ready_w,go_r],stderr=subprocess.PIPE)
        os.close(ready_w);os.close(go_r);child=None
        try:
            self.assertTrue(select.select([ready_r],[],[],10)[0], 'child never reached setup')
            child=int(os.read(ready_r,100).strip())
            parent.kill();parent.wait(timeout=5)
            os.write(go_w,b'x')
            def alive():
                try:return Path(f'/proc/{child}/stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
                except OSError:return False
            end=time.monotonic()+5
            while alive() and time.monotonic()<end:time.sleep(.02)
            self.assertFalse(alive(), 'child survived the player dying before parent-death setup')
        finally:
            os.close(ready_r);os.close(go_w)
            if parent.poll() is None:parent.kill();parent.wait(timeout=5)
            parent.stderr.close()
            if child is not None:
                try:os.kill(child,signal.SIGKILL)
                except OSError:pass

    def test_player_leaves_no_shared_memory_when_the_window_goes(self):
        import signal,time,glob
        with tempfile.TemporaryDirectory() as temp:
            clip=self.sound_clip(temp)
            cmd=[sys.executable,str(ROOT/'tools/neuronte-play.py'),clip,'--cols','6','--rows','3','--no-status','--audio-output','null','--transport','shm','--loop']
            r,w=os.pipe()
            with tempfile.TemporaryFile() as picture:
                child=subprocess.Popen(cmd+['--input-fd',str(r)],stdout=picture,stderr=subprocess.PIPE,env=dict(os.environ,COLUMNS='80',LINES='24'),pass_fds=[r]);os.close(r)
                try:
                    mine=f'/dev/shm/neuronte-play-{child.pid}-*'
                    end=time.time()+20
                    while time.time()<end and len(glob.glob(mine))<3:time.sleep(.05)
                    self.assertEqual(len(glob.glob(mine)),3)      # nobody reads them here, so three wait
                    child.send_signal(signal.SIGHUP);time.sleep(.05);child.send_signal(signal.SIGTERM)   # a closing terminal sends more than one
                    child.wait(timeout=20)
                finally:
                    os.close(w)
                    if child.poll() is None:child.kill()
                    child.stderr.close()
                self.assertEqual(glob.glob(mine),[])
                picture.seek(0);self.assertTrue(picture.read().endswith(b'\x1b[?1049l'))   # and the terminal is put back

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
