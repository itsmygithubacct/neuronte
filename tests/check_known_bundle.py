"""Native routing and pixels of a known-only replacement, including unknowns."""
import ctypes as C
import json
from pathlib import Path
import struct
import sys
import tempfile

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'train'))
import known_bundle
import pack
import strokes

lib=C.CDLL(str(Path(sys.argv[1]).resolve()))
lib.neuronte_open.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(C.c_void_p)]
lib.neuronte_close.argtypes=[C.c_void_p]
lib.neuronte_route.argtypes=[C.c_void_p,C.c_uint32]
lib.neuronte_coverage.argtypes=[C.c_void_p,C.c_uint32,C.c_int,C.c_int,C.c_int,C.POINTER(C.c_float)]

def opened(data):
 handle=C.c_void_p();assert lib.neuronte_open(data,len(data),C.byref(handle))==0
 return handle

def coverage(handle,scalar):
 buf=(C.c_float*128)();assert lib.neuronte_coverage(handle,scalar,8,16,0,buf)==0
 return bytes(buf)

with tempfile.TemporaryDirectory(prefix='known-bundle-') as tmp:
 directory=Path(tmp);paths=[]
 for i,(a,b) in enumerate(((32,78),(79,126))):
  doc={'format':'neuronte-weights','version':1,'shape':{'position_octaves':6,'code_bits':64,
       'hidden_width':4,'hidden_layers':3,'tau':.15,'parity_masks':[hex(m) for m in strokes.masks()]},
       'training':{'set':f'part-{i}','labelled':f'U+{a:04X}..U+{b:04X}'},
       'layers':{name:{'rows':r,'cols':c,'weight':[0.]*(r*c),'bias':[.01*(i+1)] if name=='out' else [0.]*r}
                 for name,r,c in pack.layers(4)}}
  p=directory/f'part{i}.json';p.write_text(json.dumps(doc));paths.append(p)
 base=(ROOT/'weights/neuronte-split-v5.nrt').read_bytes()
 combined,record=known_bundle.replace_known(base,paths,0)
 assert record['replaced_scalars']==95 and record['members']==8
 original,new=opened(base),opened(combined)
 members=[opened(pack.pack(str(p))) for p in paths]
 try:
  for c in range(32,127):
   i=0 if c<=78 else 1
   assert lib.neuronte_route(new,c)==6+i
   assert coverage(new,c)==coverage(members[i],c)
  # Probe every plane plus boundaries, invalid values, surrogate normalization,
  # known unrelated ranges and gate selections across thousands of unknowns.
  codes=set(range(0,0x110000,131))|{0,31,127,0x2500,0x2800,0x28ff,0xd7ff,0xd800,0xdfff,0xe000,0x10ffff,0x110000,0xffffffff}
  for c in codes:
   if 32<=c<=126:continue
   assert lib.neuronte_route(new,c)==lib.neuronte_route(original,c)
  for c in sorted(codes)[::97]:
   if not 32<=c<=126:assert coverage(new,c)==coverage(original,c)
 finally:
  for h in [original,new,*members]:lib.neuronte_close(h)
 for changes in ([paths[0]],paths+[paths[0]]):
  try:known_bundle.replace_known(base,changes,0)
  except ValueError:pass
  else:raise AssertionError('incomplete or overlapping replacement accepted')
 try:known_bundle.replace_known(base,paths,1)
 except ValueError:pass
 else:raise AssertionError('unrelated expert accepted')
 partial,info=known_bundle.replace_known(base,[paths[0]],0,True)
 original,new=opened(base),opened(partial)
 try:
  assert lib.neuronte_route(new,32)==6
  for c in range(79,127):assert coverage(new,c)==coverage(original,c)
 finally:lib.neuronte_close(original);lib.neuronte_close(new)
 for damaged in (base[:24],base[:-1],base+b'x'):
  try:known_bundle.replace_known(damaged,paths,0)
  except (ValueError,struct.error):pass
  else:raise AssertionError('malformed original accepted')
 # The same replacement works when the original has no gate.
 source,_=pack.bundle([str(p) for p in paths],fallback=1)
 candidate,info=known_bundle.replace_known(source,[paths[0]],0)
 h=opened(candidate)
 try:assert lib.neuronte_route(h,0x400)==1
 finally:lib.neuronte_close(h)
print('check_known_bundle: exact known pixels, original unknown/unrelated routing and pixels, partial/no-gate cases, malformed inputs passed')
