"""Second helper protocol: existing trained seeds, conservative inference.

Select K on original validation clips using <=.02dB as a safety margin.
Assess once on NEW held-out clips1901..1903; previous failed clips remain
reported in the first protocol. No retraining on either held-out set.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from neuronte_video import TwoInk
from neuronte_video_helpers import Helper,features,quality_cells,ssim
import video
from video import scenes


def evaluate(model,speed,quality,seeds,k):
    times=np.zeros(2);errors=np.zeros(2);changes=np.zeros(2,dtype=int);sim=[];count=0;digest=hashlib.sha256()
    for seed in seeds:
        prev=None;previous=None;priorbest=None
        for frame in scenes(seed):
            digest.update(frame.tobytes());model.previous=None
            t=time.perf_counter();best=model.fit(frame);times[0]+=time.perf_counter()-t
            t=time.perf_counter();score=speed(features(frame));ids=np.argpartition(score,-k,axis=1)[:,-k:].reshape(*best['indices'].shape,k);fast=model.fit(frame,ids);times[1]+=time.perf_counter()-t
            quality_result=quality_cells(model,quality,frame,prev,previous,best)
            b=model.decode(best);f=model.decode(fast);q=model.decode(quality_result)
            errors += [np.square(b.astype(float)-frame).sum(),np.square(f.astype(float)-frame).sum()];count+=frame.size
            sim.append([ssim(frame,b),ssim(frame,q)])
            if previous is not None:changes += [(best['indices']!=priorbest['indices']).sum(),(quality_result['indices']!=previous['indices']).sum()]
            prev=frame;previous=quality_result;priorbest=best
    sims=np.mean(sim,axis=0);loss=float(10*np.log10(errors[1]/errors[0]));ratio=float(times[0]/times[1])
    return dict(k=k,frames=len(seeds)*12,source_sha256=digest.hexdigest(),baseline_seconds=float(times[0]),speed_seconds=float(times[1]),speedup=ratio,psnr_loss_db=loss,
        baseline_psnr=float(10*np.log10(255**2/(errors[0]/count))),baseline_ssim=float(sims[0]),quality_ssim=float(sims[1]),ssim_loss=float(sims[0]-sims[1]),baseline_changes=int(changes[0]),quality_changes=int(changes[1]),
        speed_pass=ratio>=3 and loss<=.1,quality_pass=bool(sims[0]-sims[1]<=.001 and changes[1]<changes[0]))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('parents',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--weights',type=Path,default=ROOT/'weights/neuronte-split-v5.nrt',help='the bundle the parents were trained against')
    p.add_argument('--heldout',type=int,nargs='+',default=[1901,1902,1903],help='held-out clip seeds; use ones no earlier helper was assessed on')
    p.add_argument('--grid-seed',type=int,help='also assess one 640x384 (80x24 cell) clip with this seed')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    protocol=dict(version=2,selection='validation PSNR loss <=.02dB and speedup>=3; minimum K',validation=[101,102],heldout=a.heldout,grid_seed=a.grid_seed,weights=a.weights.name,weights_sha256=hashlib.sha256(a.weights.read_bytes()).hexdigest(),quality='neural switch + localSSIM .0001 veto + frameSSIM .001 veto',parents={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.parents.glob('*seed*.json')},script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');model=TwoInk('full',weights=a.weights);results=[]
    for seed in [0,1]:
        speed=Helper(a.parents/f'speed-seed{seed}.json','speed');quality=Helper(a.parents/f'quality-seed{seed}.json','quality')
        validation=[evaluate(model,speed,quality,[101,102],k) for k in [64,80,96]]
        passed=[r for r in validation if r['psnr_loss_db']<=.02 and r['speedup']>=3]
        k=min(passed,key=lambda r:r['k'])['k'] if passed else 96
        result=dict(seed=seed,validation=validation,heldout=evaluate(model,speed,quality,a.heldout,k),selection_pass=bool(passed))
        if a.grid_seed is not None:
            global scenes;small=scenes;scenes=lambda s:video.scenes(s,width=640,height=384)
            try:result['grid_80x24']=evaluate(model,speed,quality,[a.grid_seed],k)
            finally:scenes=small
        results.append(result)
        (a.output/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
