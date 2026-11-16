# Large desktop face v1 (`neuronte-ui-large-v1`, 33 px and up)

The same face as `neuronte-ui-large-v0` (the ui-large strokes, `font/ui-large.txt`, blended), with
the same advances, drawn by a bundle of four smaller nets instead of one 384 wide. It draws a
whole face for the first time about 12 times faster. `neuronte-ui-large-v0` is unchanged and remains
the default; a consumer takes up v1 only by changing its own file list.

**Gate result, stated plainly: NEGATIVE under the declared overlap gate. Shipped by the owner's
decision.** The gate asked for an overlap (IoU against the exact strokes, one sample per pixel) no
worse than v0's, in mean and minimum, at 32, 48, 64 and 96 px, on both seeds. v1 fails it at 32 px
(the mean, on both seeds; most of v0's 32 px lead is pixels whose true coverage is exactly one half,
which every net gets about half wrong), at 48 px (the minimum, on both seeds; the worst letter is
`^`) and at 96 px (the minimum, on seed 0). Its means at 48, 64 and 96 px are better than v0's. The
owner chose to ship it knowing these numbers. ui-large is drawn only from 33 px up.

| em | v0 mean / min | v1 seed 0 mean / min | v1 seed 1 mean / min |
|---|---|---|---|
| 32 | 0.9731 / 0.8155 | 0.9697 / 0.7946 | 0.9717 / 0.8091 |
| 48 | 0.9936 / 0.9711 | 0.9955 / 0.9653 | 0.9959 / 0.9709 |
| 64 | 0.9936 / 0.9701 | 0.9946 / 0.9733 | 0.9949 / 0.9733 |
| 96 | 0.9907 / 0.9373 | 0.9927 / 0.9367 | 0.9929 / 0.9416 |

The other gates passed on both seeds: the C library agrees with an independent float64 evaluation
within 1e-3 and the file is exactly what the packer makes (`tests/check_reference.py
--drawing-bundle`), the advance table is byte for byte v0's, and first use is more than 3 times
faster at 48 and 64 px on both test machines.

## What is in the file

One bundle of 4 band-tiled distance nets, each 192 x 192 x 192 wide (91,777 parameters each, 367,108
in all; v0 has 331,009), one contiguous group of 24 characters per net, each drawing only ui-large's
ink rows, and v0's advance table (`font/ui-large-advances.txt`). 1,473,000 bytes (v0: 1,325,072).
Printable ASCII and U+2026, regular and bold.

## Speed

The kilix-bench face experiment, as for v0's other successors: a fresh process and handle per job,
shuffled rounds, under one lock per machine. Cold draw is a new handle drawing every character once,
as a desktop builds its letter cells; ms per character (x 96 for the whole face), median.

| em | i7-10700F v0 -> v1 s0 / s1 | i7-6820HQ v0 -> v1 s0 / s1 | speed-up |
|---|---|---|---|
| 33 | 20.15 -> 1.67 / 1.65 | 18.62 -> 1.57 / 1.57 | 11.8x to 12.2x |
| 48 | 42.61 -> 3.40 / 3.36 | 39.24 -> 3.24 / 3.25 | 12.1x to 12.7x |
| 64 | 75.96 -> 5.93 / 5.89 | 69.93 -> 5.74 / 5.73 | 12.2x to 12.9x |

Cached drawing is the same as v0 (about 0.017 ms per character). Of the four recipes tried, this one
was the slowest (others reached 21x) and the only one whose 64 px minimum passed on both seeds; the
owner chose it for accuracy.

## Training

Trained on one RTX 3070, seeds 0 and 1 together:

    python3 train/face_parts.py OUT --set uilarge --band --groups 4 --width 192 --steps 80000 \
        --candidates 2048 --near 384 --clamp 0.25 --name L4-bg4w192-80k-n384-c25

then `train/pack.py --drawing-bundle neuronte-ui-large-v1.nrt font/ui-large-advances.txt MEMBERS...`.
No seed-choice rule was declared before training; seed 0 is the packed file by this repository's
convention, and seed 1's members (`neuronte-ui-large-v1.seed1-gG.json`) are kept. The members'
`sources_sha256` name the trainer as it was then; it has since only gained `--pen`, whose default
leaves this recipe unchanged. `make test-ui-large-v1` (part of `make test`) repacks both seeds and
runs the reference check on each.
