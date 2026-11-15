# Narrower desktop faces: the H192 and H256 sizes, v1

These are new drawing files for 18 desktop faces whose v0 nets are 192 or 256 wide. Each `neuronte-uiEM[-italic]-v1.nrt` holds one narrower net and the same advance table as v0. The v0 files are unchanged and are still what the installer and Kilix 95 load; using a v1 file means changing the consumer's weight path.

## What changed

Only the hidden width and the training steps. The drawings (`font/ui-EM.txt`, `font/ui-EM-italic.txt`), pen, target grid 256, tau 0.15, `--unlabelled 0`, trainer and packer are the ones at a99fe42. A net costs about 2H² + 94H multiply-adds per sample, and a desktop draws every glyph once into its letter cells, at 2 × 2 samples per pixel below 24 px. So a narrower net makes a face's cells faster to build. That cost is paid at start-up, when caches are built or rebuilt.

## Acceptance

Gates were declared before any candidate was scored. Both seeds, 0 and 1, of one recipe must reproduce all 96 source glyphs exactly at the native em, regular and bold, with their advances. The check is `tests/check_reference.py build/libneuronte.so --drawing FILE.nrt FILE.json font/...`, the same as v0's. It also requires C/NumPy coverage within 1e-3 and the packed bytes to be exactly what `train/pack.py` makes. The selected recipe is the narrowest tested width at which both seeds pass; at equal width, the fewer steps. The packed file is seed 0. Seed 1's weights are `.seed1.json`, and `make test-faces-v1-192-256` packs seed 1 into `build/` and holds it to the same gate. A v1 file had to be faster than v0 to be kept. This was measured on both x86 hosts for both seeds. Every face here passed on both.

## Results

Cold draw is the time to draw all 96 glyphs once from a fresh handle, as a desktop builds a face's letter cells: `neuronte_text_width` regular and bold, then one binary `neuronte_draw_text` per glyph at the native em. It is the median of 10 rounds, after 1 warmup, in a fresh process per job, pinned to one core, in shuffled order (kilix-bench 9b44df1 face experiment). Each cell gives v0 → v1 seed 0 / seed 1 in milliseconds, with the seed-0 speed-up in brackets. Open, warm-draw and coverage figures are in `neuronte-ui-v1-192-256.validation.json`.

| File | em | v0 width | v1 width | steps | parameters | bytes | exact, both seeds | cold draw, Intel Core i7-6820HQ | cold draw, Intel Core i7-10700F |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| `neuronte-ui13-italic-v1` | 13 | 192 | 96 | 40,000 | 27,457 | 110,864 | 96 / 96 | 370 → 149 / 153 (2.48x) | 278 → 110 / 113 (2.52x) |
| `neuronte-ui16-v1` | 16 | 192 | 128 | 40,000 | 44,801 | 180,240 | 96 / 96 | 614 → 316 / 333 (1.94x) | 457 → 234 / 246 (1.96x) |
| `neuronte-ui16-italic-v1` | 16 | 192 | 96 | 80,000 | 27,457 | 110,864 | 96 / 96 | 655 → 222 / 221 (2.95x) | 497 → 164 / 163 (3.03x) |
| `neuronte-ui17-v1` | 17 | 256 | 128 | 80,000 | 44,801 | 180,240 | 96 / 96 | 1142 → 333 / 352 (3.43x) | 884 → 249 / 261 (3.55x) |
| `neuronte-ui17-italic-v1` | 17 | 256 | 128 | 80,000 | 44,801 | 180,240 | 96 / 96 | 1090 → 343 / 363 (3.18x) | 833 → 254 / 272 (3.27x) |
| `neuronte-ui18-v1` | 18 | 192 | 96 | 80,000 | 27,457 | 110,864 | 96 / 96 | 780 → 264 / 280 (2.95x) | 583 → 194 / 206 (3.00x) |
| `neuronte-ui18-italic-v1` | 18 | 192 | 128 | 80,000 | 44,801 | 180,240 | 96 / 96 | 796 → 378 / 405 (2.11x) | 599 → 281 / 301 (2.13x) |
| `neuronte-ui19-italic-v1` | 19 | 256 | 128 | 40,000 | 44,801 | 180,240 | 96 / 96 | 1328 → 423 / 468 (3.14x) | 1000 → 317 / 347 (3.16x) |
| `neuronte-ui20-italic-v1` | 20 | 192 | 128 | 80,000 | 44,801 | 180,240 | 96 / 96 | 979 → 451 / 510 (2.17x) | 741 → 333 / 375 (2.23x) |
| `neuronte-ui21-italic-v1` | 21 | 256 | 128 | 80,000 | 44,801 | 180,240 | 96 / 96 | 1665 → 488 / 537 (3.41x) | 1284 → 365 / 402 (3.51x) |
| `neuronte-ui22-v1` | 22 | 192 | 128 | 80,000 | 44,801 | 180,240 | 96 / 96 | 1154 → 536 / 580 (2.15x) | 878 → 399 / 434 (2.20x) |
| `neuronte-ui22-italic-v1` | 22 | 256 | 160 | 80,000 | 66,241 | 266,000 | 96 / 96 | 1934 → 786 / 818 (2.46x) | 1478 → 583 / 611 (2.53x) |
| `neuronte-ui23-v1` | 23 | 192 | 128 | 80,000 | 44,801 | 180,240 | 96 / 96 | 1229 → 567 / 582 (2.17x) | 937 → 421 / 433 (2.22x) |
| `neuronte-ui23-italic-v1` | 23 | 256 | 160 | 40,000 | 66,241 | 266,000 | 96 / 96 | 1955 → 873 / 905 (2.24x) | 1477 → 653 / 674 (2.26x) |
| `neuronte-ui25-v1` | 25 | 192 | 160 | 40,000 | 66,241 | 266,000 | 96 / 96 | 383 → 279 / 282 (1.37x) | 286 → 207 / 209 (1.38x) |
| `neuronte-ui25-italic-v1` | 25 | 256 | 160 | 80,000 | 66,241 | 266,000 | 96 / 96 | 602 → 267 / 280 (2.25x) | 459 → 198 / 209 (2.32x) |
| `neuronte-ui26-v1` | 26 | 192 | 128 | 80,000 | 44,801 | 180,240 | 96 / 96 | 404 → 197 / 215 (2.06x) | 305 → 145 / 158 (2.10x) |
| `neuronte-ui26-italic-v1` | 26 | 256 | 160 | 80,000 | 66,241 | 266,000 | 96 / 96 | 706 → 290 / 314 (2.44x) | 532 → 212 / 231 (2.51x) |

Trained with `python3 train/train.py OUT.json --set uiEM[i] --width W --steps N --seed S --unlabelled 0 --score-sizes EM --scores-out SCORES.json`. Training used CUDA: a Quadro RTX 3000 (torch 2.6.0+cu124, NumPy 2.5.4) and a rented RTX 3090 (torch 2.6.0+cu124, NumPy 2.2.2). The source hashes in each JSON bind the recipe. Repack with `make pack-faces-v1-192-256`.

## Narrower recipes that failed

These were tried and rejected under the same gate; they are listed here so that no one retries them as new: ui13-italic w64 80k seed 0: 93/96; ui13-italic w64 80k seed 1: 93/96; ui16 w96 40k seed 0: 92/96; ui16 w96 80k seed 1: 95/96; ui16-italic w96 40k seed 0: 93/96; ui17 w128 40k seed 0: 95/96; ui17 w160 40k seed 0: 95/96; ui17 w96 40k seed 0: 94/96; ui17 w96 40k seed 1: 93/96; ui17 w96 80k seed 0: 95/96; ui17 w96 80k seed 1: 94/96; ui17-italic w128 40k seed 1: 95/96; ui17-italic w96 80k seed 0: 93/96; ui18 w96 40k seed 0: 92/96; ui18-italic w128 40k seed 0: 95/96; ui18-italic w96 40k seed 0: 88/96; ui19-italic w96 80k seed 0: 93/96; ui19-italic w96 80k seed 1: 94/96; ui20-italic w128 40k seed 0: 94/96; ui20-italic w96 40k seed 0: 78/96; ui21-italic w128 40k seed 0: 93/96; ui22 w128 40k seed 0: 93/96; ui22 w96 40k seed 0: 84/96; ui22-italic w128 40k seed 0: 91/96; ui22-italic w128 80k seed 0: 93/96; ui22-italic w128 80k seed 1: 95/96; ui22-italic w160 40k seed 1: 95/96; ui23 w128 40k seed 0: 92/96; ui23 w96 40k seed 0: 79/96; ui23-italic w128 40k seed 0: 93/96; ui23-italic w128 80k seed 0: 94/96; ui25 w128 40k seed 0: 90/96; ui25 w128 80k seed 0: 95/96; ui25 w128 80k seed 1: 95/96; ui25 w96 40k seed 0: 83/96; ui25-italic w128 40k seed 0: 82/96; ui25-italic w160 40k seed 0: 95/96; ui26 w128 40k seed 0: 89/96; ui26 w96 40k seed 0: 66/96; ui26-italic w128 40k seed 0: 80/96; ui26-italic w160 40k seed 0: 91/96. The ui16 and ui17 pilots trained both seeds at every width. In the 40,000-step ladders after the pilots, a width where seed 0 failed was not retried with seed 1; every 80,000-step run trained both seeds. A narrower width at 80,000 steps was tried only where the 40,000-step ladder had passed one step wider, or had missed by at most one pixel.

## Limits

Exact reproduction at the native em is the claim. Other sizes are not part of it: the desktop draws each em with its own file. Both seeds pass, which shows that each recipe reproduces exactly on more than one seed; it does not show that every seed would. The speed figures are for these two CPUs.
