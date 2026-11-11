"""Original two-cell emoji targets beside packed C renders in both themes."""
import argparse
import ctypes as ct
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'train'), str(ROOT/'tests')]
import glyphs
import pack
import strokes
from check_emoji import bind


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('out')
    p.add_argument('--library', required=True)
    p.add_argument('--weights', required=True)
    p.add_argument('--other-weights')
    p.add_argument('--nets', nargs='+', required=True, help='JSON files defining trained labels')
    p.add_argument('--size', type=int, default=16, help='one cell width; glyph spans two cells')
    p.add_argument('--columns', type=int, default=10)
    p.add_argument('--codes', help='comma separated hexadecimal scalars for a detail sheet')
    a = p.parse_args()
    pal = strokes.palette(str(ROOT/'font/emoji-palette.txt'))
    drawings = strokes.parse_layers(str(ROOT/'font/emoji.txt'), pal)
    known = set().union(*(pack.scalars(path)[1] for path in a.nets))
    codes = sorted(s for s in known if s < 0x110000)
    if a.codes:
        codes = [int(s.removeprefix('U+'), 16) for s in a.codes.split(',')]
        assert set(codes) <= known
    handles = [bind(a.library, path) for path in (a.weights, a.other_weights) if path]
    size = a.size
    samples = 8
    axis = (np.arange(2*size*samples)+.5)/(size*samples)
    yy, xx = np.meshgrid(axis, axis, indexing='ij')
    points = np.stack([xx.ravel(), yy.ravel()], 1)
    cw = 2*(1+len(handles))*(2*size+3)+8
    ch = 2*size+29
    out = Image.new('RGB', (cw*a.columns, 38+ch*((len(codes)+a.columns-1)//a.columns)), (235,237,241))
    draw = ImageDraw.Draw(out)
    draw.text((8,8), f'RC9 emoji {size}px/cell: source, seed0'+(', seed1' if a.other_weights else '')+'; dark / light', fill=(22,27,34))
    for index, scalar in enumerate(codes):
        x = index % a.columns*cw
        y = 38+index//a.columns*ch
        draw.text((x+3,y+3), f'U+{scalar:04X}', fill=(22,27,34))
        layers = drawings[chr(scalar)]
        masks = [(glyphs.signed_distance(sh, points, glyphs.PEN)>0).reshape(2*size,samples,2*size,samples).mean((1,3))
                 for _, sh in layers]
        dx = x+3
        for theme, background in enumerate(((17,21,28),(250,250,247))):
            rgb = np.broadcast_to(np.asarray(background, np.float64), (2*size,2*size,3)).copy()
            for mask, (name, _) in zip(masks, layers):
                assert pal[name][0] != 0, 'emoji source unexpectedly uses foreground'
                color = np.asarray(background if pal[name][0] == 1 else pal[name][theme+1])
                rgb = color*mask[...,None]+rgb*(1-mask[...,None])
            out.paste(Image.fromarray(np.uint8(np.rint(rgb))), (dx,y+20))
            dx += 2*size+3
            for lib, h in handles:
                assert lib.neuronte_set_theme(h,theme)==0
                pixel = 0xff000000 | background[0]<<16 | background[1]<<8 | background[2]
                pix = np.full((2*size,2*size), pixel, np.uint32)
                for half in (0,1):
                    assert lib.neuronte_draw_half(h,pix.ctypes.data,2*size,2*size,2*size,half*size,0,size,2*size,scalar,half,0xffffffff)==0
                rgb = np.uint8(np.stack([(pix>>shift)&255 for shift in (16,8,0)],-1))
                out.paste(Image.fromarray(rgb), (dx,y+20))
                dx += 2*size+3
    for lib,h in handles:
        lib.neuronte_close(h)
    out.save(a.out)
    print(json.dumps({'scalars':len(codes),'cell_width':size,'image':a.out}))


if __name__ == '__main__':
    main()
