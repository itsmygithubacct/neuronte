# Split-v5 with the draw-v3 box-drawing experts

`neuronte-split-v5-draw3.nrt` is a new, explicitly selected bundle. It is
split-v5 with its one box-drawing expert (draw-v2, width 192, 91,777
parameters) replaced by six narrower experts, draw-v3, each width 64
(14,209 parameters, 85,254 in all). Split-v5 itself is unchanged; consumers
that bind its SHA256 keep it.

| Member | Bundle index | Scalars | Glyphs |
|---|---:|---|---:|
| `neuronte-draw-v3-p0.json` | 1 | light and heavy lines and junctions U+2500..U+2503, U+250C..U+2529 | 34 |
| `neuronte-draw-v3-p1.json` | 6 | light and heavy junctions U+252A..U+254B | 34 |
| `neuronte-draw-v3-p2.json` | 7 | arcs, diagonals and half lines U+256D..U+257F | 19 |
| `neuronte-draw-v3-p3.json` | 8 | dashed lines U+2504..U+250B, U+254C..U+254F | 12 |
| `neuronte-draw-v3-p4.json` | 9 | double lines U+2550..U+256C | 29 |
| `neuronte-draw-v3-p5.json` | 10 | shades U+2591..U+2593 | 3 |

The table routes each labelled scalar to its member, so a glyph runs only
one width-64 net instead of the width-192 one. ASCII, symbol, accent, pixel
and Braille keep indices 0, 2, 3, 4 and 5 with byte-identical images; the
first draw member takes index 1. `neuronte-gate-v4-draw3.json` is gate-v4
with four outputs added whose weights are zero and bias -1e30, so they are
never selected: every gate decision is gate-v4's, and a scalar gate-v4 sent
to the draw expert would go to index 1 (gate-v4 sends none). All 1,114,112
code points route to the same expert family as in split-v5.

Training: `train/draw_split.py --design custom` with the six groups above,
width 64, 40,000 Adam/cosine steps, the original losses, teacher and
sampling, seeds 0 and 1, eager CUDA float32 with TF32 off. Seed 1 ships;
seed 0 also passes the gates below. The teacher is the boxshade target of
`train/glyphs.py`, identical to the one draw-v2 was trained on.

Grouping by glyph structure is what makes the narrow nets work. With the
same per-net widths, contiguous scalar groups (2 x 96, 4 x 48, 8 x 24,
16 x 12) and spatial tiles (2, 4, 8 tiles) all failed the gates on at least
one of two seeds. Shades, dashes and double lines, mixed with plain lines,
spoiled the groups they were in; tiles cut the lines along their centres.

Quality against the teacher through `neuronte_coverage()`, automatic
sampling (`tools/draw-quality.py`):

| Cell | Model | Exact | Firm wrong px | Nearest | MAE | p99 | Seam | Thickness max px |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 8x16 | draw-v2 | 102 | 0 | 131 | .007266 | .0508 | .109 | 0.73 |
| 8x16 | draw-v3 | 107 | 0 | 131 | .007106 | .0498 | .107 | 0.76 |
| 16x32 | draw-v2 | 129 | 0 | 131 | .005040 | .0536 | .075 | 0.32 |
| 16x32 | draw-v3 | 129 | 0 | 131 | .004861 | .0515 | .081 | 0.26 |
| 48x96 | draw-v2 | 111 | 5 | 131 | .001223 | .0372 | .195 | 1.88 |
| 48x96 | draw-v3 | 106 | 5 | 131 | .000971 | .0301 | .208 | 1.72 |

Firm pixels are those whose teacher coverage is at least 0.1 from one half.
Seam is the largest step between the edge rows or columns of two glyphs whose
arms of the same weight meet across a cell edge. No firm error falls on a
cell edge at any of these sizes. At 28 odd, small, anisotropic and 23/24/25
pixel-wide cells, draw-v3 has a lower MAE than draw-v2 at 26 of them; at
cells 24 pixels and wider (one sample per pixel) it has more firm pixels
missing ink on antialiased edges than the shipped seed (300 against 203 in
total), within the range of draw-v2's own architecture retrained on two
seeds (231 and 274). Cold and warm cached draws, clipped draws and UTF-8 box
text match coverage exactly (`tools/draw-api-check.py`).

Reproduce the package from the member weights:

```sh
python3 tools/replace-bundle-expert.py weights/neuronte-split-v5-draw3.nrt \
  --gate weights/neuronte-gate-v4.json --gate-out weights/neuronte-gate-v4-draw3.json \
  --replace 1 --nets weights/neuronte-ascii-v0.json weights/neuronte-draw-v2.json \
  weights/neuronte-symbol-v0.json weights/neuronte-accent-v2.json \
  weights/neuronte-pixel-v1.json weights/neuronte-braille-v0.json \
  --members weights/neuronte-draw-v3-p[0-5].json --reference weights/neuronte-split-v5.nrt
./build/test_api weights/neuronte-split-v5-draw3.nrt --full --accent --pixel
python3 tools/draw-api-check.py weights/neuronte-split-v5-draw3.nrt weights/neuronte-split-v5.nrt
```

The members train with `train/draw_split.py train DIR --design custom
--groups-file GROUPS.json --tag m64l --width 64 --steps 40000 --seeds 0,1`
after `train/draw_split.py prepare DIR`; GROUPS.json lists the six scalar
groups in the table above, in member order.
