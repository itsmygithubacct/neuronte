"""Two-cell colour API acceptance from an analytic, untrained fixture.

The fixture draws f=1.25-x across two consecutive cells, with independent
red/green half palettes. It exercises internal code features, range routing,
edge records, coverage, compositing and Unicode boundary preservation.
Usage: python3 tests/check_halves.py LIB.so
"""
import ctypes as C
from pathlib import Path
import struct
import sys
import numpy as np

lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
P,I,U,F,B = C.c_void_p,C.c_int,C.c_uint32,C.POINTER(C.c_float),C.POINTER(C.c_uint8)
lib.neuronte_open.argtypes = [P,C.c_size_t,C.POINTER(P)]
lib.neuronte_close.argtypes = [P]
lib.neuronte_route.argtypes = [P,U]
lib.neuronte_route_half.argtypes = [P,U,I]
lib.neuronte_set_samples.argtypes = lib.neuronte_set_snap.argtypes = lib.neuronte_set_theme.argtypes = [P,I]
lib.neuronte_coverage.argtypes = [P,U,I,I,I,F]
lib.neuronte_coverage_half.argtypes = [P,U,I,I,I,I,F]
lib.neuronte_coverage_layers.argtypes = [P,U,I,I,I,F,B]
lib.neuronte_coverage_layers_half.argtypes = [P,U,I,I,I,I,F,B]
lib.neuronte_draw_scalar.argtypes = [P,P,I,I,I,I,I,I,I,U,U]
lib.neuronte_draw_half.argtypes = [P,P,I,I,I,I,I,I,I,U,I,U]

SCALAR, RIGHT = 0x1F600, 0x12F600
H=R=8

def fixture():
    # 420-byte colour header, documented version 3 shape, one layer.
    header = struct.pack('<8s5If6I43I', b'NEURONTE',3,6,64,H,3,1.0,1,32,5,R,2,32,*([1]*43))
    dark = np.zeros((32,3),np.uint8); light = dark.copy()
    dark[2],dark[3] = (255,0,0),(0,255,0)
    light[2],light[3] = (128,0,0),(0,128,0)
    header += dark.tobytes()+light.tobytes()
    l1=np.zeros((H,90),np.float32); b1=np.zeros(H,np.float32)
    l1[0,0],l1[0,26+20],b1[0] = -.5,-.5,2.25
    hidden=np.zeros((H,H),np.float32); hidden[0,0]=1
    hb=np.zeros(H,np.float32)
    out=np.zeros((1,H),np.float32); out[0,0]=1
    ob=np.array([-2],np.float32)
    head=np.zeros((R,64),np.float32); head[0,20]=1
    headbias=np.zeros(R,np.float32); headbias[0]=1
    palette=np.zeros((5,R),np.float32); palette[0,0]=1
    pb=np.array([-1,1,-1,-1,-1],np.float32)
    params=b''.join(a.astype('<f4').tobytes() for a in
                    (l1,b1,hidden,hb,hidden,hb,out,ob,head,headbias,palette,pb))
    # Left has no boundary in its cell. Right has a falling edge at x=.25.
    edges=struct.pack('<IHHIHHfI',SCALAR,0,0,RIGHT,1,0,.25,0)
    return header+params+edges, len(header+params)


def opened(data, expected=0):
    ptr=P()
    result=lib.neuronte_open(data,len(data),C.byref(ptr))
    assert result==expected,(result,expected)
    return ptr


def coverage(ptr, scalar, half=None, w=8,h=16,ss=1,layers=False):
    out=np.zeros((h,w),np.float32); entry=np.zeros(1,np.uint8)
    args=[ptr,scalar]+([] if half is None else [half])+[w,h,ss,out.ctypes.data_as(F)]
    if layers:
        args += [entry.ctypes.data_as(B)]
    name='neuronte_coverage'+('_layers' if layers else '')+('_half' if half is not None else '')
    assert getattr(lib,name)(*args)==0
    return (out,entry[0]) if layers else out


data, edges_at=fixture()
ptr=opened(data)
try:
    for ss in (1,2,0):
        for w in (8,12):
            assert lib.neuronte_set_samples(ptr,ss)==0
            # At these widths the quarter-cell boundary is an integer pixel,
            # so snapping leaves both the analytic picture and seam unchanged.
            for snap in (0,32):
                assert lib.neuronte_set_snap(ptr,snap)==0
                for half in (0,1):
                    got,entry=coverage(ptr,SCALAR,half,w,2*w,ss,True)
                    assert entry==2+half
                    samples=ss or 2
                    x=(np.arange(w*samples)+.5)/(w*samples)+half
                    expected=np.clip(.5+w*samples*(1.25-x),0,1).reshape(w,samples).mean(1)
                    # Scalar float32 field evaluation at 12px differs from
                    # the analytic float64 ramp by at most one rounded ulp.
                    np.testing.assert_allclose(got,np.broadcast_to(expected,(2*w,w)),atol=1e-6)
                    np.testing.assert_array_equal(coverage(ptr,SCALAR,half,w,2*w,ss),got)
                    for theme in (0,1):
                        assert lib.neuronte_set_theme(ptr,theme)==0
                        pixels=np.zeros((2*w,2*w),np.uint32)
                        # The half goes at its requested pen, not an implicit
                        # scalar-dependent location. Neighbour cell untouched.
                        assert lib.neuronte_draw_half(ptr,pixels.ctypes.data,2*w,2*w,2*w,
                                                     half*w,0,w,2*w,SCALAR,half,0x80ABCDEF)==0
                        out=pixels[:,half*w:(half+1)*w]
                        np.testing.assert_array_equal(out>>24,np.floor(got*128+.5).astype(np.uint32))
                        colour=(255 if theme==0 else 128) << (16 if half==0 else 8)
                        assert ((out[got>0]&0xFFFFFF)==colour).all()
                        assert not pixels[:,(1-half)*w:(2-half)*w].any()
    # Old APIs keep invalid scalar -> replacement semantics; they must not
    # grant access to private half codes through a Unicode scalar argument.
    for invalid in (RIGHT,0x110000,0x1FFFFF,0xFFFFFFFF,0xD800):
        np.testing.assert_array_equal(coverage(ptr,invalid),coverage(ptr,0xFFFD))
        a,e=coverage(ptr,invalid,layers=True)
        b,f=coverage(ptr,0xFFFD,layers=True)
        np.testing.assert_array_equal(a,b); assert e==f==2
    np.testing.assert_array_equal(coverage(ptr,SCALAR,0),coverage(ptr,SCALAR))
    guard=np.full((16,8),-1,np.float32); entries=np.full(1,99,np.uint8)
    pix=np.full((16,8),0x12345678,np.uint32)
    for scalar,half in ((0xD800,0),(0x110000,0),(0xFFFFFFFF,1),(SCALAR,-1),(SCALAR,2),(0xF0000,1)):
        assert lib.neuronte_route_half(ptr,scalar,half)==-1
        assert lib.neuronte_coverage_half(ptr,scalar,half,8,16,1,guard.ctypes.data_as(F))==-1
        assert lib.neuronte_coverage_layers_half(ptr,scalar,half,8,16,1,guard.ctypes.data_as(F),entries.ctypes.data_as(B))==-1
        assert lib.neuronte_draw_half(ptr,pix.ctypes.data,8,8,16,0,0,8,16,scalar,half,0xFFFFFFFF)==-1
        assert (guard==-1).all() and entries[0]==99 and (pix==0x12345678).all()
    assert lib.neuronte_route_half(ptr,0xEFFFF,1)==0  # largest private code 0x1FFFFF
finally:
    lib.neuronte_close(ptr)

# Bundle range lookup includes the right code, without changing old APIs.
header=struct.pack('<8s5I2I6I',b'NEURONTE',2,2,2,0,0,len(data),len(data),
                   SCALAR,SCALAR,0,RIGHT,RIGHT,1)
bundle=header+data+data
ptr=opened(bundle)
try:
    assert lib.neuronte_route_half(ptr,SCALAR,0)==0
    assert lib.neuronte_route_half(ptr,SCALAR,1)==1
    assert lib.neuronte_route(ptr,RIGHT)==0
    assert coverage(ptr,SCALAR,1,layers=True)[1]==3
finally:
    lib.neuronte_close(ptr)
# Invalid internal codes cannot silently alias the low 21 input bits.
last=bytearray(data); struct.pack_into('<I',last,edges_at+8,0x1FFFFF)
lib.neuronte_close(opened(bytes(last)))
last=bytearray(bundle); struct.pack_into('<II',last,48,0x1FFFFF,0x1FFFFF)
ptr=opened(bytes(last))
assert lib.neuronte_route_half(ptr,0xEFFFF,1)==1
lib.neuronte_close(ptr)
bad=bytearray(data); struct.pack_into('<I',bad,edges_at+8,0x200000)
opened(bytes(bad),-2)
bad=bytearray(bundle); struct.pack_into('<II',bad,48,0x200000,0x200000)
opened(bytes(bad),-2)
print('check_halves: analytic left/right colour, seam, palettes, routing, private codes and Unicode boundaries passed')
