# wide-forms-v1: 103 wide characters drawn for a box of two cells

`neuronte-wide-forms-v1.nrt` draws the fullwidth forms of Halfwidth and Fullwidth Forms (U+FF01..FF60, U+FFE0..FFE6): characters that a terminal gives two cells
(East Asian Width W or F), 103 of the 1,335 that the four neuronte-wide
bundles draw between them, with no character in two of them. Each is this
project's own drawing for the **box of two cells**, made from its Unicode
name and the charts' description of it in words, on a grid of 18 by 18
units with pens of 2 units (1/9 of the box).

It is a **standalone** bundle: 12 known-only group nets and one blank net,
685,308 bytes. It is not a default and replaces nothing; the one-cell
bundles are unchanged.

## How a program must ask

As for `neuronte-kilix-chrome-v2`: a net's design cell is 1 wide and 2 high,
and a two-cell box W×H is about square. **Ask for the cell W×2H and average
each pair of rows:**

```c
/* a wide character c in a box w x h (w twice the cell's width); buf holds w * 2 * h floats */
neuronte_coverage(wide, c, w, 2 * h, 0, buf);
for (y = 0; y < h; y++)
    for (x = 0; x < w; x++)
        box[y * w + x] = (buf[2 * y * w + x] + buf[(2 * y + 1) * w + x]) / 2;
```

`neuronte_untrained(wide, c)` is 0 for exactly the 103 characters of
`neuronte-wide-forms-v1.symbols.txt` and 1 for every other scalar.

**This file is not a listed bundle.** Some of its code points are drawn for
one cell in a terminal bundle (for instance by `neuronte-term-rest-v1`), and
this file draws them again for another box, so the rule that no two listed
bundles claim one character (`tests/check_bundle_lists.py`) cannot hold for
it. Its list is `neuronte-wide-forms-v1.symbols.txt`; `tests/check_wide.py` holds the table
to it exactly and holds the four wide bundles apart from each other.

## Gates

Declared before any net of this bundle was trained (2026-11-18T00:25Z):
every group is judged as symbols by gates v2.3 (`gates-v2.3.json`, sha256
`2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`), unchanged, by the unchanged scoring command
(sha256 `572d573b643f5f7074ceca1fd4505eee9cc8da05bbebdf5e391d1689a9d31f2c`), at its counted cells 6×12, 8×16,
10×20, 12×24, 16×32, 24×48 and 48×96, against a teacher of all
103 drawings of the bundle (sha256 `8acadee4086429c7d371c7e6236dca6c53c3b8c7902f049b40a32e0e9875ed06`): mean error,
99th percentile error and firm wrong pixels for the group and mean error for
each character; every character nearest its own drawing; none vanished. The
cell W×2W is what a program asks for a box W×W, so 12×24 to 48×96 judge the
boxes 12×12 to 48×48.

Gates v2.3 is gates v2 with no limit tighter than what the group's own
drawing scores when sampled as the library samples it (a perfect net), with
10 % of room, and a seed that puts every pixel on the right side at every
counted size passing the error-amount rules. Nearest-to-itself and
none-vanished are never eased. **5 limits were eased** for the nets in this
bundle; each is in the validation record with the declared limit, the
perfect drawing's score and the limit applied.

A group whose two seeds pass ships the seed with the lower mean error at
8×16, 16×32 and 48×96. A group that fails is trained once more as two nets
of half its characters each; a half that fails is left out. Nothing that
failed ships.

- 11 groups trained; 10 passed with both seeds.
- 1 failed and was halved; of the 2 halves 2 passed.
- 0 halves failed again and are left out (0 characters).

## Results by net

Mean error against the teacher and mean overlap at counted cells, for the shipped seed (for a net not in the bundle: seed 0).

| Net | Characters | Gates v2.3 | Rules missed (seed 0 / seed 1) | Limits eased | In the bundle | Mean error 12×24 / 16×32 / 24×48 / 48×96 | Overlap 16×32 | Overlap 24×48 |
|---|---|---|---|---:|---|---|---:|---:|
| `twdf0` g0 | U+FF01..U+FF09 (9) | passed | 0 / 0 | 0 | seed 1 | 0.0034 0.0019 0.0023 0.0011 | 0.925 | 0.969 |
| `twdf0` g1 | U+FF0A..U+FF12 (9) | passed | 0 / 0 | 0 | seed 0 | 0.0024 0.0014 0.0016 0.0009 | 0.998 | 0.997 |
| `twdf0` g2 | U+FF13..U+FF1C (10) | passed | 0 / 0 | 0 | seed 1 | 0.0024 0.0016 0.0020 0.0009 | 0.998 | 0.975 |
| `twdf0` g3 | U+FF1D..U+FF25 (9) | passed | 0 / 0 | 0 | seed 1 | 0.0026 0.0021 0.0022 0.0010 | 0.986 | 0.946 |
| `twdf0` g4 | U+FF26..U+FF2E (9) | passed | 0 / 0 | 1 | seed 1 | 0.0032 0.0029 0.0028 0.0012 | 0.994 | 0.867 |
| `twdf0` g5 | U+FF2F..U+FF38 (10) | passed | 0 / 0 | 0 | seed 1 | 0.0027 0.0024 0.0022 0.0010 | 0.990 | 0.952 |
| `twdf0` g6 | U+FF39..U+FF41 (9) | passed | 0 / 0 | 0 | seed 1 | 0.0024 0.0018 0.0017 0.0008 | 0.976 | 0.995 |
| `twdf0` g7 | U+FF42..U+FF4A (9) | passed | 0 / 0 | 1 | seed 1 | 0.0030 0.0022 0.0027 0.0011 | 0.998 | 0.914 |
| `twdf0` g8 | U+FF4B..U+FF54 (10) | passed | 0 / 0 | 0 | seed 1 | 0.0033 0.0023 0.0025 0.0011 | 0.991 | 0.915 |
| `twdf0` g9 | U+FF55..U+FF5D (9) | passed | 0 / 0 | 0 | seed 0 | 0.0023 0.0017 0.0017 0.0009 | 1.000 | 0.918 |
| `twdf0` g10 | U+FF5E..U+FFE6 (10) | **failed** | 0 / 1: 8x16 p99 | 3 | no: halved | 0.0031 0.0019 0.0022 0.0011 | 0.971 | 0.970 |
| `twdf0r10` g0 (half) | U+FF5E..U+FFE1 (5) | passed | 0 / 0 | 3 | seed 0 | 0.0031 0.0020 0.0024 0.0010 | 0.945 | 0.972 |
| `twdf0r10` g1 (half) | U+FFE2..U+FFE6 (5) | passed | 0 / 0 | 0 | seed 0 | 0.0030 0.0018 0.0018 0.0008 | 0.993 | 0.962 |

## The boxes in use that the gates do not count (information)

The shipped seed of each net at the cell a program asks for the boxes
18×18, 20×20 and 36×36, by the scorer's own metric code against the bundle
teacher, and in the box itself (each pair of rows averaged) against the
teacher's area coverage of the box. Declared as information before
training; it decides nothing.

| Net | 18×36: error, 99th pct | 20×40 | 36×72 | Box 18×18: error | Box 20×20 | Box 36×36 | Not nearest or vanished |
|---|---|---|---|---:|---:|---:|---|
| `twdf0` g0 | 0.0019, 0.047 | 0.0014, 0.031 | 0.0014, 0.037 | 0.0016 | 0.0011 | 0.0012 | none |
| `twdf0` g1 | 0.0015, 0.047 | 0.0008, 0.021 | 0.0011, 0.033 | 0.0013 | 0.0006 | 0.0010 | none |
| `twdf0` g2 | 0.0016, 0.035 | 0.0010, 0.023 | 0.0012, 0.038 | 0.0014 | 0.0009 | 0.0011 | none |
| `twdf0` g3 | 0.0016, 0.033 | 0.0012, 0.027 | 0.0014, 0.045 | 0.0014 | 0.0010 | 0.0013 | none |
| `twdf0` g4 | 0.0020, 0.046 | 0.0010, 0.021 | 0.0016, 0.050 | 0.0019 | 0.0008 | 0.0015 | none |
| `twdf0` g5 | 0.0018, 0.035 | 0.0012, 0.024 | 0.0014, 0.042 | 0.0014 | 0.0009 | 0.0012 | none |
| `twdf0` g6 | 0.0017, 0.049 | 0.0007, 0.018 | 0.0011, 0.039 | 0.0016 | 0.0006 | 0.0010 | none |
| `twdf0` g7 | 0.0017, 0.035 | 0.0011, 0.024 | 0.0014, 0.047 | 0.0015 | 0.0009 | 0.0013 | none |
| `twdf0` g8 | 0.0020, 0.049 | 0.0010, 0.024 | 0.0015, 0.048 | 0.0018 | 0.0009 | 0.0013 | none |
| `twdf0` g9 | 0.0017, 0.049 | 0.0012, 0.033 | 0.0011, 0.034 | 0.0016 | 0.0010 | 0.0009 | none |
| `twdf0r10` g0 | 0.0015, 0.029 | 0.0018, 0.048 | 0.0014, 0.040 | 0.0012 | 0.0016 | 0.0011 | none |
| `twdf0r10` g1 | 0.0018, 0.049 | 0.0011, 0.026 | 0.0011, 0.029 | 0.0016 | 0.0009 | 0.0010 | none |

## Recipe

- **Drawings.** `train/wide.py` and its parts put each drawing of the
  18×18 box into the net's cell (1 wide, 2 high) with every stroke as its
  outline, so a lying stroke is as thick as a standing one once the cell is
  drawn at half height. Drawn from the Unicode name and the charts' words;
  no font was opened or rasterised to make or check any drawing, and no
  emoji image was looked at.
- **Sets and groups.** 1 sets, each cut in order into group nets
  (11 in all); 1 failed and were trained again as halves, so
  the bundle holds 12 nets of 5 to 10 characters.
- **Training.** `train/split_expert.py train --mode repertoire --partition
  contiguous`, unchanged: hidden width 64, 120,000 steps, the project teacher
  (grid 256), seeds 0 and 1. A halved group: the set `NAMErI` of that
  group's characters, two parts, the rest the same.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from
  each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
python3 train/build_wide_forms_v1.py    # rebuilds the .nrt byte for byte from the group nets
make test-wide-forms-v1
```

## Checks

`make test-wide-forms-v1` (part of `make test`): every group net against
the float64 reference; the bundle rebuilt byte for byte; its table exactly
`neuronte-wide-forms-v1.symbols.txt`; no character in two of the four wide bundles, 1,335 in
all; every scalar from U+0000 to U+10FFFF routed as the table says; pixels
through the bundle equal to each group net alone at 19 cell sizes, at the
five cells asked for two-cell boxes and with one sample a pixel; every
character with ink in its 18×18 box; `test_api --standalone`; and the
validation record: only nets whose two seeds passed gates v2.3 are in the
bundle, each as the selected seed.

## Speed

Not measured yet.

## Files

| File | What |
|---|---|
| `neuronte-wide-forms-v1.nrt` | The bundle, 685,308 bytes, sha256 `9c1f6ea1791d2a9119fd124fc1c6073f953fe9b4ba3f340acb3605bb3119db1b` |
| `neuronte-wide-forms-v1.symbols.txt` | The 103 characters it was trained on |
| `neuronte-wide-forms-v1-SET-gN.json` | The 12 group nets as trained (the shipped seed) |
| `neuronte-wide-forms-v1.provenance.json` | Every member's hash and scalars, written by its build script |
| `neuronte-wide-forms-v1.validation.json` | The gates' hashes, both seeds' measurements and failures for every group and half, the limits eased, what was left out |
