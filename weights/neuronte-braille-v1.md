# RC9 Braille expert

`neuronte-braille-v1.nrt` draws the 256 Braille patterns, U+2800..U+28FF. It is a
version 6 tiled net: the cell is cut on Braille's own lattice into 2 columns by
4 rows of tiles, one dot to a tile, and one net draws every tile.
`neuronte-split-v6.nrt` is split-v5 with its Braille member, `neuronte-braille-v0`
(one net 48 wide, 9,121 parameters), replaced by this file. The other five
experts, the gate and the ranges are byte for byte those of split-v5
(`tests/check_braille_v1.py`). The video player's full mode draws with split-v6;
its learned helpers stay bound to split-v5.

## How it draws

The teacher puts every dot at the centre of its tile (x = 0.25 + 0.5c,
y = 0.25 + 0.5r of the 1 x 2 design cell), so a tile holds a dot or nothing.
One net 6 wide (637 parameters, seed 4) was trained on tile (0, 0) alone, to
draw that dot or nothing. Each of the eight tile records extracts its own
dot bit from scalar - U+2800 and gives it to the net as its code, so the
same net draws all eight dots. The runtime gives every full-glyph sample
to the tile it falls in, moves it into that tile's own frame and scales the
distance-to-coverage slope by the tile's width, so every cell size works,
including those whose pixels straddle a tile edge. A sample on an edge
belongs to the tile that starts there. Tiles that use the same net, code
and local coordinates are evaluated once in a call.

## Selection

The rules were fixed before any candidate was scored. Each recipe was
trained with several seeds, and every seed had to pass:

- G1: all 256 patterns binary-exact (coverage above one half exactly where
  the teacher is) at 8 x 16, 16 x 32 and 48 x 96;
- G2: at those sizes, mean absolute coverage error at most the original's
  + 0.0015, and 99th percentile at most 0.06;
- G3: at 26 other sizes (1 x 2 to 64 x 128, odd sizes, sizes around the
  sampling change at width 24, other aspect ratios), mean error at most
  max(1.5 x original, original + 0.0015), and no pixel the teacher decides
  firmly (|teacher - 1/2| > 0.1) drawn on the wrong side where the original
  drew it right.

A recipe ships its seed with the lowest mean error over the three sizes.
Among eligible recipes the fastest wins: the lowest geometric mean of the
median uncached `neuronte_coverage()` time per glyph inside a split bundle,
over cells 8x16, 16x32, 25x49, 48x96 and three hosts: an Intel i7-10700F and an i7-6820HQ
(x86), and one Cortex-A72 core of an RK3399 board (ARM). It must be no
slower than split-v5 at any cell on any host, and candidates within 5% of
the fastest tie, broken by the lower mean error.

| Recipe | Seeds passing | Ships | Mean error, 3 sizes | Geomean µs/glyph |
|---|---:|---|---:|---:|
| q12 | 2 / 2 | q12-s1 | 0.001395 | 273.9 |
| dots6 | 1 / 2 | not eligible | - | - |
| g12w4 | 0 / 2 | not eligible | - | - |
| shared6 | 5 / 5 | shared6-s4 | 0.001401 | 62.9 |
| shared8 | 5 / 5 | shared8-s1 | 0.001426 | 73.5 |
| shared12 | 5 / 5 | shared12-s4 | 0.001441 | 84.9 |
| shared16 | 5 / 5 | shared16-s2 | 0.001440 | 101.2 |
| dots8 | 1 / 2 | not eligible | - | - |

split-v5 measures 1035.6 µs/glyph on the same scale. Fastest: `split-shared6-s4`;
within 5%: `split-shared6-s4`. Selected: **`split-shared6-s4`**.

## Quality

Against the teacher, with automatic samples (2 per axis below width 24):

| Size | Exact, v0 / v1 | Mean error, v0 | Mean error, v1 | p99, v0 | p99, v1 |
|---|---|---:|---:|---:|---:|
| 8x16 | 256 / 256 | 0.001792 | 0.001391 | 0.0146 | 0.0122 |
| 16x32 | 256 / 256 | 0.001967 | 0.001813 | 0.0278 | 0.0310 |
| 48x96 | 256 / 256 | 0.000342 | 0.001001 | 0.0156 | 0.0363 |

This is not an across-the-board improvement in antialiasing. Mean error is
higher than the original's at 48x96, inside the G2 budget; the
binary shape is exact at all three sizes either way.

At the 26 geometry sizes (exact patterns, mean error):

| Size | v0 | v1 |
|---|---|---|
| 1x2 | 121, 0.32824 | 121, 0.28861 |
| 2x4 | 256, 0.02280 | 256, 0.01408 |
| 3x6 | 256, 0.00769 | 256, 0.00658 |
| 4x8 | 256, 0.02160 | 256, 0.02182 |
| 5x10 | 256, 0.00795 | 256, 0.00728 |
| 6x12 | 256, 0.00572 | 256, 0.00519 |
| 7x14 | 256, 0.00164 | 256, 0.00249 |
| 7x13 | 16, 0.00320 | 16, 0.00303 |
| 9x17 | 256, 0.00396 | 256, 0.00424 |
| 9x19 | 256, 0.00275 | 256, 0.00314 |
| 10x21 | 256, 0.00255 | 256, 0.00251 |
| 11x23 | 256, 0.00239 | 256, 0.00300 |
| 13x27 | 256, 0.00155 | 64, 0.00176 |
| 15x31 | 256, 0.00161 | 256, 0.00162 |
| 17x35 | 1, 0.00083 | 1, 0.00121 |
| 23x46 | 256, 0.00082 | 256, 0.00093 |
| 24x48 | 256, 0.00239 | 256, 0.00272 |
| 25x50 | 256, 0.00122 | 256, 0.00155 |
| 23x47 | 16, 0.00090 | 16, 0.00096 |
| 25x49 | 3, 0.00118 | 8, 0.00163 |
| 16x16 | 256, 0.00618 | 256, 0.00706 |
| 16x48 | 1, 0.00080 | 1, 0.00099 |
| 32x16 | 256, 0.02112 | 256, 0.02013 |
| 12x40 | 256, 0.00226 | 256, 0.00286 |
| 33x61 | 16, 0.00090 | 128, 0.00133 |
| 64x128 | 256, 0.00046 | 256, 0.00082 |

Every wrong pixel at these sizes is one the original also drew wrong, or one
the teacher puts within 0.1 of one half (G3).
At 13x27 the expert is exact on fewer patterns than the original (64 against 256):
its 256 wrong pixels all have a teacher value within 0.015625 of one half.
At 1x2 the cell is too small for the lattice; both nets get the same 160 firmly decided pixels wrong.

## Speed

Median µs per glyph through the public API, inside the bundle, all 256
patterns per batch (kilix-bench `braille` production cases):

| CPU | Cell | split-v5 coverage | split-v6 coverage | split-v5 cold draw | split-v6 cold draw |
|---|---|---:|---:|---:|---:|
| i7-10700F | 8x16 | 176.5 | 9.8 | 149.6 | 10.3 |
| i7-10700F | 16x32 | 682.3 | 32.5 | 559.5 | 35.0 |
| i7-10700F | 25x49 | 331.8 | 74.4 | 341.7 | 78.6 |
| i7-10700F | 48x96 | 1167.4 | 73.9 | 1222.0 | 90.6 |
| Cortex-A72 | 8x16 | 1279.0 | 39.2 | 1275.2 | 41.4 |
| Cortex-A72 | 16x32 | 4972.9 | 124.4 | 5058.4 | 132.7 |
| Cortex-A72 | 25x49 | 3004.5 | 282.7 | 3018.4 | 300.2 |
| Cortex-A72 | 48x96 | 11119.6 | 276.0 | 11144.9 | 341.9 |
| i7-6820HQ | 8x16 | 238.1 | 13.2 | 202.1 | 14.4 |
| i7-6820HQ | 16x32 | 917.1 | 44.1 | 756.9 | 47.8 |
| i7-6820HQ | 25x49 | 448.3 | 99.6 | 462.4 | 109.2 |
| i7-6820HQ | 48x96 | 1568.9 | 99.2 | 1650.9 | 131.8 |

A primed draw (the glyph already in the draw cache, which is unchanged)
costs what it did: within 5% of split-v5 except Cortex-A72 16x32 (+9%).
Every host drew the same coverage bytes for every model and cell.
Every production case was checked against an independent float64 reading
of the packed file; the largest difference was 9.1e-06.

## Files

| File | Bytes | SHA256 |
|---|---:|---|
| `neuronte-braille-v1.nrt` | 2,948 | `96ca3cf81e0df88a1794116d9b024ef4f0b62f3ddc9834d75c51c03a6c172416` |
| `neuronte-split-v6.nrt` | 1,539,388 | `bbfa988a91f2214addbc89c291847da83387363327a6405a63d72873534b648a` |

`neuronte-braille-v1.json` holds the net with its own training record and
the tile layout; `train/pack.py` packs it. `SHA256SUMS` lists all three.

## Reproduction

Training used kilix-bench `922410d`, whose batched trainer and layouts are
the files that trained it (20,000 steps, Adam 0.002, cosine schedule, TF32
off, on one CUDA GPU). Seed 4 was trained in one batch with the group's other seeds;
the batch's per-model losses are independent:

```sh
python3 -m kilix_bench.braille_batch_train out/ --neuronte-home . --patterns 2 --compile --layout dots --parts dots-r0-c0 --width 6 --seeds 2,3,4
python3 tools/braille-tiled.py weights/neuronte-braille-v1.json --layout dots-shared out/dots-r0-c0-s4.json
python3 train/pack.py weights/neuronte-braille-v1.json weights/neuronte-braille-v1.nrt
python3 train/pack.py --bundle weights/neuronte-split-v6.nrt weights/neuronte-ascii-v0.json weights/neuronte-draw-v2.json weights/neuronte-symbol-v0.json weights/neuronte-accent-v2.json weights/neuronte-pixel-v1.json weights/neuronte-braille-v1.json --gate weights/neuronte-gate-v4.json
make test-rc9-braille
```

The shipped JSON carries a `--note`; the packed file does not depend on it.
