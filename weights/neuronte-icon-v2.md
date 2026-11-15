# Icons in colour, version 2

`neuronte-icon-v1` has 167 icons in one net, 256 wide, with K = 6. This
version splits the same icons into four nets, each 96 wide with K = 3, and
packs them as a version 2 bundle of four version 3 members. The drawings,
palette, pen, grid and tau are unchanged. The bundle routes each icon to one
member through a range table, with member 0 as the fallback and no gate.
The file is 496,184 bytes instead of 650,216, and a cold draw is about four
times faster. `neuronte-icon-v1` is unchanged, so anything bound to its hash
keeps working. This is a new name, for a consumer that chooses to move.

K = 3 is enough because no icon has more than three layers; v1's layers 3 to
5 are unused by every icon. `neuronte_layers` on this file returns 3.

The four members are contiguous runs of the icons sorted by scalar:

- g0 has 41 icons, U+E0A0..U+F00C;
- g1 has 42, U+F00D..U+F065;
- g2 has 42, U+F066..U+F109;
- g3 has 42, U+F110..U+F08AE.

`train/colour.py --group I/4` makes the same cut and records it in each
member's training record.

Reproduce from the top of the tree. Training ran on one CUDA GPU, so another
device will not give the same bits. The offset and packing ran on the CPU.

```sh
# Seed 1: --seed 1 and the .seed1 paths. Repeat for groups 1, 2 and 3.
python3 train/colour.py build/icon-v2.g0.raw.json --form A --layers 3 \
  --width 96 --steps 80000 --seed 0 --group 0/4 --device cuda \
  --scores-out weights/neuronte-icon-v2.g0.scores.json --log-every 5000
python3 tools/calibrate-output-bias.py build/icon-v2.g0.raw.json \
  weights/neuronte-icon-v2.g0.json --offsets=-0.008
python3 train/pack.py --bundle weights/neuronte-icon-v2.nrt \
  weights/neuronte-icon-v2.g0.json weights/neuronte-icon-v2.g1.json \
  weights/neuronte-icon-v2.g2.json weights/neuronte-icon-v2.g3.json
```

The calibration is v1's method. It adds one uniform offset to the distance
outputs' biases: the same offset for every member and for both seeds. The
offset is the first of 0, -.004, -.008 and -.012 with which both seeds
pass. Here that is -.008, as for v1. Each member's record keeps its raw
parent's hash and its biases before and after the offset. `.scores.json` is
the trainer's report on the raw member. Seed 0 is the published file. Seed 1
is the independent run that has to pass the same gate.

## Gate

This is v1's gate, applied to the whole file. The gate was declared before
any candidate was scored, and both seeds must pass it with the same recipe.
`tests/check_icon_quality.py` reads the members with `--also`. It draws
through the packed C API with snap off, at 12, 16 and 32 px (2x2, 2x2 and
1x1 samples), against the unchanged float16 grid-256 targets. It requires:

- a mean IoU of at least .990 over all 209 used layers at 16 px;
- at every size, no wrong palette entry;
- no thresholded coverage and no positive coverage in an unused layer;
- no lost used layer that should have ink;
- no used layer with zero coverage.

`tests/check_reference.py --bundle` checks the C runtime against an
independent float64 NumPy evaluation, with snapping on. It covers the routes
and checks that packing reproduces the bytes exactly.

| file | mean IoU 12 px | mean IoU 16 px | mean IoU 32 px | layer pixels off (12 / 16 / 32) |
|---|---|---|---|---|
| icon-v1 | .98981 | .99179 | .99150 | 82 / 114 / 433 |
| v2 seed 0 | .98193 | .99167 | .99167 | 87 / 128 / 475 |
| v2 seed 1 | .98658 | .99153 | .98999 | 108 / 126 / 522 |

Both seeds pass. At the declared bar, 16 px, v2 equals v1. It is less exact
than v1 at 12 px. Most of that difference comes from a few very small
layers. In seed 0 at 12 px, U+F014's layer 1 has no target pixel above the
threshold but one predicted pixel. U+F15B's layer 1 has one pixel right out
of two. It also has a few more layer pixels off at every size. A consumer
that needs v1's 12 px exactness should stay on v1.
`neuronte-icon-v2.validation.json` holds both seeds' full reports.

The other recipes, failures included, are recorded with the run. Recipes
whose seeds both passed:

| recipe | offset | seed 0 / seed 1 IoU 16 px |
|---|---|---|
| 4 x H128, 40,000 steps | -.004 | .99233 / .99123 |
| 8 x H96, 40,000 steps | -.004 | .99245 / .99255 |
| 2 x H160, 40,000 steps | -.004 | .99170 / .99135 |

Recipes that failed:

- 1 x H192, 40,000 steps: seed 1 loses a used layer at every offset;
- 1 x H160, 80,000 steps: the same;
- 8 x H64, 80,000 steps: seed 1's best is .98909.

Among the recipes that passed, this one has the fastest cold draw.

## Speed

Each job ran in a fresh process pinned to one core, with the host's
benchmark lock held for the whole run. A validation pass came first, then
one warmup and ten shuffled rounds. The figures are medians, in milliseconds
per pass. "Cold" is one pass of `neuronte_draw_scalar` over all 167 icons on
fresh handles, so it misses the draw cache. "Primed" draws the same cells
from the cache. The runtime was commit f5ccd01. 8 x H96 was measured in the
same round.

| CPU | file | open | 12x24 cold | 16x32 cold | 32x64 cold | 32x64 primed |
|---|---|---|---|---|---|---|
| i7-6820HQ | icon-v1 | 1.090 | 5.975 | 10.516 | 10.722 | .0339 |
| i7-6820HQ | v2 seed 0 | .198 | 1.390 | 2.360 | 2.421 | .0229 |
| i7-6820HQ | v2 seed 1 | .199 | 1.416 | 2.409 | 2.481 | .0229 |
| i7-6820HQ | 8 x H96 seed 0 | .378 | 1.427 | 2.436 | 2.505 | .0231 |
| i7-10700F | icon-v1 | .682 | 4.507 | 7.912 | 8.026 | .0250 |
| i7-10700F | v2 seed 0 | .140 | 1.025 | 1.743 | 1.792 | .0163 |
| i7-10700F | v2 seed 1 | .140 | 1.044 | 1.781 | 1.834 | .0164 |
| i7-10700F | 8 x H96 seed 0 | .269 | 1.046 | 1.810 | 1.843 | .0163 |

The geometric mean of cold draws, over three sizes, two seeds and two CPUs,
is 1.733 ms for v2 against 7.601 for icon-v1 (8 x H96: 1.805). Cold draws
and opening the file are faster for both seeds on both CPUs. Primed draws
are also faster, because they composite three layers instead of six. Routing
a scalar through the range table takes about 10 ns.
