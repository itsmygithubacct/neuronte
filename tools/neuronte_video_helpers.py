"""Optional video MLP inference and conservative temporal quality checks.

No torch dependency at playback. Quality uses a learned proposal plus an
explicit source-image veto, not an unsupported claim of model-only fidelity.
"""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import uniform_filter,gaussian_filter
from neuronte_video import patches

# Scalars in each bundle a helper may be trained against: the size of the
# speed helper's output layer and the bound on its candidate count.
MANIFESTS={'split-v4':1061,'split-v5':1176}


def features(frame,previous=None):
    p=patches(frame,8,16).astype(np.float32)/255;grid=p.shape[:2]
    small=p.reshape(*grid,4,4,2,4,3).mean(axis=(3,5)).reshape(*grid,24)
    if previous is None:return small.reshape(-1,24)
    neighbours=uniform_filter(p.mean(axis=(2,3)),size=(3,3,1),mode='nearest')
    return np.concatenate([small,features(previous).reshape(*grid,24),neighbours],axis=2).reshape(-1,51)


class Helper:
    def __init__(self,path,kind,*,runtime=False):
        self.doc=json.loads(Path(path).read_text())
        d=self.doc
        if not isinstance(d,dict):raise ValueError('video helper must be a JSON object')
        if d.get('format')!='neuronte-video-helper' or d.get('version')!=1 or d.get('kind')!=kind or d.get('cell')!=[8,16] or d.get('scalar_manifest') not in MANIFESTS:
            raise ValueError('incompatible video helper')
        scalars=MANIFESTS[d['scalar_manifest']]
        policy=d.get('inference')
        if runtime and not isinstance(policy,dict):
            raise ValueError('runtime video helper requires an inference policy object')
        if policy is not None:
            if not isinstance(policy,dict):raise ValueError('invalid inference policy object')
            if kind=='speed' and (type(policy.get('candidates')) is not int or not 1<=policy['candidates']<=scalars):
                raise ValueError('invalid candidate count')
            if kind=='quality' and (policy.get('local_ssim_loss_max')!=.0001 or policy.get('frame_ssim_loss_max')!=.001):
                raise ValueError('unsupported temporal quality policy')
        layers=d.get('layers')
        if not isinstance(layers,list) or len(layers)!=2 or not all(isinstance(x,dict) for x in layers):
            raise ValueError('video helper needs two layer objects')
        self.layers=[(np.asarray(x.get('weight'),np.float32),np.asarray(x.get('bias'),np.float32)) for x in layers]
        sizes=[24 if kind=='speed' else 51,96,scalars if kind=='speed' else 2]
        if len(self.layers)!=2:raise ValueError('video helper needs two layers')
        for i,(w,b) in enumerate(self.layers):
            if w.shape!=(sizes[i+1],sizes[i]) or b.shape!=(sizes[i+1],) or not np.isfinite(w).all() or not np.isfinite(b).all():raise ValueError('invalid video helper layer')

    def __call__(self,x):
        for i,(w,b) in enumerate(self.layers):
            x=x@w.T+b
            if i==0:x=np.maximum(x,0)
        return x


def ssim(a,b):
    a=a.astype(float);b=b.astype(float)
    blur=lambda x:gaussian_filter(x,sigma=(1.5,1.5,0),truncate=3.5,mode='reflect')
    ma,mb=blur(a),blur(b);va=blur(a*a)-ma*ma;vb=blur(b*b)-mb*mb;cov=blur(a*b)-ma*mb
    result=((2*ma*mb+6.5025)*(2*cov+58.5225))/((ma*ma+mb*mb+6.5025)*(va+vb+58.5225))
    # Crop only where the 11px window fits; tiny frames use reflected edges.
    return float(result[5:-5,5:-5].mean() if min(a.shape[:2])>10 else result.mean())


def quality_cells(model,net,frame,previous,previous_cells,best):
    if previous is None:return best
    old=model.fit(frame,previous_cells['indices'][:,:,None])
    keep=net(features(frame,previous)).argmax(1).reshape(best['indices'].shape).astype(bool)
    target=patches(frame,8,16).reshape(-1,128,3).astype(float)
    def local(a):
        a=patches(a,8,16).reshape(-1,128,3).astype(float)
        ma=a.mean(1);mb=target.mean(1);da=a-ma[:,None];db=target-mb[:,None]
        return (((2*ma*mb+6.5025)*(2*(da*db).mean(1)+58.5225))/((ma*ma+mb*mb+6.5025)*((da*da).mean(1)+(db*db).mean(1)+58.5225))).mean(1)
    decoded=model.decode(best)
    keep &= (local(model.decode(old))>=local(decoded)-.0001).reshape(keep.shape)
    selected={name:np.where(keep[:,:,None,None],old[name],best[name]) if name=='colours' else np.where(keep,old[name],best[name]) for name in best}
    # The source is present during normal encoding, so this guard is valid
    # inference, not evaluation-only access to a hidden target.
    return selected if ssim(frame,model.decode(selected))>=ssim(frame,decoded)-.001 else best
