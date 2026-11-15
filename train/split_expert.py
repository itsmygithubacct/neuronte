"""Spatial and character-group experiments for any monochrome glyph set.

This generalizes decompose.py, which is fixed to printable ASCII, to every
set in glyphs.SETS. The loss, sampling, initialization, optimizer, schedule,
batching, checkpoint and export rules are decompose.py's; its functions are
imported rather than copied, and test_split_expert.py checks that an ASCII
run here writes the same weights as decompose.py.

    python3 train/split_expert.py prepare DIR --set symbol
    python3 train/split_expert.py train DIR --mode repertoire --partition interleaved --parts 4

Character groups divide the set's labels, in scalar order, into groups whose
sizes differ by at most one: `contiguous` takes consecutive runs (few table
ranges), `interleaved` deals the labels out in turn, so neighbouring and
similar glyphs land in different groups. Spatial tiles draw one region of
every glyph and receive the original scalar. The hidden-width budget is
shared equally; the budget must divide by the part count.
MIT licence; see LICENSE.
"""
import argparse
import json
import math
from pathlib import Path
import time

import numpy as np

import decompose as d

GRIDS = {1: (1, 1), 2: (1, 2), 4: (2, 2), 8: (2, 4), 16: (4, 4), 64: (8, 8)}
PARTITIONS = ('contiguous', 'interleaved')
SIZES = ((8, 16), (16, 32), (48, 96))


def groups(scalars, count, partition):
    n = len(scalars)
    if partition == 'contiguous':
        return [scalars[n*i//count:n*(i+1)//count] for i in range(count)]
    if partition == 'interleaved':
        return [scalars[i::count] for i in range(count)]
    raise ValueError(f'no partition {partition!r}')


def specs(name, scalars, mode, count, partition='contiguous', budget=128):
    if mode not in ('spatial', 'repertoire') or count < 1 or budget % count:
        raise ValueError('unsupported decomposition')
    if mode == 'spatial' and count not in GRIDS:
        raise ValueError(f'no spatial grid for {count} parts')
    if mode == 'repertoire' and count > len(scalars):
        raise ValueError('more groups than labels')
    label = f'{name}-{mode}' + (f'-{partition}' if mode == 'repertoire' else '') + f'-k{count}'
    parts = groups(scalars, count, partition) if mode == 'repertoire' else [scalars]*count
    out = []
    for i in range(count):
        if mode == 'spatial':
            cols, rows = GRIDS[count]
            region = [i % cols / cols, (i % cols + 1) / cols, 2*(i // cols) / rows, 2*(i // cols + 1) / rows]
        else:
            region = [0., 1., 0., 2.]
        out.append({'name': f'{label}-p{i}', 'index': i, 'width': budget // count,
                    'region': region, 'scalars': list(parts[i])})
    return out


def prepare(directory, name):
    import glyphs
    directory.mkdir(parents=True, exist_ok=True)
    rows = glyphs.charset(name)
    scalars = [ord(c) for c, _, _ in rows]
    pen = glyphs.PENS.get(name, glyphs.PEN)
    sources = {f: d.digest(d.ROOT/f) for f in glyphs.sources(name) + ['font/code-masks.txt']}
    spec = {'schema': 'neuronte.split-teacher/v1', 'set': name, 'scalars': scalars, 'grid': 256,
            'tau': .15, 'pen': pen, 'sources': sources}
    path, meta = directory/'teacher.npy', directory/'teacher.json'
    if meta.exists():
        old = json.loads(meta.read_text())
        if old['identity'] != spec or d.digest(path) != old['sha256']:
            raise ValueError('teacher identity or asset changed')
        if any(d.digest(directory/t['file']) != t['sha256'] for t in old['targets'].values()):
            raise ValueError('teacher coverage target changed')
        print('existing verified teacher', path)
        return
    fields = np.stack([glyphs.field(shapes, 256, pen, .15) for _, _, shapes in rows]).astype(np.float16)
    np.save(path, fields, allow_pickle=False)
    targets = {}
    for w, h in SIZES:
        target = directory/f'truth-{w}x{h}.npy'
        np.save(target, d.teacher_masks(fields, w, h), allow_pickle=False)
        targets[f'{w}x{h}'] = {'file': target.name, 'sha256': d.digest(target)}
    meta.write_text(json.dumps({'identity': spec, 'sha256': d.digest(path), 'targets': targets}, indent=2)+'\n')
    print(meta)


def train(args):
    import torch
    import strokes
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_default_device(args.device)
    metadata = json.loads((args.directory/'teacher.json').read_text())
    if d.digest(args.directory/'teacher.npy') != metadata['sha256']:
        raise ValueError('teacher SHA256 differs')
    name, scalars = metadata['identity']['set'], metadata['identity']['scalars']
    seeds = [int(x) for x in args.seeds.split(',')]
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('seeds must be distinct')
    members = [{**spec, 'seed': seed} for seed in seeds
               for spec in specs(name, scalars, args.mode, args.parts, args.partition, args.budget)]
    members = members[args.start:args.start+args.batch_models]
    if not members:
        raise ValueError('empty training batch')
    full = np.load(args.directory/'teacher.npy', allow_pickle=False)
    model_count, glyph_count = len(members), max(len(x['scalars']) for x in members)
    width, n = members[0]['width'], metadata['identity']['grid']
    if any(m['width'] != width for m in members):
        raise ValueError('one batch must share one width')
    where = {s: i for i, s in enumerate(scalars)}
    fields, labels, valid = [], [], []
    for member in members:
        indices = [where[c] for c in member['scalars']]
        field = full[indices].astype(np.float32)
        if args.mode == 'spatial':
            field = d.crop(field, member['region'])
        pad = glyph_count-len(indices)
        fields.append(np.pad(field, ((0, pad), (0, 0), (0, 0)), constant_values=-1).astype(np.float16))
        labels.append(member['scalars']+[0]*pad)
        valid.append([1.]*len(indices)+[0.]*pad)
    target_field = torch.tensor(np.stack(fields)).flatten()
    del fields, full
    lab = torch.tensor(labels)
    valid = torch.tensor(valid)
    offsets = torch.arange(model_count*glyph_count).reshape(model_count, glyph_count, 1)*(n+1)*(2*n+1)

    def target(xy):
        u, v = xy[..., 0]*n, xy[..., 1]*n
        i, j = u.floor().clamp(0, n-1), v.floor().clamp(0, 2*n-1)
        fu, fv = u-i, v-j
        at = offsets+j.long()*(n+1)+i.long()
        a, b, c, e = (target_field[at+delta].float() for delta in (0, 1, n+1, n+2))
        return (a*(1-fu)+b*fu)*(1-fv)+(c*(1-fu)+e*fu)*fv
    masks = strokes.masks()
    mask_bits = torch.tensor([[(mask >> bit) & 1 for bit in range(21)] for mask in masks], dtype=torch.float32)
    cf = d.code(torch, lab, mask_bits)
    nets, generators = {}, {}
    for seed in sorted({m['seed'] for m in members}):
        torch.manual_seed(seed)
        net = torch.nn.Sequential(torch.nn.Linear(90, width), torch.nn.ReLU(),
                                  torch.nn.Linear(width, width), torch.nn.ReLU(), torch.nn.Linear(width, width),
                                  torch.nn.ReLU(), torch.nn.Linear(width, 1))
        nets[seed] = [layer for layer in net if isinstance(layer, torch.nn.Linear)]
        gen = torch.Generator(device=args.device)
        gen.set_state(torch.cuda.get_rng_state() if args.device.startswith('cuda') else torch.get_rng_state())
        generators[seed] = gen
    weights = [torch.nn.Parameter(torch.stack([nets[m['seed']][i].weight.detach() for m in members])) for i in range(4)]
    biases = [torch.nn.Parameter(torch.stack([nets[m['seed']][i].bias.detach() for m in members])) for i in range(4)]
    optimizer = torch.optim.Adam(weights+biases, lr=.002)
    schedule = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, args.steps)
    identity = {'schema': 'neuronte.split-training/v1', 'members': members, 'steps': args.steps,
                'teacher': metadata, 'trainer_sha256': d.digest(__file__), 'loss_sha256': d.digest(d.__file__),
                'unlabelled_weight': args.unlabelled,
                'torch': str(torch.__version__), 'cuda': torch.version.cuda, 'compiled': args.compile, 'tf32': False,
                'device': torch.cuda.get_device_name(0) if args.device.startswith('cuda') else args.device,
                'labelled_samples': 256, 'candidate_samples': 1024, 'unlabelled_samples': 256, 'unlabelled_scalars': 64,
                'optimizer': 'Adam 0.002, cosine', 'gradient_reduction': 'sum of independent per-model losses',
                'rng_policy': 'original initialization, shared draws within a seed and padded glyph-count group'}
    tag = f'-{args.partition}' if args.mode == 'repertoire' else ''
    stem = f'{args.mode}{tag}-k{args.parts}-start{args.start}-m{len(members)}'
    checkpoint = args.directory/(stem+'.pt')
    first, last = 0, []
    if args.resume:
        saved = torch.load(checkpoint, map_location=args.device, weights_only=True)
        if saved['identity'] != identity:
            raise ValueError('checkpoint identity differs')
        with torch.no_grad():
            for p, q in zip(weights+biases, saved['parameters']):
                p.copy_(q)
        optimizer.load_state_dict(saved['optimizer'])
        schedule.load_state_dict(saved['schedule'])
        for seed, state in saved['rng'].items():
            generators[seed].set_state(state.cpu())
        first, last = saved['step'], saved['losses']
    print(json.dumps(identity), flush=True)

    def loss_fn(weights, biases, xy, wanted, unlabelled, pu, truth):
        return d.objective(torch, weights, biases, cf, xy, wanted, valid, unlabelled, pu, truth, args.unlabelled)
    if args.compile:
        loss_fn = torch.compile(loss_fn, fullgraph=True)
    span = torch.tensor([1., 2.])
    started = time.monotonic()
    for step in range(first, args.steps):
        draws = {}
        for seed, gen in generators.items():
            draws[seed] = (torch.rand(glyph_count, 1024, 2, generator=gen)*span,
                           torch.randint(0, 0x110000, (64,), generator=gen),
                           torch.rand(1, 256, 2, generator=gen)*span)
        cand = torch.stack([draws[m['seed']][0] for m in members])
        v = torch.stack([draws[m['seed']][1] for m in members])
        pu = torch.stack([draws[m['seed']][2] for m in members])
        v = torch.where(((v[..., None] == lab[:, None]) & valid[:, None].bool()).any(-1) | ((v >= 0xd800) & (v <= 0xdfff)), v+0x1000, v)
        tc = target(cand)
        near = tc.abs().topk(128, dim=2, largest=False).indices
        xy = torch.cat((cand[:, :, :128], torch.gather(cand, 2, near[..., None].expand(-1, -1, -1, 2))), dim=2)
        wanted = torch.cat((tc[:, :, :128], torch.gather(tc, 2, near)), dim=2)
        truth = (target(pu.expand(-1, glyph_count, -1, -1)) > 0).float()
        optimizer.zero_grad()
        losses = loss_fn(weights, biases, xy, wanted, d.code(torch, v, mask_bits), pu.expand(-1, 64, -1, -1), truth)
        losses.sum().backward()
        optimizer.step()
        schedule.step()
        if (step+1) % args.log_every == 0 or step+1 == args.steps:
            last = losses.detach().cpu().tolist()
            if not all(math.isfinite(x) for x in last):
                raise ValueError('nonfinite training loss')
            print(json.dumps({'step': step+1, 'seconds': time.monotonic()-started, 'losses': last}), flush=True)
        stopped = args.stop_after is not None and step+1 >= args.stop_after
        if (step+1) % args.checkpoint_every == 0 or step+1 == args.steps or stopped:
            last = losses.detach().cpu().tolist()
            tmp = checkpoint.with_suffix('.tmp')
            torch.save({'identity': identity, 'step': step+1, 'parameters': [p.detach() for p in weights+biases],
                        'optimizer': optimizer.state_dict(), 'schedule': schedule.state_dict(), 'losses': last,
                        'rng': {seed: gen.get_state() for seed, gen in generators.items()}}, tmp)
            tmp.replace(checkpoint)
        if stopped and step+1 < args.steps:
            print(json.dumps({'status': 'paused', 'step': step+1, 'seconds': time.monotonic()-started}), flush=True)
            return
    for k, member in enumerate(members):
        x0, x1, _, _ = member['region']
        doc = {'format': 'neuronte-weights', 'version': 1,
               'shape': {'position_octaves': 6, 'code_bits': 64, 'hidden_width': width, 'hidden_layers': 3,
                         'tau': .15/(x1-x0), 'parity_masks': [f'0x{x:06X}' for x in masks]},
               'training': {'set': f'{name}-{args.mode}', 'labelled': ' '.join(f'U+{x:04X}' for x in member['scalars']),
                            'sources_sha256': metadata['identity']['sources'], 'pen_radius': metadata['identity']['pen'],
                            'grid': n, 'steps': args.steps, 'seed': member['seed'], 'unlabelled_weight': args.unlabelled,
                            'experiment': {'identity': identity, **member, 'final_loss': last[k]}},
               'layers': {lname: {'rows': w.shape[1], 'cols': w.shape[2], 'weight': w[k].detach().cpu().flatten().tolist(),
                                  'bias': b[k].detach().cpu().tolist()}
                          for lname, w, b in zip(('l1', 'l2', 'l3', 'out'), weights, biases)}}
        path = args.directory/(member['name']+f"-s{member['seed']}.json")
        path.write_text(json.dumps(doc)+'\n')
    print(json.dumps({'status': 'complete', 'models': len(members), 'steps': args.steps,
                      'seconds': time.monotonic()-started}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('operation', choices=('prepare', 'train'))
    parser.add_argument('directory', type=Path)
    parser.add_argument('--set', default='symbol', help='a glyphs.SETS name, for prepare')
    parser.add_argument('--mode', choices=('spatial', 'repertoire'), default='repertoire')
    parser.add_argument('--partition', choices=PARTITIONS, default='contiguous')
    parser.add_argument('--parts', type=int, default=4)
    parser.add_argument('--budget', type=int, default=128, help='total hidden width shared by the parts')
    parser.add_argument('--seeds', default='0,1')
    parser.add_argument('--steps', type=int, default=20000)
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--batch-models', type=int, default=16)
    parser.add_argument('--device', default='cuda')
    parser.add_argument('--unlabelled', type=float, default=1.)
    parser.add_argument('--compile', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--log-every', type=int, default=1000)
    parser.add_argument('--checkpoint-every', type=int, default=2000)
    parser.add_argument('--stop-after', type=int, help='checkpoint and exit after this absolute step, retaining the full schedule')
    args = parser.parse_args()
    if (min(args.steps, args.batch_models, args.log_every, args.checkpoint_every, args.parts, args.budget) < 1
            or args.start < 0 or not math.isfinite(args.unlabelled) or args.unlabelled < 0
            or (args.stop_after is not None and args.stop_after < 1)):
        parser.error('invalid training counts or loss weight')
    if args.operation == 'prepare':
        prepare(args.directory, args.set)
    else:
        train(args)


if __name__ == '__main__':
    main()
