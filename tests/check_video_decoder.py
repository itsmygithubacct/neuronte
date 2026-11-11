"""Independent numpy evaluation of the untrained C decoder timing probe."""
from pathlib import Path
import json
import subprocess
import tempfile
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def reference(width,height,h,codes):
    state=19
    def rnd():
        nonlocal state
        state=(state*1664525+1013904223)&0xffffffff
        return np.float32(np.float32(np.float32(state>>8)/np.float32(16777216))-.5)*np.float32(.2)
    cols=(width+7)//8;rows=(height+15)//16
    lat=np.array([rnd()*np.float32(5) for _ in range(rows*cols*codes)],np.float32).reshape(rows,cols,codes)
    wp=np.empty((h,26),np.float32);wc=np.empty((h,codes),np.float32);w2=np.empty((h,h),np.float32);w3=np.empty((h,h),np.float32)
    for i in range(h):
        for j in range(26):wp[i,j]=rnd()
        for j in range(codes):wc[i,j]=rnd()
        for j in range(h):w2[i,j],w3[i,j]=rnd(),rnd()
    wo=np.array([rnd() for _ in range(3*h)],np.float32).reshape(3,h)
    projected=lat@wc.T
    out=np.empty((height,width,3),np.float32)
    for y in range(height):
        for x in range(width):
            xx=np.float32((x%8+.5)/8);yy=np.float32((y%16+.5)/8)
            pos=[2*xx-1,yy-1]
            for k in range(6):
                f=np.float32(6.28318530718)*np.float32(1<<k)
                pos.extend([np.sin(f*xx),np.sin(f*yy),np.cos(f*xx),np.cos(f*yy)])
            gx=(x+.5)/8-.5;gy=(y+.5)/16-.5;ix=int(np.floor(gx));iy=int(np.floor(gy));fx=gx-ix;fy=gy-iy
            blend=sum(projected[min(max(iy+dy,0),rows-1),min(max(ix+dx,0),cols-1)]*weight for dx,dy,weight in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)])
            a=np.maximum(np.array(pos,np.float32)@wp.T+blend,0)
            b=np.maximum(a@w2.T,0);c=np.maximum(b@w3.T,0);out[y,x]=c@wo.T
    return out

with tempfile.TemporaryDirectory() as temp:
    for hidden in [32,48]:
        for codes in [16,32]:
            path=Path(temp)/'output.rgbf'
            stats=json.loads(subprocess.check_output([str(ROOT/'build/video-decoder-bench'),'24','32',str(hidden),str(codes),str(path)]))
            actual=np.fromfile(path,np.float32).reshape(32,24,3)
            expected=reference(24,32,hidden,codes)
            error=float(np.abs(actual-expected).max())
            assert error<1e-6,(hidden,codes,error)
            assert abs(actual.astype(float).sum()-stats['checksum'])<1e-7
            print(hidden,codes,'max absolute error',error)
print('decoder probe: passed (untrained numerical equivalence only)')
