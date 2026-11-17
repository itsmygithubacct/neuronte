# term-rest-v1: 197 Hebrew, Lao and face characters, on their own

`neuronte-term-rest-v1.nrt` is a terminal bundle for 197 characters no earlier bundle
was trained on: the Hebrew letters and the presentation forms that are one
letter's picture (a letter with a dagesh or another point, the wide
letters), Hebrew punctuation, Lao letters and the Lao vowel signs that
stand alone, the Thai baht sign, and the faces, cat faces, animal faces and
moon phases of Emoticons and Miscellaneous Symbols and Pictographs, in one
colour. In `neuronte-split-v9` each of them goes to the router's gate and is
drawn by a net that never saw it, so it comes out as some other shape (over
these characters split-v9's mean overlap with the drawing is
0.06 at 8×16; this bundle's is 0.94).

It is a **standalone** bundle: 26 known-only group nets and one blank net,
1,484,956 bytes, with no copy of split-v9 in it. A program opens it beside
split-v9 and asks it first (see "What a consumer changes"). It is not a
default and replaces nothing. The faces are plain one-colour terminal
characters; the colour emoji net is a different file and is not changed.

| Characters | Training set | Group nets trained | In the bundle | Gates v2.3 |
|---|---|---:|---:|---|
| 32 of 32: Hebrew letters | `trsth` | 4 | 4 | 4 of 4 groups passed |
| 16 of 16: Hebrew punctuation, the Thai baht sign, wide Hebrew letters | `trstw` | 2 | 2 | 2 of 2 groups passed |
| 34 of 34: Hebrew letters with a point | `trstd` | 4 | 5 | 3 of 4 groups passed; 1 halved, 2 of 2 halves passed |
| 39 of 39: Lao letters and vowel signs that stand alone | `trstl` | 5 | 5 | 5 of 5 groups passed |
| 55 of 55: Faces (Emoticons) | `trstf` | 7 | 7 | 7 of 7 groups passed |
| 13 of 13: Cat faces and animal faces | `trstc` | 2 | 2 | 2 of 2 groups passed |
| 8 of 8: Moon phases | `trstm` | 1 | 1 | 1 of 1 groups passed |

**What is not sure about the drawings.** No font was read to make or check
them. The Hebrew letters and the faces are drawn from what their shapes are
known to be. The Lao letters are drawn from memory of their general shape
(a head loop, stems, an arch or a bowl): the turn of a loop or the place
of a notch may be wrong, and a reader of Lao should check them before
relying on this file. `font/term-rest.txt` carries a note beside every
drawing that is not sure (32 notes, 24 of them Lao).
The ten Lao digits and the Lao ellipsis are not drawn at all.

**One cell each.** Right-to-left order is the terminal's work: every Hebrew
letter stands upright in its own cell. The faces, animals and moons are
wide characters in Unicode; here each is drawn to fill one cell, so a
terminal that gives them two cells shows the picture in the first. Moons
have ink for the dark part: the new moon is a filled disc, the full moon a
ring.

**One drawing fix after the first training.** Kilix prints the eight moons
as its tab mark, so they must differ at 8×16 and 10×20. As first drawn,
the terminator of a crescent or gibbous moon bowed by half the radius; a
gibbous moon's dark part was then a sliver about 1.7 pixels wide at 8×16,
hard to tell from the full moon's ring, and the least difference between
two phases was 4 pixels at 8×16 and 6 at 10×20 (cut at one half). It now
bows by 0.35 of the radius: 5 and 7 pixels. Only U+1F312, U+1F314, U+1F316
and U+1F318 changed. The first moon net had passed its gates; it was
dropped, and the net in the bundle was trained on the new drawings and
passes with no limit eased.

## Gates

The verdicts are those of gates v2.3 (`gates-v2.3.json`, sha256
`2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`), one declaration for the four lanes of this phase.
Each limit is the worst value among the group nets the owner had already
accepted, times 1.10; "every character nearest its own drawing" and "no
character vanishes" are absolute. Counted at 6×12, 8×16, 10×20, 12×24,
16×32, 24×48 and 48×96; letters also with one sample a pixel at 8×16,
16×32 and 48×96. Hebrew and Lao letters are judged as letters;
punctuation, the baht sign, faces and moons as symbols. The nearest
drawing is looked for among all 197 drawings of this bundle.

**The gates changed after the first scores, and this is how.** Gates v2
(`gates-v2.json`, sha256 `5bf1a3f8312c45df2a20b2e69d51ee3c690c58891ec5390cf0e41cbdf9f9b51b`)
was written before any net of this bundle was trained. Under it 9 of the 25
groups passed. Most of the failures were on overlap rules for letters, and
they were the same to three digits in both seeds. Drawing each letter from
its exact outline, sampled as the library samples it, and scoring that
with the gate's own measure showed why: the drawing itself, a perfect net,
fails those rules there (a thin stroke that falls between the sample
points at one size). No net could pass, and halving a group could not
help. The owner then decided, in three steps on 2026-11-17:

1. v2.1 (sha256 `214942e398f88110cd7c6044c194f0f274274aeedb07abcbe8e1a18dc2b323c0`):
   the worst-character overlap rule is dropped for letters. Used here only
   for information.
2. v2.2 (sha256 `dd3cc2ea30ccb49d001c28a905bcc6e2a2d11edfcd6a741464fda91162b10e70`):
   a rule the perfect drawing fails for a group at a size is not applied
   there. Under it 24 of the 25 groups passed; the bundle was first built
   from those verdicts.
3. v2.3, the final one: nothing is skipped. No limit is tighter than the
   perfect drawing's own score with 10 % of room (an error limit at 1.10
   times the perfect score; an overlap floor with the shortfall from 1
   grown by 1.10), and a seed whose net puts every pixel on the right side
   at every counted size passes the error-amount rules. Nearest-to-itself
   and none-vanished are never eased. Every net was scored again under it
   and the verdicts are the same as under v2.2, net for net.

No drawing was changed to pass a rule, and no declared limit was moved for
a rule a perfect net passes.

For the nets in this bundle **24 limits were eased** in that way, in
13 of the 26 nets: 24x48 iou_mean 9, 10x20 p99 3, 8x16 p99 3, 24x48 p99 2, s1 8x16 p99 2, 10x20 mae 1, 24x48 firm 1, s1 16x32 firm 1, s1 16x32 p99 1, s1 8x16 mae 1.
Each is listed with its net, the declared limit, the perfect drawing's
score and the limit applied in the validation record (`limits_eased`).
0 seeds passed by the pixel-exact rule.

The rule is automatic: a group whose two seeds pass ships the seed with the
lower mean error at 8×16, 16×32 and 48×96. A group that fails is trained
once more as two nets of half its characters each. A half that fails is
left out. Nobody is asked about a failed group and nothing that failed
ships.

- 25 groups trained; 24 passed with both seeds.
- 1 failed and was halved; of the 2 halves 2 passed.
- 0 halves failed again and are left out (0 characters).

Halves were also started for eleven of the other groups that had failed under
gates v2. Under gates v2.2 and v2.3 each of those groups' own net passes, so the
halves are not used: `trstwr1` finished and is kept as evidence only; the
others were stopped part-way when the final verdicts came.

Rules missed by the nets that failed, by number of nets (either seed; `s1` is one sample a pixel, `nearest` a character nearer another drawing than its own, `firm` pixels on the wrong side of one half where the drawing is at least 0.1 from it): s1 16x32 firm 1.

## What a consumer changes

Nothing, until it opens this file. It does not replace split-v9 and holds
none of its characters; `tests/check_bundle_lists.py` checks that no two
listed bundles, and no listed bundle and split-v9, share a trained scalar.

```c
neuronte_open_file("neuronte-split-v9.nrt", &base);
neuronte_open_file("neuronte-term-rest-v1.nrt", &rest);
/* for each scalar c */
font = neuronte_untrained(rest, c) ? base : rest;
```

`neuronte_untrained(rest, c)` is 0 for exactly the 197 characters in
`neuronte-term-rest-v1.list.txt` and 1 for every other scalar. A scalar outside
the list, drawn through this file anyway, comes out blank (the file's
fallback is a net that draws nothing), or as the code-made hollow box after
`neuronte_set_untrained(rest, 1)`. The file needs the current runtime
(version 2 bundles, 128-member limit). It has 27 members.

Cells are the terminal's 1:2 cell; the nets were trained and measured from
6×12 to 48×96. A two-cell form of the faces (half labels, as the colour
emoji net has) was not made.

## Recipe

- **Drawings.** `font/term-rest.txt` lists every character, set by set, in
  training order; `train/term_rest.py` makes the Hebrew letters with a
  point, the wide letters, the faces and the moons from parts, so a letter
  and its pointed form cannot drift apart. No font was read; DejaVu Sans
  Mono 2.37 gave only its list of code points.
- **Sets and groups.** Seven sets by script and shape family; each cut in
  order into group nets of 6 to 9 characters (25 in all).
- **Training.** `train/split_expert.py train --mode repertoire --partition
  contiguous`, unchanged: hidden width 64, 120,000 steps, the project
  teacher (grid 256), seeds 0 and 1. A halved group: the set `NAMErI` of
  that group's characters, two parts, the rest the same. No wider retry.
- **Selection.** As under Gates. Only the shipped seed's JSON is in
  `weights/`; the other seed's hash and measurements are in the validation
  record.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from
  each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
make pack-term-rest-v1    # rebuilds the .nrt byte for byte from the group nets
make test-term-rest-v1
```

## Checks

`make test-term-rest-v1` (part of `make test`): every group net against
the float64 reference; the bundle rebuilt byte for byte; its table exactly
`neuronte-term-rest-v1.list.txt`, which is `font/term-rest.txt`;
every scalar from U+0000 to U+10FFFF routed as the table says; pixels through
the bundle equal to each group net alone at 19 cell sizes and with one
sample a pixel; `test_api --standalone`; and the validation record: only
nets whose two seeds passed gates v2.3 are in the bundle, each as the
selected seed.

## Results by net

Mean error against the teacher at 8×16, 16×32 and 48×96 and mean overlap at 8×16 and 6×12, for the shipped seed (for a net not in the bundle: seed 0).

| Net | Characters | Judged as | Gates v2.3 | Rules missed (seed 0 / seed 1) | Limits eased | In the bundle | Mean error | Overlap 8×16 | Overlap 6×12 |
|---|---|---|---|---|---:|---|---|---:|---:|
| `trsth` g0 | U+05D3 U+05E8 U+05DA U+05D4 U+05D7 U+05EA U+05DD U+05E7 | letters | passed | 0 / 0 | 1 | seed 1 | 0.0079 0.0044 0.0015 | 0.811 | 0.689 |
| `trsth` g1 | U+05D1 U+05DB U+05E4 U+05E3 U+05E1 U+05DE U+05D8 U+05E0 | letters | passed | 0 / 0 | 1 | seed 1 | 0.0071 0.0044 0.0015 | 0.884 | 0.836 |
| `trsth` g2 | U+05D5 U+05D6 U+05D9 U+05DF U+05D2 U+05F0 U+05F1 U+05F2 | letters | passed | 0 / 0 | 0 | seed 0 | 0.0044 0.0022 0.0009 | 0.986 | 0.767 |
| `trsth` g3 | U+05D0 U+05DC U+05E2 U+05E6 U+05E5 U+05E9 U+FB20 U+FB4F | letters | passed | 0 / 0 | 0 | seed 1 | 0.0059 0.0028 0.0014 | 0.896 | 0.964 |
| `trstw` g0 | U+05BE U+05C0 U+05C3 U+05C6 U+05F3 U+05F4 U+FB29 U+0E3F | symbols | passed | 0 / 0 | 0 | seed 1 | 0.0041 0.0025 0.0009 | 0.985 | 0.725 |
| `trstw` g1 | U+FB21..U+FB28 | letters | passed | 0 / 0 | 0 | seed 0 | 0.0076 0.0042 0.0015 | 0.935 | 0.640 |
| `trstd` g0 | U+FB31 U+FB3B U+FB44 U+FB43 U+FB4C U+FB4D U+FB4E U+FB41 | letters | passed | 0 / 0 | 1 | seed 0 | 0.0078 0.0051 0.0016 | 0.907 | 0.786 |
| `trstd` g1 | U+FB33 U+FB48 U+FB3A U+FB34 U+FB4A U+FB47 U+FB3E U+FB38 U+FB40 | letters | passed | 0 / 0 | 1 | seed 1 | 0.0075 0.0043 0.0016 | 0.859 | 0.753 |
| `trstd` g2 | U+FB35 U+FB4B U+FB36 U+FB39 U+FB1D U+FB1F U+FB32 U+FB3C | letters | passed | 0 / 0 | 0 | seed 0 | 0.0042 0.0023 0.0009 | 0.959 | 0.759 |
| `trstd` g3 | U+FB2A U+FB2B U+FB2C U+FB2D U+FB49 U+FB2E U+FB2F U+FB30 U+FB46 | letters | **failed** | 0 / 1 | 1 | no: halved | 0.0084 0.0044 0.0019 | 0.959 | 0.963 |
| `trstdr3` g0 (half) | U+FB2A..U+FB2D | letters | passed | 0 / 0 | 4 | seed 0 | 0.0105 0.0053 0.0021 | 0.969 | 0.934 |
| `trstdr3` g1 (half) | U+FB49 U+FB2E U+FB2F U+FB30 U+FB46 | letters | passed | 0 / 0 | 0 | seed 1 | 0.0066 0.0035 0.0017 | 0.951 | 0.987 |
| `trstl` g0 | U+0E81 U+0E84 U+0E94..U+0E96 U+0EA5 U+0EAA | letters | passed | 0 / 0 | 1 | seed 0 | 0.0073 0.0033 0.0015 | 0.801 | 0.980 |
| `trstl` g1 | U+0E82 U+0E8A U+0E8D U+0EA2 U+0E99 U+0E9A U+0E9B U+0EA1 | letters | passed | 0 / 0 | 1 | seed 1 | 0.0080 0.0040 0.0015 | 0.803 | 0.990 |
| `trstl` g2 | U+0E9C U+0E9D U+0E9E U+0E9F U+0E97 U+0EAB U+0EDC U+0EDD | letters | passed | 0 / 0 | 5 | seed 0 | 0.0094 0.0040 0.0020 | 0.927 | 0.984 |
| `trstl` g3 | U+0E87 U+0E88 U+0EA3 U+0EA7 U+0EAD U+0EAE U+0EBD U+0EC6 | letters | passed | 0 / 0 | 1 | seed 1 | 0.0052 0.0025 0.0013 | 0.907 | 0.990 |
| `trstl` g4 | U+0EB0 U+0EB2 U+0EB3 U+0EC0..U+0EC4 | letters | passed | 0 / 0 | 0 | seed 0 | 0.0049 0.0026 0.0013 | 0.967 | 0.975 |
| `trstf` g0 | U+1F600 U+1F601 U+1F603 U+1F604 U+1F606 U+1F602 U+1F605 | symbols | passed | 0 / 0 | 0 | seed 0 | 0.0060 0.0041 0.0021 | 0.990 | 0.973 |
| `trstf` g1 | U+1F607..U+1F60E | symbols | passed | 0 / 0 | 0 | seed 0 | 0.0064 0.0035 0.0021 | 0.992 | 0.988 |
| `trstf` g2 | U+1F60F U+1F610 U+1F611 U+1F612 U+1F615 U+1F636 U+1F633 U+1F643 | symbols | passed | 0 / 0 | 0 | seed 0 | 0.0053 0.0032 0.0019 | 0.976 | 0.977 |
| `trstf` g3 | U+1F617 U+1F618 U+1F619 U+1F61A U+1F61B U+1F61C U+1F61D U+1F616 | symbols | passed | 0 / 0 | 0 | seed 0 | 0.0054 0.0035 0.0020 | 0.986 | 0.984 |
| `trstf` g4 | U+1F613 U+1F614 U+1F61E..U+1F623 | symbols | passed | 0 / 0 | 2 | seed 1 | 0.0059 0.0035 0.0021 | 0.986 | 0.973 |
| `trstf` g5 | U+1F625 U+1F626 U+1F627 U+1F628 U+1F629 U+1F62B U+1F62D U+1F62A | symbols | passed | 0 / 0 | 0 | seed 0 | 0.0064 0.0036 0.0022 | 0.974 | 0.965 |
| `trstf` g6 | U+1F62E..U+1F632 U+1F634 U+1F635 U+1F637 | symbols | passed | 0 / 0 | 1 | seed 1 | 0.0070 0.0038 0.0022 | 0.993 | 0.958 |
| `trstc` g0 | U+1F638..U+1F63D | symbols | passed | 0 / 0 | 2 | seed 1 | 0.0084 0.0039 0.0022 | 0.963 | 0.979 |
| `trstc` g1 | U+1F63E U+1F63F U+1F640 U+1F431 U+1F42D U+1F42E U+1F435 | symbols | passed | 0 / 0 | 3 | seed 1 | 0.0079 0.0036 0.0024 | 0.980 | 0.935 |
| `trstm` g0 | U+1F311..U+1F318 | symbols | passed | 0 / 0 | 0 | seed 1 | 0.0030 0.0018 0.0010 | 0.991 | 1.000 |

## The whole bundle against split-v9 on the same characters

Mean error and mean overlap against the teacher, automatic sampling, over the characters in the bundle. split-v9 draws each of these through its gate, with a net that never saw it.

| Set | Characters | split-v9 8×16 | term-rest-v1 8×16 | split-v9 16×32 | term-rest-v1 16×32 | split-v9 48×96 | term-rest-v1 48×96 |
|---|---:|---|---|---|---|---|---|
| Hebrew letters | 32 | 0.182, 0.11 | 0.0063, 0.894 | 0.198, 0.14 | 0.0035, 0.978 | 0.203, 0.14 | 0.0013, 0.990 |
| Hebrew punctuation, the Thai baht sign, wide Hebrew letters | 16 | 0.198, 0.04 | 0.0059, 0.960 | 0.208, 0.07 | 0.0033, 0.989 | 0.210, 0.08 | 0.0012, 0.995 |
| Hebrew letters with a point | 34 | 0.235, 0.03 | 0.0070, 0.920 | 0.249, 0.06 | 0.0040, 0.988 | 0.256, 0.06 | 0.0015, 0.993 |
| Lao letters and vowel signs that stand alone | 39 | 0.201, 0.09 | 0.0069, 0.883 | 0.217, 0.14 | 0.0033, 0.986 | 0.223, 0.15 | 0.0015, 0.992 |
| Faces (Emoticons) | 55 | 0.261, 0.03 | 0.0061, 0.985 | 0.282, 0.07 | 0.0036, 0.994 | 0.292, 0.08 | 0.0021, 0.993 |
| Cat faces and animal faces | 13 | 0.275, 0.03 | 0.0081, 0.972 | 0.297, 0.07 | 0.0037, 0.986 | 0.307, 0.09 | 0.0023, 0.991 |
| Moon phases | 8 | 0.317, 0.02 | 0.0030, 0.991 | 0.326, 0.06 | 0.0018, 1.000 | 0.331, 0.07 | 0.0010, 1.000 |
| All | 197 | 0.230, 0.06 | 0.0064, 0.936 | 0.247, 0.09 | 0.0035, 0.988 | 0.254, 0.10 | 0.0016, 0.993 |

## Speed

Measured on the two x86 hosts other cards use, an Intel Core i7-6820HQ and an
Intel Core i7-10700F, each under the shared benchmark lock, at commit c2765ae
(the bundle there is byte for byte the one here).
kilix-bench e21e5cd: one pinned core, a fresh process for every job, one
warmup and ten measured rounds in shuffled order, medians, raw trials kept,
every model checked against the float64 reference first. The corpus is
this bundle's 197 characters. split-v9 sends each through its gate to
another of its nets, which never saw it; term-rest-v1 looks it up in its
table and runs a small group net. Both hosts draw the same pixels.

| µs per character | split-v9, i7-6820HQ | term-rest-v1, i7-6820HQ | ratio | split-v9, i7-10700F | term-rest-v1, i7-10700F | ratio |
|---|---:|---:|---:|---:|---:|---:|
| Coverage, uncached, 8×16 | 502.1 | 183.8 | 2.73 | 381.1 | 142.9 | 2.67 |
| Coverage, uncached, 16×32 | 1979.2 | 708.5 | 2.79 | 1487.3 | 544.0 | 2.73 |
| Coverage, uncached, 48×96 | 4368.5 | 1578.9 | 2.77 | 3312.1 | 1203.9 | 2.75 |
| Draw, cold, 8×16 | 504.3 | 187.3 | 2.69 | 389.0 | 143.2 | 2.72 |
| Draw, cold, 16×32 | 1968.5 | 712.1 | 2.76 | 1493.8 | 550.1 | 2.72 |
| Draw, cold, 48×96 | 4366.4 | 1603.2 | 2.72 | 3337.4 | 1232.6 | 2.71 |
| Draw, warm, 8×16 | 4.0 | 1.0 | 4.11 | 3.0 | 0.7 | 4.18 |
| Draw, warm, 16×32 | 6.9 | 3.1 | 2.21 | 5.1 | 2.3 | 2.24 |
| Draw, warm, 48×96 | 28.1 | 22.9 | 1.23 | 20.4 | 16.4 | 1.24 |

Uncached, term-rest-v1 draws these characters 2.7 times as fast as
split-v9's fallback does (geometric mean over the three cells and both
hosts: 2.76 on the i7-6820HQ, 2.72 on the i7-10700F; cold draw 2.7,
warm draw 2.2). A lookup in its table takes 14 ns and 8 ns against
1240 ns and 912 ns for split-v9's gate. Opening the file takes 1.9 ms and
1.4 ms against 5.0 ms and 3.5 ms for split-v9; a program that opens both
pays both.

A handle caches 1,024 drawn cells. A screen that shows more distinct cells
than that redraws some each frame, whichever bundle draws them.

## Files

| File | What |
|---|---|
| `neuronte-term-rest-v1.nrt` | The bundle, 1,484,956 bytes, sha256 `9a92c86c183fa9b435d89663780c643a2031f853e0096bd233e7bfdf431a4b6d` |
| `neuronte-term-rest-v1.list.txt` | The 197 characters it was trained on |
| `neuronte-term-rest-v1-SET-gN.json` | The 26 group nets as trained (the shipped seed) |
| `neuronte-term-rest-v1.provenance.json` | Every member's hash and scalars, written by `make pack-term-rest-v1` |
| `neuronte-term-rest-v1.validation.json` | The gates' hashes, both seeds' measurements and failures for every group and half, the limits eased, what was left out |
