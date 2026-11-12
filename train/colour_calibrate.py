"""Calibrate a colour model's final layer against unchanged source coverage.

The SDF-trained body and palette head stay fixed. A separate finite phase fits
16px coverage plus a binary margin, with a penalty for departing from the
original field. This is not continuation of the original optimizer. Both its
new optimizer and RNG are checkpointed; final packed C gates remain mandatory.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
import torch

import checkpoint
import glyphs
import pack
from colour_sources import drawing_at

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('out',type=Path)
p.add_argument('--targets',type=Path);p.add_argument('--prepare-targets',action='store_true')
p.add_argument('--target-cache',type=Path)
p.add_argument('--device',default='cuda');p.add_argument('--steps',type=int,default=5000)
p.add_argument('--lr',type=float,default=.0001);p.add_argument('--margin',type=float,default=.02)
p.add_argument('--margin-weight',type=float,default=20.);p.add_argument('--field-anchor',type=float,default=.05)
p.add_argument('--batch-pixels',type=int,default=64);p.add_argument('--log-every',type=int,default=500)
checkpoint.arguments(p);a=p.parse_args()
if a.steps<1 or a.batch_pixels<1 or not all(math.isfinite(v) and v>0 for v in (a.lr,a.margin,a.margin_weight,a.field_anchor)):
    p.error('phase settings must be finite and positive')
if a.source.resolve()==a.out.resolve():p.error('output must preserve the source')
raw=a.source.read_bytes();d=json.loads(raw)
if d.get('format')!='neuronte-colour-weights' or d['shape']['form']!='A':p.error('requires a form A colour model')
pack.check_sources(d,str(a.source));labels=pack.labelled_scalars(d,str(a.source));drawings=pack.colour_drawings(d)
wpx,ss,k=16,2,d['shape']['glyph_layers'];n=d['training']['grid'];tau=d['shape']['tau']
implementation=hashlib.sha256(Path(glyphs.__file__).read_bytes()).hexdigest()
target_identity={'labels':labels,'drawings':d['training']['drawings_sha256'],'grid':n,'pen':d['training']['pen_radius'],'tau':tau,'size':wpx,'reference_samples':8,'layers':k,'glyphs_sha256':implementation}

def positions(size,samples):
    yy,xx=np.meshgrid((np.arange(2*size*samples)+.5)/(size*samples),(np.arange(size*samples)+.5)/(size*samples),indexing='ij')
    return np.stack([xx.ravel(),yy.ravel()],1)

if a.prepare_targets:
    truth=[];xy=positions(wpx,8);u,v=xy[:,0]*n,xy[:,1]*n;i0=np.clip(np.floor(u),0,n-1).astype(int);j0=np.clip(np.floor(v),0,2*n-1).astype(int);fu,fv=u-i0,v-j0
    for scalar in labels:
        layers=drawing_at(drawings,scalar)
        key=hashlib.sha256(json.dumps([layers,n,d['training']['pen_radius'],tau,k,implementation],sort_keys=True).encode()).hexdigest()
        cached=a.target_cache/(key+'.npz') if a.target_cache else None
        if cached and cached.exists():
            with np.load(cached,allow_pickle=False) as z:target=z[str(wpx)]
        else:
            target=np.zeros((k,2*wpx,wpx),np.float32)
            for layer,(_,shape) in enumerate(layers):
                f=glyphs.field(shape,n,d['training']['pen_radius'],tau).astype(np.float16).astype(np.float32)
                values=(f[j0,i0]*(1-fu)+f[j0,i0+1]*fu)*(1-fv)+(f[j0+1,i0]*(1-fu)+f[j0+1,i0+1]*fu)*fv
                target[layer]=(values>0).reshape(2*wpx,8,wpx,8).mean((1,3))
        truth.append(target)
    np.savez_compressed(a.out,identity=json.dumps(target_identity,sort_keys=True),target=np.asarray(truth))
    print(hashlib.sha256(a.out.read_bytes()).hexdigest());raise SystemExit(0)
if not a.targets:p.error('--targets is required for the phase; create it with --prepare-targets')
with np.load(a.targets,allow_pickle=False) as z:
    if json.loads(str(z['identity']))!=target_identity:p.error('source target identity mismatch')
    target=np.asarray(z['target'],np.float32)
if target.shape!=(len(labels),k,32,16) or not np.isfinite(target).all() or target.min()<0 or target.max()>1:p.error('invalid source coverages')
torch.set_num_threads(1);torch.manual_seed(d['training']['seed']);torch.set_float32_matmul_precision('highest')
params=[(torch.tensor(v['weight'],device=a.device).reshape(v['rows'],v['cols']),torch.tensor(v['bias'],device=a.device)) for v in d['layers'].values()]
xy=positions(wpx,ss);f=[xy[:,:1]*2-1,xy[:,1:]-1]
for octave in range(6):f.extend((np.sin(2*math.pi*2**octave*xy),np.cos(2*math.pi*2**octave*xy)))
pos=torch.tensor(np.column_stack(f),dtype=torch.float32,device=a.device)
masks=[1<<i for i in range(21)]+[int(v,16) for v in d['shape']['parity_masks']]
code=torch.tensor([[2*((int(s)&m).bit_count()%2)-1 for m in masks] for s in labels],dtype=torch.float32,device=a.device)
hidden=[]
with torch.no_grad():
    w,bias=params[0];base=pos@w[:,:26].T+bias;codes=code@w[:,26:].T
    for i in range(0,len(labels),4):
        x=torch.relu(base[None]+codes[i:i+4,None])
        for w,bias in params[1:-1]:x=torch.relu(x@w.T+bias)
        hidden.append(x.reshape(-1,32,2,16,2,x.shape[-1]).permute(0,1,3,2,4,5).reshape(-1,512,4,x.shape[-1]))
    hidden=torch.cat(hidden)
    original=torch.nn.functional.linear(hidden,*params[-1])
layer=torch.nn.Linear(hidden.shape[-1],k,device=a.device)
with torch.no_grad():layer.weight.copy_(params[-1][0]);layer.bias.copy_(params[-1][1])
truth=torch.tensor(target,device=a.device).permute(0,2,3,1).reshape(len(labels),512,k)
used=torch.tensor([[j<len(drawing_at(drawings,s)) for j in range(k)] for s in labels],device=a.device)
nonempty=(truth.sum(1)>0)&used
opt=torch.optim.Adam(layer.parameters(),lr=a.lr);sched=torch.optim.lr_scheduler.CosineAnnealingLR(opt,a.steps)
sources={'parent':hashlib.sha256(raw).hexdigest(),'targets':hashlib.sha256(a.targets.read_bytes()).hexdigest(),'trainer':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checkpoint':hashlib.sha256(Path(checkpoint.__file__).read_bytes()).hexdigest()}
identity=checkpoint.identity(argparse.Namespace(**{name:str(value) if isinstance(value,Path) else value for name,value in vars(a).items()}),sources);models={'out':layer};start,metrics=checkpoint.restore(a.resume,models,opt,sched,identity,a.device) if a.resume else (0,{})
gi=torch.arange(len(labels),device=a.device)[:,None];started=time.monotonic()
for step in range(start,a.steps):
    index=torch.randint(0,512,(len(labels),a.batch_pixels),device=a.device);field=layer(hidden[gi,index]);cov=(.5+field*float(np.float32(tau))*wpx*ss).clamp(0,1).mean(2);want=truth[gi,index]
    sign=torch.where(want>.5,1.,-1.)
    loss=(cov-want).square().mean()+a.margin_weight*torch.relu(a.margin-sign*(cov-.5)).square().mean()+a.field_anchor*(field-original[gi,index]).square().mean()
    opt.zero_grad();loss.backward();opt.step();sched.step()
    checkpoint.tick(a,step+1,models,opt,sched,identity,{'loss':loss})
    if a.log_every and ((step+1)%a.log_every==0 or step+1==a.steps):
        with torch.no_grad():
            cv=(.5+layer(hidden)*float(np.float32(tau))*wpx*ss).clamp(0,1).mean(2);pr=cv>.5;tr=truth>.5;inter=(pr&tr).sum(1);union=(pr|tr).sum(1);iou=torch.where(union>0,inter/union.clamp_min(1),torch.ones_like(inter))
        print(json.dumps({'step':step+1,'seconds':time.monotonic()-started,'loss':float(loss),'mean16':float(iou[nonempty].mean()),'lost':int(((inter==0)&(tr.sum(1)>0)&used).sum())}),flush=True)
d['layers']['out']['weight']=[float(v) for v in layer.weight.detach().cpu().numpy().ravel()];d['layers']['out']['bias']=[float(v) for v in layer.bias.detach().cpu().numpy()]
d['training']['coverage_calibration']={'version':1,'method':'fixed SDF features; new Adam on final layer only','source_sha256':sources['parent'],'sources_sha256':sources,'target_identity':target_identity,'steps':a.steps,'seed':d['training']['seed'],'lr':a.lr,'schedule':'new cosine phase','margin':a.margin,'margin_weight':a.margin_weight,'field_anchor':a.field_anchor,'batch_pixels':a.batch_pixels,'unchanged':['source geometry','body weights','palette head','routing'],'acceptance':'requires packed C12/16/32 and visual review'}
a.out.write_text(json.dumps(d)+'\n')
