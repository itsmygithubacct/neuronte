# Weather colour v1

`neuronte-weather-colour-v1.nrt` draws nine weather symbols in colour, for a status bar. Each symbol is two cells wide, as an emoji is: the left half is asked for by its scalar with half 0, the right half by the same scalar with half 1, through `neuronte_coverage_layers_half` or `neuronte_draw_half`. It is one colour net of width 192 behind a table of the scalars it was trained on, 396,956 bytes. It is a standalone file and **not a default**: nothing loads it unless a program opens it.

| Scalar | Unicode name | Layers |
|---|---|---:|
| U+2600 | black sun with rays | 2 |
| U+2601 | cloud | 1 |
| U+26C5 | sun behind cloud | 3 |
| U+26C8 | thunder cloud and rain | 3 |
| U+1F324 | white sun with small cloud | 3 |
| U+1F326 | white sun behind cloud with rain | 4 |
| U+1F327 | cloud with rain | 2 |
| U+1F328 | cloud with snow | 2 |
| U+1F32B | fog | 2 |

The list is also in `weights/neuronte-weather-colour-v1.symbols.txt`. `neuronte_untrained()` is 0 for these nine scalars and 1 for every other, so a program opens this file as its own handle and asks that first. The half calls themselves do not refuse an untrained scalar.

## The drawings

The nine are drawn by `train/weather.py`, which writes `font/weather.txt` in the syntax of `font/emoji.txt`, with the shape helpers of `train/emoji.py`, in the same 2 x 2 cell square and with the same palette, `font/emoji-palette.txt`. No emoji font, image or raster was read, opened or looked at to make them.

They are made of one sun, one cloud shape and one rain stroke, put together nine ways, to be told apart at 18 x 18 pixels on a dark bar. The sun is a yellow disc with eight orange rays. A cloud is three bumps on a flat base, silver; the thunder cloud is grey, with a yellow bolt and two rain strokes. Rain is blue slanted strokes, snow is five pale dots, fog is four staggered bars in silver and grey. No symbol uses palette entry 0 (the caller's colour) or 1 (clear). At 18 x 18 the ink is 14 to 16 pixels wide and 15 to 17 high, except the plain cloud (16 x 10) and the fog (16 x 12).

Three things were changed in the drawings before any training, each found by a check and not by a net:

- Two symbols had the sun's disc meeting a cloud bump edge to edge (`glyphs.layer_seams`), which leaves a dark line. The sun was moved.
- The fog bars had edges on half pixels at 16 px, where a perfect net would have scored .9842 against the .990 limit below. They were moved by at most .07 of a cell width.
- In U+1F326 the sun's disc ended exactly on the line between the two cells, which left one of the limits below to chance. The sun and cloud were moved by at most .06 of a cell width.

The owner saw the nine on a sheet at 18 x 18 and 24 x 24 before training.

## Recipe

The recipe is emoji-v1's, unchanged, for one net that holds all 18 halves:

```
python3 train/colour.py RAW.json --drawing font/weather.txt --palette font/emoji-palette.txt --wide \
    --form A --layers 6 --head-width 64 --width 192 --seed S --steps 60000 --matmul-precision high
python3 train/colour_calibrate.py RAW.json TARGETS.npz --prepare-targets
python3 train/colour_calibrate.py RAW.json OUT.json --targets TARGETS.npz --steps 10000 --lr .0001 \
    --margin .05 --margin-weight 100 --field-anchor .005 --batch-pixels 128
python3 tools/pack-bundle-members.py weights/neuronte-weather-colour-v1.nrt weights/neuronte-weather-colour-e0-v1.json
```

Both seeds were trained from commit e24a23d on a rented NVIDIA GeForce RTX 3090 with PyTorch 2.6.0 (CUDA 12.4) and NumPy 2.2.2: 283 seconds for the 60,000 steps, both seeds side by side, and 78 seconds for the coverage phase on one CPU thread. There was no tuning by net or seed and no second try.

## Gates

The gates are those emoji-v1 was held to, as its card states them, run by the same `tests/check_emoji.py` on the net's packed file with snapping off. They were written down with their hash before any training, with a check that a perfect net on these drawings meets every one (it scores .9969 at 16 px). Two seeds; both must pass; seed 0 is published. The nets were scored with `tests/check_emoji.py` as it was in 0.1.5 (sha256 `7d44d572e11e6d731b32e663f860137de57fdc38bf6053ec0dc844368f23d366`). In 0.1.6 that file changed in one place, how it writes its cache of the drawings (under another name, then renamed, so two test targets run side by side can share it); no gate and no measurement changed, `make test` scores both seeds again with the file as it is now, and the hash list holds that file.

| Limit | Value | Seed 0 (published) | Seed 1 |
|---|---|---|---|
| Mean IoU at 16 px over the nonempty half layers | at least .990 | 1.0000 | 1.0000 |
| Lost layers at 12, 16, 32 px | 0 | 0 | 0 |
| Zero coverage of a nonempty layer | 0 | 0 | 0 |
| Ink in an unused or empty layer | 0 | 0 | 0 |
| Wrong palette entry | 0 | 0 | 0 |
| Worst mean RGB error, either theme | at most 2 of 255 | 0.61 | 0.59 |
| NumPy float64 cross-check | under 1e-3 | 5.0e-07 | 3.5e-07 |
| C compositing against the layers | within 2 levels | 1 | 1 |
| Packed file made again from its JSON | byte for byte | yes | yes |
| Inventory | 9 scalars, 18 half labels | 9, 18 | 9, 18 |

Not limits, reported: the mean IoU is .9824 at 12 px and .9908 at 32 px for seed 0, and .9745 and .9895 for seed 1. Like emoji-v1, the coverage phase fits 16 px and gives a little at the sizes on either side: a perfect net would score .9885 and .9938 there. The lowest single layer is .8810 at 12 px in seed 0.

## At a status bar's sizes

`tests/check_weather.py` asks the bundle as a bar does: `neuronte_coverage_layers_half(file, scalar, half, cell_w, cell_h, 0, masks, entries)` for both halves, compositing the layers itself, at half cells of 8 x 17, 9 x 18, 10 x 19, 10 x 20, 12 x 24 and the same doubled. At every one of them each half has the drawing's palette entries, ink in every layer the drawing has ink in, and none in any other.

The library snaps a colour glyph's edges to whole pixels in cells narrower than 14 pixels, as it does for emoji-v1. So the picture a bar gets at its small sizes is a little crisper than the drawing and not the same pixels:

| Half cell | Mean difference from the drawing, dark theme, of 255: as a bar gets it | with snapping off |
|---|---:|---:|
| 9 x 18 | 6.00 | 0.84 |
| 10 x 20 | 4.87 | 0.63 |
| 12 x 24 | 3.96 | 0.61 |
| 18 x 36 | 0.43 | 0.43 |
| 20 x 40 | 0.46 | 0.46 |
| 24 x 48 | 0.52 | 0.52 |

The test holds the picture with snapping off to 2 of 255 at these sizes, a limit written before training. The snapped picture is held to 8, a bound set from the 6.0 measured at 9 x 18 to catch a change; it is not a judgement of the picture. A program that wants the drawing's own pixels at small sizes can call `neuronte_set_snap(file, 0)`.

## Not measured

Speed was not measured. The net has the shape of one emoji-v1 expert (width 192, six layers), whose speed is on that card.

## Files

- `weights/neuronte-weather-colour-v1.nrt`: the file, seed 0.
- `weights/neuronte-weather-colour-e0-v1.json` and `.nrt`: its net and the net's own packed file.
- `weights/neuronte-weather-colour-e0-v1.seed1.json` and `.nrt`: seed 1, tested, not published as the file.
- `weights/neuronte-weather-colour-v1.quality.json`: every number above, the gates as declared and the recipe.
- `weights/neuronte-weather-colour-v1.symbols.txt`: the nine scalars.
- `weights/neuronte-weather-colour-v1.sha256`: the hashes `make test` checks first.
- `make pack-weather-colour-v1` makes the packed files again; `make test-weather-colour-v1` runs the gates on both seeds and the bar test.
