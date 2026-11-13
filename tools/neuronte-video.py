#!/usr/bin/env python3
"""Pipe raw RGB24 video through Neuronte; see neuronte-video.md."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from neuronte_video import TwoInk, MultiInk, exactness, ROOT, cell_bundle


def read_frame(stream, size):
    parts = []; remaining = size
    while remaining:
        part = stream.read(remaining)
        if not part:
            if remaining == size: return None
            raise ValueError(f'truncated frame: missing {remaining} bytes')
        parts.append(part); remaining -= len(part)
    return b''.join(parts)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--width', type=int); p.add_argument('--height', type=int)
    p.add_argument('--cell', default='8x16')
    p.add_argument('--level', choices=['two','multi'], default='two')
    p.add_argument('--mode', choices=['portable','full'], default='portable')
    p.add_argument('--output', choices=['ansi','rgb'], default='rgb')
    p.add_argument('--weights'); p.add_argument('--library')
    p.add_argument('--margin',type=float,default=0)
    exact=p.add_mutually_exclusive_group()
    exact.add_argument('--check-exact',action='store_true'); exact.add_argument('--require-exact',action='store_true')
    p.add_argument('--stats',type=Path)
    p.add_argument('--helper',choices=['none','speed','quality'],default='none')
    p.add_argument('--helper-model',type=Path)
    a = p.parse_args()
    if a.require_exact and a.level!='multi':p.error('--require-exact requires --level multi')
    if a.check_exact or a.require_exact:
        check = exactness(a.weights,a.library)
        if a.check_exact:
            print(json.dumps(check,indent=2)); return 0 if check['exact'] else 1
        if not check['exact']: p.error(f'pixel-net exactness failed: max error {check["max_error"]}')
    if not a.width or not a.height or a.width < 1 or a.height < 1: p.error('positive --width and --height required')
    try: w,h = map(int,a.cell.split('x'))
    except ValueError: p.error('--cell must be WIDTHxHEIGHT')
    if w < 1 or h < 1 or a.width % w or a.height % h: p.error('frame must divide exactly into positive cells')
    if a.level == 'multi' and a.output == 'ansi': p.error('multi-ink requires RGB output')
    # A helper is bound to the bundle it was trained on; without --weights, use that one.
    renderer = (MultiInk(a.weights,a.library,w,h) if a.level == 'multi' else TwoInk(a.mode,w,h,cell_bundle(a.weights,a.helper!='none'),a.library,a.margin))
    if a.require_exact and renderer.ink_indices is None:
        p.error('neural masks are fractional at the selected cell size')
    helper=None
    if a.helper!='none':
        if a.level!='two' or a.mode!='full' or (w,h)!=(8,16) or a.margin:
            p.error('helpers require --level two --mode full --cell 8x16 and zero margin')
        from neuronte_video_helpers import Helper,features,quality_cells
        helper=Helper(a.helper_model or ROOT/f'weights/neuronte-video-{a.helper}-v1.json',a.helper,runtime=True)
        expected=helper.doc.get('scalar_bundle_sha256')
        actual=hashlib.sha256(cell_bundle(a.weights,True).read_bytes()).hexdigest()
        if not expected or expected!=actual:p.error('helper scalar manifest/weights differ from the selected bundle')
    elif a.helper_model:p.error('--helper-model requires a helper')
    count=0; error=0.; previous=None; previous_frame=None; started=time.perf_counter()
    while True:
        raw=read_frame(sys.stdin.buffer,a.width*a.height*3)
        if raw is None: break
        frame=np.frombuffer(raw,np.uint8).reshape(a.height,a.width,3)
        if helper is not None:
            renderer.previous=None
            if a.helper=='speed':
                k=helper.doc['inference']['candidates']
                scores=helper(features(frame))
                ids=np.argpartition(scores,-k,axis=1)[:,-k:].reshape(a.height//h,a.width//w,k)
                cells=renderer.fit(frame,ids)
            else:
                best=renderer.fit(frame)
                cells=quality_cells(renderer,helper,frame,previous_frame,previous,best)
        else:
            cells=renderer.encode(frame) if a.level=='multi' else renderer.fit(frame)
        decoded=renderer.decode(cells)
        error+=float(np.square(decoded.astype(float)-frame).sum()); count+=1
        if a.output=='rgb': sys.stdout.buffer.write(decoded.tobytes())
        else: sys.stdout.buffer.write(renderer.ansi(cells,previous).encode())
        previous=cells; previous_frame=frame
    elapsed=time.perf_counter()-started
    if a.stats:
        mse=error/(count*a.width*a.height*3) if count else 0
        a.stats.write_text(json.dumps(dict(frames=count,seconds=elapsed,fps=count/elapsed,
              level=a.level,mode=a.mode,helper=a.helper,cell=[w,h],mse=mse,psnr_db=10*np.log10(255**2/mse) if mse else None),indent=2)+'\n')
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError) as exc: print(str(exc),file=sys.stderr); sys.exit(2)
