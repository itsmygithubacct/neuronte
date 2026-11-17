"""Original flat-colour, two-cell weather symbols; no external artwork.

Run `python3 train/weather.py` to reproduce font/weather.txt, its manifest
and the list weights/neuronte-weather-colour-v1.symbols.txt.

Nine symbols for a status bar, drawn together so they match: one sun, one
cloud shape and one rain stroke, put together nine ways. They are made to
be told apart at 18 x 18 pixels on a dark bar: the sun is a yellow disc
with orange rays, a cloud is silver, a thunder cloud grey, rain is blue
slanted strokes, snow is pale dots, the bolt is yellow, fog is bars.

The syntax, the 2 x 2 cell square, the palette (font/emoji-palette.txt)
and the split into a left and a right half are those of train/emoji.py,
whose shape helpers are used here. No font, image or raster is read.
"""
import json
import math
import unicodedata

from emoji import ROOT, box, line, move, oval, poly, serial

RAY, RAIN = .075, .075
FOG, FOG_R = [(6 * i + 7.5) / 16 for i in range(4)], 1.5 / 16


def sun(x, y, r):
    """[(colour, shapes)]: eight rays, then the disc over them."""
    rays = []
    for i in range(8):
        c, s = math.cos(i * math.pi / 4), math.sin(i * math.pi / 4)
        rays += line((x + 1.36 * r * c, y + 1.36 * r * s), (x + 1.86 * r * c, y + 1.86 * r * s), r=RAY * min(1, r / .44))
    return [('orange', rays), ('yellow', oval(x, y, r))]


def cloud(x, y, s):
    """Three bumps on a flat base; 1.46 s wide and .95 s high, the base at y + .35 s."""
    return (oval(x - .40 * s, y + .05 * s, .30 * s) + oval(x + .02 * s, y - .18 * s, .42 * s)
            + oval(x + .44 * s, y + .03 * s, .32 * s) + box(x - .40 * s, y + .05 * s, .84 * s, .30 * s))


def rain(xs, y, length=.34):
    """Slanted strokes that start at y under each x."""
    return sum((line((x, y), (x - .34 * length, y + length), r=RAIN) for x in xs), [])


def snow(points, r=.105):
    return sum((oval(x, y, r) for x, y in points), [])


def bolt(x, y, s):
    """A bolt whose top edge is at y, about .62 s wide and 1.0 s high."""
    return poly(*[(x + s * u, y + s * v) for u, v in
                  ((.10, 0), (-.30, .52), (-.02, .52), (-.16, 1.0), (.32, .38), (.04, .38), (.24, 0))])


def drawings():
    c = 'silver'
    return {
        0x2600: sun(1, 1, .44),
        0x1F324: sun(.86, .82, .40) + [(c, cloud(1.32, 1.50, .62))],
        0x26C5: sun(.80, .70, .34) + [(c, cloud(1.10, 1.35, .98))],
        0x2601: [(c, cloud(.96, 1.15, 1.20))],
        # Fog: four bars three pixels high at 16 px, their edges on that grid.
        0x1F32B: [(c, line((.42, FOG[0]), (1.74, FOG[0]), r=FOG_R) + line((.20, FOG[2]), (1.42, FOG[2]), r=FOG_R)),
                  ('grey', line((.26, FOG[1]), (1.58, FOG[1]), r=FOG_R) + line((.58, FOG[3]), (1.80, FOG[3]), r=FOG_R))],
        # The disc stays clear of the line between the two cells, so the right half has none of it.
        0x1F326: sun(.64, .64, .30) + [(c, cloud(1.06, 1.02, .92)), ('blue', rain((.72, 1.10, 1.48), 1.48))],
        0x1F327: [(c, cloud(.97, .80, 1.12)), ('blue', rain((.60, 1.02, 1.44), 1.40, .42))],
        0x1F328: [(c, cloud(.97, .80, 1.12)),
                  ('paper', snow(((.52, 1.46), (1.00, 1.46), (1.48, 1.46), (.76, 1.80), (1.24, 1.80))))],
        0x26C8: [('grey', cloud(.97, .78, 1.12)), ('blue', rain((.50, 1.62), 1.40, .42)),
                 ('yellow', bolt(1.02, .98, .92))],
    }


def main():
    out = drawings()
    lines = ['# Original Neuronte weather symbols. Generated reproducibly by train/weather.py.',
             '# 2 x 2 cell widths; same syntax as emoji.txt, x and y design units 0..20.',
             '# No external artwork, font or raster used. The palette is font/emoji-palette.txt.']
    manifest = []
    for cp, layers in sorted(out.items()):
        name = unicodedata.name(chr(cp))
        for _, shapes in layers:
            for sh in move(shapes):
                pts = sh[1] if sh[0] == 'poly' else [sh[1:3], sh[3:5]]
                if not all(.03 <= x <= 1.97 and .03 <= y <= 1.97 for x, y in pts):
                    raise ValueError(f'U+{cp:04X} leaves the square')
        lines.append(f'# U+{cp:04X} {name}')
        lines.append(f'U+{cp:04X} ' + ' || '.join('{' + c + '} ' + serial(s) for c, s in layers))
        manifest.append({'scalar': f'U+{cp:04X}', 'name': name, 'category': 'weather', 'layers': len(layers)})
    (ROOT / 'font/weather.txt').write_text('\n'.join(lines) + '\n')
    (ROOT / 'font/weather-manifest.json').write_text(
        json.dumps({'version': 1, 'cell_columns': 2, 'glyphs': manifest}, indent=2) + '\n')
    (ROOT / 'weights/neuronte-weather-colour-v1.symbols.txt').write_text(
        '# The symbols neuronte-weather-colour-v1.nrt was trained on, one a line. Each is two cells:\n'
        '# the left half is asked for by the scalar with half 0 and the right half with half 1.\n'
        '# Every other scalar is untrained in that file (tests/check_weather.py).\n'
        + ''.join(f"{g['scalar']}  # {g['name']}\n" for g in manifest))
    print(f'{len(out)} weather symbols, max {max(map(len, out.values()))} layers')


if __name__ == '__main__':
    main()
