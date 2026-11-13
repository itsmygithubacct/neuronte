"""Check assembled spatial exports against an analytic full-cell field."""
import ctypes as c
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'train'))
import decompose as d,pack,strokes
sp=importlib.util.spec_from_file_location('assembly',ROOT/'tools/decomposition-tiled.py')
a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)


class AssemblyTests(unittest.TestCase):
    def test_identity_codes_and_odd_cell_sample_boundaries(self):
        lib=c.CDLL(str(ROOT/'build/libneuronte.so'))
        lib.neuronte_open_file.argtypes=[c.c_char_p,c.POINTER(c.c_void_p)]
        lib.neuronte_close.argtypes=[c.c_void_p]
        lib.neuronte_coverage.argtypes=[c.c_void_p,c.c_uint32,c.c_int,c.c_int,c.c_int,c.POINTER(c.c_float)]
        with tempfile.TemporaryDirectory() as directory:
            paths=[]
            for i,p in enumerate(d.specs('spatial',4,'pixel')):
                x0,x1,y0,y1=p['region'];sx=x1-x0;sy=y1-y0
                weights=[0.]*90;weights[0]=.5*sx;weights[1]=.2*sy;weights[26]=.05
                layers={'l1':dict(rows=1,cols=90,weight=weights,bias=[x0+.5*sx+.4*y0+.2*sy+.1])}
                for key in ('l2','l3','out'):layers[key]=dict(rows=1,cols=1,weight=[1.],bias=[-.7 if key=='out' else 0.])
                doc=dict(format='neuronte-weights',version=1,shape=dict(position_octaves=6,code_bits=64,hidden_width=1,hidden_layers=3,tau=.15/sx,parity_masks=[hex(m) for m in strokes.masks()]),layers=layers,
                         training=dict(experiment=dict(region=p['region'],scalars=[0,1,0x1cd00,0x1cd01],seed=0,identity={'teacher':{'identity':{'expert':'pixel'}}})))
                path=Path(directory)/f'part{i}.json';path.write_text(json.dumps(doc));paths.append(path)
            doc=a.build(paths);p=Path(directory)/'tiled.json';p.write_text(json.dumps(doc));packed=p.with_suffix('.nrt');packed.write_bytes(pack.pack(p))
            handle=c.c_void_p();self.assertEqual(lib.neuronte_open_file(str(packed).encode(),c.byref(handle)),0)
            try:
                for w,h in ((1,2),(7,13),(8,16),(23,47),(24,48),(25,49)):
                    for samples in (0,1,2,3):
                        ss=samples or (2 if w<24 else 1)
                        x=(np.arange(w*ss)+.5)/(w*ss);y=(np.arange(h*ss)+.5)/(h*ss)*2
                        for cp in (0,1,0x1cd00,0x1cd01):
                            f=x[None]+.4*y[:,None]-.6+.05*(2*(cp&1)-1)
                            want=np.clip(.5+f*.15*w*ss,0,1).reshape(h,ss,w,ss).mean((1,3))
                            got=np.empty((h,w),np.float32)
                            self.assertEqual(lib.neuronte_coverage(handle,cp,w,h,samples,got.ctypes.data_as(c.POINTER(c.c_float))),0)
                            np.testing.assert_allclose(got,want,rtol=0,atol=2e-6)
            finally:lib.neuronte_close(handle)
            with self.assertRaises(ValueError):a.build(paths[::-1])
            with self.assertRaises(ValueError):a.build(paths[:-1])


if __name__=='__main__':unittest.main()
