# Pixel repertoire groups v1

The selected pixel model is seed 1 of four H64 repertoire networks, trained
for 60,000 steps with the original unknown regularization weight 1. It draws
all 327 block, sextant and octant labels in `neuronte-split-v8.nrt`
([recipe, checks and speed](neuronte-split-v8.md)).

The selection followed visual review of the complete geometry comparisons.
Seed 1 preserves every baseline-correct nearest identity across the 22
reviewed sizes and both sampling modes. It has fewer failing geometry cases
than seed 0: six versus eight with automatic sampling, and fourteen versus
fifteen with explicit S1. Seed 0 has 39 fewer newly wrong firm pixels summed
across both modes. Identity preservation and fewer affected geometries were
prioritized in choosing seed 1.

## Recipe and assets

Each member is 90→64→64→64→1 with 14,209 parameters. Four members total
56,836 parameters, versus 44,801 for the original H128 expert. A labelled
pixel glyph evaluates one H64 member. The full bundle retains the original
H128 member for unknown-character fallback.

The exact exports are `neuronte-pixel-groups-v1-p0.json` through `-p3.json`.
The standalone `neuronte-pixel-groups-v1.nrt` is their direct composition;
it is an equivalence-check asset rather than a full font.

Training used the unchanged 327-glyph teacher, Adam with learning rate .002
and a cosine schedule, seeds 0 and 1, eager CUDA, and TF32 disabled.
PyTorch 2.6.0/CUDA 12.4 and NumPy 2.2.2 were used on an RTX 4090. The trainer
revision was `4d592e9adce8fa368ff69e9017e82bd51d7ee70d`; use that revision's
generic decomposition trainer with:

```sh
python3 train/decompose.py train EXPERIMENT --set pixel --mode repertoire \
  --parts 4 --width-budget 256 --seeds 0,1 --batch-models 8 \
  --steps 60000 --unlabelled 1 --log-every 1000 --checkpoint-every 2000
```

Teacher SHA256:
`6363f7725a259093bb8e82704c3948c62d11289e23032d475838c9b39c4d8102`.
The validation JSON records both seeds, all 22 sizes and both sampling modes.

## Quality and accepted exceptions

Both seeds pass the original standard-size quality limits at 8×16, 16×32
and 48×96, including all 327 nearest identities and the per-glyph error and
IoU limits. Seed 1's automatic mean coverage errors are
.002015524 / .001370459 / .001140358, versus
.002870822 / .002018107 / .001756367 for the previous H128 model.
Their three-size mean is 31.9% lower.

**The original strict geometry gates still fail.** Selection after visual
review does not change those measurements or relabel them as passes.
Seed 1 introduces 296 new firm wrong pixels across the additional automatic
geometry checks and 500 across explicit S1 checks. Automatic failures occur
at 25×49, 25×50, 31×63, 32×64, 33×61 and 64×128; S1 also has small-size
failures. At 64×128, 242 pixels that the original classified correctly become
firm wrong pixels. There are no baseline-correct nearest-identity losses
for seed 1. Complete counts remain in the validation JSON.

## Measured pixel performance

The measured full bundle is split-v7 with only these groups added. It is not
shipped under a name of its own; split-v8's check rebuilds it and draws every
pixel glyph exactly as it does:
`a45671b6faa733ec2b1c3b459671c63d224cbd8ee3960d0e0b289952265a245d`.
The baseline was `neuronte-split-v7.nrt`:
`b6e8ad1ac6fbc2370fbacc14727180954b4fc6d23cf7c0506a93116853f92f1f`.

| CPU | 8×16 speedup | 16×32 speedup | 48×96 speedup | Geometric mean |
|---|---:|---:|---:|---:|
| Ryzen 9 9950X | 1.375× | 1.284× | 2.366× | 1.610× |
| Core i7-10700F | 2.025× | 2.137× | 2.170× | 2.110× |

These are median uncached public-API coverage timings for all 327 glyphs,
one warmup and ten measured repeats, four complete corpus passes per batch,
one pinned CPU, and an exclusive host benchmark lock. Both seeds and the
baseline produced 726 retained raw trials across the two hosts. All nine
standard-size coverage buffers exactly agree across hosts. No ARM timing
was performed for this follow-up.

At 16×32 on the Core i7-10700F, selected-seed coverage is .808 ms/glyph,
versus 1.727 ms for the baseline. Primed drawing remains about 2.95–2.97 µs
per glyph. Opening rises from 1.91 to 2.07 ms. The speedups describe pixel
inference; they are not full-video throughput measurements.
