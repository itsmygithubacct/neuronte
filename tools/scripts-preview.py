"""Render every newly trained Greek/Russian letter beside its original target.

Usage: scripts-preview.py OUT.png --weights FILE --library FILE
"""
import argparse
import ctypes as ct
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'train'))
import glyphs

p=argparse.ArgumentParser(description=__doc__);p.add_argument('out');p.add_argument('--weights',required=True);p.add_argument('--library',required=True)
p.add_argument('--other-weights',help='the second training seed, standalone or bundled')
a=p.parse_args()
lib=ct.CDLL(str(Path(a.library).resolve()));P=ct.c_void_p;I=ct.c_int;U=ct.c_uint32
lib.neuronte_open_file.argtypes=[ct.c_char_p,ct.POINTER(P)];lib.neuronte_close.argtypes=[P]
lib.neuronte_draw_scalar.argtypes=[P,P,I,I,I,I,I,I,I,U,U]
h=P();assert lib.neuronte_open_file(a.weights.encode(),ct.byref(h))==0
handles=[h]
if a.other_weights:
    other=P();assert lib.neuronte_open_file(a.other_weights.encode(),ct.byref(other))==0;handles.append(other)
chars=[(c,s) for c,_,s in glyphs.charset('accent') if 0x370<=ord(c)<=0x4ff]
sizes=(16,48);cardw=240 if a.other_weights else 184;cardh=152;cols=10;rows=(len(chars)+cols-1)//cols
out=Image.new('RGB',(cols*cardw,40+rows*cardh),(241,239,233));draw=ImageDraw.Draw(out)
draw.text((10,10),'RC9 Greek / Russian: source, split-v5 seed0'+(', seed1' if a.other_weights else '')+'; 16 / 48 px',fill=(25,30,40))
ink=np.array([30,36,48]);bg=np.array([255,255,255])
for i,(c,sh) in enumerate(chars):
 x=(i%cols)*cardw;y=40+(i//cols)*cardh;draw.text((x+6,y+3),f'U+{ord(c):04X}',fill=(25,30,40));dx=x+5
 for cw in sizes:
  ss=4;yy,xx=np.meshgrid((np.arange(2*cw*ss)+.5)/(cw*ss),(np.arange(cw*ss)+.5)/(cw*ss),indexing='ij')
  sd=glyphs.signed_distance(sh,np.stack([xx.ravel(),yy.ravel()],1),glyphs.PEN)
  target=(sd>0).reshape(2*cw,ss,cw,ss).mean((1,3))[...,None]
  rgb=np.uint8(np.rint(bg*(1-target)+ink*target))
  out.paste(Image.fromarray(rgb),(dx,y+25))
  for j,handle in enumerate(handles,1):
   pix=np.full((2*cw,cw),0xffffffff,np.uint32)
   assert lib.neuronte_draw_scalar(handle,pix.ctypes.data,cw,cw,2*cw,0,0,cw,2*cw,ord(c),0xff1e2430)==0
   net=np.uint8(np.stack([(pix>>shift)&255 for shift in (16,8,0)],axis=-1))
   out.paste(Image.fromarray(net),(dx+j*(cw+3),y+25))
  draw.text((dx,y+128),str(cw),fill=(60,66,76));dx+=(cw+3)*(1+len(handles))+8
for handle in handles:lib.neuronte_close(handle)
out.save(a.out);print(f'{len(chars)} original targets and packed C renders -> {a.out}')
