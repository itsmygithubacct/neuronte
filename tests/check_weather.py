"""The weather colour file: exactly its nine symbols, untrained elsewhere, pixels against the drawing.

usage: check_weather.py LIB BUNDLE NET.json LIST MANIFEST [--out REPORT]

BUNDLE is weights/neuronte-weather-colour-v1.nrt: one colour net behind a
table of the scalars it was trained on, so that neuronte_untrained() is 0
for the nine symbols and 1 for every other scalar. A symbol is two cells:
the left half is asked for by its scalar and the right half by the same
scalar with half 1, through neuronte_coverage_layers_half.

The publication gates (12, 16 and 32 px half cells, snapping off) are run
by tests/check_emoji.py on the net's own packed file. This test checks
what that one does not:

- the bundle and the net's packed file are made again byte for byte from
  the net's JSON, and the drawing the net records is the one in the tree;
- the list file, the manifest and the net name the same nine scalars, and
  the net holds both halves of each and nothing else;
- of all 1,114,112 scalars only those nine are reported trained, and the
  file's dark palette is not empty (a status bar refuses a colour file
  without a table of its trained characters or without a palette);
- through the bundle, by the call a status bar makes,
  neuronte_coverage_layers_half(file, scalar, half, cell_w, cell_h, 0,
  masks, entries) for half 0 and half 1, at the half cells it asks for and
  with the file's own snapping: every half has the drawing's palette
  entries; no inked layer has entry 0 (the caller's colour, which a bar
  cannot give a colour picture) or entry 1 (clear); there is ink in each
  layer the drawing has ink in and none in a layer it leaves empty;
- where the cell is twice as high as wide, the layers composited back to
  front make a picture within PICTURE levels of the drawing's on average
  in both themes when snapping is off. In cells narrower than 14 pixels
  the file snaps edges to whole pixels, which moves them by up to half a
  pixel from the drawing's: there the picture as a bar gets it stays
  within SNAPPED levels, a bound set from what was measured (6.0 at
  9 x 18), to catch a change, not to judge the picture.
"""
import argparse
import ctypes as ct
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'train'))
import glyphs
import pack
import strokes
from colour_sources import drawing_at
from check_icon_quality import composite, interpolate, sample_points, THEMES

NINE = (0x2600, 0x2601, 0x26C5, 0x26C8, 0x1F324, 0x1F326, 0x1F327, 0x1F328, 0x1F32B)
RIGHT = 0x110000
# Half cells (width, height): the bar's own, and the same doubled.
CELLS = ((8, 17), (9, 18), (10, 19), (10, 20), (12, 24), (16, 34), (18, 36), (20, 38), (20, 40), (24, 48))
# The greatest mean difference from the drawing's picture, of 255, in either theme, over the 18 halves.
PICTURE = 2.0
SNAPPED = 8.0


def read_list(path):
    out = []
    for line in Path(path).read_text().splitlines():
        line = line.split('#')[0].strip()
        if line:
            assert line.startswith('U+'), f'{path}: {line!r} is not U+XXXX'
            out.append(int(line.split()[0][2:], 16))
    return out


def bind(lib_path, bundle):
    lib = ct.CDLL(str(Path(lib_path).resolve()))
    ptr, I, U = ct.c_void_p, ct.c_int, ct.c_uint32
    lib.neuronte_open_file.argtypes = [ct.c_char_p, ct.POINTER(ptr)]
    lib.neuronte_close.argtypes = [ptr]
    lib.neuronte_layers.argtypes = [ptr]
    lib.neuronte_untrained.argtypes = [ptr, U]
    lib.neuronte_route_half.argtypes = [ptr, U, I]
    lib.neuronte_coverage_layers_half.argtypes = [ptr, U, I, I, I, I, ptr, ptr]
    lib.neuronte_palette.argtypes = [ptr, I, ptr]
    lib.neuronte_set_snap.argtypes = [ptr, I]
    h = ptr()
    assert lib.neuronte_open_file(str(bundle).encode(), ct.byref(h)) == 0, 'the library does not open the bundle'
    return lib, h


def main():
    p = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    for name in ('lib', 'bundle', 'net', 'list', 'manifest'):
        p.add_argument(name)
    p.add_argument('--out')
    a = p.parse_args()

    # The files are made again from the JSON, and the JSON is bound to the drawing in the tree.
    d = json.loads(Path(a.net).read_text())
    pack.check_sources(d, a.net)
    t = d['training']
    assert (t['drawing'], t['palette'], t.get('cell_columns')) == ('font/weather.txt', 'font/emoji-palette.txt', 2)
    image = pack.pack(a.net)
    assert Path(a.net).with_suffix('.nrt').read_bytes() == image, "the net's packed file is not made from its JSON"
    assert Path(a.bundle).read_bytes() == pack._bundle_images([a.net], [image])[0], 'the bundle is not made from its net'

    # One inventory, four ways.
    listed = read_list(a.list)
    manifest = json.loads(Path(a.manifest).read_text())
    assert manifest['version'] == 1 and manifest['cell_columns'] == 2
    labels = pack.labelled_scalars(d, a.net)
    pal = strokes.palette(str(Path(pack.ROOT) / t['palette']))
    source = strokes.parse_layers(str(Path(pack.ROOT) / t['drawing']), pal)
    assert sorted(listed) == sorted(NINE) and len(listed) == 9, 'the list file does not name the nine symbols'
    assert sorted(int(g['scalar'][2:], 16) for g in manifest['glyphs']) == sorted(NINE), 'the manifest differs'
    assert sorted(ord(c) for c in source) == sorted(NINE), 'the drawing file differs'
    assert sorted(labels) == sorted(NINE + tuple(RIGHT + s for s in NINE)), 'the net was not trained on exactly the nine'

    lib, h = bind(a.lib, a.bundle)
    k = lib.neuronte_layers(h)
    assert k == d['shape']['glyph_layers'] == 6
    trained = [s for s in range(0x110000) if lib.neuronte_untrained(h, s) == 0]
    assert trained == sorted(NINE), f'{len(trained)} scalars are reported trained, not the nine'
    assert lib.neuronte_untrained(h, 0x10FFFD) == 1
    for s in NINE:
        assert lib.neuronte_route_half(h, s, 0) == 0 and lib.neuronte_route_half(h, s, 1) == 0
    rgb = (ct.c_uint8 * 96)()
    assert lib.neuronte_palette(h, 0, rgb) == 0 and any(rgb), 'the file has no dark palette'
    for name, (entry, dark, _) in pal.items():
        if entry >= 2:
            assert tuple(rgb[3 * entry:3 * entry + 3]) == tuple(dark), f'palette entry {name} differs'

    # Pixels, as a bar asks for them: the file's own snapping and the library's own sample count.
    drawings = pack.colour_drawings(d)
    fields = {s: [glyphs.field(sh, t['grid'], t['pen_radius'], d['shape']['tau']).astype(np.float16).astype(np.float32)
                  for _, sh in drawing_at(drawings, s)] for s in labels}
    report = {}
    for cw, ch in CELLS:
        square = ch == 2 * cw
        points = sample_points(cw) if square else None
        row = {'halves': 0, 'wrong_entries': 0, 'entry_0_or_1_inked': 0, 'ink_in_unused': 0, 'empty_layers': 0, 'ink_in_empty': 0,
               'layers_without_ink': 0,
               **({name + suffix: 0.0 for name in THEMES for suffix in ('', '_snap_off')} if square else {})}
        for s in labels:
            scalar, half = (s - RIGHT, 1) if s >= RIGHT else (s, 0)
            layers = drawing_at(drawings, s)
            entries = [pal[layers[i][0]][0] if i < len(layers) else 0 for i in range(k)]
            cov = np.zeros((k, ch, cw), np.float32)
            ent = (ct.c_uint8 * k)()
            # 0 samples: the library chooses, as it does for a bar.
            assert lib.neuronte_coverage_layers_half(h, scalar, half, cw, ch, 0, cov.ctypes.data, ent) == 0
            row['halves'] += 1
            row['wrong_entries'] += sum(x != y for x, y in zip(ent, entries))
            row['entry_0_or_1_inked'] += sum(int(e < 2 and bool((c > 0).any())) for e, c in zip(ent, cov))
            row['ink_in_unused'] += int((cov[len(layers):] > 0).any(axis=(1, 2)).sum())
            for i, f in enumerate(fields[s]):
                if f.max() <= 0:          # this half of the symbol has nothing in this layer
                    row['empty_layers'] += 1
                    row['ink_in_empty'] += int((cov[i] > 0).any())
                else:
                    row['layers_without_ink'] += int(not (cov[i] > .5).any())
            if square:
                target = np.zeros((k, ch, cw), np.float32)
                for i, f in enumerate(fields[s]):
                    target[i] = (interpolate(f, points, t['grid']) > 0).reshape(ch, 8, cw, 8).mean((1, 3))
                plain = np.zeros((k, ch, cw), np.float32)
                assert lib.neuronte_set_snap(h, 0) == 0
                assert lib.neuronte_coverage_layers_half(h, scalar, half, cw, ch, 0, plain.ctypes.data, ent) == 0
                assert lib.neuronte_set_snap(h, -1) == 0
                for theme in THEMES:
                    want = composite(target, entries, pal, theme)
                    row[theme] += float(np.abs(composite(cov, list(ent), pal, theme) - want).mean() * 255) / len(labels)
                    row[theme + '_snap_off'] += float(np.abs(composite(plain, list(ent), pal, theme) - want).mean()
                                                      * 255) / len(labels)
        report[f'{cw}x{ch}'] = row
        assert row['wrong_entries'] == row['entry_0_or_1_inked'] == row['ink_in_unused'] == row['ink_in_empty'] \
            == row['layers_without_ink'] == 0, \
            f'{cw}x{ch}: {row}'
        if square:
            assert max(row[theme + '_snap_off'] for theme in THEMES) <= PICTURE, f'{cw}x{ch}: {row}'
            assert max(row[theme] for theme in THEMES) <= (SNAPPED if cw < 14 else PICTURE), f'{cw}x{ch}: {row}'
    lib.neuronte_close(h)
    out = {'passed': True, 'trained_scalars': len(trained), 'half_labels': len(labels), 'picture_limit': PICTURE, 'snapped_limit': SNAPPED,
           'cells': report}
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'passed': True, 'trained_scalars': len(trained), 'half_labels': len(labels),
                      'worst_picture_snap_off': max(r['dark_snap_off'] for r in report.values() if 'dark' in r),
                      'worst_picture_as_drawn': max(r['dark'] for r in report.values() if 'dark' in r)}))


if __name__ == '__main__':
    main()
