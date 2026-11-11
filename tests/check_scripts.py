"""All trained Greek/Russian scalars route and render through the new bundle.

Usage: check_scripts.py LIB BUNDLE ACCENT.json [--standalone] [--out REPORT]
The independent float64 reference evaluates all115 new scalars, including
Russian Yo and Greek final sigma. A few asymmetric letters also use48px.
"""
import argparse
import ctypes as ct
import json
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'train'))
import pack
from check_emoji import reference


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('lib');p.add_argument('bundle');p.add_argument('accent')
    p.add_argument('--standalone',action='store_true');p.add_argument('--out');a=p.parse_args()
    greek=list(range(0x391,0x3a2))+list(range(0x3a3,0x3aa))+list(range(0x3b1,0x3ca))
    russian=[0x401,*range(0x410,0x450),0x451]
    assert len(greek)==49 and len(russian)==66
    d=json.loads(Path(a.accent).read_text());trained=pack.scalars(a.accent)[1]
    assert set(greek+russian)<=trained
    lib=ct.CDLL(str(Path(a.lib).resolve()));P=ct.c_void_p;I=ct.c_int;U=ct.c_uint32
    lib.neuronte_open_file.argtypes=[ct.c_char_p,ct.POINTER(P)];lib.neuronte_close.argtypes=[P]
    lib.neuronte_coverage.argtypes=[P,U,I,I,I,P];lib.neuronte_route.argtypes=[P,U]
    h=P();assert lib.neuronte_open_file(a.bundle.encode(),ct.byref(h))==0
    differences=[]
    for s in greek+russian:
        assert lib.neuronte_route(h,s)==(0 if a.standalone else 3),f'wrong route U+{s:X}'
        for cw in ((8,16,48) if s in (0x393,0x3a9,0x3c2,0x3c6,0x401,0x416,0x429,0x44f,0x451) else (16,)):
            cov=np.zeros((2*cw,cw),np.float32)
            assert lib.neuronte_coverage(h,s,cw,2*cw,2,cov.ctypes.data)==0
            ref=reference(d,s,cw,2)[0]
            difference=float(np.abs(cov-ref).max());assert difference<1e-3,(s,cw,difference)
            assert cov.sum()>0,f'lost U+{s:X}'
            differences.append(difference)
    lib.neuronte_close(h)
    report={'passed':True,'greek':49,'russian':66,'coverage_cases':len(differences),'numpy_max_difference':max(differences)}
    print(json.dumps(report))
    if a.out:Path(a.out).write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
