"""Atomic, source-bound resumable training state (own files only).

Optimizer, schedule and CPU/CUDA random generators resume together. A source
or training-argument mismatch is an error; output/log/checkpoint locations may
change when moving to a replacement rental. Checkpoints are never published
as completed weight files.
"""
import os
import time
import hashlib
from pathlib import Path
import torch


def arguments(parser):
    parser.add_argument('--checkpoint', help='atomically save resumable optimizer/RNG state here')
    parser.add_argument('--checkpoint-every', type=int, default=2000)
    parser.add_argument('--resume', help='resume a source-bound checkpoint from this trainer')
    parser.add_argument('--stop-after', type=int, help='stop with exit75 after this total step, saving a checkpoint')
    parser.add_argument('--deadline', type=float, help='UTC Unix time to save and stop with exit75')


def identity(args, sources):
    if args.checkpoint_every<1 or (args.stop_after is not None and args.stop_after<1):
        raise ValueError('checkpoint interval and stopping step must be positive')
    ignored={'out','checkpoint','checkpoint_every','resume','scores_out','log_every','stop_after','deadline',
             'continue_from','continue_source'}
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


def _restore_state(state, models, optimizer, schedule):
    if set(state['models'])!=set(models):raise ValueError('checkpoint model inventory differs')
    for name,model in models.items():model.load_state_dict(state['models'][name])
    optimizer.load_state_dict(state['optimizer'])
    if schedule is not None:schedule.load_state_dict(state['schedule'])
    torch.set_rng_state(state['rng_cpu'].cpu())
    if state['rng_cuda']:
        if not torch.cuda.is_available():raise ValueError('CUDA checkpoint requires CUDA')
        torch.cuda.set_rng_state_all([v.cpu() for v in state['rng_cuda']])
    return state['step'],state['metrics']


def restore(path, models, optimizer, schedule, metadata, device):
    state=torch.load(path,map_location=device,weights_only=True)
    saved=dict(state.get('identity',{}));lineage=saved.pop('continuation',None)
    wanted={k:v for k,v in metadata.items() if k!='continuation'}
    if state.get('version')!=1 or saved!=wanted:
        raise ValueError('checkpoint source/arguments differ from this run')
    if lineage is not None:metadata['continuation']=lineage
    return _restore_state(state,models,optimizer,schedule)


def continue_phase(path, models, optimizer, metadata, device, source_tree, learning_rate):
    """Start an explicit new phase from a completed, verified parent checkpoint.

    The parent optimizer and RNG continue; its exhausted scheduler does not.
    Only trainer/checkpoint source changes are allowed. Every historical file
    must still match the supplied immutable source export, and all target and
    feature implementations must also match the current sources.
    """
    raw=Path(path).read_bytes()
    state=torch.load(path,map_location=device,weights_only=True)
    if state.get('version')!=1:raise ValueError('unknown continuation checkpoint version')
    parent=state['identity'];old=dict(parent['arguments']);new=dict(metadata['arguments'])
    old_steps=old.pop('steps');new_steps=new.pop('steps')
    old.pop('continue_lr',None);new.pop('continue_lr',None)
    if old!=new:raise ValueError('continuation arguments differ beyond phase settings')
    if state['step']!=old_steps or new_steps<=old_steps:
        raise ValueError('continuation requires a completed parent and larger total steps')
    previous=parent['sources_sha256'];current=metadata['sources_sha256']
    if set(previous)!=set(current):raise ValueError('continuation source inventory differs')
    root=Path(source_tree).resolve()
    for name,digest in previous.items():
        historical=(root/name).resolve()
        if not historical.is_relative_to(root) or not historical.is_file() or hashlib.sha256(historical.read_bytes()).hexdigest()!=digest:
            raise ValueError('continuation historical source mismatch: '+name)
        if name not in ('train/train.py','train/checkpoint.py') and current[name]!=digest:
            raise ValueError('continuation target or feature source changed: '+name)
    metadata['continuation']={'kind':'new-cosine-phase','parent_checkpoint_sha256':hashlib.sha256(raw).hexdigest(),
        'parent_identity':parent,'parent_steps':old_steps,'phase_steps':new_steps-old_steps,
        'phase_initial_lr':learning_rate,'optimizer_state_retained':True,'rng_state_retained':True}
    return _restore_state(state,models,optimizer,None)


def tick(args, step, models, optimizer, schedule, metadata, metrics):
    stopping=(args.stop_after is not None and step>=args.stop_after) or (args.deadline is not None and time.time()>=args.deadline)
    if args.checkpoint and (step%args.checkpoint_every==0 or step==args.steps or stopping):
        save(args.checkpoint,step,models,optimizer,schedule,metadata,metrics)
    if stopping and step<args.steps:
        if not args.checkpoint:raise ValueError('--stop-after/--deadline requires --checkpoint')
        raise SystemExit(75)
