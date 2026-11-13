# ASCII character groups and spatial halves

Two new files draw the 95 printable ASCII characters, U+0020..U+007E.
Both recipes pass the declared quality limits in seeds 0 and 1 at 19 cell
sizes. Seed 0 is packaged, as declared before performance selection.

| File | Organization | Parameters | Bytes |
|---|---|---:|---:|
| `neuronte-ascii-v0.nrt` | original H128 expert | 44,801 | 179,408 |
| `neuronte-ascii-groups-v1.nrt` | four H64 character groups | 56,836 | 228,252 |
| `neuronte-ascii-spatial-v1.nrt` | two H64 top/bottom tiles | 28,418 | 114,172 |

Each network has shape 90→H→H→H→1: 26 position features, 64 code features,
three ReLU hidden layers and one scalar field output. The character groups
contain 23, 24, 24 and 24 scalars in order. Their range table selects one
network for the whole glyph. The spatial file contains a version 6 tiled
member, with one column and two rows; each sample is evaluated by its
own half's network. Both designs evaluate one H64 network per sample.

The spatial option has 36.6% fewer parameters than the original expert and
keeps total hidden width 128. Character groups have total hidden width 256
and 26.9% more parameters than the original, with lower coverage error.
Widths alone do not determine speed: native dense layers skip zero ReLU
inputs, and activation sparsity depends on the trained weights.

## Complete font packages

`neuronte-split-ascii-groups-v1.nrt` and
`neuronte-split-ascii-spatial-v1.nrt` contain the respective known-ASCII
updates with the original split-v5 fallback and other font families.
They are 1,801,868 and 1,687,436 bytes. The original ASCII member remains
available to the gate for unknown characters; new gate outputs are
suppressed after a conservative bound check. This retention explains why
the complete spatial bundle grows even though its active ASCII model is
smaller. The direct ASCII files are intended for their trained repertoire.

The character-group files use existing version 2 routing. The spatial
files require the version 6 tiled runtime. Direct and complete-package
coverage agree bit for bit for every ASCII glyph at all 19 checked sizes.
Both complete packages pass the full, accent and pixel consumer API checks.
The video tool accepts both packages in full mode through `--weights`.
Existing learned video helpers remain bound to the original split-v5 weights;
they cannot be combined with these new packages without retraining.

## Performance

The declared selection rule chooses **character 4×64**. It ranks eligible recipes
by geometric mean uncached speedup over split-v5 across both seeds, three CPUs
and three cell sizes, choosing lower mean coverage error within 5% of the fastest.
Both packages remain available for the accuracy/storage tradeoff above.

Median uncached coverage at 16×32, **milliseconds per glyph**, for packaged seed 0:

| Full bundle | Core i7-6820HQ | Core i7-10700F | Cortex-A72 / RK3399 |
|---|---:|---:|---:|
| Original split-v5 | 2.711 | 2.016 | 22.781 |
| Character 4×64 | 1.214 | 0.893 | 8.538 |
| Spatial 2×64 | 1.175 | 0.870 | 8.579 |

Geometric mean speedups over all 18 seed × CPU × size comparisons:

| Recipe | Speedup | Lowest individual speedup | Mean coverage MAE |
|---|---:|---:|---:|
| Character 4×64 | 2.286× | 1.925× | 0.003202 |
| Spatial 2×64 | 2.277× | 1.790× | 0.003493 |
| Character 2×96 (not packaged) | 1.280× | 1.156× | 0.003160 |

Opening and cached drawing have separate costs. Each entry below is
**opening ms / warm drawing µs per 16×32 glyph**, for seed 0:

| Full bundle | Core i7-6820HQ | Core i7-10700F | Cortex-A72 / RK3399 |
|---|---:|---:|---:|
| Original split-v5 | 2.641 / 3.278 | 1.823 / 2.079 | 8.887 / 8.173 |
| Character 4×64 | 2.898 / 3.293 | 1.963 / 2.080 | 9.952 / 8.074 |
| Spatial 2×64 | 2.743 / 3.276 | 1.862 / 2.070 | 9.260 / 8.168 |

Each scenario uses one warmup and ten measured repetitions. Reported values
are medians of complete 95-character batch means, including spaces; coverage
and warm drawing use four corpus passes. Each job has a fresh process and
model handles. Cases are shuffled each round and all raw trials are retained.
The tested sizes are 8×16, 16×32 and 48×96; automatic sampling uses two samples
per axis for the first two and one for the last. CPU pins are 3, 3 and 5.
The laptop uses AC power. Existing background workloads and governors remain
in place, so these are measurements of those host conditions.

Loading, uncached coverage, cold drawing, primed drawing and table routing
are separate scenarios. OS page cache is retained. Desktop startup, RC9
preload threads and persisted atlases are outside this native measurement.
An uncached inference improvement does not imply the same warm-cache benefit.

The measured runtime is `074cf185f9b805d52abb51d44d7a03b4c5674123` and the
kilix-bench harness is `8f192286dcda1474b94ff0539492e863228ce3cb`.
The packaged model bytes match the frozen benchmark inputs. Manifest SHA256:
`ce566ae36cd02a1441a2bf2a95a2c59b1c2af45d048a0d893cd06cd33deb01a8`.

## Quality

The limits compare each candidate with the original at the same size:
mean absolute coverage error may increase by 0.0015, the 99th percentile
by 0.02, firm wrong-pixel fraction by 0.0005, and each glyph's mean error
by 0.01. A firm pixel has teacher coverage at least 0.1 away from one half.
No baseline-correct nearest-teacher identity may be lost. Every trained
seed must pass; the limits were not relaxed after scoring.

The initial sizes are 7×13, 8×16, 9×17, 13×27, 16×32, 17×35, 23×47,
24×48, 25×49, 31×63, 33×61, 48×96 and 64×128. Six untouched holdouts
were added after small-size failures in other expert studies: 3×6, 4×8,
5×10, 6×12, 12×24 and 32×64. No further ASCII training followed them.

The fixed total-width sweep, 4×32, 8×16, 16×8 and 64×2, failed these
quality limits with both spatial and character partitions. A longer
character 2×64 recipe passed the initial sizes but failed the percent
sign's per-glyph allowance at 3×6 in seed 1; it was excluded. Character
2×96 passed quality but was slower overall than both packaged options.

| Model | 16×32 mean error | 48×96 mean error |
|---|---:|---:|
| Original H128 | 0.002807 | 0.002050 |
| Character 4×64, seed 0 | 0.002706 | 0.001860 |
| Character 4×64, seed 1 | 0.002656 | 0.001818 |
| Spatial 2×64, seed 0 | 0.002917 | 0.002313 |
| Spatial 2×64, seed 1 | 0.002932 | 0.002279 |

The spatial model trades some coverage accuracy for lower storage.
All recorded sizes, metrics, source hashes and both-seed qualification
evidence are in `neuronte-ascii-next.validation.json`.

## Reproduction

Training used source `074cf185f9b805d52abb51d44d7a03b4c5674123`, PyTorch
2.6.0 with CUDA 12.4, float32 arithmetic and TF32 disabled. The analytic
ASCII teacher is stored on a 257×513 FP16 grid per glyph; coverage targets
use eight subpixel samples per axis. The teacher digest and original
source hashes are retained in the validation record and exported JSON.

Run each recipe in a separate directory on active storage. These commands
retain the original unknown-character loss and train both seeds in the
same batch grouping used for the packaged weights:

```sh
python3 train/decompose.py prepare /tmp/ascii-groups
python3 train/decompose.py train /tmp/ascii-groups --mode repertoire --parts 4 --hidden-width 64 --steps 40000 --seeds 0,1 --batch-models 8 --unlabelled 1
python3 train/decompose_pack.py /tmp/ascii-groups --recipe repertoire --parts 4 --hidden-width 64 --steps 40000
python3 train/decompose.py prepare /tmp/ascii-spatial
python3 train/decompose.py train /tmp/ascii-spatial --mode spatial --parts 2 --hidden-width 64 --steps 100000 --seeds 0,1 --batch-models 4 --unlabelled 1
python3 train/decompose_pack.py /tmp/ascii-spatial --recipe spatial --parts 2 --hidden-width 64 --steps 100000
```

The supplied JSON reproduces the packaged bytes without retraining:

```sh
python3 train/pack.py --bundle groups.nrt weights/neuronte-ascii-groups-v1-p0.json weights/neuronte-ascii-groups-v1-p1.json weights/neuronte-ascii-groups-v1-p2.json weights/neuronte-ascii-groups-v1-p3.json
python3 train/pack.py weights/neuronte-ascii-spatial-v1.json spatial.nrt
python3 train/known_bundle.py weights/neuronte-split-v5.nrt split-groups.nrt weights/neuronte-ascii-groups-v1-p0.json weights/neuronte-ascii-groups-v1-p1.json weights/neuronte-ascii-groups-v1-p2.json weights/neuronte-ascii-groups-v1-p3.json --expert 0
python3 train/known_bundle.py weights/neuronte-split-v5.nrt split-spatial.nrt weights/neuronte-ascii-spatial-v1.json --expert 0
make test-ascii-next
```

The release check rebuilds the teacher, repacks the exact binaries,
checks every glyph at all 19 sizes, compares direct and complete-package
pixels, and verifies unrelated/unknown routes and representative pixels.
Qualification records cover both seeds; the supplied runtime assets and
native release check use seed 0. Other-seed exports and checkpoints are
retained with the experiment.

To prepare the packaged seed-0 benchmark with kilix-bench, use its checked
release preparer (commit `4311900` or later):

```sh
python3 -m kilix_bench.ascii_prepare /tmp/ascii-release-bench --neuronte-home .
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m kilix_bench --suite neuronte --neuronte-home . --ascii-experiment /tmp/ascii-release-bench/manifest.json --cells 8x16,16x32,48x96 --warmup 1 --repeats 10 --expert-passes 4 --cpu 3
```

Choose an allowed CPU and a new directory on active storage. This six-case
reproduction compares the original and both replacements in direct and full
form; it does not replace the original two-seed selection campaign.
