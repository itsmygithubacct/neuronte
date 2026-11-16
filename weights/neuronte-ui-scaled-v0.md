# Scalable desktop face v0 (`neuronte-ui-scaled-v0`, 17 to 32 px)

One drawing file that draws the desktop face at every em from 17 to 32 pixels, in place of one
pixel face per em, upright and (by the library's draw-time italic) italic. It is the ui-large
strokes (`font/ui-large.txt`) scaled to the em by the nets, with their stems snapped to whole
pixels. The owner chose to use it from 17 px up; from 1 to 16 px the hand pixel faces stay. No
default changes and every -v0 and -v1 pixel face is unchanged.

## What is in the file

- One bundle of 16 band-tiled distance nets, 96 x 96 x 96 wide (27,457 parameters each, 439,312 in
  all), one contiguous group of six characters per net, each drawing only ui-large's ink rows
  (`train/face_parts.py --band`). They are trained on the ui-large strokes at the ui-large pen
  (3/32 em).
- An advance table fitted to the hand faces from 17 to 32 px (`font/ui-scaled-advances.txt`).
- A letter edge table (format version 7): the straight edges of 60 of the 96 letters, probed from the
  strokes by `train/snap.py`, snapped in cells narrower than 33 px.

1,774,948 bytes. Printable ASCII and U+2026, regular and bold (bold is the library's one-pixel
smear, as for every desktop face).

## Why it snaps, and older libraries

With the 3/32 em pen, snapping gives 2-pixel stems at every em from 17 to 26 px and 3 from 27, the
hand faces' own stem widths. The same nets unsnapped draw stems of 1 to 3 pixels depending on the
em (light at 17 px, heavy at 23, 24 and 26), with no fewer wrong pixels overall. That is why the
snapped variant ships. `neuronte_set_snap(h, 0)` turns snapping off.

The letter edge table is new in this version of the library. An older library refuses the whole
file with `NEURONTE_ERR_FORMAT`; it never draws it unsnapped. A file without the table, every
other shipped file included, draws exactly as before.

## Advances

The library draws (steps x em + 50) / 100 pixels from one table in hundredths of an em, which is
linear in the em; the hand faces' whole-pixel advances are not. Per character and weight,
`train/fit_advances.py 17 32` takes the step with the least summed pixel error against the hand
faces over 17 to 32 px. Advances that then differ from the hand face, of 96 per weight, drawn minus
hand:

| em | regular | regular, by | bold | bold, by |
|---|---|---|---|---|
| 17 | 69 | -1: 69 | 84 | -2: 39, -1: 45 |
| 18 | 43 | -1: 39, +1: 4 | 56 | -1: 56 |
| 19 | 50 | -1: 43, +1: 7 | 68 | -2: 32, -1: 34, +1: 2 |
| 20 | 21 | -1: 2, +1: 19 | 6 | -1: 3, +1: 3 |
| 21 | 17 | -1: 1, +1: 16 | 5 | -2: 1, -1: 2, +1: 2 |
| 22 | 31 | +1: 31 | 7 | -1: 2, +1: 5 |
| 23 | 6 | -1: 1, +1: 5 | 21 | -1: 18, +1: 3 |
| 24 | 45 | +1: 45 | 34 | +1: 34 |
| 25 | 47 | +1: 47 | 20 | +1: 20 |
| 26 | 81 | +1: 79, +2: 2 | 66 | +1: 62, +2: 4 |
| 27 | 23 | -1: 19, +1: 4 | 31 | -1: 31 |
| 28 | 16 | -1: 6, +1: 10 | 0 | |
| 29 | 18 | -1: 13, +1: 5 | 16 | -1: 15, +1: 1 |
| 30 | 4 | -1: 2, +1: 2 | 5 | -1: 4, +1: 1 |
| 31 | 52 | -1: 52 | 43 | -1: 43 |
| 32 | 12 | -2: 2, -1: 10 | 19 | -1: 7, +1: 12 |

1,016 of 3,072 differ in all, none by more than 2 pixels. A consumer that wants the hand faces'
spacing exactly can lay out with the hand face's own table for that em (`train/pack.py --advances
font/ui-EM.txt OUT`, about 800 bytes per em).

## Italic

The same file draws italic with the library's draw-time italic (`NEURONTE_STYLE_ITALIC`), which
shears one column per four rows, the hand italics' slope. Its advances are
`neuronte-ui-scaled-italic-advances-v0.nrt` (800 bytes, an advance table alone), fitted the same
way to the hand italic faces from 17 to 32 px (`font/ui-scaled-italic-advances.txt`); 1,277 of 3,072
differ, by -2 to +3 pixels.

## How close it is to the hand faces

It is a different face, not a copy of the hand faces: their heights and shapes were fitted per em by
hand, and the scaled strokes keep one shape at every em. Wrong pixels per letter against
`font/ui-EM.txt` (upright) and `font/ui-EM-italic.txt` (draw-time italic), regular and bold, binary,
seed 0 (seed 1 within 0.1):

| em | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| upright | 30.3 | 22.1 | 15.6 | 19.5 | 21.5 | 42.5 | 28.1 | 27.1 | 29.8 | 23.6 | 72.0 | 69.4 | 52.6 | 71.3 | 89.6 | 74.8 |
| italic | 33.2 | 33.0 | 29.0 | 36.6 | 38.6 | 57.7 | 45.7 | 46.2 | 52.4 | 49.8 | 73.9 | 74.0 | 69.0 | 84.1 | 105.5 | 100.4 |

## Speed

A new handle drawing the 96 letters regular then bold, as a desktop builds its letter cells (ms,
median of 5 fresh handles), against the hand face it replaces (the newest file at that em); cached
redraw is the same for all (microseconds, within 5%).

| em | i7-10700F hand / scaled | i7-6820HQ hand / scaled |
|---|---|---|
| 17 | 223.6 / 126.3 | 217.2 / 132.9 |
| 18 | 294.5 / 139.9 | 278.6 / 144.9 |
| 19 | 28.6 / 147.3 | 28.6 / 165.2 |
| 20 | 25.2 / 161.9 | 24.9 / 178.4 |
| 21 | 38.3 / 182.7 | 37.9 / 197.3 |
| 22 | 383.8 / 191.9 | 354.1 / 211.1 |
| 23 | 404.6 / 206.1 | 428.6 / 228.6 |
| 24 | 30.4 / 63.4 | 31.5 / 70.6 |
| 25 | 296.6 / 69.5 | 284.1 / 76.8 |
| 26 | 125.6 / 73.0 | 122.1 / 80.6 |
| 27 | 35.8 / 79.2 | 38.7 / 86.5 |
| 28 | 39.8 / 81.5 | 41.6 / 92.4 |
| 29 | 42.3 / 89.3 | 44.5 / 99.4 |
| 30 | 36.6 / 99.6 | 36.1 / 108.1 |
| 31 | 200.6 / 102.0 | 206.0 / 112.1 |
| 32 | 213.0 / 110.9 | 219.3 / 121.8 |

It is faster than the wide hand faces (17, 18, 22, 23, 25, 26, 31, 32 px) and 2 to 7 times slower
than the small ones (19 to 21, 24, 27 to 30 px). Below 24 px the library samples each pixel 2 x 2,
which is why 17 to 23 cost more. The download: one
file of 1,774,948 bytes and an 800-byte italic table in place of 32 files of 17,362,624 bytes (the
newest upright and italic hand face at each em from 17 to 32).

## Training and checks

Trained on one RTX 3070, seeds 0 and 1 together, in 317 seconds:

    python3 train/face_parts.py OUT --set uilarge --band --groups 16 --width 96 --steps 40000 \
        --candidates 2048 --near 384 --clamp 0.25 --name L3-bg16w96-40k-n384-c25

then `train/pack.py --drawing-bundle neuronte-ui-scaled-v0.nrt font/ui-scaled-advances.txt MEMBERS...
--letter-edges uilarge --snap-below 33`. The members' `sources_sha256` name the trainer as it was then;
it has since only gained `--pen`, whose default leaves this recipe unchanged. No seed-choice rule
was declared before training; seed 0 is the packed file by this repository's convention, and seed
1's members (`neuronte-ui-scaled-v0.seed1-gG.json`) are kept. `make test-ui-scaled` (part of `make
test`) repacks both seeds and checks every snapped letter at every em from 8 to 32 against an
independent float64 reference (`tests/check_letter_snap.py`), and that from 33 px each draws as its
nets without the table.
