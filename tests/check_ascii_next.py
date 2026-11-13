"""Repack measured ASCII assets and check native quality against their teacher."""
import ctypes as C
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'train'))
import decompose
import known_bundle
import pack

weights=ROOT/'weights'
evidence=json.loads((weights/'neuronte-ascii-next.validation.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in evidence['files'].items():
    assert sha(weights/name)==digest,name

lib=C.CDLL(str(Path(sys.argv[1]).resolve()))
lib.neuronte_open_file.argtypes=[C.c_char_p,C.POINTER(C.c_void_p)]
lib.neuronte_close.argtypes=[C.c_void_p]
lib.neuronte_route.argtypes=[C.c_void_p,C.c_uint32]
lib.neuronte_coverage.argtypes=[C.c_void_p,C.c_uint32,C.c_int,C.c_int,C.c_int,C.POINTER(C.c_float)]
handles=[]
def open_model(path):
    handle=C.c_void_p()
    assert lib.neuronte_open_file(str(path).encode(),C.byref(handle))==0,path
    handles.append(handle)
    return handle
def coverage(handle,scalars,w,h):
    result=np.empty((len(scalars),h,w),dtype=np.float32)
    for i,scalar in enumerate(scalars):
        assert lib.neuronte_coverage(handle,scalar,w,h,0,
               result[i].ctypes.data_as(C.POINTER(C.c_float)))==0
    return result
def nearest(coverage,target):
    result=[]
    for i,glyph in enumerate(coverage):
        other=int(np.abs(target-glyph).sum((1,2)).argmin())
        result.append(bool(np.abs(target[i]-target[other]).sum()<.5))
    return np.asarray(result)
def metrics(got,wanted):
    error=np.abs(got-wanted)
    firm=int(((got>.5)!=(wanted>.5))[np.abs(wanted-.5)>=.1].sum())
    return float(error.mean((1,2)).mean()),float(np.quantile(error,.99)),firm,error.mean((1,2))

try:
    original=(weights/'neuronte-split-v5.nrt').read_bytes()
    baseline=open_model(weights/'neuronte-ascii-v0.nrt')
    old_bundle=open_model(weights/'neuronte-split-v5.nrt')
    models=[]
    for model in evidence['models']:
        sources=[str(weights/name) for name in model['sources']]
        direct=(pack.bundle(sources)[0] if model['mode']=='repertoire' else pack.pack(sources[0]))
        assert direct==(weights/model['direct']).read_bytes()
        full,proof=known_bundle.replace_known(original,sources,0)
        assert full==(weights/model['bundle']).read_bytes()
        assert proof['replaced_scalars']==95 and proof['original_members']==6
        direct_handle=open_model(weights/model['direct'])
        full_handle=open_model(weights/model['bundle'])
        routes={c:i for i,path in enumerate(sources) for c in pack.scalars(path)[1]}
        assert set(routes)==set(decompose.SCALARS)
        for c in decompose.SCALARS:
            assert lib.neuronte_route(direct_handle,c)==routes[c]
            assert lib.neuronte_route(full_handle,c)==routes[c]+6
        misses=sorted(set(range(0,0x110000,997))|{0xd800,0xdfff,0x10ffff,0xffffffff})
        misses=[c for c in misses if c not in routes]
        for c in misses:
            assert lib.neuronte_route(old_bundle,c)==lib.neuronte_route(full_handle,c)
        representatives=[0,1,127,0xa0,0x391,0x410,0x2500,0x2588,0x2801,0x1f600,0x10ffff,0xffffffff]
        assert np.array_equal(coverage(old_bundle,representatives,9,17),
                              coverage(full_handle,representatives,9,17))
        assert model['qualification_seeds']==[0,1] and model['qualification_sizes']==19
        for row in model['scores']:
            ref=row['baseline'];pixels=95*row['cell'][0]*row['cell'][1]
            assert row['coverage_mae']<=ref['coverage_mae']+.0015
            assert row['coverage_error_p99']<=ref['coverage_error_p99']+.02
            assert row['firm_wrong_pixels']/pixels<=ref['firm_wrong_pixels']/pixels+.0005
            assert row['max_glyph_mae_increase']<=.01 and not row['lost_identities']
        assert {s['seed'] for s in model['scores']}=={0,1} and len(model['scores'])==38
        models.append((model,direct_handle,full_handle))
    count=0
    with tempfile.TemporaryDirectory(prefix='ascii-next-') as temporary:
        directory=Path(temporary)
        decompose.prepare(directory)
        assert sha(directory/'teacher.npy')==evidence['teacher_sha256']
        fields=np.load(directory/'teacher.npy',allow_pickle=False)
        sizes=sorted({tuple(s['cell']) for s in models[0][0]['scores']})
        assert len(sizes)==19
        for w,h in sizes:
            target=decompose.teacher_masks(fields,w,h)
            original_coverage=coverage(baseline,decompose.SCALARS,w,h)
            b_mae,b_p99,b_firm,b_glyph=metrics(original_coverage,target)
            original_identity=nearest(original_coverage,target)
            for model,direct_handle,full_handle in models:
                got=coverage(direct_handle,decompose.SCALARS,w,h)
                assert np.array_equal(got,coverage(full_handle,decompose.SCALARS,w,h))
                mae,p99,firm,glyph=metrics(got,target)
                expected=next(s for s in model['scores'] if s['seed']==0 and s['cell']==[w,h])
                assert abs(mae-expected['coverage_mae'])<=1e-6,(model['name'],w,h,'mean')
                assert abs(p99-expected['coverage_error_p99'])<=1e-6,(model['name'],w,h,'p99')
                assert firm==expected['firm_wrong_pixels']
                assert mae<=b_mae+.0015 and p99<=b_p99+.02
                assert firm/got.size<=b_firm/got.size+.0005
                assert np.all(glyph<=b_glyph+.01)
                assert np.all(nearest(got,target)[original_identity])
                count+=len(decompose.SCALARS)
    print(f'check_ascii_next: {count} complete glyphs pass teacher gates and exact direct/bundle equivalence')
finally:
    for handle in handles:lib.neuronte_close(handle)
