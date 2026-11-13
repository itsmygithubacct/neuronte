"""Exercise large bundle routing, field selection and malformed count bounds."""
import ctypes as C
import json
import os
from pathlib import Path
import struct
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'train'))
import pack
import strokes

lib=C.CDLL(str(Path(sys.argv[1]).resolve()))
lib.neuronte_open.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_void_p)]
lib.neuronte_open_file.argtypes=[C.c_char_p,C.POINTER(C.c_void_p)]
lib.neuronte_close.argtypes=[C.c_void_p]
lib.neuronte_route.argtypes=[C.c_void_p,C.c_uint32]
lib.neuronte_coverage.argtypes=[C.c_void_p,C.c_uint32,C.c_int,C.c_int,C.c_int,C.POINTER(C.c_float)]

def opened(image):
    handle=C.c_void_p()
    rc=lib.neuronte_open(image,len(image),C.byref(handle))
    return rc,handle

with tempfile.TemporaryDirectory(prefix='neuronte-bundles-') as tmp:
    directory=Path(tmp)
    paths=[]
    masks=[hex(m) for m in strokes.masks()]
    for i in range(128):
        doc={'format':'neuronte-weights','version':1,
             'shape':{'position_octaves':6,'code_bits':64,'hidden_layers':3,
                      'hidden_width':1,'tau':.15,'parity_masks':masks},
             'training':{'set':f'part-{i}','labelled':f'U+{32+i:04X}'},
             'layers':{name:{'rows':rows,'cols':cols,'weight':[0.]*(rows*cols),
                             'bias':[(i-64)*.001] if name=='out' else [0.]*rows}
                       for name,rows,cols in pack.layers(1)}}
        path=directory/f'{i}.json';path.write_text(json.dumps(doc));paths.append(str(path))
    for count in (17,64,128):
        image,ranges=pack.bundle(paths[:count],fallback=count-1)
        assert len(ranges)==count
        rc,handle=opened(image);assert rc==0 and handle
        for i in range(count):
            assert lib.neuronte_route(handle,32+i)==i
            field=(C.c_float*128)()
            assert lib.neuronte_coverage(handle,32+i,8,16,2,field)==0
            expected=.5+(i-64)*.001*.15*8*2
            assert max(abs(v-expected) for v in field)<2e-7
        assert lib.neuronte_route(handle,0x2603)==count-1
        lib.neuronte_close(handle)
        packed=directory/'bundle.nrt';packed.write_bytes(image)
        assert lib.neuronte_open_file(os.fsencode(packed),C.byref(handle))==0
        lib.neuronte_close(handle)
    gate={'format':'neuronte-gate','version':1,'nets':[f'part-{i}' for i in range(128)],
          'hidden_width':1,'parity_masks':masks,
          'layers':{'l1':{'rows':1,'cols':64,'weight':[0.]*64,'bias':[0.]},
                    'out':{'rows':128,'cols':1,'weight':[0.]*128,'bias':list(range(128))}}}
    gpath=directory/'gate.json';gpath.write_text(json.dumps(gate))
    gated,_=pack.bundle(paths,str(gpath));rc,handle=opened(gated);assert rc==0
    assert lib.neuronte_route(handle,0x2603)==127
    assert lib.neuronte_route(handle,32)==0 # table precedes the gate
    lib.neuronte_close(handle)
    for offset,value in ((12,0),(12,129),(20,128),(28+4*128+8,128)):
        bad=bytearray(image);struct.pack_into('<I',bad,offset,value)
        rc,handle=opened(bytes(bad));assert rc!=0 and not handle
        packed.write_bytes(bad)
        assert lib.neuronte_open_file(os.fsencode(packed),C.byref(handle))!=0 and not handle
    for size in (12,27,28,28+4*128-1,len(image)-1):
        rc,handle=opened(image[:size]);assert rc!=0 and not handle
    for inventory in ([],paths+[paths[0]]):
        try:pack.bundle(inventory)
        except SystemExit:pass
        else:raise AssertionError('invalid bundle count packed')
    # Drawing v5 retains its independent 16-member limit.
    drawing=b'NEURONTE'+struct.pack('<II',5,17)+bytes(17*8)
    rc,handle=opened(drawing);assert rc!=0 and not handle
print('check_bundle_counts: 17/64/128 members, table/gate selection, fields and bounds passed')
