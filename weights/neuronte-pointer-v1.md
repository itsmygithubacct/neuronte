# Separate NW pointer, version 1

The drawing, palette, scalar, sizes and hotspots of `neuronte-pointer-v0`, with a
narrower net: width 48 rather than 64. The file is 41,984 bytes instead of 62,400, and it draws
about 36 per cent faster. `neuronte-pointer-v0` is unchanged and stays where it was;
anything bound to its hash keeps working. This is a new name, for a consumer
that chooses to move.

What a consumer must do does not change from v0. Only U+100001 is trained, and
other scalars are **not** guaranteed blank. Render the whole 1:2 cell with no
crop, at 16x32 (supersampling 2) or 32x64 (supersampling 1). The hotspots are
(1,1) and (3,3). Palette entries 2 and 3 are fixed black and white on both
themes. `neuronte-pointer-v1.manifest.json` binds seed 0's packed hash, the
source and palette hashes, the scalar, the sizes, the supersampling and the
hotspots. No other sizes are accepted.

Reproduce on CPU from the top of the tree, with torch, NumPy and Pillow. This is the v0
recipe with `--width 48`:

```sh
# Seed 1: --seed 1 and the .seed1 paths.
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python3 train/colour.py weights/neuronte-pointer-v1.raw.json \
  --form A --layers 2 --width 48 --head-width 16 --steps 20000 \
  --device cpu --seed 0 --drawing font/pointer.txt \
  --palette font/pointer-palette.txt \
  --scores-out weights/neuronte-pointer-v1.scores.json --log-every 5000
python3 train/colour_calibrate.py weights/neuronte-pointer-v1.raw.json \
  build/pointer-targets.npz --prepare-targets --device cpu
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python3 train/colour_calibrate.py weights/neuronte-pointer-v1.raw.json \
  weights/neuronte-pointer-v1.json --targets build/pointer-targets.npz \
  --device cpu --steps 5000
python3 train/pack.py weights/neuronte-pointer-v1.json weights/neuronte-pointer-v1.nrt
python3 train/pack.py weights/neuronte-pointer-v1.seed1.json weights/neuronte-pointer-v1.seed1.nrt
make build/libneuronte.so
python3 tests/check_pointer.py build/libneuronte.so weights/neuronte-pointer-v1.json \
  weights/neuronte-pointer-v1.nrt --max-xor 16:0,0 --max-xor 32:1,2
```

The target cache is the same for every pointer net, because it depends only on
the drawing. As in v0, `.scores.json` is the trainer's report for the raw
model, and the raw models are kept for audit. They are not alternatives.

## Gate

The gate was declared before any candidate was scored, and both seeds must pass
it. `tests/check_pointer.py` runs every check on v0's card, at both sizes:

- each layer's IoU against the 8x8 analytic target is at least .97;
- C and NumPy agree to within .001;
- the palette is entries 2 and 3;
- the border alpha is zero;
- the tip is within one pixel;
- the silhouette is exactly one visible component;
- each theme has at least 15 contrasting pixels;
- the mean composite error is under 4/255.

Two checks are new. The first visible pixel must be exactly the hotspot in the manifest. And no layer may
have more mask pixels off the drawing than v0 has, given as `--max-xor 16:0,0
--max-xor 32:1,2`: at 32x64 that bound is v0's worse seed in each layer.
`tests/check_reference.py` checks the C runtime against an independent float64
NumPy evaluation and that the packed bytes are reproduced exactly.

| seed | size | IoU (silhouette, fill) | pixels off drawing | first visible | mean error /255 (dark, light) |
|---|---|---|---|---|---|
| 0 | 16x32 | 1.0, 1.0 | 0, 0 | (1,1) | .440, .952 |
| 0 | 32x64 | .998120, .996599 | 1, 1 | (3,3) | .555, 1.083 |
| 1 | 16x32 | 1.0, 1.0 | 0, 0 | (1,1) | .476, 1.115 |
| 1 | 32x64 | .998120, .993197 | 1, 2 | (3,3) | .566, 1.256 |

Both seeds have one visible component and zero border alpha.
`neuronte-pointer-v1.validation.json` holds the full reports and the hashes of
every file. The narrower nets are recorded with the run, failures included. Every width from 8 to 40 failed this gate at 20,000 steps, and again at
40,000 for seed 0. Widths 48 and 56 passed with both seeds, and 48 is the narrower.

## Speed

Each job was a fresh process pinned to one core, and a host benchmark lock was held for the whole run. A
validation pass came first, then one warmup and ten shuffled rounds. The figures are medians in
milliseconds. "Cold" draws a cell on fresh handles, so it misses the draw cache. "Primed" draws
a cell that is already in the cache. The runtime is commit adab1d8.

| CPU | net | open | 16x32 cold | 32x64 cold | 16x32 primed | 32x64 primed |
|---|---|---|---|---|---|---|
| i7-6820HQ | v0 | .0343 | 1.566 | 1.619 | .0075 | .0251 |
| i7-6820HQ | v1 seed 0 | .0271 | .997 | 1.025 | .0074 | .0250 |
| i7-6820HQ | v1 seed 1 | .0272 | 1.006 | 1.036 | .0075 | .0251 |
| i7-10700F | v0 | .0202 | 1.127 | 1.174 | .0049 | .0177 |
| i7-10700F | v1 seed 0 | .0147 | .719 | .740 | .0048 | .0177 |
| i7-10700F | v1 seed 1 | .0147 | .727 | .750 | .0049 | .0177 |

Opening the file and cold draws are faster with both seeds on both CPUs. A primed draw only
reads the cache, so it does not depend on the net, and it is the same.
