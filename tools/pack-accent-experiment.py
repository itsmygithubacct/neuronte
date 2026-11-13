"""Pack trained accent splits without changing any original fallback expert.

The six original members retain their byte images and gate output rows.
Only labelled accent scalars route to appended split members. New gate outputs
are constant below a proved bound on every original logit, preserving misses.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import decompose
import pack

ORIGINALS = ['ascii-v0', 'draw-v2', 'symbol-v0', 'accent-v2', 'pixel-v1', 'braille-v0']


def build(directory, output, mode, parts, seed, budget=None):
    output.mkdir(parents=True, exist_ok=True)
    specs = decompose.specs(mode, parts, 'accent', budget)
    source_paths = [directory / (s['name'] + f'-s{seed}.json') for s in specs]
    docs = [json.loads(p.read_text()) for p in source_paths]
    identities = []
    for doc, spec in zip(docs, specs):
        experiment = doc['training']['experiment']
        if any(experiment[k] != v for k, v in spec.items()) or experiment['seed'] != seed:
            raise ValueError('trained member geometry or inventory differs')
        if doc['shape']['hidden_width'] != spec['width']:
            raise ValueError('trained width differs')
        if doc['shape']['tau'] != .15 / (spec['region'][1] - spec['region'][0]):
            raise ValueError('tile coverage scaling differs')
        identities.append(experiment['identity']['teacher'])
    if any(x != identities[0] for x in identities):
        raise ValueError('candidate members have different teachers')
    corpus = identities[0]['identity']['scalars']
    original_paths = [ROOT / 'weights' / ('neuronte-' + name + '.json') for name in ORIGINALS]
    paths, images = [], []
    for i, path in enumerate(original_paths):
        doc = json.loads(path.read_text())
        image = pack.pack(path)
        if i == 3:
            # Keep this binary expert for gate-selected unknown scalars only.
            doc['training']['labelled'] = ''
        dest = output / path.name
        dest.write_text(json.dumps(doc) + '\n')
        if pack.pack(dest) != image:
            raise ValueError('original binary expert changed')
        paths.append(dest)
        images.append(image)
    if mode == 'spatial':
        cols, rows = decompose.GRIDS[parts]
        tiled = {'format': 'neuronte-tiled-weights', 'version': 1,
                 'first': 0, 'last': 0x10ffff,
                 'columns': [i / cols for i in range(cols + 1)],
                 'rows': [2 * i / rows for i in range(rows + 1)],
                 'nets': docs,
                 'tiles': [{'net': i, 'mask': 0x1fffff, 'base': 0, 'code': 'place'} for i in range(parts)],
                 'training': {'set': 'accent-spatial',
                              'labelled': ' '.join(f'U+{c:04X}' for c in corpus)}}
        new_paths = [output / 'accent-tiled.json']
        new_paths[0].write_text(json.dumps(tiled) + '\n')
        routes = [6] * len(corpus)
    else:
        new_paths = []
        owner = {}
        for i, (source, doc, spec) in enumerate(zip(source_paths, docs, specs)):
            dest = output / source.name
            dest.write_text(json.dumps(doc) + '\n')
            new_paths.append(dest)
            owner.update({c: i + 6 for c in spec['scalars']})
        routes = [owner[c] for c in corpus]
    for path in new_paths:
        images.append(pack.pack(path))
        paths.append(path)
    gate = json.loads((ROOT / 'weights/neuronte-gate-v4.json').read_text())
    # Character inputs are +/-1. Bound the hidden ReLUs and hence all original
    # output magnitudes. A constant below -bound can never win the argmax.
    first, final = gate['layers']['l1'], gate['layers']['out']
    w = np.asarray(first['weight']).reshape(first['rows'], first['cols'])
    hidden_bound = np.maximum(0, np.abs(w).sum(1) + np.asarray(first['bias']))
    v = np.asarray(final['weight']).reshape(final['rows'], final['cols'])
    logit_bound = float((np.abs(v) @ hidden_bound + np.abs(final['bias'])).max())
    disabled = -float(2 ** int(np.ceil(np.log2(max(1, logit_bound)))) * 4)
    extra = len(new_paths)
    gate['nets'] += [pack.scalars(p)[0] for p in new_paths]
    final['rows'] += extra
    final['weight'] += [0.] * (extra * final['cols'])
    final['bias'] += [disabled] * extra
    gate_path = output / 'gate.json'
    gate_path.write_text(json.dumps(gate) + '\n')
    data, ranges = pack._bundle_images(paths, images, gate_path)
    out = output / f'neuronte-accent-next-{mode}{parts}-s{seed}.nrt'
    out.write_bytes(data)
    report = {'file': out.name, 'sha256': decompose.digest(out), 'bytes': len(data),
              'corpus': corpus, 'routes': routes, 'ranges': ranges,
              'mode': mode, 'parts': parts, 'seed': seed, 'width_sum': sum(s['width'] for s in specs),
              'widths': [s['width'] for s in specs],
              'source_models': [{'file': p.name, 'sha256': decompose.digest(p)} for p in source_paths],
              'preserved_member_sha256': [hashlib.sha256(image).hexdigest() for image in images[:6]],
              'original_gate_logit_magnitude_bound': logit_bound, 'disabled_gate_bias': disabled,
              'fallback_policy': 'original six experts and original gate rows retained; append table-only experts'}
    (output / 'package.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('file', 'sha256', 'bytes', 'mode', 'parts', 'seed')}))
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--mode', choices=('spatial', 'repertoire'), required=True)
    p.add_argument('--parts', type=int, choices=(3,) + decompose.COUNTS, required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--width-budget', type=int)
    a = p.parse_args()
    build(a.directory, a.output, a.mode, a.parts, a.seed, a.width_budget)
