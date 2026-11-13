"""Spatial and repertoire decomposition experiments for the box-drawing expert.

The shipped draw expert (neuronte-draw-v2) is one 90->192->192->192->1
distance net over the 131 boxshade scalars: box drawing U+2500..U+257F and
the shades U+2591..U+2593. Each design below keeps the total hidden width at
192 and divides it among independent nets, either by region of the cell
(spatial: every tile sees all 131 scalars and learns its region) or by
scalar (repertoire: contiguous groups of the ordered scalars, each drawn
whole by one net). C1 retrains the original shape with this batched
trainer as a recipe control.

Loss, sampling, Adam/cosine schedule and initialization are the original
trainer's; the batched evaluation and objective are imported from
decompose.py, whose equivalence tests cover them. See DECOMPOSITION.md.
MIT licence; see LICENSE.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

import decompose

ROOT = Path(__file__).resolve().parents[1]
SET = 'boxshade'
BUDGET = 192
# name: (kind, parts, grid columns, grid rows); width is BUDGET // parts.
DESIGNS = {
    'C1': ('control', 1, 1, 1),
    'S2': ('spatial', 2, 1, 2),
    'S4': ('spatial', 4, 2, 2),
    'S8': ('spatial', 8, 2, 4),
    'R2': ('repertoire', 2, 1, 1),
    'R4': ('repertoire', 4, 1, 1),
    'R8': ('repertoire', 8, 1, 1),
    'R16': ('repertoire', 16, 1, 1),
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def boxshade_scalars():
    import glyphs
    return [ord(c) for c, _, _ in glyphs.charset(SET)]


def groups(scalars, parts):
    """Contiguous groups of the ordered scalars, sizes differing by at most one."""
    n = len(scalars)
    return [scalars[n*i//parts:n*(i+1)//parts] for i in range(parts)]


def specs(design, scalars, width=None, custom=None):
    if design == 'custom':
        if not custom or not width:
            raise ValueError('a custom design needs --groups-file, --tag and --width')
        tag, chosen = custom
        if sorted(sum(chosen, [])) != sorted(set(sum(chosen, []))) or not set(sum(chosen, [])) <= set(scalars):
            raise ValueError('custom groups must be disjoint labelled scalars')
        return [{'name': f'draw-{tag}-p{i}', 'design': tag, 'index': i, 'width': width,
                 'region': [0., 1., 0., 2.], 'scalars': sorted(g)} for i, g in enumerate(chosen)]
    if design not in DESIGNS:
        raise ValueError(f'unknown draw design {design!r}')
    kind, parts, cols, rows = DESIGNS[design]
    width = width or BUDGET // parts
    out = []
    if kind == 'repertoire':
        for i, group in enumerate(groups(scalars, parts)):
            out.append({'name': f'draw-{design.lower()}-p{i}', 'design': design, 'index': i, 'width': width,
                        'region': [0., 1., 0., 2.], 'scalars': group})
    else:
        for i in range(parts):
            c, r = i % cols, i // cols
            out.append({'name': f'draw-{design.lower()}-p{i}', 'design': design, 'index': i, 'width': width,
                        'region': [c/cols, (c+1)/cols, 2*r/rows, 2*(r+1)/rows], 'scalars': scalars})
    return out


def prepare(directory):
    import glyphs
    directory.mkdir(parents=True, exist_ok=True)
    scalars = boxshade_scalars()
    sources = {name: digest(ROOT/name) for name in glyphs.sources(SET) + ['font/code-masks.txt']}
    spec = {'schema': 'neuronte.draw-teacher/v1', 'set': SET, 'scalars': scalars, 'grid': 256,
            'tau': .15, 'pen': glyphs.PENS.get(SET, glyphs.PEN), 'sources': sources}
    path, meta = directory/'teacher.npy', directory/'teacher.json'
    if meta.exists():
        old = json.loads(meta.read_text())
        if old['identity'] != spec or digest(path) != old['sha256']:
            raise ValueError('teacher identity or asset changed')
        print('existing verified teacher', path)
        return
    rows = glyphs.charset(SET)
    fields = np.stack([glyphs.field(shapes, 256, spec['pen'], .15) for _, _, shapes in rows]).astype(np.float16)
    np.save(path, fields, allow_pickle=False)
    meta.write_text(json.dumps({'identity': spec, 'sha256': digest(path)}, indent=2)+'\n')
    print(meta)


def train(args):
    import torch
    import strokes
    torch.set_num_threads(max(1, args.threads))
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_default_device(args.device)
    metadata = json.loads((args.directory/'teacher.json').read_text())
    if digest(args.directory/'teacher.npy') != metadata['sha256']:
        raise ValueError('teacher SHA256 differs')
    scalars = metadata['identity']['scalars']
    seeds = [int(x) for x in args.seeds.split(',')]
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('seeds must be distinct')
    custom = None
    if args.design == 'custom':
        custom = (args.tag, json.loads(Path(args.groups_file).read_text()))
    members = [{**spec, 'seed': seed} for seed in seeds for spec in specs(args.design, scalars, args.width, custom)]
    full = np.load(args.directory/'teacher.npy', allow_pickle=False)
    index = {s: i for i, s in enumerate(scalars)}
    model_count, glyph_count = len(members), max(len(m['scalars']) for m in members)
    width, n = members[0]['width'], metadata['identity']['grid']
    fields, labels, valid = [], [], []
    for member in members:
        rows = [index[s] for s in member['scalars']]
        field = full[rows].astype(np.float32)
        if member['region'] != [0., 1., 0., 2.]:
            field = decompose.crop(field, member['region'])
        pad = glyph_count-len(rows)
        fields.append(np.pad(field, ((0, pad), (0, 0), (0, 0)), constant_values=-1).astype(np.float16))
        labels.append(member['scalars']+[0]*pad)
        valid.append([1.]*len(rows)+[0.]*pad)
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
        a, b, c, d = (target_field[at+delta].float() for delta in (0, 1, n+1, n+2))
        return (a*(1-fu)+b*fu)*(1-fv)+(c*(1-fu)+d*fu)*fv

    masks = strokes.masks()
    mask_bits = torch.tensor([[(mask >> bit) & 1 for bit in range(21)] for mask in masks], dtype=torch.float32)
    cf = decompose.code(torch, lab, mask_bits)
    nets, generators = {}, {}
    for seed in seeds:
        torch.manual_seed(seed)
        net = torch.nn.Sequential(torch.nn.Linear(90, width), torch.nn.ReLU(),
                                  torch.nn.Linear(width, width), torch.nn.ReLU(),
                                  torch.nn.Linear(width, width), torch.nn.ReLU(),
                                  torch.nn.Linear(width, 1))
        nets[seed] = [layer for layer in net if isinstance(layer, torch.nn.Linear)]
        gen = torch.Generator(device=args.device)
        gen.set_state(torch.cuda.get_rng_state() if args.device.startswith('cuda') else torch.get_rng_state())
        generators[seed] = gen
    weights = [torch.nn.Parameter(torch.stack([nets[m['seed']][i].weight.detach() for m in members])) for i in range(4)]
    biases = [torch.nn.Parameter(torch.stack([nets[m['seed']][i].bias.detach() for m in members])) for i in range(4)]
    optimizer = torch.optim.Adam(weights+biases, lr=.002)
    schedule = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, args.steps)
    identity = {'schema': 'neuronte.draw-decomposition-training/v1', 'design': args.design, 'members': members,
                'steps': args.steps, 'teacher': metadata, 'trainer_sha256': digest(__file__),
                'objective_sha256': digest(decompose.__file__), 'unlabelled_weight': args.unlabelled,
                'torch': str(torch.__version__), 'cuda': torch.version.cuda, 'compiled': args.compile, 'tf32': False,
                'device': torch.cuda.get_device_name(0) if args.device.startswith('cuda') else args.device,
                'labelled_samples': 256, 'candidate_samples': 1024, 'unlabelled_samples': 256, 'unlabelled_scalars': 64,
                'optimizer': 'Adam 0.002, cosine', 'gradient_reduction': 'sum of independent per-model losses',
                'rng_policy': 'original initialization per seed, shared draws within a seed and padded glyph-count group'}
    stem = f'{args.tag if custom else args.design}-w{width}-s{"_".join(map(str, seeds))}'
    checkpoint = args.directory/(stem+'.pt')
    first, last = 0, []
    if args.resume and checkpoint.exists():
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
    print(json.dumps({'identity_sha256': hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest(),
                      'design': args.design, 'members': len(members), 'width': width, 'start': first}), flush=True)

    def loss_fn(weights, biases, xy, wanted, unlabelled, pu, truth):
        return decompose.objective(torch, weights, biases, cf, xy, wanted, valid, unlabelled, pu, truth, args.unlabelled)
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
        losses = loss_fn(weights, biases, xy, wanted, decompose.code(torch, v, mask_bits), pu.expand(-1, 64, -1, -1), truth)
        losses.sum().backward()
        optimizer.step()
        schedule.step()
        if (step+1) % args.log_every == 0 or step+1 == args.steps:
            last = losses.detach().cpu().tolist()
            if not all(math.isfinite(x) for x in last):
                raise ValueError('nonfinite training loss')
            print(json.dumps({'step': step+1, 'seconds': round(time.monotonic()-started, 2), 'losses': last}), flush=True)
        if (step+1) % args.checkpoint_every == 0 or step+1 == args.steps:
            last = losses.detach().cpu().tolist()
            tmp = checkpoint.with_suffix('.tmp')
            torch.save({'identity': identity, 'step': step+1, 'parameters': [p.detach() for p in weights+biases],
                        'optimizer': optimizer.state_dict(), 'schedule': schedule.state_dict(), 'losses': last,
                        'rng': {seed: gen.get_state() for seed, gen in generators.items()}}, tmp)
            tmp.replace(checkpoint)
    export(args.directory, members, weights, biases, metadata, identity, last, args, masks)
    print(json.dumps({'status': 'complete', 'design': args.design, 'models': len(members), 'steps': args.steps,
                      'seconds': round(time.monotonic()-started, 2)}), flush=True)


def export(directory, members, weights, biases, metadata, identity, last, args, masks):
    for k, member in enumerate(members):
        x0, x1, _, _ = member['region']
        doc = {'format': 'neuronte-weights', 'version': 1,
               'shape': {'position_octaves': 6, 'code_bits': 64, 'hidden_width': member['width'], 'hidden_layers': 3,
                         'tau': .15/(x1-x0), 'parity_masks': [f'0x{x:06X}' for x in masks]},
               'training': {'set': f"{SET}-{member['design'].lower()}-p{member['index']}",
                            'labelled': ' '.join(f'U+{x:04X}' for x in member['scalars']),
                            'sources_sha256': metadata['identity']['sources'], 'pen_radius': metadata['identity']['pen'],
                            'grid': metadata['identity']['grid'], 'steps': args.steps, 'seed': member['seed'],
                            'unlabelled_weight': args.unlabelled,
                            'experiment': {'trainer_sha256': identity['trainer_sha256'],
                                           'objective_sha256': identity['objective_sha256'],
                                           'teacher_sha256': metadata['sha256'], 'torch': identity['torch'],
                                           'device': identity['device'], 'compiled': identity['compiled'],
                                           **member, 'final_loss': last[k]}},
               'layers': {name: {'rows': w.shape[1], 'cols': w.shape[2], 'weight': w[k].detach().cpu().flatten().tolist(),
                                 'bias': b[k].detach().cpu().tolist()}
                          for name, w, b in zip(('l1', 'l2', 'l3', 'out'), weights, biases)}}
        path = directory/f"{member['name']}-s{member['seed']}.json"
        path.write_text(json.dumps(doc)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('operation', choices=('prepare', 'train', 'specs'))
    parser.add_argument('directory', type=Path)
    parser.add_argument('--design', choices=sorted(DESIGNS)+['custom'], default='R4')
    parser.add_argument('--groups-file', help='custom design: JSON list of scalar lists, one per net')
    parser.add_argument('--tag', help='custom design name, lower case letters and digits')
    parser.add_argument('--width', type=int, help='override the per-net width (default: budget / parts)')
    parser.add_argument('--seeds', default='0,1')
    parser.add_argument('--steps', type=int, default=20000)
    parser.add_argument('--device', default='cuda')
    parser.add_argument('--threads', type=int, default=1)
    parser.add_argument('--unlabelled', type=float, default=1.)
    parser.add_argument('--compile', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--log-every', type=int, default=1000)
    parser.add_argument('--checkpoint-every', type=int, default=2000)
    args = parser.parse_args()
    if min(args.steps, args.log_every, args.checkpoint_every) < 1 or not math.isfinite(args.unlabelled) or args.unlabelled < 0:
        parser.error('invalid training counts or loss weight')
    if args.width is not None and not 1 <= args.width <= 1024:
        parser.error('width must be 1 to 1024')
    if args.design == 'custom' and not (args.groups_file and args.tag and args.tag.isalnum() and args.tag.islower()):
        parser.error('a custom design needs --groups-file and a lower-case alphanumeric --tag')
    if args.operation == 'prepare':
        prepare(args.directory)
    elif args.operation == 'specs':
        print(json.dumps({d: specs(d, boxshade_scalars()) for d in DESIGNS}, indent=1))
    else:
        train(args)


if __name__ == '__main__':
    main()
