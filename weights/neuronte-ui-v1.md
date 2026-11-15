# Desktop faces v1: ui24 to ui30, cut into small nets that draw only their own rows

Nine faster replacements for the 384-wide desktop faces `neuronte-ui24-v0`,
`-ui24-italic-v0`, `-ui27-v0`, `-ui28-v0`, `-ui28-italic-v0`, `-ui29-v0`,
`-ui29-italic-v0`, `-ui30-v0` and `-ui30-italic-v0`. Each `neuronte-uiEM[-italic]-v1.nrt`
is a drawing file (version 5) of one bundle (version 2) and the face's
advance table. The bundle routes each of the face's 96 characters (printable
ASCII and the ellipsis) to one of its members by the characters the member
was trained on; the members are contiguous groups of 6 characters (16 groups)
or of 12 (8 groups), in code-point order.

Every member is a tiled net (version 6) of three rows: above and below the
face's em rows (cell rows 0 to UI_TOP and UI_TOP + em to 2 em, from
`font/ui-tops.json`) an empty net of width 1 whose output bias is -8, so it is
outside the ink everywhere; between them the trained net, which sees those em
rows as its whole cell. A pixel face has no ink outside its em rows, so the
trained net spends all its width there and is never evaluated elsewhere at the
cost of a full net. Nothing in the drawings, pen, grid (256), tau (.15) or
thresholds changed; there is no calibration offset, and no seed or member was
mixed between seeds or recipes.

| File | Members x width | Steps | Trained parameters | Bytes |
|---|---|---:|---:|---:|
| `neuronte-ui24-v1` | 16 x 48 | 80,000 | 145,936 | 599,400 |
| `neuronte-ui24-italic-v1` | 16 x 48 | 80,000 | 145,936 | 599,400 |
| `neuronte-ui27-v1` | 16 x 48 | 80,000 | 145,936 | 599,400 |
| `neuronte-ui28-v1` | 16 x 48 | 80,000 | 145,936 | 599,400 |
| `neuronte-ui28-italic-v1` | 16 x 64 | 40,000 | 227,344 | 925,032 |
| `neuronte-ui29-v1` | 16 x 48 | 80,000 | 145,936 | 599,400 |
| `neuronte-ui29-italic-v1` | 16 x 48 | 80,000 | 145,936 | 599,400 |
| `neuronte-ui30-v1` | 16 x 64 | 40,000 | 227,344 | 925,032 |
| `neuronte-ui30-italic-v1` | 8 x 96 | 80,000 | 219,656 | 886,888 |

The v0 files are 1 x 384, 331,009 parameters and 1,325,072 bytes each. Each
member also carries its empty net (97 parameters).

## The gate

A recipe qualified only if seeds 0 and 1 trained with it BOTH passed: the
trainer's own score at the face's em with one sample per pixel (exact == 96
characters against the drawing), and `tests/check_reference.py --drawing-bundle`
on the packed file: every character regular and bold through
`neuronte_draw_text()` with `neuronte_set_binary(1)` exactly the drawing's
pixels, the pen moving by the drawing's advance, the router sending every
character to the member that knows it, C coverage against float64 numpy
within 1e-3 (largest seen 2.5e-6), and the file byte-equal to the packer's
output. Seed 0 is shipped; seed 1's members are kept beside it
(`NAME.seed1-pG.json`, `NAME.seed1.scores.json`), and `make test-faces-v1`
repacks and checks both seeds of every face.

Recipes that failed for a face (kept with the research records): 4 x 128 at
40k steps for ui29, ui29-italic, ui30 and ui30-italic; 2 x 192 for ui29,
ui29-italic, ui30-italic; 8 x 96 at 40k for ui28-italic, ui30, ui30-italic;
8 x 64 for ui24, ui27, ui28 and ui28-italic; 16 x 64 for ui30-italic, also at 80k;
16 x 48 at 80k for ui28-italic, ui30, ui30-italic; 16 x 32 at 80k for every face
tried. Among the recipes that passed, the shipped one is the fastest by the
geometric mean of its cold-draw speed-up over v0 on two hosts for both seeds.

## Speed

Measured with the kilix-bench face experiment (`--suite neuronte
--face-experiment`, kilix-bench 9b44df1), as the desktop draws a face: a fresh
process opens the file, then for each of the 96 characters asks the regular and
bold advance and draws it once at the face's em with binary on, uncached. One
pinned core, one warmup and 10 measured rounds in shuffled order, medians,
every raw trial kept; every case was also checked exact (96 characters)
against the drawing's pixels and against a float64 reference of the file.
Cold draw is in ms per character (x 96 for a whole face); seed 0 / seed 1.

| Face | v0, Intel i7-6820HQ | v1 | v0, Intel i7-10700F | v1 | Speed-up (geomean) | Open v0, ms (i7-6820HQ / i7-10700F) | Open v1, ms, slower seed |
|---|---:|---:|---:|---:|---:|---:|---:|
| ui24 | 9.39 | 0.321 / 0.348 | 7.38 | 0.230 / 0.249 | 29.4x | 2.30 / 1.56 | 0.99 / 0.59 |
| ui24-italic | 9.63 | 0.325 / 0.353 | 7.58 | 0.233 / 0.254 | 29.7x | 2.30 / 1.64 | 1.00 / 0.60 |
| ui27 | 11.31 | 0.394 / 0.430 | 8.85 | 0.286 / 0.309 | 28.6x | 2.29 / 1.55 | 0.98 / 0.58 |
| ui28 | 11.71 | 0.423 / 0.456 | 9.18 | 0.304 / 0.329 | 27.8x | 2.29 / 1.56 | 0.99 / 0.60 |
| ui28-italic | 12.31 | 0.606 / 0.686 | 9.64 | 0.441 / 0.494 | 19.9x | 2.31 / 1.56 | 1.43 / 0.87 |
| ui29 | 12.99 | 0.569 / 0.578 | 10.14 | 0.416 / 0.422 | 23.4x | 2.32 / 1.53 | 0.99 / 0.58 |
| ui29-italic | 11.51 | 0.567 / 0.588 | 8.96 | 0.415 / 0.429 | 20.6x | 2.27 / 1.56 | 0.98 / 0.60 |
| ui30 | 13.65 | 0.659 / 0.745 | 10.69 | 0.480 / 0.540 | 20.2x | 2.29 / 1.63 | 1.40 / 0.87 |
| ui30-italic | 13.97 | 1.079 / 1.243 | 10.91 | 0.791 / 0.912 | 12.4x | 2.28 / 1.55 | 1.29 / 0.84 |

Primed (cached) draws are the same for v0 and v1 (3 to 7 microseconds per
character). The two hosts held the shared benchmark lock for the whole run;
the library was built from this tree's runtime, the drawing-file routing it merges.

## Use

A consumer that names the v0 files needs to name the v1 files to use them;
nothing here changes a default. `neuronte-ui-large-v0` stays the face above
32 px: no faster replacement passed its gates (each band recipe beat its soft
error at every em but fell just below its overlap at 32 px on a seed).

Train one face with `python3 train/face_parts.py OUT --set ui24 --band --groups 16
--width 48 --steps 80000 --seeds 0,1`; pack with `make pack` (or the
`train/pack.py --drawing-bundle` lines it holds); check with `make test-faces-v1`.
