# term-marks-v1: 166 combining marks, Lao marks and small gaps, on their own

`neuronte-term-marks-v1.nrt` is a terminal bundle for characters that no
earlier bundle was trained on and that a terminal meets in ordinary text:

- the combining diacritical marks, U+0300 to U+036F (108 of the 112);
- the Lao vowel signs, tone marks and other marks that sit over or under a
  letter, and the Lao ellipsis (18);
- four raised modifier letters, U+1DB4 to U+1DB7;
- the soft hyphen U+00AD, the typographic spaces U+2000 to U+200A, U+202F
  and U+205F, the combining grapheme joiner U+034F and the interlinear
  annotation characters U+FFF9 to U+FFFB (drawn blank);
- 19 signs a terminal gives one cell: U+25FD, U+25FE, U+2614, U+2615, the
  twelve zodiac signs U+2648 to U+2653, U+267F, U+2693 and U+26A1.

In `neuronte-split-v9` each of them goes to the router's gate and is drawn by
a net that never saw it. With this file a terminal draws a combining mark
over the letter before it, in that letter's cell, and draws the signs in one
cell where `neuronte-wide-symbols-v1` draws them for two.

It is a **standalone** bundle: 26 known-only group nets and one blank net,
1,484,368 bytes, with no copy of split-v9 in it. A program opens it beside
split-v9 and asks it first (see "What a consumer changes"). It is not a
default and replaces nothing.

| Characters | Training set | Group nets trained | In the bundle | Gates v2.3 |
|---|---|---:|---:|---|
| 42 of 42: marks above | `tmkA` | 7 | 7 | 7 of 7 groups passed |
| 49 of 49: marks below, and overlays | `tmkB` | 7 | 7 | 7 of 7 groups passed |
| 38 of 42: marks joining two letters, the medieval letters above, modifier letters, blanks, soft hyphen | `tmkJ` | 5 | 5 | 4 of 5 groups passed; 1 halved, 1 of 2 halves passed |
| 18 of 18: Lao marks | `tmkL` | 3 | 3 | 3 of 3 groups passed |
| 19 of 19: signs in one cell | `tmkS` | 4 | 4 | 4 of 4 groups passed |

**Four characters are left untrained:** U+0360 (double tilde), U+0361
(double inverted breve), U+0362 (double rightwards arrow below) and U+0363
(combining small a). Their group failed one rule with both seeds: at 6×12
the net's U+0363 is nearer the drawing of U+0366 (combining small o) than
its own. It was trained again as two halves, as the method says; the half
with these four failed the same rule with both seeds and is left out. The
drawing itself tells U+0363 from U+0366 at 6×12; the nets did not. A
program that asks this file for them gets `neuronte_untrained() == 1`.

**Where a mark is drawn.** A terminal puts a combining mark in the cell of
the letter before it and draws it over that letter, so each mark is drawn
alone in a cell, where it falls on a lowercase letter: marks above in
y 3.3 to 5.6 of the 20-unit cell (just over the x-height), marks below in
16.6 to 19.3, overlays across the middle of the x-height, all centred.
Over a capital a mark above touches the letter's top. The 32 marks that
`font/marks.txt` draws for the precomposed accented letters are those
drawings, so a mark typed after a letter looks like the mark of the
precomposed letter. A mark that joins two letters (U+035C to U+035F, and
the three left out) is drawn as its half over the first letter, from the
middle of the cell to its right edge. U+0363 to U+036F are the letters of
`font/strokes.txt` made small into the band of the marks above.

**The signs.** The 19 signs are `neuronte-wide-symbols-v1`'s drawings, their
square box put in the cell's width on the maths line. They are small at
small sizes (an anchor in 8×16 is about seven pixels wide); the two-cell
drawings stay in the wide bundle for a program that gives them two cells.

**Blanks.** The 13 spaces, U+034F and U+FFF9 to U+FFFB are trained to draw
nothing, so a terminal that draws every character through Neuronte shows an
empty cell and not the hollow box of an untrained character. Each has no
pixel above 0.25 at 8×16 or 16×32 (`make test-term-marks-v1` checks it).

**What is not sure about the drawings.** No font was read to make or check
them; each is drawn from the character's Unicode name and what its shape is
known to be. The Lao marks are drawn from memory of their general shape and
should be checked by a reader of Lao. `font/term-marks.txt` carries a note
beside every drawing that is not sure (17 notes, 9 of them Lao).

## Gates

The verdicts are those of gates v2.3 (`gates-v2.3.json`, sha256
`2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`), as
`neuronte-term-rest-v1` was judged, declared for this bundle before any net
was trained. Every group is judged as symbols. Counted at 6×12, 8×16,
10×20, 12×24, 16×32, 24×48 and 48×96. The nearest drawing is looked for
among all 170 drawings of this bundle. Two limits were eased to the perfect
drawing's own score with 10% of room (a 99th-percentile error of `tmkS` g0
at 10×20 and of `tmkS` g2 at 8×16); the validation record lists both.

## What a consumer changes

Nothing, until it opens this file. It does not replace split-v9 and holds
none of its characters; `tests/check_bundle_lists.py` checks that no two
listed bundles, and no listed bundle and split-v9, share a trained scalar.

```c
neuronte_open_file("neuronte-split-v9.nrt", &base);
neuronte_open_file("neuronte-term-marks-v1.nrt", &marks);
/* for each scalar c */
font = neuronte_untrained(marks, c) ? base : marks;
```

`neuronte_untrained(marks, c)` is 0 for exactly the 166 characters in
`neuronte-term-marks-v1.list.txt` and 1 for every other scalar. A terminal
draws a cell's marks over its base character, each as a whole-cell mask.
The file needs the current runtime (version 2 bundles, 128-member limit).
It has 27 members.

## Recipe

- **Drawings.** `font/term-marks.txt` lists every character, set by set, in
  training order, and draws those with strokes; `train/term_marks.py` makes
  the rest: the marks of `font/marks.txt`, the small letters, the modifier
  letters (from `font/term-letters.txt`), U+0EBC (from term-rest's lo), the
  blanks, the soft hyphen and the one-cell signs.
- **Sets and groups.** Five sets; each cut in order into group nets of 2 to
  9 characters (26 in all, 27 trained with the two halves).
- **Training.** `train/split_expert.py train --mode repertoire --partition
  contiguous`, unchanged: hidden width 64, 120,000 steps, the project
  teacher (grid 256), seeds 0 and 1. A halved group: the set `NAMErI` of
  that group's characters, two parts, the rest the same. No wider retry.
  Two sets were trained on an RTX 3070 and the rest on rented RTX 3090s.
- **Selection.** A net ships when both seeds pass, as the seed with the
  lower mean error at 8×16, 16×32 and 48×96. Only the shipped seed's JSON
  is in `weights/`; the other seed's hash and measurements are in the
  validation record.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from
  each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
make pack-term-marks-v1    # rebuilds the .nrt byte for byte from the group nets
make test-term-marks-v1
```

## Checks

`make test-term-marks-v1` (part of `make test`): every group net against
the float64 reference; the bundle rebuilt byte for byte; its table exactly
`neuronte-term-marks-v1.list.txt`, which is `font/term-marks.txt` less the
half left out; every scalar from U+0000 to U+10FFFF routed as the table
says; pixels through the bundle equal to each group net alone at 19 cell
sizes and with one sample a pixel; ink at 16×32 for every drawn character
and none above 0.25 for the blanks; `test_api --standalone`; and the
validation record: only nets whose two seeds passed gates v2.3 are in the
bundle, each as the selected seed.

## Results by net

Mean error against the teacher at 8×16, 16×32 and 48×96 and mean overlap at 8×16 and 6×12, for the shipped seed (for a net not in the bundle: seed 0).

| Net | Characters | Gates v2.3 | Rules missed (seed 0 / seed 1) | Limits eased | In the bundle | Mean error | Overlap 8×16 | Overlap 6×12 |
|---|---|---|---|---:|---|---|---:|---:|
| `tmkA` g0 | U+0300..U+0305 | passed | 0 / 0 | 0 | seed 1 | 0.0018 0.0007 0.0004 | 1.000 | 0.967 |
| `tmkA` g1 | U+0306..U+030B | passed | 0 / 0 | 0 | seed 1 | 0.0013 0.0006 0.0004 | 1.000 | 1.000 |
| `tmkA` g2 | U+030C..U+0311 | passed | 0 / 0 | 0 | seed 1 | 0.0017 0.0010 0.0005 | 0.944 | 0.833 |
| `tmkA` g3 | U+0312..U+0315 U+031A U+031B | passed | 0 / 0 | 0 | seed 1 | 0.0009 0.0006 0.0003 | 1.000 | 1.000 |
| `tmkA` g4 | U+033D..U+0342 | passed | 0 / 0 | 0 | seed 0 | 0.0020 0.0011 0.0005 | 1.000 | 0.917 |
| `tmkA` g5 | U+0343 U+0344 U+0346 U+034A..U+034C | passed | 0 / 0 | 0 | seed 1 | 0.0020 0.0011 0.0006 | 1.000 | 0.972 |
| `tmkA` g6 | U+0350..U+0352 U+0357 U+0358 U+035B | passed | 0 / 0 | 0 | seed 0 | 0.0013 0.0006 0.0004 | 0.917 | 0.944 |
| `tmkB` g0 | U+0316..U+0319 U+031C..U+031E | passed | 0 / 0 | 0 | seed 1 | 0.0018 0.0008 0.0004 | 0.905 | 1.000 |
| `tmkB` g1 | U+031F..U+0325 | passed | 0 / 0 | 0 | seed 0 | 0.0013 0.0007 0.0003 | 0.907 | 1.000 |
| `tmkB` g2 | U+0326..U+032C | passed | 0 / 0 | 0 | seed 1 | 0.0017 0.0007 0.0004 | 0.964 | 1.000 |
| `tmkB` g3 | U+032D..U+0333 | passed | 0 / 0 | 0 | seed 1 | 0.0026 0.0014 0.0006 | 1.000 | 0.929 |
| `tmkB` g4 | U+0334..U+033A | passed | 0 / 0 | 0 | seed 0 | 0.0024 0.0010 0.0006 | 1.000 | 0.714 |
| `tmkB` g5 | U+033B U+033C U+0345 U+0347..U+0349 U+034D | passed | 0 / 0 | 0 | seed 0 | 0.0024 0.0012 0.0005 | 0.919 | 0.857 |
| `tmkB` g6 | U+034E U+0353..U+0356 U+0359 U+035A | passed | 0 / 0 | 0 | seed 0 | 0.0022 0.0007 0.0005 | 0.984 | 1.000 |
| `tmkJ` g0 | U+035C..U+0363 | **failed** | 1 / 1 | 0 | no: halved | 0.0014 0.0008 0.0004 | 0.975 | 0.927 |
| `tmkJr0` g0 (half) | U+035C..U+035F | passed | 0 / 0 | 0 | seed 1 | 0.0015 0.0007 0.0003 | 0.950 | 1.000 |
| `tmkJr0` g1 (half) | U+0360..U+0363 | **failed** | 1 / 1 | 0 | no: left out | 0.0014 0.0008 0.0004 | 1.000 | 0.938 |
| `tmkJ` g1 | U+0364..U+036B | passed | 0 / 0 | 0 | seed 0 | 0.0023 0.0010 0.0005 | 0.957 | 0.927 |
| `tmkJ` g2 | U+036C..U+036F U+1DB4..U+1DB7 U+00AD | passed | 0 / 0 | 0 | seed 0 | 0.0030 0.0010 0.0007 | 0.915 | 0.907 |
| `tmkJ` g3 | U+034F U+2000..U+2006 | passed | 0 / 0 | 0 | seed 0 | 0.0000 0.0000 0.0000 | 1.000 | 1.000 |
| `tmkJ` g4 | U+2007..U+200A U+202F U+205F U+FFF9..U+FFFB | passed | 0 / 0 | 0 | seed 0 | 0.0000 0.0000 0.0000 | 1.000 | 1.000 |
| `tmkL` g0 | U+0EAF U+0EB1 U+0EB4..U+0EB7 | passed | 0 / 0 | 0 | seed 0 | 0.0025 0.0012 0.0006 | 0.955 | 0.981 |
| `tmkL` g1 | U+0EB8..U+0EBC U+0EC8 | passed | 0 / 0 | 0 | seed 0 | 0.0014 0.0007 0.0004 | 0.958 | 0.889 |
| `tmkL` g2 | U+0EC9..U+0ECE | passed | 0 / 0 | 0 | seed 1 | 0.0016 0.0007 0.0004 | 1.000 | 1.000 |
| `tmkS` g0 | U+25FD U+25FE U+2614 U+2615 | passed | 0 / 0 | 1 | seed 0 | 0.0048 0.0022 0.0011 | 0.967 | 1.000 |
| `tmkS` g1 | U+2648..U+264C | passed | 0 / 0 | 0 | seed 1 | 0.0043 0.0020 0.0009 | 0.893 | 0.870 |
| `tmkS` g2 | U+264D..U+2651 | passed | 0 / 0 | 1 | seed 0 | 0.0052 0.0023 0.0012 | 0.903 | 0.875 |
| `tmkS` g3 | U+2652 U+2653 U+267F U+2693 U+26A1 | passed | 0 / 0 | 0 | seed 0 | 0.0048 0.0023 0.0013 | 0.921 | 0.917 |

Speed was not measured for this bundle; its nets have the width and depth
of `neuronte-term-rest-v1`'s.

## Files

| File | What |
|---|---|
| `neuronte-term-marks-v1.nrt` | The bundle, 1,484,368 bytes, sha256 `ae6979c3b0177bc0900a03f2d7b9e2105e72310f420f5195abf2083b6bffc6af` |
| `neuronte-term-marks-v1.list.txt` | The 166 characters it was trained on |
| `neuronte-term-marks-v1-SET-gN.json` | The 26 group nets as trained (the shipped seed) |
| `neuronte-term-marks-v1.provenance.json` | Every member's hash and scalars, written by `make pack-term-marks-v1` |
| `neuronte-term-marks-v1.validation.json` | The gates' hashes, both seeds' measurements and failures for every group and half, the limits eased, what was left out |
