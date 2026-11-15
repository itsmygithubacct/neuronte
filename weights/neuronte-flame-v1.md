# Kilix flame, version 1

The flame of `neuronte-flame-v0` with a narrower net. It uses the same
drawing (`font/flame.txt`), the same palette, the same scalar (U+100000) and
the same 96 blanks, but the width is 56 instead of 64. It has 14,226
parameters instead of 16,914, the file is 57,372 bytes instead of 68,124, and a
cold draw is 10 to 17 per cent faster. `neuronte-flame-v0` is unchanged, so a
consumer bound to its hash keeps working. Moving to this file means binding
the new hash.

Drawing it is the same as for v0. Evaluate an `s` by `2*s` cell, at 16 px
for Start and at 32 for the desktop, and take rows `s/2` through
`3*s/2 - 1`. The file's snap threshold is 14, so neither size snaps.

Reproduce from the top of the tree. Training ran on one CUDA GPU, so a CPU
run will not give the same bits. Calibration ran on the CPU with one thread.

```sh
# Seed 1: --seed 1 and the .seed1 paths.
python3 train/colour.py weights/neuronte-flame-v1.raw.json \
  --form A --layers 3 --width 56 --steps 20000 --seed 0 --device cuda \
  --drawing font/flame.txt --palette font/flame-palette.txt \
  --blank U+0020..U+007E,U+FFFD \
  --scores-out weights/neuronte-flame-v1.scores.json --log-every 5000
python3 train/colour_calibrate.py weights/neuronte-flame-v1.raw.json \
  build/flame-targets.npz --prepare-targets --device cpu
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python3 train/colour_calibrate.py weights/neuronte-flame-v1.raw.json \
  weights/neuronte-flame-v1.json --targets build/flame-targets.npz \
  --device cpu --steps 5000
python3 train/pack.py weights/neuronte-flame-v1.json weights/neuronte-flame-v1.nrt
make build/libneuronte.so
python3 tests/check_flame.py build/libneuronte.so weights/neuronte-flame-v1.json \
  weights/neuronte-flame-v1.nrt --max-xor 16:7,2,0 --max-xor 32:6,3,5
```

The calibration step is the pointer card's. It trains only the final distance
layer, for 5,000 steps at its default settings. The body, the palette head
and the seed are not changed. `.scores.json` is the trainer's report on the
raw model. The raw models are kept, for audit only. They are not alternatives.

## Gate

The gate was declared before any candidate was scored. Both seeds must pass
it with the same recipe. `tests/check_flame.py` checks the cell the way Kilix
95 draws it, at 16 and 32 px, and requires:

- the palette entries are red, yellow and white (2, 3 and 4);
- in the middle square, on both themes, no channel of the composite is more
  than 32/255 from the drawing, and the mean is at most 2/255;
- `neuronte_draw_scalar` into an `s` by `s` buffer, compared premultiplied,
  is within 32/255;
- the 96 blanks write no pixel;
- no layer's mask has more pixels off the drawing than flame-v0's (16 px:
  7, 2, 0; 32 px: 6, 3, 5).

`tests/check_reference.py` checks the C runtime against an independent
float64 NumPy evaluation, and checks that packing reproduces the bytes
exactly.

| file | size | mask pixels off drawing | composite max /255 | consumer max /255 |
|---|---|---|---|---|
| flame-v0 | 16 | 7, 2, 0 | 19.87 | 20.19 |
| flame-v0 | 32 | 6, 3, 5 | 29.99 | 30.44 |
| v1 seed 0 | 16 | 0, 0, 0 | 11.88 | 12.16 |
| v1 seed 0 | 32 | 0, 0, 0 | 27.16 | 27.00 |
| v1 seed 1 | 16 | 0, 0, 0 | 11.00 | 11.44 |
| v1 seed 1 | 32 | 0, 0, 0 | 27.33 | 28.25 |

The composite mean is at most .72/255 for every row. All four masks per seed
match the drawing exactly. `neuronte-flame-v1.validation.json` holds the full
reports and the hash of every file.

The narrower candidates are recorded with the run, failures included. Every
width from 16 to 56 failed with its raw model, both seeds, at 20,000 steps.
With calibration:

| width | 20,000 steps | 40,000 steps |
|---|---|---|
| 56 | both seeds pass | not tried |
| 48 | neither seed passes | only seed 1 passes |
| 40 | only seed 1 passes | only seed 0 passes |
| 32 | neither seed passes | neither seed passes |
| 24 | neither seed passes | neither seed passes |
| 16 | neither seed passes | not tried |

Most of the near misses were a single pixel past 32/255 at 32 px. Width 16 was
not retried at 40,000 steps, although the plan said every failing width would
be. Widths 24 and 32 failed with both seeds at 40,000.

## Speed

Each job ran in a fresh process pinned to one core, and a host benchmark lock
was held for the whole run. A validation pass came first, then one warmup
and ten shuffled rounds. The figures are medians, in milliseconds. "Cold"
draws on fresh handles, so it always misses the draw cache. "Primed" draws a
cell that is already cached. The runtime was commit f5ccd01.

| CPU | net | open | 16 cold | 32 cold | 16 primed | 32 primed |
|---|---|---|---|---|---|---|
| i7-6820HQ | v0 | .0360 | 1.470 | 1.513 | .0054 | .0185 |
| i7-6820HQ | v1 seed 0 | .0354 | 1.319 | 1.356 | .0054 | .0182 |
| i7-6820HQ | v1 seed 1 | .0356 | 1.217 | 1.252 | .0053 | .0184 |
| i7-10700F | v0 | .0213 | 1.072 | 1.102 | .0034 | .0128 |
| i7-10700F | v1 seed 0 | .0205 | .968 | .986 | .0035 | .0127 |
| i7-10700F | v1 seed 1 | .0195 | .896 | .909 | .0033 | .0128 |

Cold draws are faster with both seeds on both CPUs. Opening the file and
primed draws are about the same.
