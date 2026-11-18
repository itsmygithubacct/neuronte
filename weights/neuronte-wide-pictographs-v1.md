# wide-pictographs-v1: 416 wide characters drawn for a box of two cells

`neuronte-wide-pictographs-v1.nrt` draws the wide characters of Miscellaneous Symbols and Pictographs (U+1F300..1F5FF): characters that a terminal gives two cells
(East Asian Width W or F), 559 of the 1,335 that the four neuronte-wide
bundles draw between them, with no character in two of them. Each is this
project's own drawing for the **box of two cells**, made from its Unicode
name and the charts' description of it in words, on a grid of 18 by 18
units with pens of 2 units (1/9 of the box).

It is a **standalone** bundle: 103 known-only group nets and one blank net,
5,877,536 bytes. It is not a default and replaces nothing; the one-cell
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

`neuronte_untrained(wide, c)` is 0 for exactly the 416 characters of
`neuronte-wide-pictographs-v1.symbols.txt` and 1 for every other scalar.

**This file is not a listed bundle.** Some of its code points are drawn for
one cell in a terminal bundle (for instance by `neuronte-term-rest-v1`), and
this file draws them again for another box, so the rule that no two listed
bundles claim one character (`tests/check_bundle_lists.py`) cannot hold for
it. Its list is `neuronte-wide-pictographs-v1.symbols.txt`; `tests/check_wide.py` holds the table
to it exactly and holds the four wide bundles apart from each other.

## Colour twins, by the owner's choice

Unicode tells 16 of these characters apart from a sibling only by
colour. A one-colour font has no way to show that, and the owner chose
(2026-11-18) **identical twins**: each shape is drawn once and every colour
of it the same, as in a one-colour font. They are in the bundle as twins on
purpose, and the gates allow identical drawings.

U+1F34E U+1F34F U+1F499 U+1F49A U+1F49B U+1F49C U+1F4D5 U+1F4D7 U+1F4D8 U+1F4D9 U+1F534 U+1F535 U+1F536 U+1F537 U+1F538 U+1F539

## Left out

**143 drawn characters are not in the bundle.** Their nets failed the
gates twice (as a group, then as a half) and were left out by rule; the
characters stay untrained:
U+1F305 U+1F306 U+1F307 U+1F308 U+1F309 U+1F30A U+1F339 U+1F33A U+1F33B U+1F33C U+1F33D U+1F341 U+1F342 U+1F343 U+1F346 U+1F347 U+1F348 U+1F35D U+1F35E U+1F35F U+1F36B U+1F36C U+1F36D U+1F36E U+1F36F U+1F382 U+1F383 U+1F384 U+1F385 U+1F386 U+1F387 U+1F390 U+1F391 U+1F392 U+1F3A5 U+1F3A6 U+1F3A7 U+1F3A8 U+1F3A9 U+1F3B8 U+1F3B9 U+1F3BA U+1F3BE U+1F3BF U+1F3C0 U+1F3C3 U+1F3C4 U+1F3C5 U+1F3C9 U+1F3CA U+1F3CF U+1F3E1 U+1F3E2 U+1F3E3 U+1F3E4 U+1F3E5 U+1F3E6 U+1F3E7 U+1F3E8 U+1F3E9 U+1F3EA U+1F3EB U+1F3EC U+1F3ED U+1F3EE U+1F406 U+1F407 U+1F408 U+1F414 U+1F415 U+1F416 U+1F417 U+1F418 U+1F419 U+1F41A U+1F41B U+1F42D U+1F42E U+1F42F U+1F438 U+1F439 U+1F43A U+1F47B U+1F47C U+1F47D U+1F47E U+1F47F U+1F480 U+1F4A2 U+1F4A3 U+1F4A4 U+1F4A5 U+1F4A6 U+1F4A7 U+1F4B3 U+1F4B4 U+1F4B5 U+1F4B6 U+1F4B7 U+1F4B8 U+1F4C6 U+1F4C7 U+1F4C8 U+1F4CC U+1F4CD U+1F4CE U+1F4E0 U+1F4E1 U+1F4E5 U+1F4E6 U+1F4E7 U+1F4F3 U+1F4F4 U+1F4F5 U+1F4F6 U+1F4F7 U+1F4F8 U+1F4F9 U+1F4FA U+1F4FB U+1F500 U+1F501 U+1F502 U+1F50F U+1F510 U+1F511 U+1F512 U+1F513 U+1F517 U+1F518 U+1F519 U+1F51C U+1F51D U+1F51E U+1F51F U+1F520 U+1F521 U+1F522 U+1F523 U+1F524 U+1F54E U+1F550 U+1F551.

## Gates

Declared before any net of this bundle was trained (2026-11-18T00:25Z):
every group is judged as symbols by gates v2.3 (`gates-v2.3.json`, sha256
`2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`), unchanged, by the unchanged scoring command
(sha256 `572d573b643f5f7074ceca1fd4505eee9cc8da05bbebdf5e391d1689a9d31f2c`), at its counted cells 6×12, 8×16,
10×20, 12×24, 16×32, 24×48 and 48×96, against a teacher of all
559 drawings of the bundle (sha256 `3fef46bb66b43e3709939e025862b7ca5d3be811180899c02e554c61aa2c9391`): mean error,
99th percentile error and firm wrong pixels for the group and mean error for
each character; every character nearest its own drawing; none vanished. The
cell W×2W is what a program asks for a box W×W, so 12×24 to 48×96 judge the
boxes 12×12 to 48×48.

Gates v2.3 is gates v2 with no limit tighter than what the group's own
drawing scores when sampled as the library samples it (a perfect net), with
10 % of room, and a seed that puts every pixel on the right side at every
counted size passing the error-amount rules. Nearest-to-itself and
none-vanished are never eased. **572 limits were eased** for the nets in this
bundle; each is in the validation record with the declared limit, the
perfect drawing's score and the limit applied.

A group whose two seeds pass ships the seed with the lower mean error at
8×16, 16×32 and 48×96. A group that fails is trained once more as two nets
of half its characters each; a half that fails is left out. Nothing that
failed ships.

- 100 groups trained; 47 passed with both seeds.
- 53 failed and were halved; of the 106 halves 56 passed.
- 50 halves failed again and are left out (143 characters).

## Results by net

Mean error against the teacher and mean overlap at counted cells, for the shipped seed (for a net not in the bundle: seed 0).

| Net | Characters | Gates v2.3 | Rules missed (seed 0 / seed 1) | Limits eased | In the bundle | Mean error 12×24 / 16×32 / 24×48 / 48×96 | Overlap 16×32 | Overlap 24×48 |
|---|---|---|---|---:|---|---|---:|---:|
| `twdp0` g0 | U+1F300..U+1F304 (5) | **failed** | 1 / 0: 24x48 p99 | 7 | no: halved | 0.0069 0.0058 0.0060 0.0028 | 0.992 | 0.969 |
| `twdp0r0` g0 (half) | U+1F300..U+1F301 (2) | passed | 0 / 0 | 2 | seed 1 | 0.0072 0.0051 0.0054 0.0028 | 0.985 | 0.968 |
| `twdp0r0` g1 (half) | U+1F302..U+1F304 (3) | passed | 0 / 0 | 9 | seed 1 | 0.0064 0.0061 0.0056 0.0020 | 0.998 | 0.969 |
| `twdp0` g1 | U+1F305..U+1F30A (6) | **failed** | 3 / 3: 24x48 mae, 24x48 p99, 48x96 mae | 11 | no: halved | 0.0082 0.0070 0.0072 0.0033 | 0.984 | 0.973 |
| `twdp0r1` g0 (half) | U+1F305..U+1F307 (3) | **failed** | 1 / 0: 24x48 mae | 7 | **no: left out** | 0.0082 0.0078 0.0065 0.0028 | 0.980 | 0.983 |
| `twdp0r1` g1 (half) | U+1F308..U+1F30A (3) | **failed** | 1 / 0: 10x20 p99 | 10 | **no: left out** | 0.0075 0.0058 0.0061 0.0029 | 0.990 | 0.961 |
| `twdp0` g2 | U+1F30B..U+1F30F (5) | passed | 0 / 0 | 5 | seed 1 | 0.0056 0.0049 0.0055 0.0024 | 0.984 | 0.994 |
| `twdp0` g3 | U+1F310..U+1F315 (6) | **failed** | 1 / 1: 8x16 p99 | 5 | no: halved | 0.0051 0.0037 0.0048 0.0021 | 0.984 | 0.997 |
| `twdp0r3` g0 (half) | U+1F310..U+1F312 (3) | passed | 0 / 0 | 9 | seed 0 | 0.0062 0.0047 0.0062 0.0024 | 0.983 | 1.000 |
| `twdp0r3` g1 (half) | U+1F313..U+1F315 (3) | passed | 0 / 0 | 1 | seed 0 | 0.0042 0.0029 0.0034 0.0016 | 0.982 | 0.995 |
| `twdp0` g4 | U+1F316..U+1F31A (5) | passed | 0 / 0 | 1 | seed 0 | 0.0035 0.0025 0.0032 0.0015 | 0.987 | 0.989 |
| `twdp0` g5 | U+1F31B..U+1F320 (6) | **failed** | 1 / 1: 24x48 p99 | 2 | no: halved | 0.0052 0.0036 0.0056 0.0026 | 0.979 | 0.976 |
| `twdp0r5` g0 (half) | U+1F31B..U+1F31D (3) | passed | 0 / 0 | 1 | seed 1 | 0.0044 0.0033 0.0043 0.0017 | 0.987 | 0.990 |
| `twdp0r5` g1 (half) | U+1F31E..U+1F320 (3) | passed | 0 / 0 | 2 | seed 1 | 0.0057 0.0035 0.0062 0.0025 | 0.974 | 0.967 |
| `twdp0` g6 | U+1F32D..U+1F331 (5) | passed | 0 / 0 | 3 | seed 0 | 0.0047 0.0030 0.0045 0.0019 | 0.979 | 0.982 |
| `twdp0` g7 | U+1F332..U+1F338 (6) | passed | 0 / 0 | 2 | seed 1 | 0.0055 0.0037 0.0042 0.0019 | 0.977 | 0.993 |
| `twdp0` g8 | U+1F339..U+1F33D (5) | **failed** | 1 / 0: 24x48 mae | 7 | no: halved | 0.0065 0.0040 0.0073 0.0026 | 0.980 | 0.974 |
| `twdp0r8` g0 (half) | U+1F339..U+1F33A (2) | **failed** | 1 / 0: 8x16 p99 | 6 | **no: left out** | 0.0055 0.0032 0.0056 0.0018 | 1.000 | 0.978 |
| `twdp0r8` g1 (half) | U+1F33B..U+1F33D (3) | **failed** | 2 / 0: 16x32 p99, 6x12 p99 | 10 | **no: left out** | 0.0068 0.0044 0.0075 0.0027 | 0.978 | 0.969 |
| `twdp0` g9 | U+1F33E..U+1F343 (6) | **failed** | 2 / 0: 24x48 p99, 6x12 p99 | 2 | no: halved | 0.0056 0.0036 0.0058 0.0023 | 0.897 | 0.984 |
| `twdp0r9` g0 (half) | U+1F33E..U+1F340 (3) | passed | 0 / 0 | 2 | seed 1 | 0.0058 0.0041 0.0056 0.0023 | 0.855 | 0.985 |
| `twdp0r9` g1 (half) | U+1F341..U+1F343 (3) | **failed** | 2 / 2: 10x20 p99, 6x12 p99 | 4 | **no: left out** | 0.0046 0.0028 0.0049 0.0017 | 0.953 | 0.988 |
| `twdp1` g0 | U+1F344..U+1F348 (5) | **failed** | 1 / 2: 10x20 firm, 24x48 firm | 7 | no: halved | 0.0062 0.0042 0.0054 0.0026 | 0.989 | 0.985 |
| `twdp1r0` g0 (half) | U+1F344..U+1F345 (2) | passed | 0 / 0 | 5 | seed 0 | 0.0055 0.0038 0.0046 0.0019 | 0.983 | 0.978 |
| `twdp1r0` g1 (half) | U+1F346..U+1F348 (3) | **failed** | 1 / 1: 24x48 firm | 7 | **no: left out** | 0.0067 0.0041 0.0059 0.0027 | 0.994 | 0.987 |
| `twdp1` g1 | U+1F349..U+1F34E (6) | **failed** | 0 / 3: 10x20 p99, 24x48 firm, 24x48 p99 | 3 | no: halved | 0.0045 0.0031 0.0042 0.0020 | 0.983 | 0.985 |
| `twdp1r1` g0 (half) | U+1F349..U+1F34B (3) | passed | 0 / 0 | 0 | seed 1 | 0.0037 0.0027 0.0032 0.0013 | 0.992 | 0.987 |
| `twdp1r1` g1 (half) | U+1F34C..U+1F34E (3) | passed | 0 / 0 | 6 | seed 1 | 0.0051 0.0035 0.0049 0.0022 | 0.970 | 0.981 |
| `twdp1` g2 | U+1F34F..U+1F353 (5) | passed | 0 / 0 | 1 | seed 1 | 0.0032 0.0027 0.0030 0.0015 | 0.990 | 0.993 |
| `twdp1` g3 | U+1F354..U+1F359 (6) | passed | 0 / 0 | 1 | seed 0 | 0.0048 0.0035 0.0037 0.0018 | 0.966 | 0.995 |
| `twdp1` g4 | U+1F35A..U+1F35F (6) | **failed** | 2 / 4: 10x20 p99, 48x96 mae, 48x96 p99, 6x12 p99 | 10 | no: halved | 0.0073 0.0049 0.0070 0.0031 | 0.986 | 0.982 |
| `twdp1r4` g0 (half) | U+1F35A..U+1F35C (3) | passed | 0 / 0 | 10 | seed 1 | 0.0077 0.0050 0.0074 0.0028 | 0.979 | 0.990 |
| `twdp1r4` g1 (half) | U+1F35D..U+1F35F (3) | **failed** | 0 / 1: 10x20 p99 | 6 | **no: left out** | 0.0066 0.0048 0.0061 0.0027 | 0.991 | 0.974 |
| `twdp1` g5 | U+1F360..U+1F364 (5) | passed | 0 / 0 | 1 | seed 0 | 0.0039 0.0026 0.0031 0.0015 | 0.993 | 0.996 |
| `twdp1` g6 | U+1F365..U+1F36A (6) | passed | 0 / 0 | 4 | seed 1 | 0.0045 0.0038 0.0050 0.0021 | 0.984 | 0.991 |
| `twdp1` g7 | U+1F36B..U+1F36F (5) | **failed** | 1 / 1: 24x48 p99 | 6 | no: halved | 0.0067 0.0045 0.0057 0.0025 | 0.944 | 0.988 |
| `twdp1r7` g0 (half) | U+1F36B..U+1F36C (2) | **failed** | 0 / 1: 12x24 p99 | 4 | **no: left out** | 0.0066 0.0038 0.0054 0.0023 | 0.967 | 0.988 |
| `twdp1r7` g1 (half) | U+1F36D..U+1F36F (3) | **failed** | 1 / 2: 16x32 p99, 24x48 p99 | 5 | **no: left out** | 0.0066 0.0047 0.0054 0.0021 | 0.931 | 0.985 |
| `twdp1` g8 | U+1F370..U+1F375 (6) | passed | 0 / 0 | 4 | seed 1 | 0.0081 0.0062 0.0054 0.0025 | 0.927 | 0.969 |
| `twdp1` g9 | U+1F376..U+1F37B (6) | passed | 0 / 0 | 5 | seed 0 | 0.0056 0.0045 0.0052 0.0022 | 0.925 | 0.958 |
| `twdp2` g0 | U+1F37C..U+1F381 (5) | passed | 0 / 0 | 6 | seed 1 | 0.0073 0.0050 0.0060 0.0026 | 0.969 | 0.974 |
| `twdp2` g1 | U+1F382..U+1F387 (6) | **failed** | 5 / 6: 16x32 p99, 24x48 glyph_mae, 24x48 mae, 24x48 p99, 48x96 mae, 48x96 p99 | 17 | no: halved | 0.0096 0.0071 0.0099 0.0043 | 0.968 | 0.971 |
| `twdp2r1` g0 (half) | U+1F382..U+1F384 (3) | **failed** | 1 / 1: 24x48 p99 | 5 | **no: left out** | 0.0079 0.0057 0.0068 0.0027 | 0.972 | 0.985 |
| `twdp2r1` g1 (half) | U+1F385..U+1F387 (3) | **failed** | 2 / 2: 48x96 mae, 48x96 p99 | 19 | **no: left out** | 0.0111 0.0080 0.0111 0.0044 | 0.991 | 0.965 |
| `twdp2` g2 | U+1F388..U+1F38C (5) | passed | 0 / 0 | 4 | seed 1 | 0.0056 0.0047 0.0050 0.0025 | 0.966 | 0.975 |
| `twdp2` g3 | U+1F38D..U+1F392 (6) | **failed** | 2 / 2: 10x20 p99, 24x48 p99, 8x16 p99 | 1 | no: halved | 0.0084 0.0057 0.0053 0.0028 | 0.986 | 0.976 |
| `twdp2r3` g0 (half) | U+1F38D..U+1F38F (3) | passed | 0 / 0 | 3 | seed 1 | 0.0091 0.0058 0.0051 0.0024 | 0.998 | 0.977 |
| `twdp2r3` g1 (half) | U+1F390..U+1F392 (3) | **failed** | 1 / 1: 10x20 p99 | 0 | **no: left out** | 0.0063 0.0053 0.0048 0.0026 | 0.979 | 0.976 |
| `twdp2` g4 | U+1F393..U+1F3A4 (6) | **failed** | 1 / 2: 48x96 mae, 8x16 p99 | 16 | no: halved | 0.0083 0.0064 0.0079 0.0032 | 0.974 | 0.969 |
| `twdp2r4` g0 (half) | U+1F393..U+1F3A1 (3) | passed | 0 / 0 | 17 | seed 1 | 0.0094 0.0069 0.0081 0.0030 | 0.974 | 0.962 |
| `twdp2r4` g1 (half) | U+1F3A2..U+1F3A4 (3) | passed | 0 / 0 | 7 | seed 1 | 0.0070 0.0053 0.0066 0.0025 | 0.985 | 0.980 |
| `twdp2` g5 | U+1F3A5..U+1F3A9 (5) | **failed** | 1 / 1: 24x48 mae, 48x96 mae | 14 | no: halved | 0.0074 0.0073 0.0064 0.0030 | 0.963 | 0.966 |
| `twdp2r5` g0 (half) | U+1F3A5..U+1F3A6 (2) | **failed** | 2 / 1: 24x48 firm, 48x96 mae | 16 | **no: left out** | 0.0083 0.0106 0.0079 0.0037 | 0.990 | 0.928 |
| `twdp2r5` g1 (half) | U+1F3A7..U+1F3A9 (3) | **failed** | 1 / 0: 6x12 p99 | 6 | **no: left out** | 0.0062 0.0051 0.0048 0.0023 | 0.944 | 0.991 |
| `twdp2` g6 | U+1F3AA..U+1F3AF (6) | **failed** | 1 / 1: 10x20 p99 | 11 | no: halved | 0.0082 0.0065 0.0065 0.0029 | 0.987 | 0.971 |
| `twdp2r6` g0 (half) | U+1F3AA..U+1F3AC (3) | passed | 0 / 0 | 11 | seed 1 | 0.0099 0.0084 0.0070 0.0029 | 0.990 | 0.961 |
| `twdp2r6` g1 (half) | U+1F3AD..U+1F3AF (3) | passed | 0 / 0 | 5 | seed 1 | 0.0066 0.0041 0.0057 0.0023 | 0.980 | 0.981 |
| `twdp2` g7 | U+1F3B0..U+1F3B4 (5) | **failed** | 1 / 2: 48x96 mae, 8x16 p99 | 9 | no: halved | 0.0092 0.0067 0.0069 0.0031 | 0.994 | 0.986 |
| `twdp2r7` g0 (half) | U+1F3B0..U+1F3B1 (2) | passed | 0 / 0 | 6 | seed 0 | 0.0067 0.0065 0.0059 0.0027 | 0.981 | 0.978 |
| `twdp2r7` g1 (half) | U+1F3B2..U+1F3B4 (3) | passed | 0 / 0 | 9 | seed 0 | 0.0103 0.0068 0.0069 0.0030 | 0.998 | 0.989 |
| `twdp2` g8 | U+1F3B5..U+1F3BA (6) | **failed** | 4 / 3: 16x32 firm, 16x32 glyph_mae, 16x32 p99, 24x48 p99, 48x96 p99 | 10 | no: halved | 0.0070 0.0066 0.0053 0.0030 | 0.981 | 0.957 |
| `twdp2r8` g0 (half) | U+1F3B5..U+1F3B7 (3) | passed | 0 / 0 | 1 | seed 0 | 0.0049 0.0039 0.0039 0.0016 | 1.000 | 0.955 |
| `twdp2r8` g1 (half) | U+1F3B8..U+1F3BA (3) | **failed** | 1 / 2: 24x48 firm, 48x96 mae | 17 | **no: left out** | 0.0088 0.0086 0.0062 0.0034 | 0.975 | 0.961 |
| `twdp2` g9 | U+1F3BB..U+1F3C0 (6) | **failed** | 2 / 2: 12x24 p99, 48x96 mae | 11 | no: halved | 0.0083 0.0061 0.0076 0.0031 | 0.959 | 0.960 |
| `twdp2r9` g0 (half) | U+1F3BB..U+1F3BD (3) | passed | 0 / 0 | 11 | seed 0 | 0.0083 0.0064 0.0063 0.0027 | 0.946 | 0.964 |
| `twdp2r9` g1 (half) | U+1F3BE..U+1F3C0 (3) | **failed** | 1 / 1: 8x16 p99 | 10 | **no: left out** | 0.0080 0.0053 0.0083 0.0031 | 0.970 | 0.958 |
| `twdp3` g0 | U+1F3C1..U+1F3C5 (5) | **failed** | 1 / 1: 24x48 p99 | 9 | no: halved | 0.0073 0.0047 0.0071 0.0029 | 0.934 | 0.980 |
| `twdp3r0` g0 (half) | U+1F3C1..U+1F3C2 (2) | passed | 0 / 0 | 14 | seed 1 | 0.0102 0.0066 0.0094 0.0039 | 0.844 | 0.974 |
| `twdp3r0` g1 (half) | U+1F3C3..U+1F3C5 (3) | **failed** | 1 / 2: 12x24 p99, 24x48 p99 | 4 | **no: left out** | 0.0053 0.0033 0.0053 0.0018 | 0.991 | 0.984 |
| `twdp3` g1 | U+1F3C6..U+1F3CF (6) | **failed** | 0 / 1: 8x16 p99 | 5 | no: halved | 0.0044 0.0033 0.0051 0.0019 | 0.991 | 0.986 |
| `twdp3r1` g0 (half) | U+1F3C6..U+1F3C8 (3) | passed | 0 / 0 | 3 | seed 1 | 0.0046 0.0034 0.0050 0.0018 | 0.989 | 0.983 |
| `twdp3r1` g1 (half) | U+1F3C9..U+1F3CF (3) | **failed** | 1 / 1: 8x16 p99 | 4 | **no: left out** | 0.0039 0.0028 0.0048 0.0017 | 0.988 | 0.989 |
| `twdp3` g2 | U+1F3D0..U+1F3E0 (5) | passed | 0 / 0 | 3 | seed 0 | 0.0043 0.0037 0.0040 0.0018 | 0.979 | 0.974 |
| `twdp3` g3 | U+1F3E1..U+1F3E6 (6) | **failed** | 3 / 4: 16x32 p99, 24x48 firm, 48x96 mae, 48x96 p99 | 18 | no: halved | 0.0150 0.0128 0.0126 0.0070 | 0.969 | 0.957 |
| `twdp3r3` g0 (half) | U+1F3E1..U+1F3E3 (3) | **failed** | 1 / 1: 48x96 p99 | 13 | **no: left out** | 0.0145 0.0110 0.0102 0.0052 | 0.963 | 0.956 |
| `twdp3r3` g1 (half) | U+1F3E4..U+1F3E6 (3) | **failed** | 1 / 1: 48x96 p99 | 17 | **no: left out** | 0.0149 0.0135 0.0130 0.0071 | 0.974 | 0.964 |
| `twdp3` g4 | U+1F3E7..U+1F3EC (6) | **failed** | 5 / 6: 16x32 p99, 24x48 glyph_mae, 24x48 mae, 48x96 mae, 48x96 p99, 8x16 firm | 29 | no: halved | 0.0148 0.0129 0.0128 0.0058 | 0.989 | 0.963 |
| `twdp3r4` g0 (half) | U+1F3E7..U+1F3E9 (3) | **failed** | 3 / 3: 24x48 mae, 48x96 mae, 8x16 firm | 21 | **no: left out** | 0.0108 0.0116 0.0100 0.0035 | 0.988 | 0.983 |
| `twdp3r4` g1 (half) | U+1F3EA..U+1F3EC (3) | **failed** | 2 / 2: 12x24 firm, 48x96 p99 | 23 | **no: left out** | 0.0176 0.0138 0.0134 0.0066 | 0.995 | 0.943 |
| `twdp3` g5 | U+1F3ED..U+1F3F4 (5) | **failed** | 1 / 1: 48x96 p99 | 23 | no: halved | 0.0122 0.0091 0.0101 0.0045 | 0.942 | 0.967 |
| `twdp3r5` g0 (half) | U+1F3ED..U+1F3EE (2) | **failed** | 1 / 1: 24x48 p99 | 8 | **no: left out** | 0.0076 0.0058 0.0062 0.0025 | 0.986 | 0.958 |
| `twdp3r5` g1 (half) | U+1F3EF..U+1F3F4 (3) | passed | 0 / 0 | 23 | seed 1 | 0.0151 0.0112 0.0125 0.0057 | 0.913 | 0.973 |
| `twdp3` g6 | U+1F3F8..U+1F3FD (6) | **failed** | 1 / 1: 8x16 p99 | 17 | no: halved | 0.0101 0.0078 0.0090 0.0034 | 0.879 | 0.899 |
| `twdp3r6` g0 (half) | U+1F3F8..U+1F3FA (3) | passed | 0 / 0 | 9 | seed 0 | 0.0071 0.0058 0.0072 0.0025 | 0.938 | 0.970 |
| `twdp3r6` g1 (half) | U+1F3FB..U+1F3FD (3) | passed | 0 / 0 | 16 | seed 1 | 0.0133 0.0095 0.0110 0.0041 | 0.824 | 0.827 |
| `twdp3` g7 | U+1F3FE..U+1F402 (5) | passed | 0 / 0 | 4 | seed 1 | 0.0058 0.0043 0.0050 0.0021 | 0.979 | 0.942 |
| `twdp3` g8 | U+1F403..U+1F408 (6) | **failed** | 1 / 1: 48x96 mae | 14 | no: halved | 0.0090 0.0058 0.0079 0.0033 | 0.979 | 0.969 |
| `twdp3r8` g0 (half) | U+1F403..U+1F405 (3) | passed | 0 / 0 | 15 | seed 0 | 0.0094 0.0061 0.0087 0.0031 | 0.964 | 0.971 |
| `twdp3r8` g1 (half) | U+1F406..U+1F408 (3) | **failed** | 1 / 0: 10x20 p99 | 9 | **no: left out** | 0.0078 0.0052 0.0061 0.0026 | 0.991 | 0.967 |
| `twdp3` g9 | U+1F409..U+1F40E (6) | passed | 0 / 0 | 6 | seed 1 | 0.0052 0.0040 0.0054 0.0023 | 0.972 | 0.959 |
| `twdp4` g0 | U+1F40F..U+1F413 (5) | passed | 0 / 0 | 6 | seed 0 | 0.0052 0.0036 0.0050 0.0022 | 0.990 | 0.983 |
| `twdp4` g1 | U+1F414..U+1F419 (6) | **failed** | 0 / 1: 10x20 firm | 5 | no: halved | 0.0053 0.0042 0.0055 0.0024 | 0.990 | 0.970 |
| `twdp4r1` g0 (half) | U+1F414..U+1F416 (3) | **failed** | 1 / 0: 10x20 firm | 6 | **no: left out** | 0.0049 0.0039 0.0058 0.0020 | 0.993 | 0.949 |
| `twdp4r1` g1 (half) | U+1F417..U+1F419 (3) | **failed** | 1 / 0: 24x48 p99 | 4 | **no: left out** | 0.0059 0.0043 0.0049 0.0021 | 0.987 | 0.988 |
| `twdp4` g2 | U+1F41A..U+1F41E (5) | **failed** | 0 / 1: 10x20 p99 | 10 | no: halved | 0.0059 0.0053 0.0056 0.0027 | 0.965 | 0.975 |
| `twdp4r2` g0 (half) | U+1F41A..U+1F41B (2) | **failed** | 1 / 0: 24x48 p99 | 8 | **no: left out** | 0.0066 0.0051 0.0057 0.0026 | 0.946 | 0.980 |
| `twdp4r2` g1 (half) | U+1F41C..U+1F41E (3) | passed | 0 / 0 | 8 | seed 1 | 0.0054 0.0051 0.0050 0.0023 | 0.972 | 0.970 |
| `twdp4` g3 | U+1F41F..U+1F424 (6) | passed | 0 / 0 | 8 | seed 0 | 0.0059 0.0044 0.0061 0.0027 | 0.953 | 0.981 |
| `twdp4` g4 | U+1F425..U+1F42A (6) | **failed** | 1 / 1: 24x48 p99 | 4 | no: halved | 0.0050 0.0036 0.0049 0.0024 | 0.991 | 0.978 |
| `twdp4r4` g0 (half) | U+1F425..U+1F427 (3) | passed | 0 / 0 | 4 | seed 0 | 0.0046 0.0032 0.0043 0.0021 | 0.987 | 0.979 |
| `twdp4r4` g1 (half) | U+1F428..U+1F42A (3) | passed | 0 / 0 | 4 | seed 0 | 0.0049 0.0039 0.0051 0.0022 | 0.990 | 0.974 |
| `twdp4` g5 | U+1F42B..U+1F42F (5) | **failed** | 1 / 1: 10x20 p99 | 9 | no: halved | 0.0062 0.0043 0.0061 0.0028 | 0.966 | 0.982 |
| `twdp4r5` g0 (half) | U+1F42B..U+1F42C (2) | passed | 0 / 0 | 4 | seed 0 | 0.0046 0.0034 0.0044 0.0020 | 0.969 | 0.976 |
| `twdp4r5` g1 (half) | U+1F42D..U+1F42F (3) | **failed** | 0 / 1: 8x16 p99 | 9 | **no: left out** | 0.0074 0.0048 0.0073 0.0029 | 0.951 | 0.978 |
| `twdp4` g6 | U+1F430..U+1F435 (6) | passed | 0 / 0 | 10 | seed 1 | 0.0069 0.0045 0.0068 0.0027 | 0.987 | 0.975 |
| `twdp4` g7 | U+1F436..U+1F43A (5) | **failed** | 1 / 2: 48x96 mae, 8x16 p99 | 11 | no: halved | 0.0074 0.0049 0.0079 0.0031 | 0.950 | 0.964 |
| `twdp4r7` g0 (half) | U+1F436..U+1F437 (2) | passed | 0 / 0 | 13 | seed 0 | 0.0085 0.0047 0.0083 0.0030 | 0.924 | 0.976 |
| `twdp4r7` g1 (half) | U+1F438..U+1F43A (3) | **failed** | 2 / 3: 10x20 p99, 12x24 p99, 48x96 firm | 8 | **no: left out** | 0.0067 0.0047 0.0070 0.0028 | 0.969 | 0.974 |
| `twdp4` g8 | U+1F43B..U+1F442 (6) | passed | 0 / 0 | 5 | seed 1 | 0.0050 0.0032 0.0052 0.0020 | 0.986 | 0.959 |
| `twdp4` g9 | U+1F443..U+1F448 (6) | passed | 0 / 0 | 1 | seed 1 | 0.0044 0.0032 0.0035 0.0016 | 0.960 | 0.953 |
| `twdp5` g0 | U+1F449..U+1F44D (5) | **failed** | 1 / 0: 12x24 firm | 5 | no: halved | 0.0056 0.0044 0.0048 0.0019 | 0.958 | 0.970 |
| `twdp5r0` g0 (half) | U+1F449..U+1F44A (2) | passed | 0 / 0 | 1 | seed 1 | 0.0049 0.0032 0.0043 0.0014 | 0.934 | 0.987 |
| `twdp5r0` g1 (half) | U+1F44B..U+1F44D (3) | passed | 0 / 0 | 6 | seed 1 | 0.0058 0.0051 0.0048 0.0020 | 0.974 | 0.961 |
| `twdp5` g1 | U+1F44E..U+1F453 (6) | passed | 0 / 0 | 4 | seed 1 | 0.0057 0.0038 0.0047 0.0019 | 0.976 | 0.973 |
| `twdp5` g2 | U+1F454..U+1F458 (5) | passed | 0 / 0 | 2 | seed 0 | 0.0052 0.0046 0.0041 0.0020 | 0.957 | 0.988 |
| `twdp5` g3 | U+1F459..U+1F45E (6) | passed | 0 / 0 | 0 | seed 0 | 0.0054 0.0045 0.0037 0.0019 | 0.961 | 0.987 |
| `twdp5` g4 | U+1F45F..U+1F464 (6) | passed | 0 / 0 | 1 | seed 0 | 0.0045 0.0034 0.0033 0.0016 | 0.966 | 0.991 |
| `twdp5` g5 | U+1F465..U+1F469 (5) | passed | 0 / 0 | 1 | seed 1 | 0.0044 0.0033 0.0036 0.0017 | 0.983 | 0.989 |
| `twdp5` g6 | U+1F46A..U+1F46F (6) | passed | 0 / 0 | 1 | seed 1 | 0.0055 0.0042 0.0045 0.0021 | 0.997 | 0.970 |
| `twdp5` g7 | U+1F470..U+1F474 (5) | passed | 0 / 0 | 7 | seed 1 | 0.0053 0.0032 0.0052 0.0020 | 0.992 | 0.977 |
| `twdp5` g8 | U+1F475..U+1F47A (6) | passed | 0 / 0 | 3 | seed 0 | 0.0046 0.0038 0.0049 0.0022 | 0.992 | 0.985 |
| `twdp5` g9 | U+1F47B..U+1F480 (6) | **failed** | 6 / 7: 10x20 firm, 10x20 glyph_mae, 10x20 p99, 48x96 mae, 48x96 p99, 8x16 glyph_mae | 23 | no: halved | 0.0105 0.0081 0.0106 0.0049 | 0.988 | 0.976 |
| `twdp5r9` g0 (half) | U+1F47B..U+1F47D (3) | **failed** | 1 / 0: 24x48 firm | 8 | **no: left out** | 0.0056 0.0042 0.0057 0.0021 | 1.000 | 0.983 |
| `twdp5r9` g1 (half) | U+1F47E..U+1F480 (3) | **failed** | 2 / 1: 10x20 firm, 6x12 firm, 8x16 p99 | 23 | **no: left out** | 0.0146 0.0113 0.0148 0.0071 | 0.979 | 0.967 |
| `twdp6` g0 | U+1F481..U+1F485 (5) | passed | 0 / 0 | 1 | seed 0 | 0.0050 0.0045 0.0040 0.0019 | 0.981 | 0.978 |
| `twdp6` g1 | U+1F486..U+1F48B (6) | passed | 0 / 0 | 1 | seed 1 | 0.0036 0.0031 0.0040 0.0019 | 0.978 | 0.997 |
| `twdp6` g2 | U+1F48C..U+1F490 (5) | passed | 0 / 0 | 5 | seed 0 | 0.0066 0.0041 0.0049 0.0023 | 0.994 | 0.983 |
| `twdp6` g3 | U+1F491..U+1F496 (6) | passed | 0 / 0 | 4 | seed 0 | 0.0042 0.0030 0.0042 0.0019 | 0.983 | 0.963 |
| `twdp6` g4 | U+1F497..U+1F49C (6) | passed | 0 / 0 | 0 | seed 1 | 0.0031 0.0021 0.0032 0.0014 | 0.994 | 0.995 |
| `twdp6` g5 | U+1F49D..U+1F4A1 (5) | **failed** | 0 / 1: 48x96 mae | 11 | no: halved | 0.0069 0.0048 0.0068 0.0029 | 0.953 | 0.975 |
| `twdp6r5` g0 (half) | U+1F49D..U+1F49E (2) | passed | 0 / 0 | 12 | seed 0 | 0.0061 0.0032 0.0084 0.0028 | 0.970 | 0.971 |
| `twdp6r5` g1 (half) | U+1F49F..U+1F4A1 (3) | passed | 0 / 0 | 7 | seed 1 | 0.0072 0.0058 0.0056 0.0027 | 0.939 | 0.973 |
| `twdp6` g6 | U+1F4A2..U+1F4A7 (6) | **failed** | 2 / 2: 24x48 p99, 8x16 firm | 4 | no: halved | 0.0048 0.0034 0.0049 0.0021 | 0.987 | 0.983 |
| `twdp6r6` g0 (half) | U+1F4A2..U+1F4A4 (3) | **failed** | 1 / 0: 8x16 p99 | 2 | **no: left out** | 0.0046 0.0030 0.0041 0.0017 | 0.995 | 0.991 |
| `twdp6r6` g1 (half) | U+1F4A5..U+1F4A7 (3) | **failed** | 1 / 1: 24x48 p99 | 6 | **no: left out** | 0.0047 0.0032 0.0050 0.0017 | 0.980 | 0.973 |
| `twdp6` g7 | U+1F4A8..U+1F4AC (5) | passed | 0 / 0 | 3 | seed 1 | 0.0049 0.0031 0.0037 0.0015 | 0.977 | 0.980 |
| `twdp6` g8 | U+1F4AD..U+1F4B2 (6) | **failed** | 3 / 2: 10x20 p99, 48x96 mae, 48x96 p99 | 14 | no: halved | 0.0084 0.0055 0.0078 0.0032 | 0.975 | 0.969 |
| `twdp6r8` g0 (half) | U+1F4AD..U+1F4AF (3) | passed | 0 / 0 | 15 | seed 1 | 0.0100 0.0062 0.0089 0.0030 | 0.965 | 0.970 |
| `twdp6r8` g1 (half) | U+1F4B0..U+1F4B2 (3) | passed | 0 / 0 | 7 | seed 1 | 0.0065 0.0045 0.0064 0.0026 | 0.989 | 0.961 |
| `twdp6` g9 | U+1F4B3..U+1F4B8 (6) | **failed** | 1 / 2: 10x20 p99, 24x48 p99 | 10 | no: halved | 0.0111 0.0063 0.0058 0.0028 | 0.990 | 0.983 |
| `twdp6r9` g0 (half) | U+1F4B3..U+1F4B5 (3) | **failed** | 1 / 0: 8x16 firm | 6 | **no: left out** | 0.0111 0.0061 0.0050 0.0025 | 0.995 | 0.989 |
| `twdp6r9` g1 (half) | U+1F4B6..U+1F4B8 (3) | **failed** | 1 / 1: 10x20 p99 | 12 | **no: left out** | 0.0106 0.0063 0.0059 0.0026 | 0.983 | 0.980 |
| `twdp7` g0 | U+1F4B9..U+1F4BD (5) | **failed** | 1 / 0: 24x48 p99 | 9 | no: halved | 0.0092 0.0066 0.0059 0.0026 | 0.974 | 0.991 |
| `twdp7r0` g0 (half) | U+1F4B9..U+1F4BA (2) | passed | 0 / 0 | 9 | seed 1 | 0.0074 0.0071 0.0057 0.0030 | 0.961 | 0.996 |
| `twdp7r0` g1 (half) | U+1F4BB..U+1F4BD (3) | passed | 0 / 0 | 6 | seed 0 | 0.0102 0.0064 0.0060 0.0021 | 0.996 | 0.990 |
| `twdp7` g1 | U+1F4BE..U+1F4C3 (6) | passed | 0 / 0 | 5 | seed 1 | 0.0081 0.0069 0.0050 0.0023 | 0.990 | 0.977 |
| `twdp7` g2 | U+1F4C4..U+1F4C8 (5) | **failed** | 4 / 3: 24x48 mae, 24x48 p99, 48x96 mae, 8x16 firm | 12 | no: halved | 0.0112 0.0110 0.0076 0.0037 | 0.974 | 0.951 |
| `twdp7r2` g0 (half) | U+1F4C4..U+1F4C5 (2) | passed | 0 / 0 | 10 | seed 0 | 0.0119 0.0106 0.0088 0.0040 | 0.977 | 0.933 |
| `twdp7r2` g1 (half) | U+1F4C6..U+1F4C8 (3) | **failed** | 1 / 1: 48x96 mae | 11 | **no: left out** | 0.0106 0.0112 0.0061 0.0031 | 0.978 | 0.965 |
| `twdp7` g3 | U+1F4C9..U+1F4CE (6) | **failed** | 3 / 4: 10x20 firm, 10x20 p99, 12x24 p99, 24x48 p99, 8x16 p99 | 5 | no: halved | 0.0077 0.0057 0.0055 0.0022 | 0.980 | 0.990 |
| `twdp7r3` g0 (half) | U+1F4C9..U+1F4CB (3) | passed | 0 / 0 | 7 | seed 0 | 0.0098 0.0077 0.0054 0.0024 | 0.972 | 0.991 |
| `twdp7r3` g1 (half) | U+1F4CC..U+1F4CE (3) | **failed** | 1 / 2: 12x24 p99, 24x48 p99 | 5 | **no: left out** | 0.0055 0.0035 0.0050 0.0018 | 0.982 | 0.993 |
| `twdp7` g4 | U+1F4CF..U+1F4D4 (6) | **failed** | 2 / 2: 10x20 firm, 16x32 p99, 48x96 p99 | 17 | no: halved | 0.0096 0.0071 0.0085 0.0041 | 0.962 | 0.988 |
| `twdp7r4` g0 (half) | U+1F4CF..U+1F4D1 (3) | passed | 0 / 0 | 14 | seed 1 | 0.0089 0.0061 0.0081 0.0035 | 0.986 | 0.982 |
| `twdp7r4` g1 (half) | U+1F4D2..U+1F4D4 (3) | passed | 0 / 0 | 13 | seed 1 | 0.0098 0.0082 0.0084 0.0043 | 0.941 | 0.993 |
| `twdp7` g5 | U+1F4D5..U+1F4D9 (5) | passed | 0 / 0 | 8 | seed 1 | 0.0131 0.0083 0.0119 0.0037 | 1.000 | 0.977 |
| `twdp7` g6 | U+1F4DA..U+1F4DF (6) | **failed** | 2 / 3: 10x20 p99, 24x48 p99, 8x16 p99 | 6 | no: halved | 0.0082 0.0072 0.0054 0.0026 | 0.983 | 0.970 |
| `twdp7r6` g0 (half) | U+1F4DA..U+1F4DC (3) | passed | 0 / 0 | 9 | seed 0 | 0.0109 0.0082 0.0057 0.0027 | 0.980 | 0.987 |
| `twdp7r6` g1 (half) | U+1F4DD..U+1F4DF (3) | passed | 0 / 0 | 0 | seed 1 | 0.0049 0.0061 0.0040 0.0021 | 0.988 | 0.955 |
| `twdp7` g7 | U+1F4E0..U+1F4E4 (5) | **failed** | 3 / 1: 24x48 p99, 48x96 mae, 6x12 firm | 14 | no: halved | 0.0084 0.0064 0.0063 0.0030 | 0.988 | 0.987 |
| `twdp7r7` g0 (half) | U+1F4E0..U+1F4E1 (2) | **failed** | 3 / 3: 24x48 mae, 24x48 p99, 48x96 p99, 6x12 firm | 17 | **no: left out** | 0.0100 0.0071 0.0076 0.0039 | 0.995 | 0.983 |
| `twdp7r7` g1 (half) | U+1F4E2..U+1F4E4 (3) | passed | 0 / 0 | 3 | seed 1 | 0.0070 0.0056 0.0047 0.0019 | 0.977 | 0.992 |
| `twdp7` g8 | U+1F4E5..U+1F4EA (6) | **failed** | 1 / 3: 10x20 firm, 24x48 mae, 48x96 mae | 9 | no: halved | 0.0090 0.0068 0.0072 0.0032 | 0.964 | 0.984 |
| `twdp7r8` g0 (half) | U+1F4E5..U+1F4E7 (3) | **failed** | 2 / 1: 12x24 p99, 24x48 p99 | 11 | **no: left out** | 0.0098 0.0075 0.0070 0.0032 | 0.993 | 0.990 |
| `twdp7r8` g1 (half) | U+1F4E8..U+1F4EA (3) | passed | 0 / 0 | 7 | seed 1 | 0.0079 0.0058 0.0069 0.0028 | 0.933 | 0.984 |
| `twdp7` g9 | U+1F4EB..U+1F4F0 (6) | **failed** | 4 / 3: 16x32 p99, 48x96 mae, 48x96 p99, 8x16 p99 | 12 | no: halved | 0.0100 0.0071 0.0072 0.0036 | 0.965 | 0.985 |
| `twdp7r9` g0 (half) | U+1F4EB..U+1F4ED (3) | passed | 0 / 0 | 13 | seed 1 | 0.0103 0.0079 0.0085 0.0034 | 0.947 | 0.984 |
| `twdp7r9` g1 (half) | U+1F4EE..U+1F4F0 (3) | passed | 0 / 0 | 6 | seed 0 | 0.0095 0.0062 0.0049 0.0025 | 0.975 | 0.985 |
| `twdp8` g0 | U+1F4F1..U+1F4F5 (5) | **failed** | 5 / 3: 16x32 firm, 24x48 mae, 24x48 p99, 48x96 mae, 48x96 p99 | 14 | no: halved | 0.0107 0.0106 0.0084 0.0041 | 0.934 | 0.914 |
| `twdp8r0` g0 (half) | U+1F4F1..U+1F4F2 (2) | passed | 0 / 0 | 6 | seed 1 | 0.0072 0.0076 0.0066 0.0028 | 0.889 | 0.788 |
| `twdp8r0` g1 (half) | U+1F4F3..U+1F4F5 (3) | **failed** | 2 / 2: 24x48 mae, 48x96 mae | 14 | **no: left out** | 0.0129 0.0121 0.0081 0.0039 | 0.968 | 0.998 |
| `twdp8` g1 | U+1F4F6..U+1F4FB (6) | **failed** | 2 / 3: 12x24 p99, 24x48 mae, 24x48 p99, 48x96 mae | 13 | no: halved | 0.0118 0.0090 0.0073 0.0035 | 0.950 | 0.982 |
| `twdp8r1` g0 (half) | U+1F4F6..U+1F4F8 (3) | **failed** | 1 / 2: 16x32 p99, 24x48 p99 | 15 | **no: left out** | 0.0133 0.0112 0.0087 0.0041 | 0.906 | 0.977 |
| `twdp8r1` g1 (half) | U+1F4F9..U+1F4FB (3) | **failed** | 1 / 2: 10x20 p99, 8x16 p99 | 7 | **no: left out** | 0.0102 0.0069 0.0052 0.0024 | 0.996 | 0.988 |
| `twdp8` g2 | U+1F4FC..U+1F502 (5) | **failed** | 2 / 1: 10x20 p99, 12x24 p99, 8x16 p99 | 9 | no: halved | 0.0079 0.0046 0.0063 0.0028 | 0.986 | 0.968 |
| `twdp8r2` g0 (half) | U+1F4FC..U+1F4FF (2) | passed | 0 / 0 | 12 | seed 1 | 0.0113 0.0060 0.0074 0.0039 | 0.990 | 0.946 |
| `twdp8r2` g1 (half) | U+1F500..U+1F502 (3) | **failed** | 1 / 1: 24x48 p99 | 6 | **no: left out** | 0.0055 0.0037 0.0054 0.0021 | 0.990 | 0.982 |
| `twdp8` g3 | U+1F503..U+1F508 (6) | passed | 0 / 0 | 0 | seed 0 | 0.0043 0.0029 0.0041 0.0018 | 0.982 | 0.985 |
| `twdp8` g4 | U+1F509..U+1F50E (6) | **failed** | 0 / 1: 6x12 p99 | 6 | no: halved | 0.0058 0.0042 0.0042 0.0020 | 0.972 | 0.985 |
| `twdp8r4` g0 (half) | U+1F509..U+1F50B (3) | passed | 0 / 0 | 7 | seed 0 | 0.0070 0.0056 0.0046 0.0023 | 0.989 | 0.989 |
| `twdp8r4` g1 (half) | U+1F50C..U+1F50E (3) | passed | 0 / 0 | 1 | seed 1 | 0.0043 0.0029 0.0036 0.0016 | 0.957 | 0.983 |
| `twdp8` g5 | U+1F50F..U+1F513 (5) | **failed** | 1 / 1: 8x16 p99 | 4 | no: halved | 0.0049 0.0035 0.0039 0.0016 | 0.988 | 0.984 |
| `twdp8r5` g0 (half) | U+1F50F..U+1F510 (2) | **failed** | 1 / 0: 8x16 p99 | 6 | **no: left out** | 0.0067 0.0042 0.0056 0.0020 | 0.996 | 0.991 |
| `twdp8r5` g1 (half) | U+1F511..U+1F513 (3) | **failed** | 1 / 2: 6x12 p99, 8x16 p99 | 1 | **no: left out** | 0.0035 0.0029 0.0027 0.0012 | 0.986 | 0.979 |
| `twdp8` g6 | U+1F514..U+1F519 (6) | **failed** | 1 / 1: 6x12 p99 | 4 | no: halved | 0.0061 0.0041 0.0055 0.0020 | 0.989 | 0.981 |
| `twdp8r6` g0 (half) | U+1F514..U+1F516 (3) | passed | 0 / 0 | 0 | seed 0 | 0.0050 0.0039 0.0045 0.0017 | 0.991 | 0.989 |
| `twdp8r6` g1 (half) | U+1F517..U+1F519 (3) | **failed** | 1 / 1: 12x24 firm, 8x16 p99 | 10 | **no: left out** | 0.0073 0.0045 0.0065 0.0022 | 0.984 | 0.978 |
| `twdp8` g7 | U+1F51A..U+1F51E (5) | **failed** | 2 / 2: 12x24 p99, 48x96 mae, 8x16 firm | 15 | no: halved | 0.0089 0.0065 0.0079 0.0031 | 0.925 | 0.980 |
| `twdp8r7` g0 (half) | U+1F51A..U+1F51B (2) | passed | 0 / 0 | 15 | seed 1 | 0.0088 0.0074 0.0072 0.0028 | 0.916 | 0.974 |
| `twdp8r7` g1 (half) | U+1F51C..U+1F51E (3) | **failed** | 2 / 2: 10x20 p99, 8x16 firm | 14 | **no: left out** | 0.0089 0.0060 0.0076 0.0029 | 0.931 | 0.986 |
| `twdp8` g8 | U+1F51F..U+1F524 (6) | **failed** | 3 / 2: 24x48 mae, 48x96 mae, 6x12 firm | 18 | no: halved | 0.0115 0.0095 0.0077 0.0036 | 0.915 | 0.991 |
| `twdp8r8` g0 (half) | U+1F51F..U+1F521 (3) | **failed** | 2 / 2: 24x48 mae, 48x96 mae | 14 | **no: left out** | 0.0121 0.0097 0.0073 0.0034 | 0.915 | 0.992 |
| `twdp8r8` g1 (half) | U+1F522..U+1F524 (3) | **failed** | 2 / 3: 12x24 p99, 24x48 mae, 48x96 mae | 16 | **no: left out** | 0.0115 0.0093 0.0078 0.0033 | 0.923 | 0.989 |
| `twdp8` g9 | U+1F525..U+1F52A (6) | passed | 0 / 0 | 4 | seed 1 | 0.0039 0.0027 0.0041 0.0020 | 0.984 | 0.984 |
| `twdp9` g0 | U+1F52B..U+1F52F (5) | passed | 0 / 0 | 2 | seed 0 | 0.0050 0.0038 0.0043 0.0021 | 0.992 | 0.977 |
| `twdp9` g1 | U+1F530..U+1F535 (6) | passed | 0 / 0 | 7 | seed 1 | 0.0080 0.0066 0.0043 0.0024 | 0.966 | 0.974 |
| `twdp9` g2 | U+1F536..U+1F53A (5) | passed | 0 / 0 | 0 | seed 0 | 0.0006 0.0010 0.0013 0.0005 | 0.997 | 0.974 |
| `twdp9` g3 | U+1F53B..U+1F54D (6) | passed | 0 / 0 | 3 | seed 1 | 0.0055 0.0048 0.0040 0.0018 | 0.996 | 0.995 |
| `twdp9` g4 | U+1F54E..U+1F554 (6) | **failed** | 2 / 3: 24x48 firm, 24x48 glyph_mae, 48x96 mae | 12 | no: halved | 0.0079 0.0044 0.0070 0.0031 | 0.993 | 0.948 |
| `twdp9r4` g0 (half) | U+1F54E..U+1F551 (3) | **failed** | 2 / 2: 12x24 p99, 24x48 glyph_mae, 48x96 mae | 16 | **no: left out** | 0.0097 0.0062 0.0088 0.0038 | 0.993 | 0.943 |
| `twdp9r4` g1 (half) | U+1F552..U+1F554 (3) | passed | 0 / 0 | 2 | seed 0 | 0.0058 0.0027 0.0048 0.0019 | 1.000 | 0.954 |
| `twdp9` g5 | U+1F555..U+1F559 (5) | passed | 0 / 0 | 2 | seed 1 | 0.0057 0.0027 0.0049 0.0020 | 0.999 | 0.951 |
| `twdp9` g6 | U+1F55A..U+1F55F (6) | passed | 0 / 0 | 2 | seed 0 | 0.0056 0.0028 0.0047 0.0020 | 0.991 | 0.948 |
| `twdp9` g7 | U+1F560..U+1F564 (5) | passed | 0 / 0 | 2 | seed 0 | 0.0051 0.0027 0.0043 0.0019 | 0.995 | 0.950 |
| `twdp9` g8 | U+1F565..U+1F596 (6) | passed | 0 / 0 | 1 | seed 1 | 0.0051 0.0030 0.0042 0.0018 | 0.993 | 0.971 |
| `twdp9` g9 | U+1F5A4..U+1F5FF (6) | passed | 0 / 0 | 5 | seed 1 | 0.0039 0.0034 0.0038 0.0017 | 0.990 | 0.979 |

## Recipe

- **Drawings.** `train/wide.py` and its parts put each drawing of the
  18×18 box into the net's cell (1 wide, 2 high) with every stroke as its
  outline, so a lying stroke is as thick as a standing one once the cell is
  drawn at half height. Drawn from the Unicode name and the charts' words;
  no font was opened or rasterised to make or check any drawing, and no
  emoji image was looked at.
- **Sets and groups.** 10 sets, each cut in order into group nets
  (100 in all); 53 failed and were trained again as halves, so
  the bundle holds 103 nets of 2 to 6 characters.
- **Training.** `train/split_expert.py train --mode repertoire --partition
  contiguous`, unchanged: hidden width 64, 120,000 steps, the project teacher
  (grid 256), seeds 0 and 1. A halved group: the set `NAMErI` of that
  group's characters, two parts, the rest the same.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from
  each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
python3 train/build_wide_pictographs_v1.py    # rebuilds the .nrt byte for byte from the group nets
make test-wide-pictographs-v1
```

## Checks

`make test-wide-pictographs-v1` (part of `make test`): every group net against
the float64 reference; the bundle rebuilt byte for byte; its table exactly
`neuronte-wide-pictographs-v1.symbols.txt`; no character in two of the four wide bundles, 1,335 in
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
| `neuronte-wide-pictographs-v1.nrt` | The bundle, 5,877,536 bytes, sha256 `23927eee77ed3fface892c71538167b3dfb34bc16e15123f3856a6f8d31d7eeb` |
| `neuronte-wide-pictographs-v1.symbols.txt` | The 416 characters it was trained on |
| `neuronte-wide-pictographs-v1-SET-gN.json` | The 103 group nets as trained (the shipped seed) |
| `neuronte-wide-pictographs-v1.provenance.json` | Every member's hash and scalars, written by its build script |
| `neuronte-wide-pictographs-v1.validation.json` | The gates' hashes, both seeds' measurements and failures for every group and half, the limits eased, what was left out |
