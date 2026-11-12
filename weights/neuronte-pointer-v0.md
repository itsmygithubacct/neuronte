# Separate NW pointer

Original two-polygon artwork in `font/pointer.txt`, with a fixed black
silhouette and inset white fill. MIT license, as the project. The accepted
167-icon inventory and learned symbol-v0 were inspected: neither has a
conventional NW mouse arrow. E0B2 is a left-pointing powerline triangle.
U+100001 was absent from existing font sources and expanded trained label
ranges before this addition. The flame keeps U+100000.

This is a separate optional colour net. It does not replace icon-v1, change
the terminal bundle, or alter any earlier source or trained weights. The
baseline integration is c586369; the associated accepted runtime is 51d8b61.

Only U+100001 is trained. Consumers must select this asset explicitly for
that scalar; other scalars are **not** guaranteed blank. Render the entire
1:2 cell, with no crop: 16x32 (supersampling 2) or 32x64 (supersampling 1).
The design tip is (0.9375, 0.9375) on the 10x20 design grid. Integer hotspot
coordinates are (1,1) and (3,3), respectively; subtract these from the mouse
position to obtain the image origin. Palette entries 2/3 are fixed black/white
on both themes. Other sizes have not been accepted by this review.

Reproduce on CPU from the repository root, with torch, NumPy and Pillow:

```sh
# Repeat with seed 1 and output suffix .seed1 for the independent run.
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python3 train/colour.py weights/neuronte-pointer-v0.raw.json \
  --form A --layers 2 --width 64 --head-width 16 --steps 20000 \
  --device cpu --seed 0 --drawing font/pointer.txt \
  --palette font/pointer-palette.txt \
  --scores-out weights/neuronte-pointer-v0.scores.json --log-every 2000
# Prepare one target cache, reused by both seeds.
python3 train/colour_calibrate.py weights/neuronte-pointer-v0.raw.json \
  build/pointer-targets.npz --prepare-targets --device cpu
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python3 train/colour_calibrate.py weights/neuronte-pointer-v0.raw.json \
  weights/neuronte-pointer-v0.json --targets build/pointer-targets.npz \
  --device cpu --steps 5000
# Repeat calibration using the .seed1.raw.json and .seed1.json paths.
python3 train/pack.py weights/neuronte-pointer-v0.json weights/neuronte-pointer-v0.nrt
python3 train/pack.py weights/neuronte-pointer-v0.seed1.json weights/neuronte-pointer-v0.seed1.nrt
make build/libneuronte.so
OPENBLAS_NUM_THREADS=1 python3 tools/pointer-preview.py
```

Both runs use the existing unmodified stroke/colour training and packing
pipeline, grid 256, float32, one CPU thread, and distinct fixed seeds.
Training records source, drawing and palette hashes. Validation records
model and packed-file hashes and verifies exact repacking. The NumPy
reference reads JSON independently of the C loader.

The pointer-specific acceptance checks at both requested sizes, for both
seeds, require each layer's analytic-target mask IoU >= .97, C/NumPy maximum
coverage error < .001, correct palette, zero border coverage, first visible
tip within one pixel of the source, exactly one eight-connected visible
component, at least 15 contrasting pixels on each theme, and mean composite
error below 4/255. These are bounded cursor checks, not the 167-icon gate.
The source target uses 8x8 analytic samples; the trainer separately reports
its interpolated grid target at widths 12/16/32.

`previews/pointer-sheet.png` compares the source and both C-rendered seeds
on light/dark backgrounds at native size and enlarged. PNGs are review
artifacts only; runtime pixels come from the trained distance network.

The first 20,000-step models are retained as `.raw.json` and `.raw.nrt`.
Their original trainer reports remain `.scores.json`; these describe the raw
models, not the calibrated ones. Raw 16px silhouette IoUs were .90076 and
.921875, below the predeclared .97 gate despite low colour error. The existing
`train/colour_calibrate.py` then trained only the final distance layer for
5,000 steps per seed (about 4.6 seconds each), using its default learning
rate, margin and field anchor. Geometry, hidden body, palette head and seed
identity are unchanged. Calibration provenance binds each parent model,
target cache and implementation. Raw models are retained for audit, not
accepted alternatives. The raw failure report and comparison sheet remain
with the external run artifacts.

Both calibrated seeds pass the unchanged pointer gate. At 16x32 both layers
have IoU 1.0. At 32x64 seed 0 has silhouette/fill IoU .998120/.996599;
seed 1 has 1.0/.993220. Maximum C/NumPy coverage difference is below 9.1e-7.
Border alpha is zero; each silhouette has one visible component. The first
visible pixel is (1,1) or (3,3), matching the chosen hotspot; at the small
size the analytic source first exceeds 0.1 coverage one row later. Mean
composite error is at most 1.004/255. The source and both C seed previews
were visually inspected at native and enlarged sizes on both themes.
This establishes local asset quality, not deployment or mouse latency.

The optional `neuronte-pointer-v0.manifest.json` names seed 0 and binds its
packed hash, source/palette hashes, scalar, dimensions, supersampling and
hotspots. The consumer must verify these bindings before loading. The
validation JSON binds both seeds and raw parents. Existing SHA256SUMS is
preserved; new artifacts have `neuronte-pointer-v0.sha256`.
