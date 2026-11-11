"""Compare original italic pixel drawings with both packed C seeds at native em."""
import argparse
import ctypes as ct
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'train'))
import glyphs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('out');p.add_argument('--library',required=True)
    p.add_argument('--models',required=True,help='JSON mapping each em to an array of packed seed paths')
    p.add_argument('--text',default='Ag MWxy 09!? @&')
    a=p.parse_args();models=json.loads(Path(a.models).read_text())
    lib=ct.CDLL(str(Path(a.library).resolve()));P=ct.c_void_p;I=ct.c_int
    lib.neuronte_open_file.argtypes=[ct.c_char_p,ct.POINTER(P)];lib.neuronte_close.argtypes=[P]
    lib.neuronte_set_binary.argtypes=[P,I]
    lib.neuronte_draw_text.argtypes=[P,P]+[I]*7+[ct.c_char_p,ct.c_size_t,ct.c_uint32]
    cards=[]
    for em,paths in sorted(models.items(),key=lambda item:int(item[0])):
        em=int(em);face=glyphs.pixel_face(em,str(ROOT/f'font/ui-{em}-italic.txt'))
        scale=max(1,min(4,64//em));text=a.text.encode();width=sum(face[c][0]+1 for c in a.text)+em
        panels=[]
        for bold in (0,1):
            source=np.zeros((em,width),bool);pen=0
            for c in a.text:
                advance,art=face[c];mask=np.array([[v=='#' for v in row] for row in art])
                for dx in range(bold+1):source[:,pen+dx:pen+dx+mask.shape[1]]|=mask
                pen+=advance+bold
            panels.append(source)
            for path in paths:
                h=P();assert lib.neuronte_open_file(str(path).encode(),ct.byref(h))==0
                try:
                    assert lib.neuronte_set_binary(h,1)==0
                    pixels=np.zeros((em,width),np.uint32)
                    moved=lib.neuronte_draw_text(h,pixels.ctypes.data,width,width,em,0,-glyphs.UI_TOP[em],em,bold,text,len(text),0xffffffff)
                    assert moved==pen
                    rendered=pixels!=0
                    assert np.array_equal(source,rendered),f'preview differs at{em}px bold={bold}: {path}'
                    panels.append(rendered)
                finally:lib.neuronte_close(h)
        image=Image.new('RGB',(max(400,width*scale+16),len(panels)*(em*scale+15)+34),'white')
        draw=ImageDraw.Draw(image);draw.text((8,6),f'{em}px italic: source / seed0 / seed1; regular then bold; {scale}x',fill='black')
        y=30
        for panel in panels:
            rgb=np.where(panel[...,None],np.array([25,31,42]),np.array([255,255,255])).astype(np.uint8)
            image.paste(Image.fromarray(rgb).resize((width*scale,em*scale),Image.Resampling.NEAREST),(8,y));y+=em*scale+15
        cards.append(image)
    out=Image.new('RGB',(max(c.width for c in cards),sum(c.height for c in cards)),(235,237,241));y=0
    for card in cards:out.paste(card,(0,y));y+=card.height
    out.save(a.out);print(f'{len(cards)} italic sizes, source and both C seeds, exactly equal')


if __name__=='__main__':main()
