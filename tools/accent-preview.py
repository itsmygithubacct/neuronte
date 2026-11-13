"""Render teacher / baseline / candidate triplets for every accent scalar."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--teacher', type=Path, required=True)
p.add_argument('--baseline', type=Path, required=True)
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--size', default='16x32')
p.add_argument('--script', choices=('all', 'latin', 'greek', 'russian'), default='all')
a = p.parse_args()
w, h = map(int, a.size.split('x'))
meta = json.loads((a.teacher / 'teacher.json').read_text())
scalars = meta['identity']['scalars']
arrays = [np.load(a.teacher / meta['targets'][a.size]['file'], allow_pickle=False),
          np.load(a.baseline / f'coverage-{a.size}.npy', allow_pickle=False),
          np.load(a.candidate / f'coverage-{a.size}.npy', allow_pickle=False)]
if any(x.shape != (len(scalars), h, w) or not np.isfinite(x).all() for x in arrays):
    raise ValueError('coverage arrays do not match the teacher inventory')
scale = 2 if w <= 16 else 1
cw, ch = w * scale, h * scale
columns = 8
indices = [i for i, c in enumerate(scalars) if a.script == 'all' or
           a.script == ('latin' if c < 0x370 else 'greek' if c < 0x400 else 'russian')]
slot_w, slot_h = 3 * (cw + 3) + 8, ch + 21
sheet = Image.new('RGB', (columns * slot_w, ((len(indices) + columns - 1) // columns) * slot_h + 30), 'white')
draw = ImageDraw.Draw(sheet)
draw.text((6, 6), 'Every cell: teacher | baseline | candidate. Unicode scalar labels; original scalar order.', fill='black')
for position, i in enumerate(indices):
    scalar = scalars[i]
    x, y = (position % columns) * slot_w, (position // columns) * slot_h + 30
    draw.text((x + 3, y), f'U+{scalar:04X}', fill='black')
    for j, array in enumerate(arrays):
        pixels = np.round((1 - np.clip(array[i], 0, 1)) * 255).astype(np.uint8)
        tile = Image.fromarray(pixels).resize((cw, ch), Image.Resampling.NEAREST).convert('RGB')
        sheet.paste(tile, (x + 3 + j * (cw + 3), y + 16))
a.out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(a.out)
