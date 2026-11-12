"""Validate both trained pointer seeds through C and NumPy; render review sheets.
Run after make build/libneuronte.so and packing both JSON files.
"""
import ctypes
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'train'), str(ROOT / 'tests')]
import glyphs
import pack
import strokes
from check_icon_quality import sample_points, counts, composite

SCALAR = 0x100001


def numpy_masks(doc, w, ss):
    """Independent float64 inference from JSON; no packed data or C calls."""
    def linear(x, layer):
        weight = np.asarray(layer['weight'], dtype=np.float32).astype(float)
        bias = np.asarray(layer['bias'], dtype=np.float32).astype(float)
        return x @ weight.reshape(layer['rows'], layer['cols']).T + bias
    masks = [int(m, 16) for m in doc['shape']['parity_masks']]
    bits = [(SCALAR >> i) & 1 for i in range(21)]
    bits += [(SCALAR & m).bit_count() & 1 for m in masks]
    code = 2*np.array(bits)-1
    yy, xx = np.meshgrid((np.arange(2*w*ss)+.5)/(w*ss),
                         (np.arange(w*ss)+.5)/(w*ss), indexing='ij')
    x, y = xx.ravel(), yy.ravel()
    features = [2*x-1, y-1]
    for octave in range(6):
        f = 2*np.pi*2**octave
        features += [np.sin(f*x),np.sin(f*y),np.cos(f*x),np.cos(f*y)]
    inp = np.concatenate([np.stack(features,1), np.broadcast_to(code,(x.size,64))],1)
    for key in ('l1','l2','l3'):
        inp = np.maximum(linear(inp,doc['layers'][key]),0)
    field = linear(inp,doc['layers']['out'])
    tau = float(np.float32(doc['shape']['tau']))
    cov = np.clip(.5+field*tau*w*ss,0,1).reshape(2*w,ss,w,ss,2).mean((1,3))
    logits = linear(np.maximum(linear(code,doc['head']['h1']),0),doc['head']['out'])
    entries = [sum(int(logits[k*5+b]>0)<<b for b in range(5)) for k in range(2)]
    return np.moveaxis(cov,-1,0), entries


def components(mask):
    """Count eight-connected visible components, detecting detached specks."""
    remaining = set(map(tuple, np.argwhere(mask)))
    total = 0
    while remaining:
        total += 1
        stack = [remaining.pop()]
        while stack:
            y, x = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    point = (y+dy, x+dx)
                    if point in remaining:
                        remaining.remove(point)
                        stack.append(point)
    return total


def main():
    pal = strokes.palette(ROOT / 'font/pointer-palette.txt')
    layers = strokes.parse_layers(ROOT / 'font/pointer.txt', pal)[chr(SCALAR)]
    lib = ctypes.CDLL(str(ROOT / 'build/libneuronte.so'))
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.neuronte_close.argtypes = [ctypes.c_void_p]
    lib.neuronte_coverage_layers.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
    report = {'scalar': 'U+100001', 'seeds': {}, 'passed': True}
    sheet = Image.new('RGB', (960, 660), '#d8dce0')
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 8), 'NW pointer: analytic source / C seed 0 / C seed 1. Native + enlarged. Full cells.', fill='black')
    for wi, w in enumerate((16, 32)):
        points = sample_points(w)
        target = np.stack([(glyphs.signed_distance(sh, points, glyphs.PEN) > 0)
            .reshape(2*w, 8, w, 8).mean((1, 3)) for _, sh in layers])
        variants = [('source', target)]
        for seed in (0, 1):
            stem = 'neuronte-pointer-v0' + ('.seed1' if seed else '')
            jp, bp = ROOT / f'weights/{stem}.json', ROOT / f'weights/{stem}.nrt'
            doc = json.loads(jp.read_text())
            pack.check_sources(doc, str(jp))
            assert bp.read_bytes() == pack.pack(str(jp))
            handle = ctypes.c_void_p()
            assert lib.neuronte_open_file(str(bp).encode(), ctypes.byref(handle)) == 0
            cov = np.zeros((2, 2*w, w), np.float32)
            entries = (ctypes.c_uint8 * 2)()
            ss = 2 if w == 16 else 1
            assert lib.neuronte_coverage_layers(handle, SCALAR, w, 2*w, ss, cov.ctypes.data, entries) == 0
            lib.neuronte_close(handle)
            ref, ent = numpy_masks(doc, w, ss)
            delta = float(np.max(np.abs(ref-cov)))
            layer_scores = [counts(t > .5, c > .5) for t, c in zip(target, cov)]
            alpha = 1 - (1-cov[0])*(1-cov[1])
            edge = float(max(alpha[0].max(), alpha[-1].max(), alpha[:,0].max(), alpha[:,-1].max()))
            # Tip and hotspot use the first row of visible silhouette, tolerance one pixel.
            ty, tx = np.argwhere(target[0] > .1)[0]
            py, px = np.argwhere(cov[0] > .1)[0]
            tip_error = int(max(abs(int(tx)-int(px)), abs(int(ty)-int(py))))
            connected = components(alpha > .1)
            contrast = {theme: int((np.abs(composite(cov, entries, pal, theme) -
                np.array((17,21,28) if theme == 'dark' else (250,250,247))/255)
                .max(-1) > .5).sum()) for theme in ('dark','light')}
            errors = {theme: float(np.abs(composite(cov, entries, pal, theme)-
                composite(target, [2,3], pal, theme)).mean()*255) for theme in ('dark','light')}
            passed = (list(entries) == ent == [2,3] and delta < 1e-3
                and min(x['iou'] for x in layer_scores) >= .97
                and edge == 0 and tip_error <= 1 and connected == 1 and min(contrast.values()) >= 15
                and max(errors.values()) < 4)
            report['passed'] &= passed
            report['seeds'].setdefault(str(seed), {})[str(w)] = dict(layers=layer_scores,
                numpy_max_error=delta, border_alpha_max=edge, tip_error_pixels=tip_error,
                first_visible_xy=[int(px),int(py)], visible_components=connected, contrast_pixels=contrast,
                composite_mean_error_255=errors, passed=passed)
            variants.append((f'C seed {seed}', cov))
        for vi, (name, cov) in enumerate(variants):
            x = vi*320; y = 36+wi*310
            draw.text((x+10,y), f'{name} {w}x{2*w}', fill='black')
            for ti, theme in enumerate(('dark','light')):
                rgb = np.rint(composite(cov, [2,3], pal, theme)*255).clip(0,255).astype('uint8')
                im = Image.fromarray(rgb)
                sheet.paste(im,(x+10+ti*154,y+24))
                sheet.paste(im.resize((112,224),Image.Resampling.NEAREST),(x+42+ti*154,y+24))
                if vi:
                    im.save(ROOT / f'previews/pointer-seed{vi-1}-{w}-{theme}.png')
    sheet.save(ROOT / 'previews/pointer-sheet.png')
    paths = ['font/pointer.txt','font/pointer-palette.txt','tools/pointer-preview.py']
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'weights').glob('neuronte-pointer*.json'))
              if not p.name.endswith(('validation.json', 'manifest.json'))]
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'weights').glob('neuronte-pointer*.nrt'))]
    report['sha256'] = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    (ROOT/'weights/neuronte-pointer-v0.validation.json').write_text(json.dumps(report,indent=2)+'\n')
    if report['passed']:
        manifest = {
            'format': 'neuronte-pointer-manifest', 'version': 1,
            'scalar': SCALAR, 'model': 'weights/neuronte-pointer-v0.nrt',
            'model_sha256': report['sha256']['weights/neuronte-pointer-v0.nrt'],
            'source_sha256': {p: report['sha256'][p] for p in
                ('font/pointer.txt', 'font/pointer-palette.txt')},
            'palette_entries': [2, 3], 'palette_rgb': [[0,0,0], [255,255,255]],
            'sizes': [
                {'width': 16, 'height': 32, 'supersampling': 2, 'hotspot': [1,1]},
                {'width': 32, 'height': 64, 'supersampling': 1, 'hotspot': [3,3]}],
            'crop': None, 'other_scalars': 'unsupported',
            'validation': 'weights/neuronte-pointer-v0.validation.json',
            'preview': 'previews/pointer-sheet.png',
        }
        (ROOT/'weights/neuronte-pointer-v0.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
