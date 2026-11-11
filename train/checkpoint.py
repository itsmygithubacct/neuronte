"""Atomic, source-bound resumable training state (own files only).

Optimizer, schedule and CPU/CUDA random generators resume together. A source
or training-argument mismatch is an error; output/log/checkpoint locations may
change when moving to a replacement rental. Checkpoints are never published
as completed weight files.
"""
import os
from pathlib import Path
import torch


def arguments(parser):
    parser.add_argument('--checkpoint', help='atomically save resumable optimizer/RNG state here')
    parser.add_argument('--checkpoint-every', type=int, default=2000)
    parser.add_argument('--resume', help='resume a source-bound checkpoint from this trainer')
    parser.add_argument('--stop-after', type=int, help='stop with exit75 after this total step, saving a checkpoint')


def identity(args, sources):
    if args.checkpoint_every<1 or (args.stop_after is not None and args.stop_after<1):
        raise ValueError('checkpoint interval and stopping step must be positive')
    ignored={'out','checkpoint','checkpoint_every','resume','scores_out','log_every','stop_after'}
    return {'arguments':{k:v for k,v in vars(args).items() if k not in ignored},'sources_sha256':sources}


def save(path, step, models, optimizer, schedule, metadata, metrics):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    state={'version':1,'step':step,'identity':metadata,'models':{k:v.state_dict() for k,v in models.items()},
           'optimizer':optimizer.state_dict(),'schedule':schedule.state_dict(),
           'rng_cpu':torch.get_rng_state(),'rng_cuda':torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
           'metrics':{k:float(v.detach()) for k,v in metrics.items()}}
    temp=path.with_name(path.name+'.tmp')
    torch.save(state,temp)
    os.replace(temp,path)


def restore(path, models, optimizer, schedule, metadata, device):
    state=torch.load(path,map_location=device,weights_only=True)
    if state.get('version')!=1 or state.get('identity')!=metadata:
        raise ValueError('checkpoint source/arguments differ from this run')
    if set(state['models'])!=set(models):raise ValueError('checkpoint model inventory differs')
    for name,model in models.items():model.load_state_dict(state['models'][name])
    optimizer.load_state_dict(state['optimizer']);schedule.load_state_dict(state['schedule'])
    torch.set_rng_state(state['rng_cpu'].cpu())
    if state['rng_cuda']:
        if not torch.cuda.is_available():raise ValueError('CUDA checkpoint requires CUDA')
        torch.cuda.set_rng_state_all([v.cpu() for v in state['rng_cuda']])
    return state['step'],state['metrics']


def tick(args, step, models, optimizer, schedule, metadata, metrics):
    stopping=args.stop_after is not None and step>=args.stop_after
    if args.checkpoint and (step%args.checkpoint_every==0 or step==args.steps or stopping):
        save(args.checkpoint,step,models,optimizer,schedule,metadata,metrics)
    if stopping and step<args.steps:
        if not args.checkpoint:raise ValueError('--stop-after requires --checkpoint')
        raise SystemExit(75)
