"""Verify labelled overrides preserve original gate and coverage behavior."""
import ctypes as c
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'train'))
import pack
spec=importlib.util.spec_from_file_location('override',ROOT/'tools/override-bundle.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)


class OverrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib=c.CDLL(str(ROOT/'build/libneuronte.so'))
        cls.lib.neuronte_open_file.argtypes=[c.c_char_p,c.POINTER(c.c_void_p)]
        cls.lib.neuronte_close.argtypes=[c.c_void_p]
        cls.lib.neuronte_route.argtypes=[c.c_void_p,c.c_uint32]
        cls.lib.neuronte_coverage.argtypes=[c.c_void_p,c.c_uint32,c.c_int,c.c_int,c.c_int,c.POINTER(c.c_float)]
        cls.base=(ROOT/'weights/neuronte-split-v5.nrt').read_bytes()
        cls.pixel=pack.pack(ROOT/'weights/neuronte-pixel-v1.json')
        cls.labels=sorted(pack.scalars(ROOT/'weights/neuronte-pixel-v1.json')[1])

    def test_routes_unknowns_and_native_coverage(self):
        groups=(self.labels[:164],self.labels[164:])
        data=o.override(self.base,[(self.pixel,g) for g in groups])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'overrides.nrt';path.write_bytes(data)
            handles=[]
            try:
                for p in (ROOT/'weights/neuronte-split-v5.nrt',path):
                    handle=c.c_void_p()
                    self.assertEqual(self.lib.neuronte_open_file(str(p).encode(),c.byref(handle)),0)
                    handles.append(handle)
                first,second=handles
                expected={cp:6+i for i,g in enumerate(groups) for cp in g}
                # Entire labelled repertoire plus many misses across the code space.
                codes=set(range(32,127))|set(self.labels)|set(range(0,0x110000,67))|{0xfffd,0x10ffff,0x110000,0xffffffff}
                for cp in codes:
                    old=self.lib.neuronte_route(first,cp)
                    new=self.lib.neuronte_route(second,cp)
                    self.assertEqual(new,expected.get(cp,old),(cp,old,new))
                samples=self.labels[::17]+[65,0x2500,0x2600,0x2801,0x00e9,0xfffd,0x1234,0x10ffff]
                for w,h in ((1,2),(7,13),(24,48),(25,49)):
                    a=np.empty((h,w),np.float32);b=np.empty_like(a)
                    for cp in samples:
                        for handle,out in ((first,a),(second,b)):
                            self.assertEqual(self.lib.neuronte_coverage(handle,cp,w,h,0,out.ctypes.data_as(c.POINTER(c.c_float))),0)
                        np.testing.assert_array_equal(a,b)
            finally:
                for h in handles:self.lib.neuronte_close(h)

    def test_refuse_missing_or_duplicate_labels_and_nested_bundles(self):
        for additions in ([],[(self.pixel,[])],[(self.pixel,[0x10ffff])],
                          [(self.pixel,[self.labels[0]]),(self.pixel,[self.labels[0]])],
                          [(self.base,self.labels)]):
            with self.assertRaises(ValueError):o.override(self.base,additions)
        with self.assertRaises(ValueError):o.override(self.base+b'x',[(self.pixel,self.labels)])


if __name__=='__main__':unittest.main()
