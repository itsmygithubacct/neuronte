"""Reproducible spatial and character-group experiments for the ASCII expert.

Prepare a shared teacher once, then train independent models in bounded batches.
All checkpoints and exports belong in the supplied experiment directory.
MIT licence; see LICENSE.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
COUNTS = (4, 8, 16, 64)
GRIDS = {4: (2, 2), 8: (2, 4), 16: (4, 4), 64: (8, 8)}
SCALARS = list(range(32, 127))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def specs(mode, count):
    if mode not in ('spatial', 'repertoire') or count not in COUNTS:
        raise ValueError('unsupported ASCII decomposition')
    cols, rows = GRIDS[count]
    out = []
    for i in range(count):
        region = [i % cols / cols, (i % cols + 1) / cols,
                  2 * (i // cols) / rows, 2 * (i // cols + 1) / rows]
        out.append({'name': f'ascii-{mode}-k{count}-p{i}', 'index': i,
                    'width': 128 // count, 'region': region if mode == 'spatial' else [0., 1., 0., 2.],
                    'scalars': SCALARS if mode == 'spatial' else SCALARS[95*i//count:95*(i+1)//count]})
    return out


def crop(full, region):
    x0, x1, y0, y1 = region
    n = full.shape[-1] - 1
    if full.shape[-2:] != (2*n+1, n+1):
        raise ValueError('expected the full 1:2 teacher grid')
    x = np.arange(n+1, dtype=np.float64)*(x1-x0) + x0*n
    y = np.arange(2*n+1, dtype=np.float64)*(y1-y0)/2 + y0*n
    ix, iy = x.astype(np.int64), y.astype(np.int64)
    fx, fy = x-ix, y-iy
    across = full[..., ix]*(1-fx) + full[..., np.minimum(ix+1, n)]*fx
    return across[..., iy, :]*(1-fy[:, None]) + across[..., np.minimum(iy+1, 2*n), :]*fy[:, None]


def teacher_masks(fields, w, h, samples=8):
    n = fields.shape[-1]-1
    x = (np.arange(w*samples, dtype=np.float32)+.5)/(w*samples)*n
    y = (np.arange(h*samples, dtype=np.float32)+.5)/(h*samples)*2*n
    ix, iy = np.minimum(x.astype(int), n-1), np.minimum(y.astype(int), 2*n-1)
    fx, fy = x-ix.astype(np.float32), y-iy.astype(np.float32)
    out = []
    for field in fields:
        field = field.astype(np.float32)
        a = field[iy[:, None], ix]*(1-fx) + field[iy[:, None], ix+1]*fx
        b = field[iy[:, None]+1, ix]*(1-fx) + field[iy[:, None]+1, ix+1]*fx
        inside = a*(1-fy[:, None]) + b*fy[:, None] > 0
        out.append(inside.reshape(h, samples, w, samples).mean((1, 3)))
    return np.asarray(out, dtype=np.float32)


def prepare(directory):
    import glyphs
    directory.mkdir(parents=True, exist_ok=True)
    path = directory/'teacher.npy'
    sources = {name: digest(ROOT/name) for name in glyphs.sources('ascii') + ['font/code-masks.txt']}
    spec = {'schema': 'neuronte.ascii-teacher/v1', 'scalars': SCALARS, 'grid': 256,
            'tau': .15, 'pen': glyphs.PEN, 'sources': sources}
    meta = directory/'teacher.json'
    if meta.exists():
        old = json.loads(meta.read_text())
        if old['identity'] != spec or digest(path) != old['sha256']:
            raise ValueError('teacher identity or asset changed')
        if any(digest(directory/t['file']) != t['sha256'] for t in old['targets'].values()):
            raise ValueError('teacher coverage target changed')
        print('existing verified teacher', path)
        return
    rows = glyphs.charset('ascii')
    assert [ord(c) for c, _, _ in rows] == SCALARS
    fields = np.stack([glyphs.field(shapes, 256, glyphs.PEN, .15) for _, _, shapes in rows]).astype(np.float16)
    np.save(path, fields, allow_pickle=False)
    targets = {}
    for w, h in ((8, 16), (16, 32), (48, 96)):
        target = directory/f'truth-{w}x{h}.npy'
        np.save(target, teacher_masks(fields, w, h), allow_pickle=False)
        targets[f'{w}x{h}'] = {'file': target.name, 'sha256': digest(target)}
    meta.write_text(json.dumps({'identity': spec, 'sha256': digest(path), 'targets': targets}, indent=2)+'\n')
    print(meta)


def position(torch, xy):
    out = [xy[..., :1]*2-1, xy[..., 1:]-1]
    for octave in range(6):
        phase = (2*math.pi*2**octave)*xy
        out.extend((torch.sin(phase), torch.cos(phase)))
    return torch.cat(out, dim=-1)


def code(torch, scalars, masks):
    bits = ((scalars[..., None] >> torch.arange(21, device=scalars.device)) & 1).float()
    return 2*torch.cat((bits, torch.remainder(bits@masks.T, 2)), dim=-1)-1


def evaluate(torch, weights, biases, character, xy):
    m, g, points, _ = xy.shape
    value = torch.cat((position(torch, xy), character[:, :, None].expand(-1, -1, points, -1)), dim=-1)
    value = value.reshape(m, g*points, 90)
    for i in range(4):
        value = torch.bmm(value, weights[i].transpose(1, 2)) + biases[i][:, None]
        if i < 3:
            value = torch.relu(value)
    return value.reshape(m, g, points)


def objective(torch, weights, biases, character, xy, wanted, valid,
              unlabelled, pu, truth, unlabelled_weight):
    fitted = evaluate(torch, weights, biases, character, xy)
    error = (fitted-wanted).abs().mean(-1)
    value = (error*valid).sum(1)/valid.sum(1)
    if unlabelled_weight:
        su = torch.sigmoid(8*evaluate(torch, weights, biases, unlabelled, pu))
        area = su.mean(-1)
        # cdist avoids materializing M*U*G*points differences. The metric is
        # the same mean absolute distance as the original trainer.
        dd = torch.cdist(su, su, p=1)/su.shape[-1]
        dt = torch.cdist(su, truth, p=1)/su.shape[-1]
        u = su.shape[1]
        distinct = (torch.relu(.12-dd).sum((1, 2))-.12*u)/(u*(u-1))
        apart = (torch.relu(.12-dt)*valid[:, None]).sum((1, 2))/(u*valid.sum(1))
        value = value + unlabelled_weight*((torch.relu(.08-area)+torch.relu(area-.25)).mean(1)+distinct+apart)
    return value


def train(args):
    import torch
    import strokes
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_default_device(args.device)
    seeds = [int(x) for x in args.seeds.split(',')]
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('seeds must be distinct')
    members = [{**spec, 'seed': seed} for seed in seeds for spec in specs(args.mode, args.parts)]
    members = members[args.start:args.start+args.batch_models]
    if not members:
        raise ValueError('empty training batch')
    metadata = json.loads((args.directory/'teacher.json').read_text())
    if digest(args.directory/'teacher.npy') != metadata['sha256']:
        raise ValueError('teacher SHA256 differs')
    full = np.load(args.directory/'teacher.npy', allow_pickle=False)
    model_count, glyph_count = len(members), max(len(x['scalars']) for x in members)
    width, n = members[0]['width'], metadata['identity']['grid']
    fields, labels, valid = [], [], []
    for member in members:
        indices = [c-32 for c in member['scalars']]
        field = full[indices].astype(np.float32)
        if args.mode == 'spatial':
            field = crop(field, member['region'])
        pad = glyph_count-len(indices)
        fields.append(np.pad(field, ((0,pad),(0,0),(0,0)), constant_values=-1).astype(np.float16))
        labels.append(member['scalars']+[0]*pad)
        valid.append([1.]*len(indices)+[0.]*pad)
    target_field = torch.tensor(np.stack(fields)).flatten()
    del fields, full
    lab = torch.tensor(labels)
    valid = torch.tensor(valid)
    offsets = torch.arange(model_count*glyph_count).reshape(model_count,glyph_count,1)*(n+1)*(2*n+1)
    def target(xy):
        u, v = xy[...,0]*n, xy[...,1]*n
        i, j = u.floor().clamp(0,n-1), v.floor().clamp(0,2*n-1)
        fu, fv = u-i, v-j
        at = offsets+j.long()*(n+1)+i.long()
        a,b,c,d = (target_field[at+delta].float() for delta in (0,1,n+1,n+2))
        return (a*(1-fu)+b*fu)*(1-fv)+(c*(1-fu)+d*fu)*fv
    masks = strokes.masks()
    mask_bits = torch.tensor([[(mask>>bit)&1 for bit in range(21)] for mask in masks], dtype=torch.float32)
    cf = code(torch,lab,mask_bits)
    nets, generators = {}, {}
    for seed in sorted({m['seed'] for m in members}):
        torch.manual_seed(seed)
        net = torch.nn.Sequential(torch.nn.Linear(90,width),torch.nn.ReLU(),
             torch.nn.Linear(width,width),torch.nn.ReLU(),torch.nn.Linear(width,width),
             torch.nn.ReLU(),torch.nn.Linear(width,1))
        nets[seed] = [layer for layer in net if isinstance(layer,torch.nn.Linear)]
        gen = torch.Generator(device=args.device)
        gen.set_state(torch.cuda.get_rng_state() if args.device.startswith('cuda') else torch.get_rng_state())
        generators[seed] = gen
    weights = [torch.nn.Parameter(torch.stack([nets[m['seed']][i].weight.detach() for m in members])) for i in range(4)]
    biases = [torch.nn.Parameter(torch.stack([nets[m['seed']][i].bias.detach() for m in members])) for i in range(4)]
    optimizer = torch.optim.Adam(weights+biases,lr=.002)
    schedule = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,args.steps)
    identity = {'schema':'neuronte.decomposition-training/v1','members':members,'steps':args.steps,
        'teacher':metadata,'trainer_sha256':digest(__file__),'unlabelled_weight':args.unlabelled,
        'torch':str(torch.__version__),'cuda':torch.version.cuda,'compiled':args.compile,'tf32':False,
        'device':torch.cuda.get_device_name(0) if args.device.startswith('cuda') else args.device,
        'labelled_samples':256,'candidate_samples':1024,'unlabelled_samples':256,'unlabelled_scalars':64,
        'optimizer':'Adam 0.002, cosine','gradient_reduction':'sum of independent per-model losses',
        'rng_policy':'original initialization, shared draws within a seed and padded glyph-count group'}
    stem=f'{args.mode}-k{args.parts}-start{args.start}-m{len(members)}'
    checkpoint=args.directory/(stem+'.pt')
    first, last = 0, []
    if args.resume:
        saved=torch.load(checkpoint,map_location=args.device,weights_only=True)
        if saved['identity']!=identity:
            raise ValueError('checkpoint identity differs')
        with torch.no_grad():
            for p,q in zip(weights+biases,saved['parameters']): p.copy_(q)
        optimizer.load_state_dict(saved['optimizer']);schedule.load_state_dict(saved['schedule'])
        for seed,state in saved['rng'].items():generators[seed].set_state(state.cpu())
        first,last=saved['step'],saved['losses']
    print(json.dumps(identity),flush=True)
    def loss_fn(weights,biases,xy,wanted,unlabelled,pu,truth):
        return objective(torch,weights,biases,cf,xy,wanted,valid,unlabelled,pu,truth,args.unlabelled)
    if args.compile:loss_fn=torch.compile(loss_fn,fullgraph=True)
    span=torch.tensor([1.,2.])
    started=time.monotonic()
    for step in range(first,args.steps):
        draws={}
        for seed,gen in generators.items():
            draws[seed]=(torch.rand(glyph_count,1024,2,generator=gen)*span,
                         torch.randint(0,0x110000,(64,),generator=gen),
                         torch.rand(1,256,2,generator=gen)*span)
        cand=torch.stack([draws[m['seed']][0] for m in members])
        v=torch.stack([draws[m['seed']][1] for m in members])
        pu=torch.stack([draws[m['seed']][2] for m in members])
        v=torch.where(((v[...,None]==lab[:,None]) & valid[:,None].bool()).any(-1)|((v>=0xd800)&(v<=0xdfff)),v+0x1000,v)
        tc=target(cand)
        near=tc.abs().topk(128,dim=2,largest=False).indices
        xy=torch.cat((cand[:,:,:128],torch.gather(cand,2,near[...,None].expand(-1,-1,-1,2))),dim=2)
        wanted=torch.cat((tc[:,:,:128],torch.gather(tc,2,near)),dim=2)
        truth=(target(pu.expand(-1,glyph_count,-1,-1))>0).float()
        optimizer.zero_grad()
        losses=loss_fn(weights,biases,xy,wanted,code(torch,v,mask_bits),pu.expand(-1,64,-1,-1),truth)
        losses.sum().backward();optimizer.step();schedule.step()
        if (step+1)%args.log_every==0 or step+1==args.steps:
            last=losses.detach().cpu().tolist()
            if not all(math.isfinite(v) for v in last):raise ValueError('nonfinite training loss')
            print(json.dumps({'step':step+1,'seconds':time.monotonic()-started,'losses':last}),flush=True)
        stopped = args.stop_after is not None and step+1 >= args.stop_after
        if (step+1)%args.checkpoint_every==0 or step+1==args.steps or stopped:
            last=losses.detach().cpu().tolist()
            tmp=checkpoint.with_suffix('.tmp')
            torch.save({'identity':identity,'step':step+1,'parameters':[p.detach() for p in weights+biases],
                'optimizer':optimizer.state_dict(),'schedule':schedule.state_dict(),'losses':last,
                'rng':{seed:gen.get_state() for seed,gen in generators.items()}},tmp)
            tmp.replace(checkpoint)
        if stopped and step+1 < args.steps:
            print(json.dumps({'status':'paused','step':step+1,'seconds':time.monotonic()-started}),flush=True)
            return
    for k,member in enumerate(members):
        x0,x1,_,_=member['region']
        doc={'format':'neuronte-weights','version':1,
             'shape':{'position_octaves':6,'code_bits':64,'hidden_width':width,'hidden_layers':3,
                      'tau':.15/(x1-x0),'parity_masks':[f'0x{x:06X}' for x in masks]},
             'training':{'set':'ascii-'+args.mode,'labelled':' '.join(f'U+{x:04X}' for x in member['scalars']),
                         'sources_sha256':metadata['identity']['sources'],'pen_radius':metadata['identity']['pen'],
                         'grid':n,'steps':args.steps,'seed':member['seed'],'unlabelled_weight':args.unlabelled,
                         'experiment':{'identity':identity,**member,'final_loss':last[k]}},
             'layers':{name:{'rows':w.shape[1],'cols':w.shape[2],'weight':w[k].detach().cpu().flatten().tolist(),
                             'bias':b[k].detach().cpu().tolist()}
                       for name,w,b in zip(('l1','l2','l3','out'),weights,biases)}}
        path=args.directory/(member['name']+f"-s{member['seed']}.json")
        path.write_text(json.dumps(doc)+'\n')
    print(json.dumps({'status':'complete','models':len(members),'steps':args.steps,'seconds':time.monotonic()-started}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('prepare','train'))
    parser.add_argument('directory',type=Path)
    parser.add_argument('--mode',choices=('spatial','repertoire'),default='spatial')
    parser.add_argument('--parts',type=int,choices=COUNTS,default=4)
    parser.add_argument('--seeds',default='0,1')
    parser.add_argument('--steps',type=int,default=20000)
    parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--batch-models',type=int,default=16)
    parser.add_argument('--device',default='cuda')
    parser.add_argument('--unlabelled',type=float,default=1.)
    parser.add_argument('--compile',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--log-every',type=int,default=1000)
    parser.add_argument('--checkpoint-every',type=int,default=2000)
    parser.add_argument('--stop-after',type=int,help='checkpoint and exit after this absolute step, retaining the full schedule')
    args=parser.parse_args()
    if min(args.steps,args.batch_models,args.log_every,args.checkpoint_every)<1 or args.start<0 or not math.isfinite(args.unlabelled) or args.unlabelled<0 or (args.stop_after is not None and args.stop_after<1):
        parser.error('invalid training counts or loss weight')
    if args.operation=='prepare':prepare(args.directory)
    else:train(args)


if __name__=='__main__':
    main()
