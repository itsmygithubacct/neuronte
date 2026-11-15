# Desktop faces v1: ui33 to ui39 and ui43, cut into small nets that draw only their own rows

Faster replacements for the 512-wide desktop faces `neuronte-ui33-v0` to `neuronte-ui39-v0` and `neuronte-ui43-v0` (repository faces; the operating system installs faces up to 32 px and the scalable face above). Each `neuronte-uiEM-v1.nrt` is a drawing file (version 5) of one bundle (version 2) and the face's advance table, built exactly as the 24-30 px v1 faces (`neuronte-ui-v1.md`): the bundle routes each of the 96 characters (printable ASCII and the ellipsis) to the member trained on it, members being contiguous groups of characters in code-point order, and each member is a tiled net (version 6) whose trained net draws only the face's em rows (from `font/ui-tops.json`), with a width-1 empty net (output bias -8) above and below. Drawings, pen, grid (256), tau (.15) and thresholds are unchanged; no calibration offset; no seed or member mixed between seeds or recipes.

| File | Members x width | Steps | Trained parameters | Bytes |
|---|---|---:|---:|---:|
| `neuronte-ui33-v1` | 16 x 64 | 80,000 | 227,344 | 925,032 |
| `neuronte-ui34-v1` | 32 x 48 | 80,000 | 291,872 | 1,197,928 |
| `neuronte-ui35-v1` | 32 x 48 | 80,000 | 291,872 | 1,197,928 |
| `neuronte-ui36-v1` | 16 x 64 | 80,000 | 227,344 | 925,032 |
| `neuronte-ui37-v1` | 16 x 64 | 80,000 | 227,344 | 925,032 |
| `neuronte-ui38-v1` | 32 x 48 | 80,000 | 291,872 | 1,197,928 |
| `neuronte-ui39-v1` | 32 x 48 | 80,000 | 291,872 | 1,197,928 |
| `neuronte-ui43-v1` | 32 x 48 | 80,000 | 291,872 | 1,197,928 |

The v0 files are 1 x 512, 572,417 parameters and 2,290,704 bytes each. Each member also carries its empty net (97 parameters).

## The gate

Declared before any candidate was trained: a recipe qualified only if seeds 0 and 1 trained with it BOTH passed `tests/check_reference.py --drawing-bundle` on the packed file: every character regular and bold through `neuronte_draw_text()` with `neuronte_set_binary(1)` exactly the drawing's pixels, the pen moving by the drawing's advance, the router sending every character to the member that knows it, C coverage against float64 numpy within 1e-3, and the file byte-equal to the packer's output. Seed 0 is shipped; seed 1's members are kept beside it (`NAME.seed1-pG.json`, `NAME.seed1.scores.json`), and `make test-faces-v1-h512` repacks and checks both seeds of every face.

Recipes tried, each with seeds 0 and 1: 16 x 64 and 32 x 48 at 80,000 steps for every face, and 8 x 128 at 40,000 steps for ui43 (after its 16 x 64 failed a seed). Recipes that failed on at least one seed (kept with the research records): ui33-bg32w48-80k seed 0 (U+0040 weight 0: 1 pixels are not the face's; U+0040 weight 1: 1 pixels are not the face's); ui33-bg32w48-80k seed 1 (U+0040 weight 0: 1 pixels are not the face's); ui36-bg32w48-80k seed 0 (U+0040 weight 0: 1 pixels are not the face's); ui37-bg32w48-80k seed 1 (U+0045 weight 0: 1 pixels are not the face's; U+0045 weight 1: 1 pixels are not the face's); ui43-bg16w64-80k seed 0 (U+0040 weight 0: 1 pixels are not the face's; U+0040 weight 1: 1 pixels are not the face's). Every other recipe tried passed on both seeds (ui43's 8 x 128 passed, 13.7x faster than v0, and was not chosen). Among the recipes that passed, the shipped one is the fastest by the geometric mean of its cold-draw speed-up over v0 on two hosts for both seeds (a recipe within 5% of the fastest would go to the smaller file).

## Speed

Measured with the kilix-bench face experiment (`--suite neuronte --face-experiment`, kilix-bench 9b44df1), as a desktop draws a face: a fresh process opens the file, then for each of the 96 characters asks the regular and bold advance and draws it once at the face's em with binary on, uncached. One pinned core, one warmup and 10 measured rounds in shuffled order, medians, every raw trial kept; every case was also checked exact (96 characters) against the drawing's pixels and against a float64 reference of the file. Cold draw is in ms per character (x 96 for a whole face); seed 0 / seed 1. v0 and v1 were measured in the same run.

| Face | v0, Intel i7-6820HQ | v1 | v0, Intel i7-10700F | v1 | Speed-up (geomean) | Open v0, ms (i7-6820HQ / i7-10700F) | Open v1, ms, slower seed |
|---|---:|---:|---:|---:|---:|---:|---:|
| ui33 | 25.49 | 0.750 / 0.845 | 20.07 | 0.550 / 0.611 | 33.3x | 4.68 / 3.35 | 1.38 / 0.91 |
| ui34 | 27.25 | 0.570 / 0.608 | 21.50 | 0.412 / 0.437 | 48.4x | 4.72 / 3.23 | 1.72 / 1.11 |
| ui35 | 27.65 | 0.596 / 0.631 | 21.76 | 0.428 / 0.461 | 47.0x | 4.69 / 3.34 | 1.76 / 1.11 |
| ui36 | 29.34 | 0.888 / 0.998 | 23.10 | 0.644 / 0.727 | 32.4x | 4.67 / 3.30 | 1.38 / 0.90 |
| ui37 | 30.58 | 0.940 / 1.051 | 24.26 | 0.682 / 0.762 | 32.2x | 4.68 / 3.23 | 1.38 / 0.90 |
| ui38 | 32.24 | 0.695 / 0.745 | 25.58 | 0.501 / 0.534 | 47.1x | 4.69 / 3.29 | 1.77 / 1.08 |
| ui39 | 32.95 | 0.731 / 0.778 | 26.11 | 0.527 / 0.565 | 45.7x | 4.72 / 3.23 | 1.79 / 1.07 |
| ui43 | 39.66 | 0.867 / 0.923 | 31.33 | 0.634 / 0.670 | 46.2x | 4.73 / 3.21 | 1.75 / 1.07 |

Primed (cached) draw, ms per character: v0 0.006-0.013, v1 0.006-0.013. Full results: the research records of this work (round 2 of the faces-h512-rest benchmark).

The -v0 files are unchanged and still shipped; nothing that loads a face by its -v0 name changes. A consumer that wants these faces opens the -v1 names.
