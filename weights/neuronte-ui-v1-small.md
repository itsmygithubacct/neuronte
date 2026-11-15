# Small desktop faces v1 (`neuronte-uiEM[-italic]-v1`, 1 to 21 px)

New -v1 drawing files for the 30 small desktop faces listed below. Each is a drawing file
(format version 5) holding one bundle of small distance nets and the face's own advances (at 1 and 2 px,
where the drawings have only 2 and 5 distinct shapes, a single net instead of a bundle). Each net draws
only the ink band of its own characters: the em rows from `UI_TOP[em]`, a version 6 tiled member whose
rows above and below the band are a constructed width-1 net that is outside the ink everywhere. Routing
is by the bundle's range table, one contiguous group of characters per net (`train/face_parts.py`).
At 1 px the band reaches the bottom of the cell, so that member has no row below it.

The -v0 files are unchanged and remain the defaults: the installer and Kilix 95 bind the -v0 names and
hashes. A consumer takes up a -v1 face only by changing its own file list.

## Quality bar (the shipped one)

Both seeds of every listed recipe reproduce all 96 characters (printable ASCII and U+2026), regular and
bold, exactly as the face's drawing at its native em through `neuronte_draw_text` with binary on (2 x 2
samples per pixel below 24 px), with every advance exact, C and float64 NumPy coverage within 1e-3 and the
packed bytes identical to the packer's output: `tests/check_reference.py ... --drawing-bundle` (`--drawing`
for the single-net faces). Seed 0 is
the packed file; seed 1's members (`NAME.seed1-gG.json`, G the group) are kept so the gate reruns on both:
`make test-faces-v1-small` (part of `make test`). No calibration, no seed mixing, no relaxed threshold.

## Speed

Measured with the kilix-bench face experiment (whole face at its em, regular, binary, `text_width` regular
and bold then `draw_text` per character, fresh process per job, pinned CPU 3, 1 warmup + 10 shuffled
rounds, medians) on an Intel i7-6820HQ and an Intel i7-10700F, same runtime for v0 and v1. Cold draw is a
new handle drawing the whole face once, as a desktop builds its letter cells; ms per face, i7-6820HQ /
i7-10700F, seed 0. Speed-up = v0 / v1 cold draw, seeds 0/1 per host, and the geometric mean over 2 seeds x
2 hosts. Opening (ms) is reported apart: it grows with the number of nets. The last column counts both,
v0 / v1 opening plus cold draw, the least over 2 seeds x 2 hosts. A recipe was chosen only if
both seeds were faster than v0 on both hosts; the fastest such recipe by the geometric mean was taken,
or within 5% of it the smaller file.

| Face | Recipe | Bytes | Cold draw, whole face, ms: v0 -> v1 | Speed-up (geomean) | Open, ms: v0 -> v1 | Open + cold draw, least speed-up |
|---|---|---:|---|---|---|---:|
| ui1 | ink band, one net 16 wide, 80,000 steps | 9,788 | 1.3 / 0.9 -> 0.3 / 0.2 | 4.0x/4.1x, 4.3x/4.1x (4.1x) | 0.33 -> 0.23 / 0.16 -> 0.10 | 3.0x |
| ui2 | ink band, one net 16 wide, 80,000 steps | 9,808 | 5.8 / 4.2 -> 0.6 / 0.5 | 9.3x/9.3x, 9.2x/8.9x (9.2x) | 0.32 -> 0.22 / 0.22 -> 0.11 | 7.2x |
| ui3 | ink band, 32 nets x 16 wide, 80,000 steps | 288,616 | 11.3 / 8.0 -> 1.3 / 0.9 | 8.9x/8.4x, 9.1x/9.0x (8.9x) | 0.32 -> 0.67 / 0.17 -> 0.35 | 5.8x |
| ui3-italic | ink band, 32 nets x 16 wide, 80,000 steps | 288,616 | 11.7 / 8.5 -> 1.2 / 0.9 | 9.3x/9.4x, 9.4x/9.4x (9.4x) | 0.31 -> 0.68 / 0.17 -> 0.36 | 6.2x |
| ui4 | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 18.2 / 13.2 -> 1.7 / 1.2 | 10.4x/10.2x, 10.7x/10.3x (10.4x) | 0.31 -> 1.59 / 0.16 -> 0.82 | 5.6x |
| ui4-italic | ink band, 32 nets x 16 wide, 80,000 steps | 288,616 | 18.5 / 13.4 -> 1.9 / 1.3 | 9.9x/9.9x, 10.2x/9.7x (9.9x) | 0.31 -> 0.66 / 0.16 -> 0.34 | 7.4x |
| ui5 | ink band, 32 nets x 16 wide, 80,000 steps | 288,616 | 27.9 / 20.4 -> 2.6 / 1.9 | 10.8x/10.6x, 11.0x/10.7x (10.8x) | 0.31 -> 0.67 / 0.17 -> 0.35 | 8.5x |
| ui5-italic | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 28.3 / 20.5 -> 2.6 / 1.8 | 11.0x/10.9x, 11.4x/11.0x (11.1x) | 0.31 -> 1.59 / 0.17 -> 0.90 | 6.9x |
| ui6 | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 39.0 / 28.5 -> 3.2 / 2.3 | 12.2x/12.1x, 12.5x/12.3x (12.3x) | 0.30 -> 1.51 / 0.17 -> 0.87 | 8.3x |
| ui6-italic | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 40.1 / 29.3 -> 3.3 / 2.3 | 12.1x/11.8x, 12.6x/12.2x (12.2x) | 0.32 -> 1.53 / 0.17 -> 0.99 | 8.2x |
| ui7 | ink band, 32 nets x 16 wide, 80,000 steps | 288,616 | 52.7 / 38.2 -> 4.3 / 3.1 | 12.3x/11.9x, 12.4x/12.0x (12.1x) | 0.29 -> 0.67 / 0.17 -> 0.35 | 10.4x |
| ui7-italic | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 51.9 / 38.6 -> 4.2 / 3.0 | 12.4x/12.0x, 12.8x/12.5x (12.4x) | 0.31 -> 1.53 / 0.17 -> 0.85 | 8.9x |
| ui8 | ink band, 32 nets x 16 wide, 80,000 steps | 288,616 | 65.2 / 47.5 -> 5.4 / 3.9 | 12.0x/11.9x, 12.2x/11.9x (12.0x) | 0.31 -> 0.66 / 0.17 -> 0.38 | 10.7x |
| ui8-italic | ink band, 32 nets x 16 wide, 80,000 steps | 288,616 | 85.7 / 62.7 -> 5.4 / 3.9 | 15.7x/15.3x, 16.2x/15.6x (15.7x) | 0.50 -> 0.66 / 0.29 -> 0.36 | 13.7x |
| ui9 | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 84.2 / 59.6 -> 6.2 / 4.4 | 13.6x/13.1x, 13.5x/13.2x (13.4x) | 0.31 -> 1.50 / 0.17 -> 0.92 | 10.6x |
| ui9-italic | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 83.3 / 61.5 -> 6.3 / 4.4 | 13.3x/12.9x, 13.8x/13.5x (13.4x) | 0.31 -> 1.53 / 0.17 -> 0.90 | 10.4x |
| ui10 | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 100.2 / 74.3 -> 7.3 / 5.3 | 13.7x/13.3x, 14.1x/13.7x (13.7x) | 0.32 -> 1.57 / 0.17 -> 0.96 | 11.1x |
| ui10-italic | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 101.8 / 74.4 -> 7.5 / 5.4 | 13.6x/13.2x, 13.9x/13.6x (13.6x) | 0.31 -> 1.52 / 0.17 -> 0.86 | 11.1x |
| ui11 | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 120.7 / 89.6 -> 8.5 / 6.1 | 14.2x/13.9x, 14.6x/14.4x (14.3x) | 0.29 -> 1.50 / 0.17 -> 0.92 | 11.9x |
| ui11-italic | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 121.1 / 89.6 -> 8.8 / 6.3 | 13.7x/13.5x, 14.2x/14.0x (13.8x) | 0.31 -> 1.53 / 0.17 -> 0.85 | 11.5x |
| ui12 | ink band, 96 nets x 20 wide, 80,000 steps | 1,119,068 | 191.7 / 142.5 -> 12.7 / 9.3 | 15.1x/14.1x, 15.3x/14.3x (14.7x) | 0.50 -> 1.83 / 0.29 -> 1.10 | 12.5x |
| ui12-italic | ink band, 96 nets x 20 wide, 80,000 steps | 1,119,068 | 186.9 / 139.6 -> 13.0 / 9.5 | 14.4x/13.5x, 14.7x/13.8x (14.1x) | 0.49 -> 1.79 / 0.29 -> 1.18 | 11.9x |
| ui13 | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 227.2 / 168.0 -> 11.5 / 8.4 | 19.8x/19.6x, 20.1x/19.9x (19.9x) | 0.49 -> 1.54 / 0.29 -> 0.90 | 17.4x |
| ui14 | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 269.9 / 192.5 -> 14.5 / 9.4 | 18.6x/19.7x, 20.6x/20.3x (19.8x) | 0.49 -> 1.55 / 0.29 -> 0.85 | 16.9x |
| ui14-italic | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 256.9 / 192.9 -> 13.2 / 9.4 | 19.5x/18.7x, 20.5x/19.7x (19.6x) | 0.49 -> 1.49 / 0.29 -> 0.93 | 16.8x |
| ui15 | ink band, 96 nets x 20 wide, 80,000 steps | 1,119,068 | 286.2 / 214.9 -> 18.5 / 13.5 | 15.4x/14.3x, 15.9x/14.8x (15.1x) | 0.49 -> 1.78 / 0.29 -> 1.16 | 13.2x |
| ui15-italic | ink band, 96 nets x 16 wide, 80,000 steps | 864,092 | 298.6 / 213.0 -> 15.7 / 10.9 | 19.0x/18.6x, 19.5x/19.2x (19.1x) | 0.48 -> 1.63 / 0.31 -> 0.92 | 17.0x |
| ui19 | ink band, 96 nets x 20 wide, 80,000 steps | 1,119,068 | 652.2 / 482.8 -> 28.8 / 21.0 | 22.7x/21.2x, 22.9x/21.4x (22.0x) | 0.54 -> 1.78 / 0.33 -> 1.14 | 20.0x |
| ui20 | ink band, 96 nets x 16 wide, 160,000 steps | 864,092 | 748.2 / 538.2 -> 25.3 / 17.5 | 29.6x/29.2x, 30.7x/29.8x (29.8x) | 0.55 -> 1.51 / 0.32 -> 0.91 | 27.5x |
| ui21 | ink band, 32 nets x 24 wide, 80,000 steps | 466,792 | 847.5 / 618.4 -> 39.7 / 27.7 | 21.4x/20.9x, 22.3x/21.9x (21.6x) | 0.53 -> 0.87 / 0.33 -> 0.51 | 20.5x |

## Training

`python3 train/face_parts.py OUT --set uiEM[i] --band --groups K --width W --steps N --seeds 0,1` on one
GPU (torch 2.6, CUDA 12.4, TF32 off), the trainer's recipe unchanged: Adam 0.002 with a cosine schedule,
1,024 candidate points per character per step, the first 128 and the 128 nearest an edge fitted by mean
absolute error to the clamped field over tau; no unlabelled scalars. Pack seed 0 with
`train/pack.py --drawing-bundle weights/NAME.nrt font/ui-EM[-italic].txt weights/NAME-g0.json ...`, or
`train/pack.py --drawing weights/NAME.nrt weights/NAME-g0.json font/ui-EM.txt` for one net; `make
pack-faces-v1-small` repacks them all.

## Recipes that did not pass (kept as evidence, not shipped)

ui3 ink band, 96 nets x 12 wide, 80,000 steps (seed 0); ui3 ink band, 96 nets x 8 wide, 80,000 steps (seed 0, 1); ui5 ink band, 96 nets x 16 wide, 80,000 steps (seed 0); ui8 ink band, 96 nets x 16 wide, 80,000 steps (seed 1); ui8-italic ink band, 96 nets x 16 wide, 80,000 steps (seed 0); ui9 ink band, one net 48 wide, 80,000 steps (seed 0, 1); ui9 ink band, 96 nets x 12 wide, 80,000 steps (seed 0, 1); ui9 ink band, 96 nets x 8 wide, 80,000 steps (seed 0, 1); ui10 ink band, 32 nets x 16 wide, 80,000 steps (seed 0); ui10-italic ink band, 32 nets x 16 wide, 80,000 steps (seed 1); ui11-italic ink band, 32 nets x 16 wide, 80,000 steps (seed 1); ui12 ink band, 32 nets x 16 wide, 80,000 steps (seed 0, 1); ui12 ink band, 96 nets x 16 wide, 80,000 steps (seed 0); ui12-italic ink band, 32 nets x 16 wide, 80,000 steps (seed 0, 1); ui12-italic ink band, 96 nets x 16 wide, 80,000 steps (seed 0); ui13 ink band, 32 nets x 16 wide, 80,000 steps (seed 0, 1); ui14 ink band, one net 64 wide, 80,000 steps (seed 0, 1); ui14 ink band, 32 nets x 16 wide, 80,000 steps (seed 0, 1); ui14 ink band, 96 nets x 12 wide, 80,000 steps (seed 0, 1); ui14 ink band, 96 nets x 8 wide, 80,000 steps (seed 0, 1); ui14-italic ink band, 32 nets x 16 wide, 80,000 steps (seed 0, 1); ui14-italic ink band, 32 nets x 24 wide, 80,000 steps (seed 1); ui15 ink band, 32 nets x 16 wide, 80,000 steps (seed 0, 1); ui15 ink band, 32 nets x 24 wide, 80,000 steps (seed 1); ui15 ink band, 96 nets x 16 wide, 80,000 steps (seed 1); ui15-italic ink band, 32 nets x 16 wide, 80,000 steps (seed 0, 1); ui19 ink band, 48 nets x 20 wide, 80,000 steps (seed 1); ui19 ink band, 96 nets x 16 wide, 160,000 steps (seed 1); ui20 ink band, 48 nets x 20 wide, 80,000 steps (seed 1); ui21 ink band, one net 80 wide, 80,000 steps (seed 0, 1); ui21 ink band, 32 nets x 16 wide, 80,000 steps (seed 0, 1); ui21 ink band, 48 nets x 20 wide, 80,000 steps (seed 0, 1); ui21 ink band, 96 nets x 12 wide, 80,000 steps (seed 0, 1); ui21 ink band, 96 nets x 16 wide, 160,000 steps (seed 0, 1); ui21 ink band, 96 nets x 16 wide, 80,000 steps (seed 0, 1); ui21 ink band, 96 nets x 20 wide, 80,000 steps (seed 0); ui21 ink band, 96 nets x 8 wide, 80,000 steps (seed 0, 1).
