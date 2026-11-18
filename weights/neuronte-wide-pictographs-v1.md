# wide-pictographs-v1: 273 wide characters drawn for a box of two cells

`neuronte-wide-pictographs-v1.nrt` draws the first half of the wide characters of Miscellaneous Symbols and Pictographs (U+1F300..1F448): characters that a terminal gives two cells
(East Asian Width W or F), 279 of the 1,335 that the five neuronte-wide
bundles draw between them, with no character in two of them.
The pictographs are two files, neuronte-wide-pictographs-v1 (U+1F300..1F448)
and neuronte-wide-pictographs2-v1 (U+1F449..1F5FF), because one bundle file
holds at most 127 group nets and the pictographs, with the failed nets the
owner chose to ship, have 146. A program that wants all of them opens both. Each is this
project's own drawing for the **box of two cells**, made from its Unicode
name and the charts' description of it in words, on a grid of 18 by 18
units with pens of 2 units (1/9 of the box).

It is a **standalone** bundle: 78 known-only group nets and one blank net,
4,451,088 bytes. It is not a default and replaces nothing; the one-cell
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

`neuronte_untrained(wide, c)` is 0 for exactly the 273 characters of
`neuronte-wide-pictographs-v1.symbols.txt` and 1 for every other scalar.

**This file is not a listed bundle.** Some of its code points are drawn for
one cell in a terminal bundle (for instance by `neuronte-term-rest-v1`), and
this file draws them again for another box, so the rule that no two listed
bundles claim one character (`tests/check_bundle_lists.py`) cannot hold for
it. Its list is `neuronte-wide-pictographs-v1.symbols.txt`; `tests/check_wide.py` holds the table
to it exactly and holds the five wide bundles apart from each other.

## Colour twins, by the owner's choice

Unicode tells 2 of these characters apart from a sibling only by
colour. A one-colour font has no way to show that, and the owner chose
(2026-11-18) **identical twins**: each shape is drawn once and every colour
of it the same, as in a one-colour font. They are in the bundle as twins on
purpose, and the gates allow identical drawings.

U+1F34E U+1F34F

## FAILED nets in the bundle, by the owner's word

**27 nets in this bundle FAILED gates v2.3** (as a group and again as a half).
The owner looked at a sheet of every failed half, each drawing beside its
net (2026-11-18), and chose "Within 25%": every failed half whose
lower-error seed misses its limits by at most 25% ships all the same, as
that seed. Over the five wide bundles that is 95 of the 120 failed halves;
the other 25 stay out (below). They are marked FAILED in the table below
and in the validation record (`failed_gates_shipped_by_owner`, with the
margin in `owner_margin`). For each: the shipped seed's worst miss, as
value against limit, and every rule either seed missed:

- `twdp0r1` g0 (U+1F305 U+1F306 U+1F307): seed 0 misses 24x48 mae by 1.9% (0.0065 against 0.0064); missed 24x48 mae
- `twdp0r1` g1 (U+1F308 U+1F309 U+1F30A): seed 0 misses 10x20 p99 by 3.7% (0.0832 against 0.0803); missed 10x20 p99
- `twdp0r8` g0 (U+1F339 U+1F33A): seed 1 passed, only the other seed failed; missed 8x16 p99
- `twdp0r8` g1 (U+1F33B U+1F33C U+1F33D): seed 1 passed, only the other seed failed; missed 16x32 p99, 6x12 p99
- `twdp0r9` g1 (U+1F341 U+1F342 U+1F343): seed 1 misses 6x12 p99 by 24.1% (0.1423 against 0.1146); missed 10x20 p99, 6x12 p99
- `twdp1r0` g1 (U+1F346 U+1F347 U+1F348): seed 0 misses 24x48 firm by 13.6% (0.0014 against 0.0013); missed 24x48 firm
- `twdp1r4` g1 (U+1F35D U+1F35E U+1F35F): seed 0 passed, only the other seed failed; missed 10x20 p99
- `twdp1r7` g0 (U+1F36B U+1F36C): seed 1 misses 12x24 p99 by 2.8% (0.0838 against 0.0815); missed 12x24 p99
- `twdp1r7` g1 (U+1F36D U+1F36E U+1F36F): seed 1 misses 24x48 p99 by 4.4% (0.1035 against 0.0992); missed 16x32 p99, 24x48 p99
- `twdp2r1` g0 (U+1F382 U+1F383 U+1F384): seed 1 misses 24x48 p99 by 2.9% (0.1320 against 0.1282); missed 24x48 p99
- `twdp2r1` g1 (U+1F385 U+1F386 U+1F387): seed 1 misses 48x96 p99 by 17.4% (0.0818 against 0.0697); missed 48x96 mae, 48x96 p99
- `twdp2r3` g1 (U+1F390 U+1F391 U+1F392): seed 1 misses 10x20 p99 by 12.1% (0.0798 against 0.0711); missed 10x20 p99
- `twdp2r5` g0 (U+1F3A5 U+1F3A6): seed 1 misses 48x96 mae by 1.7% (0.0037 against 0.0036); missed 24x48 firm, 48x96 mae
- `twdp2r5` g1 (U+1F3A7 U+1F3A8 U+1F3A9): seed 0 misses 6x12 p99 by 3.2% (0.1429 against 0.1385); missed 6x12 p99
- `twdp2r8` g1 (U+1F3B8 U+1F3B9 U+1F3BA): seed 0 misses 48x96 mae by 4.4% (0.0034 against 0.0032); missed 24x48 firm, 48x96 mae
- `twdp2r9` g1 (U+1F3BE U+1F3BF U+1F3C0): seed 1 misses 8x16 p99 by 0.6% (0.1170 against 0.1163); missed 8x16 p99
- `twdp3r0` g1 (U+1F3C3 U+1F3C4 U+1F3C5): seed 0 misses 12x24 p99 by 12.3% (0.0947 against 0.0843); missed 12x24 p99, 24x48 p99
- `twdp3r1` g1 (U+1F3C9 U+1F3CA U+1F3CF): seed 0 misses 8x16 p99 by 6.5% (0.1060 against 0.0995); missed 8x16 p99
- `twdp3r3` g0 (U+1F3E1 U+1F3E2 U+1F3E3): seed 1 misses 48x96 p99 by 20.1% (0.0802 against 0.0668); missed 48x96 p99
- `twdp3r3` g1 (U+1F3E4 U+1F3E5 U+1F3E6): seed 0 misses 48x96 p99 by 24.2% (0.0830 against 0.0668); missed 48x96 p99
- `twdp3r5` g0 (U+1F3ED U+1F3EE): seed 0 misses 24x48 p99 by 2.3% (0.0927 against 0.0905); missed 24x48 p99
- `twdp3r8` g1 (U+1F406 U+1F407 U+1F408): seed 1 passed, only the other seed failed; missed 10x20 p99
- `twdp4r1` g0 (U+1F414 U+1F415 U+1F416): seed 1 passed, only the other seed failed; missed 10x20 firm
- `twdp4r1` g1 (U+1F417 U+1F418 U+1F419): seed 0 misses 24x48 p99 by 1.1% (0.0938 against 0.0928); missed 24x48 p99
- `twdp4r2` g0 (U+1F41A U+1F41B): seed 1 passed, only the other seed failed; missed 24x48 p99
- `twdp4r5` g1 (U+1F42D U+1F42E U+1F42F): seed 1 misses 8x16 p99 by 4.5% (0.1420 against 0.1359); missed 8x16 p99
- `twdp4r7` g1 (U+1F438 U+1F439 U+1F43A): seed 1 misses 10x20 p99 by 4.2% (0.0755 against 0.0724); missed 10x20 p99, 12x24 p99, 48x96 firm

## Left out

**6 drawn characters are not in the bundle.** Their nets failed the
gates twice (as a group, then as a half), and the better seed missed its
limits by more than 25%, so they are outside the owner's choice "Within
25%" and stay out; the characters stay untrained:
U+1F3E7 U+1F3E8 U+1F3E9 U+1F3EA U+1F3EB U+1F3EC.

Across the five wide bundles, the halves that failed again missed
error-amount rules (the 99th percentile, the mean error, firm wrong pixels),
mostly at 24×48 and 48×96. No group or half failed the rule that each
character is nearest its own drawing, and none vanished. These width-64
nets draw the detailed pictographs recognisably but not exactly enough at
the large boxes. Of the 120 failed halves, the owner shipped the 95 within
25% (marked FAILED above) and left out the other 25 (74 characters); 9 of
those miss by more than double.

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
none-vanished are never eased. **532 limits were eased** for the nets in this
bundle; each is in the validation record with the declared limit, the
perfect drawing's score and the limit applied.

A group whose two seeds pass ships the seed with the lower mean error at
8×16, 16×32 and 48×96. A group that fails is trained once more as two nets
of half its characters each; a half that fails is left out. Nothing else that failed ships: the owner named the failed halves in the
bundle after looking at each beside its drawing.

- 50 groups trained; 20 passed with both seeds.
- 30 failed and were halved; of the 60 halves 58 passed.
- 2 halves failed again and are left out (6 characters); 27 more failed again and are in the bundle by the owner's word, marked FAILED.

## Results by net

Mean error against the teacher and mean overlap at counted cells, for the shipped seed (for a net not in the bundle: seed 0).

| Net | Characters | Gates v2.3 | Rules missed (seed 0 / seed 1) | Limits eased | In the bundle | Mean error 12×24 / 16×32 / 24×48 / 48×96 | Overlap 16×32 | Overlap 24×48 |
|---|---|---|---|---:|---|---|---:|---:|
| `twdp0` g0 | U+1F300..U+1F304 (5) | **failed** | 1 / 0: 24x48 p99 | 7 | no: halved | 0.0069 0.0058 0.0060 0.0028 | 0.992 | 0.969 |
| `twdp0r0` g0 (half) | U+1F300..U+1F301 (2) | passed | 0 / 0 | 2 | seed 1 | 0.0072 0.0051 0.0054 0.0028 | 0.985 | 0.968 |
| `twdp0r0` g1 (half) | U+1F302..U+1F304 (3) | passed | 0 / 0 | 9 | seed 1 | 0.0064 0.0061 0.0056 0.0020 | 0.998 | 0.969 |
| `twdp0` g1 | U+1F305..U+1F30A (6) | **failed** | 3 / 3: 24x48 mae, 24x48 p99, 48x96 mae | 11 | no: halved | 0.0082 0.0070 0.0072 0.0033 | 0.984 | 0.973 |
| `twdp0r1` g0 (half) | U+1F305..U+1F307 (3) | **failed** | 1 / 0: 24x48 mae | 7 | **seed 0: FAILED, in by the owner's word** | 0.0082 0.0078 0.0065 0.0028 | 0.980 | 0.983 |
| `twdp0r1` g1 (half) | U+1F308..U+1F30A (3) | **failed** | 1 / 0: 10x20 p99 | 10 | **seed 0: FAILED, in by the owner's word** | 0.0075 0.0058 0.0061 0.0029 | 0.990 | 0.961 |
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
| `twdp0r8` g0 (half) | U+1F339..U+1F33A (2) | **failed** | 1 / 0: 8x16 p99 | 6 | **seed 1: FAILED, in by the owner's word** | 0.0054 0.0032 0.0055 0.0018 | 1.000 | 0.976 |
| `twdp0r8` g1 (half) | U+1F33B..U+1F33D (3) | **failed** | 2 / 0: 16x32 p99, 6x12 p99 | 10 | **seed 1: FAILED, in by the owner's word** | 0.0068 0.0043 0.0074 0.0026 | 0.975 | 0.971 |
| `twdp0` g9 | U+1F33E..U+1F343 (6) | **failed** | 2 / 0: 24x48 p99, 6x12 p99 | 2 | no: halved | 0.0056 0.0036 0.0058 0.0023 | 0.897 | 0.984 |
| `twdp0r9` g0 (half) | U+1F33E..U+1F340 (3) | passed | 0 / 0 | 2 | seed 1 | 0.0058 0.0041 0.0056 0.0023 | 0.855 | 0.985 |
| `twdp0r9` g1 (half) | U+1F341..U+1F343 (3) | **failed** | 2 / 2: 10x20 p99, 6x12 p99 | 4 | **seed 1: FAILED, in by the owner's word** | 0.0046 0.0028 0.0049 0.0016 | 0.949 | 0.986 |
| `twdp1` g0 | U+1F344..U+1F348 (5) | **failed** | 1 / 2: 10x20 firm, 24x48 firm | 7 | no: halved | 0.0062 0.0042 0.0054 0.0026 | 0.989 | 0.985 |
| `twdp1r0` g0 (half) | U+1F344..U+1F345 (2) | passed | 0 / 0 | 5 | seed 0 | 0.0055 0.0038 0.0046 0.0019 | 0.983 | 0.978 |
| `twdp1r0` g1 (half) | U+1F346..U+1F348 (3) | **failed** | 1 / 1: 24x48 firm | 7 | **seed 0: FAILED, in by the owner's word** | 0.0067 0.0041 0.0059 0.0027 | 0.994 | 0.987 |
| `twdp1` g1 | U+1F349..U+1F34E (6) | **failed** | 0 / 3: 10x20 p99, 24x48 firm, 24x48 p99 | 3 | no: halved | 0.0045 0.0031 0.0042 0.0020 | 0.983 | 0.985 |
| `twdp1r1` g0 (half) | U+1F349..U+1F34B (3) | passed | 0 / 0 | 0 | seed 1 | 0.0037 0.0027 0.0032 0.0013 | 0.992 | 0.987 |
| `twdp1r1` g1 (half) | U+1F34C..U+1F34E (3) | passed | 0 / 0 | 6 | seed 1 | 0.0051 0.0035 0.0049 0.0022 | 0.970 | 0.981 |
| `twdp1` g2 | U+1F34F..U+1F353 (5) | passed | 0 / 0 | 1 | seed 1 | 0.0032 0.0027 0.0030 0.0015 | 0.990 | 0.993 |
| `twdp1` g3 | U+1F354..U+1F359 (6) | passed | 0 / 0 | 1 | seed 0 | 0.0048 0.0035 0.0037 0.0018 | 0.966 | 0.995 |
| `twdp1` g4 | U+1F35A..U+1F35F (6) | **failed** | 2 / 4: 10x20 p99, 48x96 mae, 48x96 p99, 6x12 p99 | 10 | no: halved | 0.0073 0.0049 0.0070 0.0031 | 0.986 | 0.982 |
| `twdp1r4` g0 (half) | U+1F35A..U+1F35C (3) | passed | 0 / 0 | 10 | seed 1 | 0.0077 0.0050 0.0074 0.0028 | 0.979 | 0.990 |
| `twdp1r4` g1 (half) | U+1F35D..U+1F35F (3) | **failed** | 0 / 1: 10x20 p99 | 6 | **seed 0: FAILED, in by the owner's word** | 0.0066 0.0048 0.0061 0.0027 | 0.991 | 0.974 |
| `twdp1` g5 | U+1F360..U+1F364 (5) | passed | 0 / 0 | 1 | seed 0 | 0.0039 0.0026 0.0031 0.0015 | 0.993 | 0.996 |
| `twdp1` g6 | U+1F365..U+1F36A (6) | passed | 0 / 0 | 4 | seed 1 | 0.0045 0.0038 0.0050 0.0021 | 0.984 | 0.991 |
| `twdp1` g7 | U+1F36B..U+1F36F (5) | **failed** | 1 / 1: 24x48 p99 | 6 | no: halved | 0.0067 0.0045 0.0057 0.0025 | 0.944 | 0.988 |
| `twdp1r7` g0 (half) | U+1F36B..U+1F36C (2) | **failed** | 0 / 1: 12x24 p99 | 4 | **seed 1: FAILED, in by the owner's word** | 0.0066 0.0037 0.0055 0.0023 | 0.967 | 0.988 |
| `twdp1r7` g1 (half) | U+1F36D..U+1F36F (3) | **failed** | 1 / 2: 16x32 p99, 24x48 p99 | 5 | **seed 1: FAILED, in by the owner's word** | 0.0067 0.0046 0.0055 0.0021 | 0.931 | 0.986 |
| `twdp1` g8 | U+1F370..U+1F375 (6) | passed | 0 / 0 | 4 | seed 1 | 0.0081 0.0062 0.0054 0.0025 | 0.927 | 0.969 |
| `twdp1` g9 | U+1F376..U+1F37B (6) | passed | 0 / 0 | 5 | seed 0 | 0.0056 0.0045 0.0052 0.0022 | 0.925 | 0.958 |
| `twdp2` g0 | U+1F37C..U+1F381 (5) | passed | 0 / 0 | 6 | seed 1 | 0.0073 0.0050 0.0060 0.0026 | 0.969 | 0.974 |
| `twdp2` g1 | U+1F382..U+1F387 (6) | **failed** | 5 / 6: 16x32 p99, 24x48 glyph_mae, 24x48 mae, 24x48 p99, 48x96 mae, 48x96 p99 | 17 | no: halved | 0.0096 0.0071 0.0099 0.0043 | 0.968 | 0.971 |
| `twdp2r1` g0 (half) | U+1F382..U+1F384 (3) | **failed** | 1 / 1: 24x48 p99 | 5 | **seed 1: FAILED, in by the owner's word** | 0.0080 0.0056 0.0067 0.0028 | 0.970 | 0.986 |
| `twdp2r1` g1 (half) | U+1F385..U+1F387 (3) | **failed** | 2 / 2: 48x96 mae, 48x96 p99 | 19 | **seed 1: FAILED, in by the owner's word** | 0.0109 0.0079 0.0113 0.0045 | 0.986 | 0.957 |
| `twdp2` g2 | U+1F388..U+1F38C (5) | passed | 0 / 0 | 4 | seed 1 | 0.0056 0.0047 0.0050 0.0025 | 0.966 | 0.975 |
| `twdp2` g3 | U+1F38D..U+1F392 (6) | **failed** | 2 / 2: 10x20 p99, 24x48 p99, 8x16 p99 | 1 | no: halved | 0.0084 0.0057 0.0053 0.0028 | 0.986 | 0.976 |
| `twdp2r3` g0 (half) | U+1F38D..U+1F38F (3) | passed | 0 / 0 | 3 | seed 1 | 0.0091 0.0058 0.0051 0.0024 | 0.998 | 0.977 |
| `twdp2r3` g1 (half) | U+1F390..U+1F392 (3) | **failed** | 1 / 1: 10x20 p99 | 0 | **seed 1: FAILED, in by the owner's word** | 0.0064 0.0054 0.0047 0.0025 | 0.975 | 0.976 |
| `twdp2` g4 | U+1F393..U+1F3A4 (6) | **failed** | 1 / 2: 48x96 mae, 8x16 p99 | 16 | no: halved | 0.0083 0.0064 0.0079 0.0032 | 0.974 | 0.969 |
| `twdp2r4` g0 (half) | U+1F393..U+1F3A1 (3) | passed | 0 / 0 | 17 | seed 1 | 0.0094 0.0069 0.0081 0.0030 | 0.974 | 0.962 |
| `twdp2r4` g1 (half) | U+1F3A2..U+1F3A4 (3) | passed | 0 / 0 | 7 | seed 1 | 0.0070 0.0053 0.0066 0.0025 | 0.985 | 0.980 |
| `twdp2` g5 | U+1F3A5..U+1F3A9 (5) | **failed** | 1 / 1: 24x48 mae, 48x96 mae | 14 | no: halved | 0.0074 0.0073 0.0064 0.0030 | 0.963 | 0.966 |
| `twdp2r5` g0 (half) | U+1F3A5..U+1F3A6 (2) | **failed** | 2 / 1: 24x48 firm, 48x96 mae | 16 | **seed 1: FAILED, in by the owner's word** | 0.0082 0.0106 0.0078 0.0037 | 0.992 | 0.928 |
| `twdp2r5` g1 (half) | U+1F3A7..U+1F3A9 (3) | **failed** | 1 / 0: 6x12 p99 | 6 | **seed 0: FAILED, in by the owner's word** | 0.0062 0.0051 0.0048 0.0023 | 0.944 | 0.991 |
| `twdp2` g6 | U+1F3AA..U+1F3AF (6) | **failed** | 1 / 1: 10x20 p99 | 11 | no: halved | 0.0082 0.0065 0.0065 0.0029 | 0.987 | 0.971 |
| `twdp2r6` g0 (half) | U+1F3AA..U+1F3AC (3) | passed | 0 / 0 | 11 | seed 1 | 0.0099 0.0084 0.0070 0.0029 | 0.990 | 0.961 |
| `twdp2r6` g1 (half) | U+1F3AD..U+1F3AF (3) | passed | 0 / 0 | 5 | seed 1 | 0.0066 0.0041 0.0057 0.0023 | 0.980 | 0.981 |
| `twdp2` g7 | U+1F3B0..U+1F3B4 (5) | **failed** | 1 / 2: 48x96 mae, 8x16 p99 | 9 | no: halved | 0.0092 0.0067 0.0069 0.0031 | 0.994 | 0.986 |
| `twdp2r7` g0 (half) | U+1F3B0..U+1F3B1 (2) | passed | 0 / 0 | 6 | seed 0 | 0.0067 0.0065 0.0059 0.0027 | 0.981 | 0.978 |
| `twdp2r7` g1 (half) | U+1F3B2..U+1F3B4 (3) | passed | 0 / 0 | 9 | seed 0 | 0.0103 0.0068 0.0069 0.0030 | 0.998 | 0.989 |
| `twdp2` g8 | U+1F3B5..U+1F3BA (6) | **failed** | 4 / 3: 16x32 firm, 16x32 glyph_mae, 16x32 p99, 24x48 p99, 48x96 p99 | 10 | no: halved | 0.0070 0.0066 0.0053 0.0030 | 0.981 | 0.957 |
| `twdp2r8` g0 (half) | U+1F3B5..U+1F3B7 (3) | passed | 0 / 0 | 1 | seed 0 | 0.0049 0.0039 0.0039 0.0016 | 1.000 | 0.955 |
| `twdp2r8` g1 (half) | U+1F3B8..U+1F3BA (3) | **failed** | 1 / 2: 24x48 firm, 48x96 mae | 17 | **seed 0: FAILED, in by the owner's word** | 0.0088 0.0086 0.0062 0.0034 | 0.975 | 0.961 |
| `twdp2` g9 | U+1F3BB..U+1F3C0 (6) | **failed** | 2 / 2: 12x24 p99, 48x96 mae | 11 | no: halved | 0.0083 0.0061 0.0076 0.0031 | 0.959 | 0.960 |
| `twdp2r9` g0 (half) | U+1F3BB..U+1F3BD (3) | passed | 0 / 0 | 11 | seed 0 | 0.0083 0.0064 0.0063 0.0027 | 0.946 | 0.964 |
| `twdp2r9` g1 (half) | U+1F3BE..U+1F3C0 (3) | **failed** | 1 / 1: 8x16 p99 | 10 | **seed 1: FAILED, in by the owner's word** | 0.0079 0.0053 0.0081 0.0030 | 0.970 | 0.961 |
| `twdp3` g0 | U+1F3C1..U+1F3C5 (5) | **failed** | 1 / 1: 24x48 p99 | 9 | no: halved | 0.0073 0.0047 0.0071 0.0029 | 0.934 | 0.980 |
| `twdp3r0` g0 (half) | U+1F3C1..U+1F3C2 (2) | passed | 0 / 0 | 14 | seed 1 | 0.0102 0.0066 0.0094 0.0039 | 0.844 | 0.974 |
| `twdp3r0` g1 (half) | U+1F3C3..U+1F3C5 (3) | **failed** | 1 / 2: 12x24 p99, 24x48 p99 | 4 | **seed 0: FAILED, in by the owner's word** | 0.0053 0.0033 0.0053 0.0018 | 0.991 | 0.984 |
| `twdp3` g1 | U+1F3C6..U+1F3CF (6) | **failed** | 0 / 1: 8x16 p99 | 5 | no: halved | 0.0044 0.0033 0.0051 0.0019 | 0.991 | 0.986 |
| `twdp3r1` g0 (half) | U+1F3C6..U+1F3C8 (3) | passed | 0 / 0 | 3 | seed 1 | 0.0046 0.0034 0.0050 0.0018 | 0.989 | 0.983 |
| `twdp3r1` g1 (half) | U+1F3C9..U+1F3CF (3) | **failed** | 1 / 1: 8x16 p99 | 4 | **seed 0: FAILED, in by the owner's word** | 0.0039 0.0028 0.0048 0.0017 | 0.988 | 0.989 |
| `twdp3` g2 | U+1F3D0..U+1F3E0 (5) | passed | 0 / 0 | 3 | seed 0 | 0.0043 0.0037 0.0040 0.0018 | 0.979 | 0.974 |
| `twdp3` g3 | U+1F3E1..U+1F3E6 (6) | **failed** | 3 / 4: 16x32 p99, 24x48 firm, 48x96 mae, 48x96 p99 | 18 | no: halved | 0.0150 0.0128 0.0126 0.0070 | 0.969 | 0.957 |
| `twdp3r3` g0 (half) | U+1F3E1..U+1F3E3 (3) | **failed** | 1 / 1: 48x96 p99 | 13 | **seed 1: FAILED, in by the owner's word** | 0.0143 0.0111 0.0104 0.0052 | 0.971 | 0.956 |
| `twdp3r3` g1 (half) | U+1F3E4..U+1F3E6 (3) | **failed** | 1 / 1: 48x96 p99 | 17 | **seed 0: FAILED, in by the owner's word** | 0.0149 0.0135 0.0130 0.0071 | 0.974 | 0.964 |
| `twdp3` g4 | U+1F3E7..U+1F3EC (6) | **failed** | 5 / 6: 16x32 p99, 24x48 glyph_mae, 24x48 mae, 48x96 mae, 48x96 p99, 8x16 firm | 29 | no: halved | 0.0148 0.0129 0.0128 0.0058 | 0.989 | 0.963 |
| `twdp3r4` g0 (half) | U+1F3E7..U+1F3E9 (3) | **failed** | 3 / 3: 24x48 mae, 48x96 mae, 8x16 firm | 21 | **no: left out** | 0.0108 0.0116 0.0100 0.0035 | 0.988 | 0.983 |
| `twdp3r4` g1 (half) | U+1F3EA..U+1F3EC (3) | **failed** | 2 / 2: 12x24 firm, 48x96 p99 | 23 | **no: left out** | 0.0176 0.0138 0.0134 0.0066 | 0.995 | 0.943 |
| `twdp3` g5 | U+1F3ED..U+1F3F4 (5) | **failed** | 1 / 1: 48x96 p99 | 23 | no: halved | 0.0122 0.0091 0.0101 0.0045 | 0.942 | 0.967 |
| `twdp3r5` g0 (half) | U+1F3ED..U+1F3EE (2) | **failed** | 1 / 1: 24x48 p99 | 8 | **seed 0: FAILED, in by the owner's word** | 0.0076 0.0058 0.0062 0.0025 | 0.986 | 0.958 |
| `twdp3r5` g1 (half) | U+1F3EF..U+1F3F4 (3) | passed | 0 / 0 | 23 | seed 1 | 0.0151 0.0112 0.0125 0.0057 | 0.913 | 0.973 |
| `twdp3` g6 | U+1F3F8..U+1F3FD (6) | **failed** | 1 / 1: 8x16 p99 | 17 | no: halved | 0.0101 0.0078 0.0090 0.0034 | 0.879 | 0.899 |
| `twdp3r6` g0 (half) | U+1F3F8..U+1F3FA (3) | passed | 0 / 0 | 9 | seed 0 | 0.0071 0.0058 0.0072 0.0025 | 0.938 | 0.970 |
| `twdp3r6` g1 (half) | U+1F3FB..U+1F3FD (3) | passed | 0 / 0 | 16 | seed 1 | 0.0133 0.0095 0.0110 0.0041 | 0.824 | 0.827 |
| `twdp3` g7 | U+1F3FE..U+1F402 (5) | passed | 0 / 0 | 4 | seed 1 | 0.0058 0.0043 0.0050 0.0021 | 0.979 | 0.942 |
| `twdp3` g8 | U+1F403..U+1F408 (6) | **failed** | 1 / 1: 48x96 mae | 14 | no: halved | 0.0090 0.0058 0.0079 0.0033 | 0.979 | 0.969 |
| `twdp3r8` g0 (half) | U+1F403..U+1F405 (3) | passed | 0 / 0 | 15 | seed 0 | 0.0094 0.0061 0.0087 0.0031 | 0.964 | 0.971 |
| `twdp3r8` g1 (half) | U+1F406..U+1F408 (3) | **failed** | 1 / 0: 10x20 p99 | 9 | **seed 1: FAILED, in by the owner's word** | 0.0080 0.0051 0.0062 0.0026 | 0.988 | 0.968 |
| `twdp3` g9 | U+1F409..U+1F40E (6) | passed | 0 / 0 | 6 | seed 1 | 0.0052 0.0040 0.0054 0.0023 | 0.972 | 0.959 |
| `twdp4` g0 | U+1F40F..U+1F413 (5) | passed | 0 / 0 | 6 | seed 0 | 0.0052 0.0036 0.0050 0.0022 | 0.990 | 0.983 |
| `twdp4` g1 | U+1F414..U+1F419 (6) | **failed** | 0 / 1: 10x20 firm | 5 | no: halved | 0.0053 0.0042 0.0055 0.0024 | 0.990 | 0.970 |
| `twdp4r1` g0 (half) | U+1F414..U+1F416 (3) | **failed** | 1 / 0: 10x20 firm | 6 | **seed 1: FAILED, in by the owner's word** | 0.0048 0.0040 0.0057 0.0021 | 0.995 | 0.956 |
| `twdp4r1` g1 (half) | U+1F417..U+1F419 (3) | **failed** | 1 / 0: 24x48 p99 | 4 | **seed 0: FAILED, in by the owner's word** | 0.0059 0.0043 0.0049 0.0021 | 0.987 | 0.988 |
| `twdp4` g2 | U+1F41A..U+1F41E (5) | **failed** | 0 / 1: 10x20 p99 | 10 | no: halved | 0.0059 0.0053 0.0056 0.0027 | 0.965 | 0.975 |
| `twdp4r2` g0 (half) | U+1F41A..U+1F41B (2) | **failed** | 1 / 0: 24x48 p99 | 8 | **seed 1: FAILED, in by the owner's word** | 0.0066 0.0051 0.0057 0.0027 | 0.949 | 0.982 |
| `twdp4r2` g1 (half) | U+1F41C..U+1F41E (3) | passed | 0 / 0 | 8 | seed 1 | 0.0054 0.0051 0.0050 0.0023 | 0.972 | 0.970 |
| `twdp4` g3 | U+1F41F..U+1F424 (6) | passed | 0 / 0 | 8 | seed 0 | 0.0059 0.0044 0.0061 0.0027 | 0.953 | 0.981 |
| `twdp4` g4 | U+1F425..U+1F42A (6) | **failed** | 1 / 1: 24x48 p99 | 4 | no: halved | 0.0050 0.0036 0.0049 0.0024 | 0.991 | 0.978 |
| `twdp4r4` g0 (half) | U+1F425..U+1F427 (3) | passed | 0 / 0 | 4 | seed 0 | 0.0046 0.0032 0.0043 0.0021 | 0.987 | 0.979 |
| `twdp4r4` g1 (half) | U+1F428..U+1F42A (3) | passed | 0 / 0 | 4 | seed 0 | 0.0049 0.0039 0.0051 0.0022 | 0.990 | 0.974 |
| `twdp4` g5 | U+1F42B..U+1F42F (5) | **failed** | 1 / 1: 10x20 p99 | 9 | no: halved | 0.0062 0.0043 0.0061 0.0028 | 0.966 | 0.982 |
| `twdp4r5` g0 (half) | U+1F42B..U+1F42C (2) | passed | 0 / 0 | 4 | seed 0 | 0.0046 0.0034 0.0044 0.0020 | 0.969 | 0.976 |
| `twdp4r5` g1 (half) | U+1F42D..U+1F42F (3) | **failed** | 0 / 1: 8x16 p99 | 9 | **seed 1: FAILED, in by the owner's word** | 0.0072 0.0047 0.0073 0.0027 | 0.951 | 0.984 |
| `twdp4` g6 | U+1F430..U+1F435 (6) | passed | 0 / 0 | 10 | seed 1 | 0.0069 0.0045 0.0068 0.0027 | 0.987 | 0.975 |
| `twdp4` g7 | U+1F436..U+1F43A (5) | **failed** | 1 / 2: 48x96 mae, 8x16 p99 | 11 | no: halved | 0.0074 0.0049 0.0079 0.0031 | 0.950 | 0.964 |
| `twdp4r7` g0 (half) | U+1F436..U+1F437 (2) | passed | 0 / 0 | 13 | seed 0 | 0.0085 0.0047 0.0083 0.0030 | 0.924 | 0.976 |
| `twdp4r7` g1 (half) | U+1F438..U+1F43A (3) | **failed** | 2 / 3: 10x20 p99, 12x24 p99, 48x96 firm | 8 | **seed 1: FAILED, in by the owner's word** | 0.0068 0.0046 0.0071 0.0028 | 0.973 | 0.972 |
| `twdp4` g8 | U+1F43B..U+1F442 (6) | passed | 0 / 0 | 5 | seed 1 | 0.0050 0.0032 0.0052 0.0020 | 0.986 | 0.959 |
| `twdp4` g9 | U+1F443..U+1F448 (6) | passed | 0 / 0 | 1 | seed 1 | 0.0044 0.0032 0.0035 0.0016 | 0.960 | 0.953 |

## The boxes in use that the gates do not count (information)

The shipped seed of each net at the cell a program asks for the boxes
18×18, 20×20 and 36×36, by the scorer's own metric code against the bundle
teacher, and in the box itself (each pair of rows averaged) against the
teacher's area coverage of the box. Declared as information before
training; it decides nothing.

| Net | 18×36: error, 99th pct | 20×40 | 36×72 | Box 18×18: error | Box 20×20 | Box 36×36 | Not nearest or vanished |
|---|---|---|---|---:|---:|---:|---|
| `twdp0r0` g0 | 0.0048, 0.051 | 0.0043, 0.044 | 0.0034, 0.053 | 0.0043 | 0.0039 | 0.0029 | none |
| `twdp0r0` g1 | 0.0039, 0.055 | 0.0054, 0.057 | 0.0027, 0.047 | 0.0037 | 0.0050 | 0.0026 | none |
| `twdp0r1` g0 | 0.0058, 0.081 | 0.0064, 0.059 | 0.0040, 0.069 | 0.0055 | 0.0061 | 0.0038 | none |
| `twdp0r1` g1 | 0.0053, 0.053 | 0.0043, 0.057 | 0.0041, 0.062 | 0.0047 | 0.0038 | 0.0037 | none |
| `twdp0` g2 | 0.0032, 0.041 | 0.0043, 0.048 | 0.0034, 0.064 | 0.0027 | 0.0037 | 0.0029 | none |
| `twdp0r3` g0 | 0.0038, 0.057 | 0.0033, 0.053 | 0.0030, 0.050 | 0.0030 | 0.0028 | 0.0025 | none |
| `twdp0r3` g1 | 0.0024, 0.031 | 0.0020, 0.029 | 0.0021, 0.043 | 0.0019 | 0.0017 | 0.0017 | none |
| `twdp0` g4 | 0.0020, 0.028 | 0.0020, 0.032 | 0.0019, 0.045 | 0.0017 | 0.0017 | 0.0015 | none |
| `twdp0r5` g0 | 0.0024, 0.031 | 0.0024, 0.035 | 0.0023, 0.045 | 0.0019 | 0.0019 | 0.0019 | none |
| `twdp0r5` g1 | 0.0040, 0.048 | 0.0032, 0.038 | 0.0036, 0.061 | 0.0032 | 0.0026 | 0.0032 | none |
| `twdp0` g6 | 0.0034, 0.052 | 0.0024, 0.043 | 0.0024, 0.047 | 0.0031 | 0.0022 | 0.0021 | none |
| `twdp0` g7 | 0.0035, 0.053 | 0.0025, 0.047 | 0.0023, 0.045 | 0.0032 | 0.0022 | 0.0020 | none |
| `twdp0r8` g0 | 0.0038, 0.055 | 0.0030, 0.038 | 0.0028, 0.051 | 0.0033 | 0.0024 | 0.0025 | none |
| `twdp0r8` g1 | 0.0041, 0.061 | 0.0033, 0.044 | 0.0038, 0.070 | 0.0034 | 0.0027 | 0.0034 | none |
| `twdp0r9` g0 | 0.0038, 0.049 | 0.0044, 0.056 | 0.0035, 0.057 | 0.0033 | 0.0038 | 0.0032 | none |
| `twdp0r9` g1 | 0.0024, 0.032 | 0.0022, 0.043 | 0.0025, 0.054 | 0.0021 | 0.0019 | 0.0022 | none |
| `twdp1r0` g0 | 0.0029, 0.053 | 0.0029, 0.045 | 0.0025, 0.054 | 0.0024 | 0.0026 | 0.0022 | none |
| `twdp1r0` g1 | 0.0045, 0.055 | 0.0038, 0.051 | 0.0035, 0.055 | 0.0037 | 0.0034 | 0.0031 | none |
| `twdp1r1` g0 | 0.0022, 0.039 | 0.0017, 0.030 | 0.0018, 0.041 | 0.0017 | 0.0013 | 0.0016 | none |
| `twdp1r1` g1 | 0.0032, 0.059 | 0.0030, 0.058 | 0.0032, 0.054 | 0.0027 | 0.0026 | 0.0027 | none |
| `twdp1` g2 | 0.0021, 0.032 | 0.0022, 0.041 | 0.0019, 0.040 | 0.0016 | 0.0018 | 0.0016 | none |
| `twdp1` g3 | 0.0032, 0.051 | 0.0028, 0.051 | 0.0022, 0.048 | 0.0030 | 0.0026 | 0.0019 | none |
| `twdp1r4` g0 | 0.0046, 0.065 | 0.0041, 0.069 | 0.0040, 0.060 | 0.0041 | 0.0037 | 0.0037 | none |
| `twdp1r4` g1 | 0.0044, 0.053 | 0.0045, 0.058 | 0.0041, 0.065 | 0.0041 | 0.0042 | 0.0037 | none |
| `twdp1` g5 | 0.0026, 0.050 | 0.0021, 0.053 | 0.0021, 0.050 | 0.0022 | 0.0018 | 0.0018 | none |
| `twdp1` g6 | 0.0028, 0.049 | 0.0027, 0.041 | 0.0024, 0.050 | 0.0024 | 0.0022 | 0.0021 | none |
| `twdp1r7` g0 | 0.0033, 0.052 | 0.0032, 0.046 | 0.0036, 0.062 | 0.0028 | 0.0027 | 0.0032 | none |
| `twdp1r7` g1 | 0.0041, 0.055 | 0.0034, 0.045 | 0.0035, 0.064 | 0.0036 | 0.0030 | 0.0032 | none |
| `twdp1` g8 | 0.0048, 0.053 | 0.0047, 0.053 | 0.0037, 0.062 | 0.0043 | 0.0043 | 0.0034 | none |
| `twdp1` g9 | 0.0035, 0.053 | 0.0040, 0.057 | 0.0030, 0.062 | 0.0032 | 0.0036 | 0.0027 | none |
| `twdp2` g0 | 0.0043, 0.060 | 0.0037, 0.054 | 0.0035, 0.065 | 0.0037 | 0.0031 | 0.0031 | none |
| `twdp2r1` g0 | 0.0055, 0.064 | 0.0040, 0.054 | 0.0043, 0.083 | 0.0050 | 0.0037 | 0.0038 | none |
| `twdp2r1` g1 | 0.0055, 0.091 | 0.0061, 0.088 | 0.0061, 0.122 | 0.0046 | 0.0054 | 0.0055 | none |
| `twdp2` g2 | 0.0038, 0.053 | 0.0034, 0.050 | 0.0029, 0.052 | 0.0034 | 0.0031 | 0.0027 | none |
| `twdp2r3` g0 | 0.0064, 0.055 | 0.0051, 0.057 | 0.0034, 0.055 | 0.0061 | 0.0048 | 0.0032 | none |
| `twdp2r3` g1 | 0.0043, 0.051 | 0.0039, 0.056 | 0.0032, 0.057 | 0.0039 | 0.0034 | 0.0029 | none |
| `twdp2r4` g0 | 0.0046, 0.052 | 0.0055, 0.059 | 0.0041, 0.068 | 0.0041 | 0.0050 | 0.0037 | none |
| `twdp2r4` g1 | 0.0045, 0.051 | 0.0046, 0.057 | 0.0033, 0.051 | 0.0040 | 0.0041 | 0.0029 | none |
| `twdp2r5` g0 | 0.0056, 0.061 | 0.0081, 0.069 | 0.0052, 0.069 | 0.0053 | 0.0077 | 0.0048 | none |
| `twdp2r5` g1 | 0.0020, 0.050 | 0.0043, 0.057 | 0.0015, 0.035 | 0.0019 | 0.0038 | 0.0013 | none |
| `twdp2r6` g0 | 0.0061, 0.067 | 0.0070, 0.061 | 0.0050, 0.062 | 0.0059 | 0.0067 | 0.0048 | none |
| `twdp2r6` g1 | 0.0033, 0.044 | 0.0031, 0.035 | 0.0033, 0.057 | 0.0027 | 0.0024 | 0.0028 | none |
| `twdp2r7` g0 | 0.0038, 0.050 | 0.0047, 0.057 | 0.0033, 0.053 | 0.0033 | 0.0043 | 0.0029 | none |
| `twdp2r7` g1 | 0.0057, 0.054 | 0.0042, 0.047 | 0.0043, 0.061 | 0.0052 | 0.0037 | 0.0039 | none |
| `twdp2r8` g0 | 0.0032, 0.050 | 0.0029, 0.056 | 0.0023, 0.053 | 0.0029 | 0.0027 | 0.0021 | none |
| `twdp2r8` g1 | 0.0054, 0.061 | 0.0069, 0.079 | 0.0045, 0.063 | 0.0052 | 0.0065 | 0.0042 | none |
| `twdp2r9` g0 | 0.0047, 0.049 | 0.0045, 0.060 | 0.0046, 0.072 | 0.0040 | 0.0040 | 0.0042 | none |
| `twdp2r9` g1 | 0.0036, 0.049 | 0.0043, 0.057 | 0.0036, 0.057 | 0.0028 | 0.0036 | 0.0029 | none |
| `twdp3r0` g0 | 0.0054, 0.054 | 0.0055, 0.058 | 0.0034, 0.053 | 0.0049 | 0.0052 | 0.0033 | none |
| `twdp3r0` g1 | 0.0031, 0.053 | 0.0021, 0.037 | 0.0026, 0.056 | 0.0027 | 0.0018 | 0.0023 | none |
| `twdp3r1` g0 | 0.0032, 0.050 | 0.0023, 0.052 | 0.0025, 0.051 | 0.0027 | 0.0020 | 0.0021 | none |
| `twdp3r1` g1 | 0.0026, 0.041 | 0.0019, 0.028 | 0.0026, 0.054 | 0.0022 | 0.0016 | 0.0022 | none |
| `twdp3` g2 | 0.0029, 0.050 | 0.0026, 0.045 | 0.0024, 0.050 | 0.0025 | 0.0022 | 0.0020 | none |
| `twdp3r3` g0 | 0.0090, 0.069 | 0.0100, 0.066 | 0.0063, 0.079 | 0.0086 | 0.0098 | 0.0062 | none |
| `twdp3r3` g1 | 0.0109, 0.074 | 0.0126, 0.089 | 0.0091, 0.122 | 0.0104 | 0.0123 | 0.0089 | none |
| `twdp3r5` g0 | 0.0043, 0.053 | 0.0050, 0.058 | 0.0036, 0.058 | 0.0042 | 0.0048 | 0.0034 | none |
| `twdp3r5` g1 | 0.0091, 0.195 | 0.0072, 0.112 | 0.0074, 0.192 | 0.0089 | 0.0069 | 0.0072 | none |
| `twdp3r6` g0 | 0.0040, 0.058 | 0.0040, 0.057 | 0.0038, 0.065 | 0.0035 | 0.0036 | 0.0034 | none |
| `twdp3r6` g1 | 0.0055, 0.051 | 0.0071, 0.077 | 0.0037, 0.052 | 0.0055 | 0.0071 | 0.0037 | none |
| `twdp3` g7 | 0.0038, 0.053 | 0.0028, 0.052 | 0.0028, 0.055 | 0.0036 | 0.0026 | 0.0026 | none |
| `twdp3r8` g0 | 0.0059, 0.074 | 0.0054, 0.061 | 0.0043, 0.065 | 0.0052 | 0.0048 | 0.0039 | none |
| `twdp3r8` g1 | 0.0043, 0.054 | 0.0046, 0.059 | 0.0035, 0.064 | 0.0040 | 0.0042 | 0.0032 | none |
| `twdp3` g9 | 0.0037, 0.059 | 0.0030, 0.045 | 0.0031, 0.067 | 0.0033 | 0.0025 | 0.0029 | none |
| `twdp4` g0 | 0.0034, 0.054 | 0.0031, 0.052 | 0.0030, 0.062 | 0.0030 | 0.0028 | 0.0027 | none |
| `twdp4r1` g0 | 0.0037, 0.053 | 0.0032, 0.049 | 0.0028, 0.058 | 0.0034 | 0.0029 | 0.0026 | none |
| `twdp4r1` g1 | 0.0038, 0.052 | 0.0032, 0.051 | 0.0031, 0.056 | 0.0031 | 0.0026 | 0.0026 | none |
| `twdp4r2` g0 | 0.0034, 0.055 | 0.0037, 0.057 | 0.0035, 0.059 | 0.0029 | 0.0033 | 0.0033 | none |
| `twdp4r2` g1 | 0.0037, 0.052 | 0.0039, 0.053 | 0.0027, 0.053 | 0.0033 | 0.0034 | 0.0025 | none |
| `twdp4` g3 | 0.0037, 0.055 | 0.0032, 0.049 | 0.0036, 0.073 | 0.0032 | 0.0028 | 0.0031 | none |
| `twdp4r4` g0 | 0.0027, 0.050 | 0.0027, 0.046 | 0.0023, 0.046 | 0.0023 | 0.0022 | 0.0020 | none |
| `twdp4r4` g1 | 0.0033, 0.048 | 0.0029, 0.041 | 0.0031, 0.059 | 0.0029 | 0.0024 | 0.0028 | none |
| `twdp4r5` g0 | 0.0028, 0.050 | 0.0022, 0.040 | 0.0026, 0.054 | 0.0024 | 0.0020 | 0.0023 | none |
| `twdp4r5` g1 | 0.0044, 0.051 | 0.0035, 0.039 | 0.0041, 0.063 | 0.0035 | 0.0028 | 0.0035 | none |
| `twdp4` g6 | 0.0042, 0.052 | 0.0035, 0.048 | 0.0038, 0.068 | 0.0034 | 0.0029 | 0.0032 | none |
| `twdp4r7` g0 | 0.0047, 0.051 | 0.0041, 0.059 | 0.0046, 0.079 | 0.0037 | 0.0035 | 0.0039 | none |
| `twdp4r7` g1 | 0.0043, 0.051 | 0.0036, 0.048 | 0.0042, 0.064 | 0.0036 | 0.0030 | 0.0035 | none |
| `twdp4` g8 | 0.0028, 0.041 | 0.0024, 0.033 | 0.0028, 0.052 | 0.0022 | 0.0019 | 0.0023 | none |
| `twdp4` g9 | 0.0028, 0.053 | 0.0025, 0.051 | 0.0022, 0.052 | 0.0026 | 0.0022 | 0.0020 | none |

## Recipe

- **Drawings.** `train/wide.py` and its parts put each drawing of the
  18×18 box into the net's cell (1 wide, 2 high) with every stroke as its
  outline, so a lying stroke is as thick as a standing one once the cell is
  drawn at half height. Drawn from the Unicode name and the charts' words;
  no font was opened or rasterised to make or check any drawing, and no
  emoji image was looked at.
- **Sets and groups.** 5 sets, each cut in order into group nets
  (50 in all); 30 failed and were trained again as halves, so
  the bundle holds 78 nets of 2 to 6 characters.
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
`neuronte-wide-pictographs-v1.symbols.txt`; no character in two of the five wide bundles, 1,335 in
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
| `neuronte-wide-pictographs-v1.nrt` | The bundle, 4,451,088 bytes, sha256 `fd6a943eed3366653911a4ec9be9915f09edd540df3316cf1948270bbc2917d2` |
| `neuronte-wide-pictographs-v1.symbols.txt` | The 273 characters it was trained on |
| `neuronte-wide-pictographs-v1-SET-gN.json` | The 78 group nets as trained (the shipped seed) |
| `neuronte-wide-pictographs-v1.provenance.json` | Every member's hash and scalars, written by its build script |
| `neuronte-wide-pictographs-v1.validation.json` | The gates' hashes, both seeds' measurements and failures for every group and half, the limits eased, what was left out |
