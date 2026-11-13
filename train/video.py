"""Train and gate two small video helpers on original, disjoint synthetic clips.

Quality: a learned temporal switch chooses between the exhaustive winner and
refitting the preceding character. Inputs include neighbouring cells and the
previous frame. Gate: held-out mean SSIM loss <=.001, fewer character changes.
Speed: MLP proposes K candidates for the same bounded exact colour fit. Gate:
>=3x total speedup and <=.1dB PSNR loss. Both seeds must pass before adoption.
Artifacts, clips and rejected weights go to --output, never normal text assets.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.ndimage import uniform_filter, gaussian_filter
import torch
from torch import nn
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from neuronte_video import TwoInk,patches


def scenes(seed,count=12,width=96,height=64):
    rng=np.random.default_rng(seed);y,x=np.mgrid[:height,:width]
    base=rng.uniform(0,255,(3,3)); phase=rng.uniform(0,6.28,3)
    velocity=rng.uniform(-3,3,2); centre=rng.uniform([0,0],[width,height]); colour=rng.integers(0,256,3)
    frequency=rng.uniform(.03,.15); size=rng.uniform(5,18)
    for t in range(count):
        f=np.stack([np.sin(x*frequency+phase[0]+t*.03),np.cos(y*frequency+phase[1]-t*.04),np.sin((x+y)*frequency*.5+phase[2])],-1)
        rgb=np.clip((f+1)@base/6,0,255)
        cx,cy=(centre+t*velocity)%[width,height]
        rgb[(x-cx)**2+(y-cy)**2<size**2]=colour
        stripe=((x+t*2)//int(size)%2==0)&(y>height*.7)
        rgb[stripe]=255-colour
        yield np.rint(rgb).astype(np.uint8)


def ssim(a,b):
    a=a.astype(float);b=b.astype(float)
    # Standard luminance/contrast/structure SSIM with Gaussian11 window,
    # sigma1.5, RGB channel mean, population covariance, data range255.
    blur=lambda x: gaussian_filter(x,sigma=(1.5,1.5,0),truncate=3.5,mode='reflect')
    ma,mb=blur(a),blur(b);va=blur(a*a)-ma*ma;vb=blur(b*b)-mb*mb;cov=blur(a*b)-ma*mb
    result=((2*ma*mb+6.5025)*(2*cov+58.5225))/((ma*ma+mb*mb+6.5025)*(va+vb+58.5225))
    return float(result[5:-5,5:-5].mean())


def features(frame,previous=None):
    p=patches(frame,8,16).astype(np.float32)/255
    grid=p.shape[:2]
    small=p.reshape(*grid,4,4,2,4,3).mean(axis=(3,5)).reshape(*grid,-1)
    means=p.mean(axis=(2,3)); neighbour=uniform_filter(means,size=(3,3,1),mode='nearest')
    if previous is None:return small.reshape(-1,24)
    old=features(previous).reshape(*grid,24)
    return np.concatenate([small,old,neighbour],axis=2).reshape(-1,51)


def make_data(model,seeds):
    xs=[];ys=[];qx=[];qy=[];digest=hashlib.sha256()
    for seed in seeds:
        previous=None;prev_cells=None
        for frame in scenes(seed):
            digest.update(frame.tobytes());model.previous=None
            best=model.fit(frame);xs.append(features(frame));ys.append(best['indices'].ravel())
            if previous is not None:
                old=model.fit(frame,prev_cells['indices'][:,:,None])
                # Local patch SSIM teacher, relaxed by .001; this target is
                # evaluated independently on complete held-out frames below.
                newp=patches(model.decode(best),8,16).reshape(-1,128,3).astype(float)
                oldp=patches(model.decode(old),8,16).reshape(-1,128,3).astype(float)
                target=patches(frame,8,16).reshape(-1,128,3).astype(float)
                def local(a):
                    ma=a.mean(1);mb=target.mean(1); da=a-ma[:,None];db=target-mb[:,None]
                    return (((2*ma*mb+6.5025)*(2*(da*db).mean(1)+58.5225))/((ma*ma+mb*mb+6.5025)*((da*da).mean(1)+(db*db).mean(1)+58.5225))).mean(1)
                qx.append(features(frame,previous));qy.append((local(oldp)>=local(newp)-.001).astype(np.int64))
            previous=frame;prev_cells=best
    return tuple(np.concatenate(v) for v in [xs,ys,qx,qy]),digest.hexdigest()


def fit_net(x,y,outputs,seed,epochs):
    torch.manual_seed(seed)
    net=nn.Sequential(nn.Linear(x.shape[1],96),nn.ReLU(),nn.Linear(96,outputs))
    opt=torch.optim.Adam(net.parameters(),lr=.003);tx=torch.from_numpy(x);ty=torch.from_numpy(y)
    for epoch in range(epochs):
        order=torch.randperm(len(tx))
        for ids in order.split(256):
            opt.zero_grad();loss=nn.functional.cross_entropy(net(tx[ids]),ty[ids]);loss.backward();opt.step()
    return net.eval()


def logits(net,x):
    with torch.no_grad():return net(torch.from_numpy(x)).numpy()


def manifest_name(weights):
    return Path(weights).stem.removeprefix('neuronte-')


def save(net,path,kind,seed,datahash,weights):
    doc=dict(format='neuronte-video-helper',version=1,kind=kind,seed=seed,source_frames_sha256=datahash,
        source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cell=[8,16],
        scalar_manifest=manifest_name(weights),scalar_bundle_sha256=hashlib.sha256(Path(weights).read_bytes()).hexdigest(),layers=[dict(weight=m.weight.detach().numpy().tolist(),bias=m.bias.detach().numpy().tolist()) for m in net if isinstance(m,nn.Linear)])
    path.write_text(json.dumps(doc,separators=(',',':'))+'\n')


def evaluate(model,speed,quality,seeds,k):
    exact_seconds=speed_seconds=0.;base_err=speed_err=0.;base_ssim=[];quality_ssim=[];base_changes=quality_changes=0;pixels=0;heldhash=hashlib.sha256()
    for seed in seeds:
        previous=None;prev_base=None;prev_quality=None
        for frame in scenes(seed):
            heldhash.update(frame.tobytes());model.previous=None
            begin=time.perf_counter();best=model.fit(frame);exact_seconds+=time.perf_counter()-begin
            begin=time.perf_counter();scores=logits(speed,features(frame)); proposal=np.argpartition(scores,-k,axis=1)[:,-k:].reshape(*best['indices'].shape,k)
            quick=model.fit(frame,proposal);speed_seconds+=time.perf_counter()-begin
            b=model.decode(best);s=model.decode(quick);base_err+=np.square(b.astype(float)-frame).sum();speed_err+=np.square(s.astype(float)-frame).sum();pixels+=frame.size
            q=best
            if previous is not None:
                old=model.fit(frame,prev_quality['indices'][:,:,None]);keep=logits(quality,features(frame,previous)).argmax(1).reshape(best['indices'].shape).astype(bool)
                q={name:np.where(keep[:,:,None,None],old[name],best[name]) if name=='colours' else np.where(keep,old[name],best[name]) for name in best}
                base_changes+=int((best['indices']!=prev_base['indices']).sum());quality_changes+=int((q['indices']!=prev_quality['indices']).sum())
            base_ssim.append(ssim(frame,b));quality_ssim.append(ssim(frame,model.decode(q)))
            previous=frame;prev_base=best;prev_quality=q
    loss=10*np.log10(speed_err/base_err)
    ssim_loss=float(np.mean(base_ssim)-np.mean(quality_ssim))
    return dict(k=k,source_sha256=heldhash.hexdigest(),frames=len(seeds)*12,exact_seconds=exact_seconds,speed_seconds=speed_seconds,speedup=exact_seconds/speed_seconds,
        baseline_psnr=10*np.log10(255**2/(base_err/pixels)),psnr_loss_db=float(loss),speed_pass=bool(exact_seconds/speed_seconds>=3 and loss<=.1),
        baseline_ssim=float(np.mean(base_ssim)),quality_ssim=float(np.mean(quality_ssim)),ssim_loss=ssim_loss,baseline_changes=base_changes,quality_changes=quality_changes,
        quality_pass=bool(ssim_loss<=.001 and quality_changes<base_changes))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--epochs',type=int,default=100);p.add_argument('--weights',type=Path,default=ROOT/'weights/neuronte-split-v5.nrt',help='bundle the helpers are trained against and bound to');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(2);model=TwoInk('full',weights=a.weights);(x,y,qx,qy),digest=make_data(model,range(10,18))
    (a.output/'protocol.json').write_text(json.dumps(dict(train_seeds=list(range(10,18)),validation_seeds=[101,102],heldout_seeds=[901,902,903],epochs=a.epochs,speed_gate='>=3x and <=.1dB loss',quality_gate='SSIM loss <=.001 and fewer character changes',training_rgb_sha256=digest,weights=a.weights.name,weights_sha256=hashlib.sha256(a.weights.read_bytes()).hexdigest()),indent=2))
    all_results=[]
    for seed in [0,1]:
        speed=fit_net(x,y,len(model.scalars),seed,a.epochs);quality=fit_net(qx,qy,2,seed,a.epochs)
        save(speed,a.output/f'speed-seed{seed}.json','speed',seed,digest,a.weights);save(quality,a.output/f'quality-seed{seed}.json','quality',seed,digest,a.weights)
        validation=[evaluate(model,speed,quality,[101,102],k) for k in [16,32,64,96,128]]
        passing=[r for r in validation if r['speed_pass']]
        chosen=min(passing,key=lambda r:r['k'])['k'] if passing else 128
        result=dict(seed=seed,validation=validation,heldout=evaluate(model,speed,quality,[901,902,903],chosen))
        all_results.append(result);(a.output/'results.json').write_text(json.dumps(all_results,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
