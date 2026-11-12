"""Independent packed C acceptance for the original two-cell emoji bundle.

Usage: check_emoji.py LIB BUNDLE JSON... --out REPORT [--manifest FILE] [--report-only]

Scores every half/layer against the recorded float16 training grid and exact
palette head; unused layers must have zero positive coverage. Intentionally
empty half layers are reported separately and must also remain empty. Used
nonempty halves have mean16px IoU >= .990 for each expert, no lost layer or
zero coverage, and RGB mean error <=2/255 in each theme at12/16/32px.
A separate float64 numpy evaluation checks sampled halves against the C API.
--manifest additionally requires the complete 300-scalar/600-half, three-expert
publication inventory. Without it, individual training shards remain testable.
"""
import argparse
import ctypes as ct
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'train'))
import glyphs
import pack
import snap
import strokes
from colour_sources import drawing_at
from check_icon_quality import composite, counts, interpolate, sample_points, THEMES


def arrays(d, group):
    return {k:(np.asarray(v['weight'],np.float32).astype(np.float64).reshape(v['rows'],v['cols']),
               np.asarray(v['bias'],np.float32).astype(np.float64)) for k,v in d[group].items()}


def features(s,masks):
    return np.asarray([2*((s>>i)&1)-1 for i in range(21)]+[2*((s&m).bit_count()%2)-1 for m in masks],np.float64)


def head(d,s):
    h=arrays(d,'head'); code=features(s,[int(v,16) for v in d['shape']['parity_masks']])
    y=np.maximum(h['h1'][0]@code+h['h1'][1],0)
    bits=(h['out'][0]@y+h['out'][1]).reshape(-1,5)>0
    return np.sum(bits*(1<<np.arange(5)),axis=1).tolist()


def reference(d,s,cw,ss,records=None):
    rec=None if records is None else records[s]
    xs=snap.sample_positions(cw,ss,None if rec is None else snap.axis_knots(rec,0,cw,2*cw),cw)
    ys=snap.sample_positions(2*cw,ss,None if rec is None else snap.axis_knots(rec,1,cw,2*cw),cw)
    yy,xx=np.meshgrid(ys,xs,indexing='ij'); xy=np.stack([xx.ravel(),yy.ravel()],1)
    f=[xy[:,:1]*2-1,xy[:,1:]-1]
    for i in range(6):
        w=2*math.pi*2**i; f += [np.sin(w*xy),np.cos(w*xy)]
    code=features(s,[int(v,16) for v in d['shape']['parity_masks']])
    x=np.column_stack(f+[np.broadcast_to(code,(len(xy),64))])
    for i,(w,b) in enumerate(arrays(d,'layers').values()):
        x=x@w.T+b
        if i<3: x=np.maximum(x,0)
    cv=np.clip(.5+x*float(np.float32(d['shape']['tau']))*cw*ss,0,1)
    return cv.T.reshape(-1,2*cw,ss,cw,ss).mean((2,4))


def bind(path,bundle):
    lib=ct.CDLL(str(Path(path).resolve())); ptr=ct.c_void_p; I=ct.c_int; U=ct.c_uint32
    lib.neuronte_open_file.argtypes=[ct.c_char_p,ct.POINTER(ptr)]
    lib.neuronte_close.argtypes=[ptr]
    lib.neuronte_set_snap.argtypes=[ptr,I]
    lib.neuronte_set_theme.argtypes=[ptr,I]
    lib.neuronte_layers.argtypes=[ptr]
    lib.neuronte_route_half.argtypes=[ptr,U,I]
    lib.neuronte_coverage_layers_half.argtypes=[ptr,U,I,I,I,I,ptr,ptr]
    lib.neuronte_draw_half.argtypes=[ptr,ptr,I,I,I,I,I,I,I,U,I,U]
    h=ptr(); assert lib.neuronte_open_file(str(bundle).encode(),ct.byref(h))==0, 'C loader rejected emoji bundle'
    return lib,h


def c_mask(lib,h,s,cw,k,ss=None):
    half=int(s>=0x110000); scalar=s-half*0x110000
    cov=np.zeros((k,2*cw,cw),np.float32); ent=(ct.c_uint8*k)()
    rc=lib.neuronte_coverage_layers_half(h,scalar,half,cw,2*cw,ss or (2 if cw<24 else 1),cov.ctypes.data,ent)
    assert rc==0, f'C half coverage failed U+{scalar:04X} half{half}: {rc}'
    return cov,list(ent)


def publication_inventory(manifest_path, paths):
    raw=Path(manifest_path).read_bytes();manifest=json.loads(raw)
    assert manifest['version']==1 and manifest['cell_columns']==2, 'wrong emoji manifest format'
    listed=[int(item['scalar'].removeprefix('U+'),16) for item in manifest['glyphs']]
    expected=set(listed)
    assert len(listed)==len(expected)==300, 'manifest must name exactly 300 distinct source scalars'
    assert all(0<=s<=0xeffff and not 0xd800<=s<=0xdfff for s in expected), 'invalid wide source scalar'
    assert len(paths)==3, 'publication requires exactly three experts'
    owners={};sources={};experts=[]
    for index,path in enumerate(paths):
        d=json.loads(Path(path).read_text());t=d['training']
        assert t.get('cell_columns')==2, 'publication expert is not two-cell'
        drawing=Path(pack.ROOT)/t['drawing'];palette=Path(pack.ROOT)/t['palette']
        source=strokes.parse_layers(str(drawing),strokes.palette(str(palette)))
        assert {ord(c) for c in source}==expected, 'manifest differs from the actual source drawing set'
        sources[t['drawing']]=hashlib.sha256(drawing.read_bytes()).hexdigest()
        labels=pack.labelled_scalars(d,path)
        for code in labels:
            assert code not in owners, f'duplicate expert ownership U+{code:X}'
            owners[code]=index
        experts.append({'name':Path(path).name,'half_labels':len(labels),
                        'source_scalars':sum(s<0x110000 for s in labels)})
    required=expected|{0x110000+s for s in expected}
    missing=required-set(owners);extra=set(owners)-required
    assert not missing and not extra, f'publication half inventory missing={sorted(missing)} extra={sorted(extra)}'
    assert len(owners)==600, 'publication requires exactly 600 half labels'
    assert all(owners[s]==owners[0x110000+s] for s in expected), 'a scalar has halves owned by different experts'
    return {'passed':True,'source_scalars':300,'half_labels':600,'expert_count':3,
            'manifest_sha256':hashlib.sha256(raw).hexdigest(),'sources_sha256':sources,
            'experts':experts,'ownership':{f'U+{s:04X}':owners[s] for s in sorted(expected)}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('lib');p.add_argument('bundle');p.add_argument('nets',nargs='+')
    p.add_argument('--out',required=True);p.add_argument('--report-only',action='store_true')
    p.add_argument('--target-cache',help='reuse hash-bound target coverages across seeds/calibration trials')
    p.add_argument('--manifest',help='require the complete 300-scalar/600-half publication inventory')
    a=p.parse_args()
    inventory=publication_inventory(a.manifest,a.nets) if a.manifest else None
    images=[pack.pack(n) for n in a.nets]
    want=pack.bundle(a.nets)[0] if len(a.nets)>1 else images[0]
    assert Path(a.bundle).read_bytes()==want, 'packed bytes differ from reproducible source packing'
    lib,h=bind(a.lib,a.bundle); k=lib.neuronte_layers(h)
    assert lib.neuronte_set_snap(h,0)==0
    points={w:sample_points(w) for w in (12,16,32)}
    cache=Path(a.target_cache) if a.target_cache else None
    if cache:cache.mkdir(parents=True,exist_ok=True)
    target_implementation=hashlib.sha256(Path(glyphs.__file__).read_bytes()).hexdigest()
    results={}; maxdiff=0.; maxpixel=0; known=set()
    for ni,(path,packed) in enumerate(zip(a.nets,images)):
        d=json.loads(Path(path).read_text()); assert d['training'].get('cell_columns')==2
        pack.check_sources(d,path); labelled=pack.labelled_scalars(d,path)
        drawings=pack.colour_drawings(d); pal=strokes.palette(str(pack.ROOT+'/'+d['training']['palette']))
        records=dict(pack.read_colour(packed)['records'])
        group={str(w):{'layers':[],'head_wrong':0,'unused_positive':0,'empty_half_positive':0,
                      'lost':0,'zero_coverage':0,'empty_halves':0,
                      **{t:{'mean_err':0.} for t in THEMES}} for w in points}
        for index,s in enumerate(labelled):
            assert s not in known;known.add(s)
            scalar=s-0x110000 if s>=0x110000 else s; half=int(s>=0x110000)
            assert lib.neuronte_route_half(h,scalar,half)==ni
            layers=drawing_at(drawings,s)
            entries=[pal[layers[i][0]][0] if i<len(layers) else 0 for i in range(k)]
            assert head(d,s)==entries, f'numpy palette mismatch U+{s:X}'
            key=hashlib.sha256(json.dumps([layers,d['training']['grid'],d['training']['pen_radius'],
                                          d['shape']['tau'],k,target_implementation],sort_keys=True).encode()).hexdigest()
            cached=cache/(key+'.npz') if cache else None
            if cached and cached.exists():
                with np.load(cached,allow_pickle=False) as archive:
                    targets={w:archive[str(w)] for w in points}
            else:
                fields=[glyphs.field(sh,d['training']['grid'],d['training']['pen_radius'],d['shape']['tau']).astype(np.float16).astype(np.float32) for _,sh in layers]
                targets={w:np.zeros((k,2*w,w),np.float32) for w in points}
                for cw in points:
                    for i,f in enumerate(fields):
                        v=interpolate(f,points[cw],d['training']['grid'])
                        targets[cw][i]=(v>0).reshape(2*cw,8,cw,8).mean((1,3))
                if cached:
                    np.savez_compressed(cached,**{str(w):t for w,t in targets.items()})
            for cw in points:
                r=group[str(cw)]; cov,ent=c_mask(lib,h,s,cw,k)
                r['head_wrong']+=sum(x!=y for x,y in zip(ent,entries))
                r['unused_positive']+=int((cov[len(layers):]>0).any(axis=(1,2)).sum())
                target=targets[cw]
                for i in range(len(layers)):
                    tc=float(target[i].sum()); pc=float(cov[i].sum())
                    c=counts(target[i]>.5,cov[i]>.5)
                    row={'code':f'U+{s:X}','layer':i,**c,'target_coverage':tc,'predicted_coverage':pc}
                    r['layers'].append(row)
                    if tc==0:
                        r['empty_halves']+=1;r['empty_half_positive']+=int(pc>0)
                    else:
                        r['lost']+=int(c['target_ink']>0 and c['intersection']==0)
                        r['zero_coverage']+=int(pc==0)
                for theme in THEMES:
                    err=np.abs(composite(cov,ent,pal,theme)-composite(target,entries,pal,theme))*255
                    r[theme]['mean_err']+=float(err.mean())/len(labelled)
            # Check float64 reference with and without the actual packed snap table,
            # for every tenth half, covering both halves across all experts.
            if index%10==0:
                for snapping in (False,True):
                    assert lib.neuronte_set_snap(h,14 if snapping else 0)==0
                    got,ent=c_mask(lib,h,s,8,k,2)
                    ref=reference(d,s,8,2,records if snapping else None)
                    diff=float(np.abs(got-ref).max());maxdiff=max(maxdiff,diff)
                    assert diff<1e-3, f'C/numpy masks U+{s:X}: {diff}'
                assert lib.neuronte_set_snap(h,0)==0
                # Draw each half through the compositing API; no layer masks supplied
                # by the test, exercising internal half routing and both palettes.
                cov,ent=c_mask(lib,h,s,16,k)
                for theme_id,theme in enumerate(THEMES):
                    assert lib.neuronte_set_theme(h,theme_id)==0
                    bg,fg=THEMES[theme]
                    bp=0xff000000|(bg[0]<<16)|(bg[1]<<8)|bg[2]
                    fp=0xff000000|(fg[0]<<16)|(fg[1]<<8)|fg[2]
                    pix=np.full((32,16),bp,np.uint32)
                    assert lib.neuronte_draw_half(h,pix.ctypes.data,16,16,32,0,0,16,32,scalar,half,fp)==0
                    rgb=np.stack([(pix>>shift)&255 for shift in (16,8,0)],axis=-1).astype(int)
                    ref=np.rint(composite(cov,ent,pal,theme)*255).astype(int)
                    pd=int(np.abs(rgb-ref).max());maxpixel=max(maxpixel,pd)
                    assert pd<=2, f'C half composition U+{s:X}: {pd}'
        for r in group.values():
            used=[v for v in r['layers'] if v['target_coverage']>0]
            r['iou_mean']=float(np.mean([v['iou'] for v in used]));r['iou_min']=min(v['iou'] for v in used)
        passed=group['16']['iou_mean']>=.990 and all(
            r['head_wrong']==r['unused_positive']==r['empty_half_positive']==r['lost']==r['zero_coverage']==0
            and all(r[t]['mean_err']<=2 for t in THEMES) for r in group.values())
        results[Path(path).name]={'passed':passed,'sizes':group}
    for s,half in ((0xd800,0),(0x110000,0),(0x41,2),(0xf0000,1)):
        assert lib.neuronte_route_half(h,s,half)==-1,'invalid half request accepted'
    lib.neuronte_close(h)
    report={'passed':all(r['passed'] for r in results.values()),'codes':len(known),'scalars':sum(s<0x110000 for s in known),
            'numpy_max_difference':maxdiff,'composition_max_channel_difference':maxpixel,'experts':results,
            'publication_inventory':inventory}
    Path(a.out).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({**{k:v for k,v in report.items() if k!='experts'},'experts':{n:{'passed':v['passed'],'sizes':{w:{k:x for k,x in r.items() if k!='layers'} for w,r in v['sizes'].items()}} for n,v in results.items()}},indent=2))
    if not report['passed'] and not a.report_only:raise SystemExit(1)


if __name__=='__main__': main()
