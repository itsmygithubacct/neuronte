"""Compare packed ASCII cases with independent calls to each trained member."""
import ctypes as C
import json
from pathlib import Path
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'train'))
import decompose as d

lib=C.CDLL(str(Path(sys.argv[1]).resolve()))
lib.neuronte_open_file.argtypes=[C.c_char_p,C.POINTER(C.c_void_p)]
lib.neuronte_close.argtypes=[C.c_void_p]
lib.neuronte_coverage.argtypes=[C.c_void_p,C.c_uint32,C.c_int,C.c_int,C.c_int,C.POINTER(C.c_float)]
lib.neuronte_route.argtypes=[C.c_void_p,C.c_uint32]
manifest_path=Path(sys.argv[2]).resolve()
manifest=json.loads(manifest_path.read_text());directory=manifest_path.parent
count=0

def open_net(path):
    handle=C.c_void_p()
    assert lib.neuronte_open_file(str(path).encode(),C.byref(handle))==0
    return handle

def coverage(handle,scalar,w,h,samples):
    buffer=(C.c_float*(w*h))()
    assert lib.neuronte_coverage(handle,scalar,w,h,samples,buffer)==0
    return np.frombuffer(buffer,np.float32).reshape(h,w).copy()

for case in manifest['cases']:
    mode=case.get('design')
    if mode not in ('spatial','repertoire'):continue
    parts,seed=case['parts'],case['seed']
    specs=d.specs(mode,parts)
    path=directory/manifest['models'][case['members'][0]]['file']
    whole=open_net(path)
    members=[open_net(directory/(s['name']+f'-s{seed}.nrt')) for s in specs]
    try:
        for w,h in ((8,16),(16,32),(48,96)):
            samples=2 if w<24 else 1
            for scalar in d.SCALARS:
                got=coverage(whole,scalar,w,h,0)
                if mode=='repertoire':
                    index=next(i for i,s in enumerate(specs) if scalar in s['scalars'])
                    assert lib.neuronte_route(whole,scalar)==index
                    expected=coverage(members[index],scalar,w,h,samples)
                else:
                    cols,rows=d.GRIDS[parts];tw,th=w//cols,h//rows
                    expected=np.empty((h,w),np.float32)
                    for i,member in enumerate(members):
                        x,y=i%cols*tw,i//cols*th
                        expected[y:y+th,x:x+tw]=coverage(member,scalar,tw,th,samples)
                assert got.tobytes()==expected.tobytes(), (case['name'],scalar,w,h,float(abs(got-expected).max()))
                count+=1
    finally:
        lib.neuronte_close(whole)
        for member in members:lib.neuronte_close(member)
print(f'check_decomposition_assets: {count} complete glyphs bit-identical to independent member calls')
