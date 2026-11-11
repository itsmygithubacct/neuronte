# Kilix flame drawing

The in-house Start-button flame is drawn as one named colour glyph with
three flat layers, back to front: red outer flame, yellow middle, white
core. [flame.txt](flame.txt) is the drawing source for form A, one filled
polygon per layer, in the syntax of `icons.txt`. No Unicode code point is
assigned to the mark; its net is trained and drawn at U+100000, the first
scalar of Supplementary Private Use Area-B, which no Nerd Font uses. It
stays separate from the widget icon batch.

The teacher is `_flame` in `kilix-desktops/kilix-95/icons.py`. The three
polygons retain its vertices and its red, yellow and white fills. The
teacher's dark-red outline is omitted to keep exactly the three requested
flat layers. Lower polygons remain filled under the upper ones. There are
no cutouts or strokes.

The teacher uses a 16 by 16 grid, with polygon vertices centred on logical
pixels. A vertex `(x, y)` becomes `(0.625 * (x + 0.5), 5 + 0.625 * (y + 0.5))`
on Neuronte's 10 by 20 design grid. The drawing occupies the middle square,
`[0, 5, 10, 15]`. `strokes.parse_layers()` reads it as the shapes used by
`glyphs.signed_distance()` and `glyphs.field()`.

The same polygons are sampled independently at 16 pixels for Start and at
32 pixels for desktop use. These are smooth polygon targets; the 32-pixel
image is not an enlargement of the 16-pixel bitmap. To draw the mark from
its net, evaluate an `s` by `2*s` cell and take rows `s/2` through
`3*s/2 - 1`. Evaluating the whole cell at `s` by `s` would compress the mark
vertically.

The [dedicated palette](flame-palette.txt) uses the teacher's fixed colours
in both themes. Entries 0 and 1 keep the usual foreground and clear
meanings; the drawing uses entries 2, 3 and 4. It does not change the
existing icon palette.

| Layer | Palette entry | Colour |
|---|---:|---|
| Outer flame | 2 red | `#FF0000` |
| Middle | 3 yellow | `#FFFF00` |
| Core | 4 white | `#FFFFFF` |

The [preview sheet](../previews/flame-sheet.png) shows both sizes on light
and dark backgrounds, with native pixels, nearest-neighbour enlargements,
and the three layers separately. Transparent target renders are
[flame-16.png](../previews/flame-16.png) and
[flame-32.png](../previews/flame-32.png).

Regenerate the previews from the repository root with numpy and Pillow:

```sh
python3 tools/flame-preview.py
```

The script measures the polygons with the existing signed-distance code,
takes 8 by 8 samples per pixel, and composites coverage back to front using
form A's rule. It checks the existing layer-seam criterion, visible red,
yellow and white pixels at both sizes, unchanged outer alpha when the
inner layers are added, transparent exterior pixels, and identical colours
in both themes. Sheet labels use only the project's `ui-10.txt` pixel face.

Train its net with the colour trainer, three layers, on this drawing and
palette, with the printable ASCII and U+FFFD as blanks so that any other
scalar draws nothing:

```sh
python3 train/colour.py OUT.json --form A --layers 3 --drawing font/flame.txt \
    --palette font/flame-palette.txt --blank U+0020..U+007E,U+FFFD
```

These files are the original drawing and its previews. No installed
application PNG was replaced, and no desktop code was changed. MIT
licence; see the repository's LICENSE.
