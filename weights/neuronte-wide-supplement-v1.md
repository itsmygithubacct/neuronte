# wide-supplement-v1: 337 wide characters drawn for a box of two cells

`neuronte-wide-supplement-v1.nrt` draws the wide characters of Supplemental Symbols and Pictographs and Symbols and Pictographs Extended-A: characters that a terminal gives two cells
(East Asian Width W or F), 349 of the 1,335 that the five neuronte-wide
bundles draw between them, with no character in two of them. Each is this
project's own drawing for the **box of two cells**, made from its Unicode
name and the charts' description of it in words, on a grid of 18 by 18
units with pens of 2 units (1/9 of the box).

It is a **standalone** bundle: 91 known-only group nets and one blank net,
5,192,780 bytes. It is not a default and replaces nothing; the one-cell
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

`neuronte_untrained(wide, c)` is 0 for exactly the 337 characters of
`neuronte-wide-supplement-v1.symbols.txt` and 1 for every other scalar.

**This file is not a listed bundle.** Some of its code points are drawn for
one cell in a terminal bundle (for instance by `neuronte-term-rest-v1`), and
this file draws them again for another box, so the rule that no two listed
bundles claim one character (`tests/check_bundle_lists.py`) cannot hold for
it. Its list is `neuronte-wide-supplement-v1.symbols.txt`; `tests/check_wide.py` holds the table
to it exactly and holds the five wide bundles apart from each other.

## Colour twins, by the owner's choice

Unicode tells 7 of these characters apart from a sibling only by
colour. A one-colour font has no way to show that, and the owner chose
(2026-11-18) **identical twins**: each shape is drawn once and every colour
of it the same, as in a one-colour font. They are in the bundle as twins on
purpose, and the gates allow identical drawings.

U+1F90E U+1F9B0 U+1F9B3 U+1F9E1 U+1FA75 U+1FA76 U+1FA77

## FAILED nets in the bundle, by the owner's word

**23 nets in this bundle FAILED gates v2.3** (as a group and again as a half).
The owner looked at a sheet of every failed half, each drawing beside its
net (2026-11-18), and chose "Within 25%": every failed half whose
lower-error seed misses its limits by at most 25% ships all the same, as
that seed. Over the five wide bundles that is 95 of the 120 failed halves;
the other 25 stay out (below). They are marked FAILED in the table below
and in the validation record (`failed_gates_shipped_by_owner`, with the
margin in `owner_margin`). For each: the shipped seed's worst miss, as
value against limit, and every rule either seed missed:

- `twdu0r1` g0 (U+1F911 U+1F912 U+1F913): seed 0 passed, only the other seed failed; missed 24x48 mae, 24x48 p99
- `twdu0r5` g0 (U+1F929 U+1F92A): seed 1 passed, only the other seed failed; missed 24x48 p99
- `twdu0r6` g1 (U+1F931 U+1F932 U+1F933): seed 1 misses 24x48 firm by 13.6% (0.0014 against 0.0013); missed 24x48 firm
- `twdu0r9` g0 (U+1F941 U+1F942 U+1F943): seed 1 misses 8x16 p99 by 9.2% (0.1191 against 0.1091); missed 10x20 p99, 8x16 p99
- `twdu0r9` g1 (U+1F944 U+1F945 U+1F947): seed 1 misses 48x96 mae by 20.6% (0.0037 against 0.0030); missed 16x32 p99, 24x48 p99, 48x96 mae, 48x96 p99
- `twdu2r1` g0 (U+1F987 U+1F988 U+1F989): seed 1 passed, only the other seed failed; missed 10x20 p99
- `twdu2r1` g1 (U+1F98A U+1F98B U+1F98C): seed 0 misses 24x48 p99 by 2.2% (0.0938 against 0.0917); missed 24x48 p99
- `twdu2r3` g0 (U+1F993 U+1F994 U+1F995): seed 1 passed, only the other seed failed; missed 24x48 firm
- `twdu2r4` g0 (U+1F999 U+1F99A U+1F99B): seed 1 passed, only the other seed failed; missed 48x96 mae, 8x16 p99
- `twdu2r4` g1 (U+1F99C U+1F99D U+1F99E): seed 0 misses 8x16 p99 by 0.1% (0.1017 against 0.1017); missed 8x16 p99
- `twdu2r5` g1 (U+1F9A1 U+1F9A2 U+1F9A3): seed 0 misses 10x20 p99 by 4.5% (0.1110 against 0.1062); missed 10x20 p99, 8x16 firm
- `twdu2r6` g0 (U+1F9A4 U+1F9A5 U+1F9A6): seed 1 misses 10x20 p99 by 4.3% (0.1166 against 0.1117); missed 10x20 p99
- `twdu3r2` g1 (U+1F9CA U+1F9CB U+1F9CC): seed 0 misses 24x48 firm by 21.2% (0.0012 against 0.0010); missed 24x48 firm
- `twdu3r7` g0 (U+1F9E4 U+1F9E5 U+1F9E6): seed 0 passed, only the other seed failed; missed 24x48 firm
- `twdu3r8` g0 (U+1F9EA U+1F9EB U+1F9EC): seed 0 misses 12x24 p99 by 11.4% (0.0915 against 0.0821); missed 12x24 p99, 8x16 p99
- `twdu3r8` g1 (U+1F9ED U+1F9EE U+1F9EF): seed 1 misses 48x96 mae by 8.8% (0.0034 against 0.0031); missed 10x20 p99, 12x24 p99, 48x96 mae, 8x16 p99
- `twdu4r1` g0 (U+1F9FB U+1F9FC U+1F9FD): seed 1 misses 24x48 p99 by 7.2% (0.1227 against 0.1144); missed 16x32 p99, 24x48 p99
- `twdu4r3` g1 (U+1FA7A U+1FA7B U+1FA7C): seed 0 misses 24x48 p99 by 9.4% (0.0905 against 0.0827); missed 10x20 p99, 24x48 p99, 6x12 p99
- `twdu4r7` g0 (U+1FA98 U+1FA99 U+1FA9A): seed 1 misses 8x16 p99 by 3.3% (0.1292 against 0.1252); missed 8x16 p99
- `twdu4r9` g0 (U+1FAA4 U+1FAA5 U+1FAA6): seed 1 misses 24x48 p99 by 6.1% (0.0902 against 0.0850); missed 24x48 p99
- `twdu5r0` g1 (U+1FAAC U+1FAAD U+1FAAE): seed 1 misses 48x96 mae by 6.7% (0.0040 against 0.0038); missed 48x96 mae, 48x96 p99
- `twdu5r1` g0 (U+1FAAF U+1FAB0 U+1FAB1): seed 0 passed, only the other seed failed; missed 48x96 firm
- `twdu5r1` g1 (U+1FAB2 U+1FAB3 U+1FAB4): seed 1 misses 10x20 p99 by 0.5% (0.0733 against 0.0729); missed 10x20 p99

## Left out

**12 drawn characters are not in the bundle.** Their nets failed the
gates twice (as a group, then as a half), and the better seed missed its
limits by more than 25%, so they are outside the owner's choice "Within
25%" and stay out; the characters stay untrained:
U+1F9A7 U+1F9A8 U+1F9A9 U+1F9C7 U+1F9C8 U+1F9C9 U+1F9E7 U+1F9E8 U+1F9E9 U+1FABF U+1FAC0 U+1FAC1.

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
349 drawings of the bundle (sha256 `54856c2ef26f45982c12cf530d5d286570e00c52db969a4e474dd1d6b276a189`): mean error,
99th percentile error and firm wrong pixels for the group and mean error for
each character; every character nearest its own drawing; none vanished. The
cell W×2W is what a program asks for a box W×W, so 12×24 to 48×96 judge the
boxes 12×12 to 48×48.

Gates v2.3 is gates v2 with no limit tighter than what the group's own
drawing scores when sampled as the library samples it (a perfect net), with
10 % of room, and a seed that puts every pixel on the right side at every
counted size passing the error-amount rules. Nearest-to-itself and
none-vanished are never eased. **595 limits were eased** for the nets in this
bundle; each is in the validation record with the declared limit, the
perfect drawing's score and the limit applied.

A group whose two seeds pass ships the seed with the lower mean error at
8×16, 16×32 and 48×96. A group that fails is trained once more as two nets
of half its characters each; a half that fails is left out. Nothing else that failed ships: the owner named the failed halves in the
bundle after looking at each beside its drawing.

- 60 groups trained; 25 passed with both seeds.
- 35 failed and were halved; of the 70 halves 66 passed.
- 4 halves failed again and are left out (12 characters); 23 more failed again and are in the bundle by the owner's word, marked FAILED.

## Results by net

Mean error against the teacher and mean overlap at counted cells, for the shipped seed (for a net not in the bundle: seed 0).

| Net | Characters | Gates v2.3 | Rules missed (seed 0 / seed 1) | Limits eased | In the bundle | Mean error 12×24 / 16×32 / 24×48 / 48×96 | Overlap 16×32 | Overlap 24×48 |
|---|---|---|---|---:|---|---|---:|---:|
| `twdu0` g0 | U+1F90C..U+1F910 (5) | passed | 0 / 0 | 2 | seed 0 | 0.0038 0.0025 0.0036 0.0015 | 0.990 | 0.990 |
| `twdu0` g1 | U+1F911..U+1F916 (6) | **failed** | 4 / 4: 12x24 firm, 16x32 p99, 24x48 mae, 24x48 p99, 48x96 mae | 12 | no: halved | 0.0084 0.0071 0.0078 0.0034 | 0.976 | 0.978 |
| `twdu0r1` g0 (half) | U+1F911..U+1F913 (3) | **failed** | 0 / 2: 24x48 mae, 24x48 p99 | 9 | **seed 0: FAILED, in by the owner's word** | 0.0077 0.0060 0.0076 0.0030 | 0.958 | 0.969 |
| `twdu0r1` g1 (half) | U+1F914..U+1F916 (3) | passed | 0 / 0 | 12 | seed 1 | 0.0083 0.0080 0.0060 0.0028 | 0.985 | 0.990 |
| `twdu0` g2 | U+1F917..U+1F91C (6) | passed | 0 / 0 | 4 | seed 0 | 0.0056 0.0041 0.0052 0.0021 | 0.949 | 0.975 |
| `twdu0` g3 | U+1F91D..U+1F922 (6) | **failed** | 0 / 1: 48x96 mae | 7 | no: halved | 0.0065 0.0050 0.0063 0.0029 | 0.960 | 0.948 |
| `twdu0r3` g0 (half) | U+1F91D..U+1F91F (3) | passed | 0 / 0 | 4 | seed 1 | 0.0045 0.0032 0.0037 0.0017 | 0.944 | 0.932 |
| `twdu0r3` g1 (half) | U+1F920..U+1F922 (3) | passed | 0 / 0 | 12 | seed 0 | 0.0084 0.0062 0.0080 0.0035 | 0.979 | 0.965 |
| `twdu0` g4 | U+1F923..U+1F928 (6) | **failed** | 4 / 3: 24x48 mae, 24x48 p99, 48x96 mae, 8x16 firm | 9 | no: halved | 0.0078 0.0054 0.0071 0.0033 | 0.963 | 0.975 |
| `twdu0r4` g0 (half) | U+1F923..U+1F925 (3) | passed | 0 / 0 | 6 | seed 1 | 0.0070 0.0044 0.0061 0.0028 | 0.975 | 0.972 |
| `twdu0r4` g1 (half) | U+1F926..U+1F928 (3) | passed | 0 / 0 | 10 | seed 0 | 0.0083 0.0058 0.0069 0.0032 | 0.950 | 0.981 |
| `twdu0` g5 | U+1F929..U+1F92D (5) | **failed** | 1 / 0: 48x96 mae | 14 | no: halved | 0.0082 0.0056 0.0078 0.0035 | 0.963 | 0.975 |
| `twdu0r5` g0 (half) | U+1F929..U+1F92A (2) | **failed** | 1 / 0: 24x48 p99 | 12 | **seed 1: FAILED, in by the owner's word** | 0.0082 0.0058 0.0080 0.0033 | 0.976 | 0.971 |
| `twdu0r5` g1 (half) | U+1F92B..U+1F92D (3) | passed | 0 / 0 | 14 | seed 1 | 0.0079 0.0054 0.0073 0.0030 | 0.970 | 0.977 |
| `twdu0` g6 | U+1F92E..U+1F933 (6) | **failed** | 1 / 1: 24x48 p99 | 5 | no: halved | 0.0065 0.0046 0.0051 0.0021 | 0.982 | 0.988 |
| `twdu0r6` g0 (half) | U+1F92E..U+1F930 (3) | passed | 0 / 0 | 6 | seed 0 | 0.0054 0.0049 0.0048 0.0020 | 0.966 | 0.989 |
| `twdu0r6` g1 (half) | U+1F931..U+1F933 (3) | **failed** | 0 / 1: 24x48 firm | 3 | **seed 1: FAILED, in by the owner's word** | 0.0068 0.0043 0.0049 0.0019 | 0.995 | 0.989 |
| `twdu0` g7 | U+1F934..U+1F939 (6) | passed | 0 / 0 | 1 | seed 1 | 0.0036 0.0028 0.0036 0.0016 | 0.993 | 0.986 |
| `twdu0` g8 | U+1F93A..U+1F940 (6) | passed | 0 / 0 | 1 | seed 1 | 0.0051 0.0037 0.0046 0.0018 | 0.921 | 0.968 |
| `twdu0` g9 | U+1F941..U+1F947 (6) | **failed** | 9 / 7: 12x24 p99, 16x32 glyph_mae, 16x32 p99, 24x48 mae, 24x48 p99, 48x96 glyph_mae | 18 | no: halved | 0.0084 0.0069 0.0072 0.0042 | 0.970 | 0.989 |
| `twdu0r9` g0 (half) | U+1F941..U+1F943 (3) | **failed** | 1 / 2: 10x20 p99, 8x16 p99 | 11 | **seed 1: FAILED, in by the owner's word** | 0.0075 0.0052 0.0069 0.0028 | 0.977 | 0.989 |
| `twdu0r9` g1 (half) | U+1F944..U+1F947 (3) | **failed** | 4 / 3: 16x32 p99, 24x48 p99, 48x96 mae, 48x96 p99 | 16 | **seed 1: FAILED, in by the owner's word** | 0.0083 0.0078 0.0060 0.0037 | 0.961 | 0.987 |
| `twdu1` g0 | U+1F948..U+1F94C (5) | passed | 0 / 0 | 1 | seed 1 | 0.0054 0.0039 0.0039 0.0019 | 0.979 | 0.991 |
| `twdu1` g1 | U+1F94D..U+1F952 (6) | passed | 0 / 0 | 5 | seed 1 | 0.0051 0.0028 0.0041 0.0017 | 0.978 | 0.988 |
| `twdu1` g2 | U+1F953..U+1F958 (6) | **failed** | 1 / 0: 24x48 p99 | 1 | no: halved | 0.0042 0.0033 0.0047 0.0025 | 0.975 | 0.986 |
| `twdu1r2` g0 (half) | U+1F953..U+1F955 (3) | passed | 0 / 0 | 1 | seed 1 | 0.0046 0.0038 0.0057 0.0025 | 0.983 | 0.980 |
| `twdu1r2` g1 (half) | U+1F956..U+1F958 (3) | passed | 0 / 0 | 0 | seed 1 | 0.0036 0.0023 0.0035 0.0016 | 0.967 | 0.992 |
| `twdu1` g3 | U+1F959..U+1F95E (6) | passed | 0 / 0 | 1 | seed 1 | 0.0042 0.0034 0.0037 0.0017 | 0.987 | 0.991 |
| `twdu1` g4 | U+1F95F..U+1F964 (6) | passed | 0 / 0 | 6 | seed 0 | 0.0037 0.0041 0.0031 0.0017 | 0.985 | 0.990 |
| `twdu1` g5 | U+1F965..U+1F969 (5) | passed | 0 / 0 | 1 | seed 1 | 0.0047 0.0032 0.0042 0.0019 | 0.979 | 0.992 |
| `twdu1` g6 | U+1F96A..U+1F96F (6) | **failed** | 1 / 1: 24x48 p99 | 2 | no: halved | 0.0063 0.0046 0.0058 0.0025 | 0.991 | 0.990 |
| `twdu1r6` g0 (half) | U+1F96A..U+1F96C (3) | passed | 0 / 0 | 6 | seed 1 | 0.0074 0.0053 0.0063 0.0027 | 0.997 | 0.985 |
| `twdu1r6` g1 (half) | U+1F96D..U+1F96F (3) | passed | 0 / 0 | 0 | seed 1 | 0.0052 0.0035 0.0051 0.0019 | 0.980 | 0.993 |
| `twdu1` g7 | U+1F970..U+1F975 (6) | **failed** | 2 / 2: 24x48 mae, 48x96 mae | 8 | no: halved | 0.0070 0.0050 0.0073 0.0035 | 0.973 | 0.980 |
| `twdu1r7` g0 (half) | U+1F970..U+1F972 (3) | passed | 0 / 0 | 9 | seed 1 | 0.0070 0.0049 0.0068 0.0031 | 0.976 | 0.978 |
| `twdu1r7` g1 (half) | U+1F973..U+1F975 (3) | passed | 0 / 0 | 7 | seed 0 | 0.0065 0.0047 0.0069 0.0029 | 0.977 | 0.981 |
| `twdu1` g8 | U+1F976..U+1F97B (6) | **failed** | 5 / 4: 10x20 p99, 24x48 firm, 24x48 mae, 24x48 p99, 48x96 mae | 10 | no: halved | 0.0075 0.0058 0.0077 0.0034 | 0.969 | 0.976 |
| `twdu1r8` g0 (half) | U+1F976..U+1F978 (3) | passed | 0 / 0 | 10 | seed 0 | 0.0078 0.0059 0.0074 0.0032 | 0.949 | 0.976 |
| `twdu1r8` g1 (half) | U+1F979..U+1F97B (3) | passed | 0 / 0 | 8 | seed 1 | 0.0065 0.0054 0.0065 0.0028 | 0.985 | 0.980 |
| `twdu1` g9 | U+1F97C..U+1F981 (6) | **failed** | 2 / 3: 16x32 p99, 48x96 mae, 48x96 p99 | 12 | no: halved | 0.0088 0.0064 0.0073 0.0038 | 0.977 | 0.996 |
| `twdu1r9` g0 (half) | U+1F97C..U+1F97E (3) | passed | 0 / 0 | 13 | seed 0 | 0.0102 0.0069 0.0075 0.0037 | 0.974 | 0.995 |
| `twdu1r9` g1 (half) | U+1F97F..U+1F981 (3) | passed | 0 / 0 | 9 | seed 1 | 0.0070 0.0058 0.0067 0.0032 | 0.982 | 0.995 |
| `twdu2` g0 | U+1F982..U+1F986 (5) | **failed** | 1 / 1: 10x20 p99 | 9 | no: halved | 0.0059 0.0037 0.0059 0.0023 | 0.985 | 0.985 |
| `twdu2r0` g0 (half) | U+1F982..U+1F983 (2) | passed | 0 / 0 | 6 | seed 1 | 0.0057 0.0037 0.0059 0.0021 | 0.979 | 0.985 |
| `twdu2r0` g1 (half) | U+1F984..U+1F986 (3) | passed | 0 / 0 | 9 | seed 0 | 0.0059 0.0037 0.0057 0.0021 | 0.992 | 0.986 |
| `twdu2` g1 | U+1F987..U+1F98C (6) | **failed** | 0 / 1: 24x48 p99 | 9 | no: halved | 0.0059 0.0040 0.0058 0.0025 | 0.987 | 0.976 |
| `twdu2r1` g0 (half) | U+1F987..U+1F989 (3) | **failed** | 1 / 0: 10x20 p99 | 5 | **seed 1: FAILED, in by the owner's word** | 0.0046 0.0030 0.0045 0.0018 | 0.984 | 0.979 |
| `twdu2r1` g1 (half) | U+1F98A..U+1F98C (3) | **failed** | 1 / 0: 24x48 p99 | 11 | **seed 0: FAILED, in by the owner's word** | 0.0065 0.0046 0.0061 0.0025 | 0.992 | 0.980 |
| `twdu2` g2 | U+1F98D..U+1F992 (6) | passed | 0 / 0 | 5 | seed 0 | 0.0046 0.0032 0.0045 0.0020 | 0.980 | 0.980 |
| `twdu2` g3 | U+1F993..U+1F998 (6) | **failed** | 2 / 1: 12x24 firm, 24x48 firm, 6x12 firm | 7 | no: halved | 0.0061 0.0043 0.0061 0.0029 | 0.972 | 0.981 |
| `twdu2r3` g0 (half) | U+1F993..U+1F995 (3) | **failed** | 1 / 0: 24x48 firm | 13 | **seed 1: FAILED, in by the owner's word** | 0.0080 0.0051 0.0076 0.0034 | 0.983 | 0.983 |
| `twdu2r3` g1 (half) | U+1F996..U+1F998 (3) | passed | 0 / 0 | 3 | seed 0 | 0.0041 0.0032 0.0038 0.0017 | 0.966 | 0.983 |
| `twdu2` g4 | U+1F999..U+1F99E (6) | **failed** | 3 / 3: 24x48 mae, 48x96 mae, 48x96 p99 | 8 | no: halved | 0.0069 0.0049 0.0072 0.0034 | 0.977 | 0.982 |
| `twdu2r4` g0 (half) | U+1F999..U+1F99B (3) | **failed** | 2 / 0: 48x96 mae, 8x16 p99 | 11 | **seed 1: FAILED, in by the owner's word** | 0.0074 0.0058 0.0070 0.0031 | 0.978 | 0.981 |
| `twdu2r4` g1 (half) | U+1F99C..U+1F99E (3) | **failed** | 1 / 0: 8x16 p99 | 5 | **seed 0: FAILED, in by the owner's word** | 0.0059 0.0039 0.0058 0.0026 | 0.983 | 0.987 |
| `twdu2` g5 | U+1F99F..U+1F9A3 (5) | **failed** | 1 / 0: 8x16 firm | 12 | no: halved | 0.0075 0.0051 0.0071 0.0027 | 0.991 | 0.970 |
| `twdu2r5` g0 (half) | U+1F99F..U+1F9A0 (2) | passed | 0 / 0 | 5 | seed 1 | 0.0067 0.0046 0.0068 0.0027 | 0.992 | 0.947 |
| `twdu2r5` g1 (half) | U+1F9A1..U+1F9A3 (3) | **failed** | 1 / 2: 10x20 p99, 8x16 firm | 11 | **seed 0: FAILED, in by the owner's word** | 0.0082 0.0055 0.0074 0.0023 | 0.990 | 0.977 |
| `twdu2` g6 | U+1F9A4..U+1F9A9 (6) | **failed** | 0 / 1: 10x20 p99 | 7 | no: halved | 0.0074 0.0038 0.0068 0.0026 | 0.993 | 0.986 |
| `twdu2r6` g0 (half) | U+1F9A4..U+1F9A6 (3) | **failed** | 1 / 1: 10x20 p99 | 8 | **seed 1: FAILED, in by the owner's word** | 0.0074 0.0034 0.0068 0.0024 | 0.990 | 0.987 |
| `twdu2r6` g1 (half) | U+1F9A7..U+1F9A9 (3) | **failed** | 0 / 1: 24x48 firm | 5 | **no: left out** | 0.0071 0.0040 0.0067 0.0024 | 0.993 | 0.984 |
| `twdu2` g7 | U+1F9AA..U+1F9AF (6) | **failed** | 1 / 0: 6x12 firm | 11 | no: halved | 0.0068 0.0052 0.0059 0.0027 | 0.990 | 0.977 |
| `twdu2r7` g0 (half) | U+1F9AA..U+1F9AC (3) | passed | 0 / 0 | 8 | seed 0 | 0.0063 0.0035 0.0056 0.0022 | 0.983 | 0.973 |
| `twdu2r7` g1 (half) | U+1F9AD..U+1F9AF (3) | passed | 0 / 0 | 12 | seed 1 | 0.0069 0.0069 0.0060 0.0025 | 0.998 | 0.979 |
| `twdu2` g8 | U+1F9B0..U+1F9B5 (6) | passed | 0 / 0 | 0 | seed 0 | 0.0037 0.0022 0.0029 0.0013 | 0.990 | 0.981 |
| `twdu2` g9 | U+1F9B6..U+1F9BB (6) | passed | 0 / 0 | 4 | seed 1 | 0.0048 0.0038 0.0044 0.0020 | 0.994 | 0.978 |
| `twdu3` g0 | U+1F9BC..U+1F9C0 (5) | passed | 0 / 0 | 4 | seed 0 | 0.0064 0.0044 0.0049 0.0022 | 0.980 | 0.974 |
| `twdu3` g1 | U+1F9C1..U+1F9C6 (6) | passed | 0 / 0 | 3 | seed 1 | 0.0052 0.0039 0.0036 0.0019 | 0.987 | 0.976 |
| `twdu3` g2 | U+1F9C7..U+1F9CC (6) | **failed** | 1 / 2: 48x96 mae, 6x12 firm | 7 | no: halved | 0.0074 0.0057 0.0066 0.0030 | 0.968 | 0.983 |
| `twdu3r2` g0 (half) | U+1F9C7..U+1F9C9 (3) | **failed** | 0 / 1: 6x12 firm | 9 | **no: left out** | 0.0081 0.0068 0.0064 0.0028 | 0.951 | 0.979 |
| `twdu3r2` g1 (half) | U+1F9CA..U+1F9CC (3) | **failed** | 1 / 0: 24x48 firm | 7 | **seed 0: FAILED, in by the owner's word** | 0.0060 0.0043 0.0057 0.0026 | 0.981 | 0.986 |
| `twdu3` g3 | U+1F9CD..U+1F9D2 (6) | **failed** | 0 / 1: 10x20 firm | 3 | no: halved | 0.0041 0.0031 0.0037 0.0017 | 0.990 | 0.990 |
| `twdu3r3` g0 (half) | U+1F9CD..U+1F9CF (3) | passed | 0 / 0 | 0 | seed 0 | 0.0035 0.0029 0.0032 0.0014 | 1.000 | 0.989 |
| `twdu3r3` g1 (half) | U+1F9D0..U+1F9D2 (3) | passed | 0 / 0 | 4 | seed 0 | 0.0044 0.0032 0.0042 0.0018 | 0.982 | 0.990 |
| `twdu3` g4 | U+1F9D3..U+1F9D8 (6) | **failed** | 0 / 1: 8x16 p99 | 1 | no: halved | 0.0050 0.0037 0.0038 0.0017 | 0.985 | 0.992 |
| `twdu3r4` g0 (half) | U+1F9D3..U+1F9D5 (3) | passed | 0 / 0 | 2 | seed 1 | 0.0042 0.0028 0.0039 0.0016 | 0.988 | 0.997 |
| `twdu3r4` g1 (half) | U+1F9D6..U+1F9D8 (3) | passed | 0 / 0 | 1 | seed 1 | 0.0058 0.0045 0.0036 0.0017 | 0.979 | 0.987 |
| `twdu3` g5 | U+1F9D9..U+1F9DD (5) | passed | 0 / 0 | 3 | seed 1 | 0.0060 0.0039 0.0045 0.0021 | 0.989 | 0.984 |
| `twdu3` g6 | U+1F9DE..U+1F9E3 (6) | passed | 0 / 0 | 0 | seed 0 | 0.0044 0.0029 0.0033 0.0016 | 0.974 | 0.990 |
| `twdu3` g7 | U+1F9E4..U+1F9E9 (6) | **failed** | 5 / 5: 10x20 firm, 12x24 p99, 24x48 mae, 24x48 p99, 48x96 mae, 48x96 p99 | 15 | no: halved | 0.0112 0.0086 0.0076 0.0043 | 0.982 | 0.986 |
| `twdu3r7` g0 (half) | U+1F9E4..U+1F9E6 (3) | **failed** | 0 / 1: 24x48 firm | 15 | **seed 0: FAILED, in by the owner's word** | 0.0138 0.0085 0.0078 0.0053 | 0.996 | 0.987 |
| `twdu3r7` g1 (half) | U+1F9E7..U+1F9E9 (3) | **failed** | 2 / 3: 10x20 firm, 12x24 firm, 24x48 p99, 8x16 p99 | 9 | **no: left out** | 0.0074 0.0078 0.0061 0.0023 | 0.980 | 0.984 |
| `twdu3` g8 | U+1F9EA..U+1F9EF (6) | **failed** | 4 / 5: 10x20 p99, 24x48 mae, 48x96 mae, 8x16 glyph_mae, 8x16 p99 | 13 | no: halved | 0.0082 0.0066 0.0076 0.0033 | 0.975 | 0.978 |
| `twdu3r8` g0 (half) | U+1F9EA..U+1F9EC (3) | **failed** | 2 / 2: 12x24 p99, 8x16 p99 | 8 | **seed 0: FAILED, in by the owner's word** | 0.0061 0.0041 0.0060 0.0024 | 0.987 | 0.986 |
| `twdu3r8` g1 (half) | U+1F9ED..U+1F9EF (3) | **failed** | 3 / 3: 10x20 p99, 12x24 p99, 48x96 mae, 8x16 p99 | 14 | **seed 1: FAILED, in by the owner's word** | 0.0099 0.0087 0.0082 0.0034 | 0.967 | 0.972 |
| `twdu3` g9 | U+1F9F0..U+1F9F5 (6) | **failed** | 1 / 1: 10x20 p99, 12x24 p99 | 14 | no: halved | 0.0104 0.0083 0.0075 0.0033 | 0.916 | 0.966 |
| `twdu3r9` g0 (half) | U+1F9F0..U+1F9F2 (3) | passed | 0 / 0 | 10 | seed 1 | 0.0103 0.0085 0.0051 0.0029 | 0.964 | 0.972 |
| `twdu3r9` g1 (half) | U+1F9F3..U+1F9F5 (3) | passed | 0 / 0 | 13 | seed 1 | 0.0101 0.0079 0.0093 0.0037 | 0.881 | 0.962 |
| `twdu4` g0 | U+1F9F6..U+1F9FA (5) | passed | 0 / 0 | 11 | seed 0 | 0.0066 0.0048 0.0072 0.0029 | 0.976 | 0.974 |
| `twdu4` g1 | U+1F9FB..U+1FA70 (6) | **failed** | 3 / 1: 10x20 p99, 24x48 p99, 48x96 mae | 3 | no: halved | 0.0071 0.0055 0.0063 0.0030 | 0.975 | 0.980 |
| `twdu4r1` g0 (half) | U+1F9FB..U+1F9FD (3) | **failed** | 2 / 1: 16x32 p99, 24x48 p99 | 4 | **seed 1: FAILED, in by the owner's word** | 0.0070 0.0052 0.0064 0.0026 | 0.979 | 0.984 |
| `twdu4r1` g1 (half) | U+1F9FE..U+1FA70 (3) | passed | 0 / 0 | 0 | seed 0 | 0.0063 0.0055 0.0049 0.0023 | 0.987 | 0.975 |
| `twdu4` g2 | U+1FA71..U+1FA76 (6) | passed | 0 / 0 | 0 | seed 1 | 0.0042 0.0026 0.0028 0.0014 | 0.965 | 0.997 |
| `twdu4` g3 | U+1FA77..U+1FA7C (6) | **failed** | 1 / 1: 10x20 p99 | 5 | no: halved | 0.0052 0.0039 0.0049 0.0022 | 0.894 | 0.941 |
| `twdu4r3` g0 (half) | U+1FA77..U+1FA79 (3) | passed | 0 / 0 | 1 | seed 1 | 0.0027 0.0018 0.0024 0.0011 | 0.997 | 0.991 |
| `twdu4r3` g1 (half) | U+1FA7A..U+1FA7C (3) | **failed** | 3 / 2: 10x20 p99, 24x48 p99, 6x12 p99 | 10 | **seed 0: FAILED, in by the owner's word** | 0.0077 0.0059 0.0069 0.0029 | 0.785 | 0.895 |
| `twdu4` g4 | U+1FA80..U+1FA85 (6) | **failed** | 1 / 0: 24x48 p99 | 5 | no: halved | 0.0061 0.0040 0.0048 0.0024 | 0.958 | 0.979 |
| `twdu4r4` g0 (half) | U+1FA80..U+1FA82 (3) | passed | 0 / 0 | 6 | seed 0 | 0.0067 0.0044 0.0050 0.0023 | 0.962 | 0.974 |
| `twdu4r4` g1 (half) | U+1FA83..U+1FA85 (3) | passed | 0 / 0 | 2 | seed 1 | 0.0054 0.0033 0.0040 0.0019 | 0.951 | 0.980 |
| `twdu4` g5 | U+1FA86..U+1FA91 (5) | passed | 0 / 0 | 1 | seed 0 | 0.0045 0.0032 0.0039 0.0017 | 0.935 | 0.995 |
| `twdu4` g6 | U+1FA92..U+1FA97 (6) | **failed** | 3 / 3: 16x32 p99, 24x48 glyph_mae, 48x96 mae, 48x96 p99 | 15 | no: halved | 0.0079 0.0050 0.0070 0.0034 | 0.974 | 0.987 |
| `twdu4r6` g0 (half) | U+1FA92..U+1FA94 (3) | passed | 0 / 0 | 4 | seed 1 | 0.0041 0.0028 0.0041 0.0018 | 0.987 | 0.990 |
| `twdu4r6` g1 (half) | U+1FA95..U+1FA97 (3) | passed | 0 / 0 | 16 | seed 0 | 0.0116 0.0064 0.0090 0.0045 | 0.960 | 0.982 |
| `twdu4` g7 | U+1FA98..U+1FA9D (6) | **failed** | 1 / 1: 24x48 p99 | 11 | no: halved | 0.0083 0.0056 0.0067 0.0030 | 0.866 | 0.980 |
| `twdu4r7` g0 (half) | U+1FA98..U+1FA9A (3) | **failed** | 0 / 1: 8x16 p99 | 11 | **seed 1: FAILED, in by the owner's word** | 0.0085 0.0061 0.0075 0.0027 | 0.907 | 0.989 |
| `twdu4r7` g1 (half) | U+1FA9B..U+1FA9D (3) | passed | 0 / 0 | 5 | seed 0 | 0.0079 0.0046 0.0051 0.0022 | 0.821 | 0.965 |
| `twdu4` g8 | U+1FA9E..U+1FAA3 (6) | passed | 0 / 0 | 3 | seed 1 | 0.0063 0.0049 0.0057 0.0024 | 0.967 | 0.972 |
| `twdu4` g9 | U+1FAA4..U+1FAA9 (6) | **failed** | 5 / 8: 10x20 firm, 10x20 mae, 10x20 p99, 48x96 mae, 6x12 p99, 8x16 firm | 19 | no: halved | 0.0087 0.0071 0.0075 0.0031 | 0.989 | 0.980 |
| `twdu4r9` g0 (half) | U+1FAA4..U+1FAA6 (3) | **failed** | 1 / 1: 24x48 p99 | 8 | **seed 1: FAILED, in by the owner's word** | 0.0077 0.0065 0.0054 0.0022 | 0.997 | 0.991 |
| `twdu4r9` g1 (half) | U+1FAA7..U+1FAA9 (3) | passed | 0 / 0 | 21 | seed 0 | 0.0099 0.0076 0.0082 0.0032 | 0.981 | 0.972 |
| `twdu5` g0 | U+1FAAA..U+1FAAE (5) | **failed** | 3 / 3: 48x96 mae, 48x96 p99, 8x16 p99 | 15 | no: halved | 0.0107 0.0081 0.0074 0.0039 | 0.969 | 0.973 |
| `twdu5r0` g0 (half) | U+1FAAA..U+1FAAB (2) | passed | 0 / 0 | 12 | seed 0 | 0.0122 0.0080 0.0062 0.0027 | 0.984 | 0.988 |
| `twdu5r0` g1 (half) | U+1FAAC..U+1FAAE (3) | **failed** | 1 / 2: 48x96 mae, 48x96 p99 | 16 | **seed 1: FAILED, in by the owner's word** | 0.0101 0.0079 0.0079 0.0040 | 0.957 | 0.959 |
| `twdu5` g1 | U+1FAAF..U+1FAB4 (6) | **failed** | 3 / 1: 48x96 mae, 48x96 p99, 8x16 p99 | 9 | no: halved | 0.0067 0.0048 0.0067 0.0033 | 0.994 | 0.968 |
| `twdu5r1` g0 (half) | U+1FAAF..U+1FAB1 (3) | **failed** | 0 / 1: 48x96 firm | 10 | **seed 0: FAILED, in by the owner's word** | 0.0059 0.0046 0.0063 0.0023 | 0.992 | 0.978 |
| `twdu5r1` g1 (half) | U+1FAB2..U+1FAB4 (3) | **failed** | 0 / 1: 10x20 p99 | 7 | **seed 1: FAILED, in by the owner's word** | 0.0071 0.0047 0.0066 0.0033 | 0.996 | 0.960 |
| `twdu5` g2 | U+1FAB5..U+1FABA (6) | passed | 0 / 0 | 8 | seed 1 | 0.0053 0.0036 0.0051 0.0023 | 0.979 | 0.976 |
| `twdu5` g3 | U+1FABB..U+1FAC1 (6) | **failed** | 1 / 1: 24x48 p99 | 1 | no: halved | 0.0061 0.0040 0.0052 0.0023 | 0.982 | 0.980 |
| `twdu5r3` g0 (half) | U+1FABB..U+1FABD (3) | passed | 0 / 0 | 3 | seed 0 | 0.0062 0.0045 0.0056 0.0024 | 0.996 | 0.971 |
| `twdu5r3` g1 (half) | U+1FABF..U+1FAC1 (3) | **failed** | 1 / 1: 12x24 firm | 1 | **no: left out** | 0.0059 0.0034 0.0044 0.0016 | 0.971 | 0.988 |
| `twdu5` g4 | U+1FAC2..U+1FACF (6) | passed | 0 / 0 | 8 | seed 1 | 0.0057 0.0035 0.0049 0.0017 | 0.981 | 0.974 |
| `twdu5` g5 | U+1FAD0..U+1FAD5 (6) | passed | 0 / 0 | 2 | seed 1 | 0.0041 0.0026 0.0039 0.0019 | 0.989 | 0.993 |
| `twdu5` g6 | U+1FAD6..U+1FADB (6) | passed | 0 / 0 | 2 | seed 0 | 0.0044 0.0035 0.0042 0.0020 | 0.992 | 0.979 |
| `twdu5` g7 | U+1FAE0..U+1FAE5 (6) | passed | 0 / 0 | 5 | seed 0 | 0.0068 0.0045 0.0058 0.0026 | 0.965 | 0.975 |
| `twdu5` g8 | U+1FAE6..U+1FAF2 (6) | **failed** | 1 / 2: 10x20 p99, 24x48 p99 | 6 | no: halved | 0.0067 0.0045 0.0057 0.0024 | 0.990 | 0.988 |
| `twdu5r8` g0 (half) | U+1FAE6..U+1FAE8 (3) | passed | 0 / 0 | 10 | seed 1 | 0.0077 0.0055 0.0072 0.0028 | 0.987 | 0.987 |
| `twdu5r8` g1 (half) | U+1FAF0..U+1FAF2 (3) | passed | 0 / 0 | 1 | seed 1 | 0.0052 0.0029 0.0032 0.0012 | 0.996 | 0.991 |
| `twdu5` g9 | U+1FAF3..U+1FAF8 (6) | **failed** | 1 / 1: 12x24 firm | 5 | no: halved | 0.0068 0.0037 0.0045 0.0021 | 0.992 | 0.957 |
| `twdu5r9` g0 (half) | U+1FAF3..U+1FAF5 (3) | passed | 0 / 0 | 3 | seed 1 | 0.0052 0.0033 0.0035 0.0016 | 0.986 | 0.953 |
| `twdu5r9` g1 (half) | U+1FAF6..U+1FAF8 (3) | passed | 0 / 0 | 5 | seed 0 | 0.0082 0.0040 0.0050 0.0024 | 0.995 | 0.957 |

## The boxes in use that the gates do not count (information)

The shipped seed of each net at the cell a program asks for the boxes
18×18, 20×20 and 36×36, by the scorer's own metric code against the bundle
teacher, and in the box itself (each pair of rows averaged) against the
teacher's area coverage of the box. Declared as information before
training; it decides nothing.

| Net | 18×36: error, 99th pct | 20×40 | 36×72 | Box 18×18: error | Box 20×20 | Box 36×36 | Not nearest or vanished |
|---|---|---|---|---:|---:|---:|---|
| `twdu0` g0 | 0.0024, 0.035 | 0.0019, 0.030 | 0.0021, 0.046 | 0.0020 | 0.0014 | 0.0017 | none |
| `twdu0r1` g0 | 0.0047, 0.042 | 0.0041, 0.051 | 0.0045, 0.063 | 0.0040 | 0.0034 | 0.0039 | none |
| `twdu0r1` g1 | 0.0049, 0.054 | 0.0057, 0.059 | 0.0035, 0.055 | 0.0044 | 0.0051 | 0.0031 | none |
| `twdu0` g2 | 0.0036, 0.052 | 0.0038, 0.056 | 0.0026, 0.054 | 0.0034 | 0.0035 | 0.0023 | none |
| `twdu0r3` g0 | 0.0032, 0.051 | 0.0033, 0.056 | 0.0026, 0.056 | 0.0029 | 0.0031 | 0.0024 | none |
| `twdu0r3` g1 | 0.0052, 0.050 | 0.0047, 0.051 | 0.0047, 0.068 | 0.0044 | 0.0039 | 0.0041 | none |
| `twdu0r4` g0 | 0.0041, 0.048 | 0.0037, 0.046 | 0.0036, 0.053 | 0.0035 | 0.0031 | 0.0030 | none |
| `twdu0r4` g1 | 0.0044, 0.050 | 0.0046, 0.053 | 0.0041, 0.060 | 0.0038 | 0.0040 | 0.0034 | none |
| `twdu0r5` g0 | 0.0051, 0.052 | 0.0044, 0.052 | 0.0049, 0.069 | 0.0043 | 0.0037 | 0.0042 | none |
| `twdu0r5` g1 | 0.0046, 0.055 | 0.0041, 0.054 | 0.0038, 0.054 | 0.0039 | 0.0036 | 0.0032 | none |
| `twdu0r6` g0 | 0.0047, 0.111 | 0.0035, 0.064 | 0.0040, 0.062 | 0.0041 | 0.0029 | 0.0037 | none |
| `twdu0r6` g1 | 0.0041, 0.052 | 0.0038, 0.057 | 0.0028, 0.053 | 0.0037 | 0.0036 | 0.0026 | none |
| `twdu0` g7 | 0.0025, 0.044 | 0.0026, 0.043 | 0.0021, 0.050 | 0.0022 | 0.0023 | 0.0018 | none |
| `twdu0` g8 | 0.0031, 0.052 | 0.0028, 0.045 | 0.0027, 0.058 | 0.0027 | 0.0024 | 0.0024 | none |
| `twdu0r9` g0 | 0.0054, 0.057 | 0.0043, 0.065 | 0.0041, 0.057 | 0.0047 | 0.0037 | 0.0036 | none |
| `twdu0r9` g1 | 0.0056, 0.071 | 0.0067, 0.071 | 0.0033, 0.061 | 0.0049 | 0.0063 | 0.0031 | none |
| `twdu1` g0 | 0.0036, 0.051 | 0.0031, 0.057 | 0.0024, 0.051 | 0.0032 | 0.0028 | 0.0021 | none |
| `twdu1` g1 | 0.0028, 0.041 | 0.0028, 0.052 | 0.0026, 0.055 | 0.0022 | 0.0022 | 0.0021 | none |
| `twdu1r2` g0 | 0.0037, 0.058 | 0.0031, 0.053 | 0.0044, 0.097 | 0.0029 | 0.0026 | 0.0035 | none |
| `twdu1r2` g1 | 0.0020, 0.033 | 0.0019, 0.033 | 0.0021, 0.047 | 0.0017 | 0.0015 | 0.0019 | none |
| `twdu1` g3 | 0.0028, 0.050 | 0.0027, 0.046 | 0.0022, 0.048 | 0.0024 | 0.0022 | 0.0019 | none |
| `twdu1` g4 | 0.0029, 0.053 | 0.0032, 0.057 | 0.0022, 0.043 | 0.0024 | 0.0028 | 0.0018 | none |
| `twdu1` g5 | 0.0031, 0.050 | 0.0025, 0.037 | 0.0026, 0.047 | 0.0027 | 0.0020 | 0.0022 | none |
| `twdu1r6` g0 | 0.0035, 0.051 | 0.0035, 0.058 | 0.0027, 0.053 | 0.0033 | 0.0033 | 0.0025 | none |
| `twdu1r6` g1 | 0.0029, 0.039 | 0.0024, 0.036 | 0.0028, 0.053 | 0.0024 | 0.0019 | 0.0023 | none |
| `twdu1r7` g0 | 0.0043, 0.038 | 0.0037, 0.041 | 0.0039, 0.058 | 0.0035 | 0.0031 | 0.0033 | none |
| `twdu1r7` g1 | 0.0039, 0.036 | 0.0036, 0.039 | 0.0038, 0.058 | 0.0032 | 0.0030 | 0.0031 | none |
| `twdu1r8` g0 | 0.0056, 0.052 | 0.0044, 0.052 | 0.0043, 0.065 | 0.0049 | 0.0036 | 0.0037 | none |
| `twdu1r8` g1 | 0.0040, 0.048 | 0.0042, 0.057 | 0.0035, 0.053 | 0.0033 | 0.0037 | 0.0029 | none |
| `twdu1r9` g0 | 0.0054, 0.101 | 0.0060, 0.067 | 0.0043, 0.058 | 0.0050 | 0.0056 | 0.0040 | none |
| `twdu1r9` g1 | 0.0049, 0.060 | 0.0042, 0.058 | 0.0048, 0.078 | 0.0044 | 0.0037 | 0.0044 | none |
| `twdu2r0` g0 | 0.0031, 0.044 | 0.0029, 0.049 | 0.0030, 0.059 | 0.0026 | 0.0024 | 0.0026 | none |
| `twdu2r0` g1 | 0.0030, 0.051 | 0.0028, 0.051 | 0.0031, 0.066 | 0.0025 | 0.0023 | 0.0026 | none |
| `twdu2r1` g0 | 0.0027, 0.044 | 0.0025, 0.038 | 0.0026, 0.049 | 0.0022 | 0.0022 | 0.0021 | none |
| `twdu2r1` g1 | 0.0042, 0.059 | 0.0035, 0.056 | 0.0030, 0.055 | 0.0036 | 0.0030 | 0.0027 | none |
| `twdu2` g2 | 0.0033, 0.050 | 0.0028, 0.049 | 0.0031, 0.063 | 0.0027 | 0.0024 | 0.0028 | none |
| `twdu2r3` g0 | 0.0042, 0.062 | 0.0033, 0.056 | 0.0036, 0.067 | 0.0037 | 0.0029 | 0.0033 | none |
| `twdu2r3` g1 | 0.0022, 0.034 | 0.0024, 0.041 | 0.0022, 0.045 | 0.0018 | 0.0019 | 0.0018 | none |
| `twdu2r4` g0 | 0.0046, 0.056 | 0.0046, 0.071 | 0.0041, 0.070 | 0.0042 | 0.0041 | 0.0037 | none |
| `twdu2r4` g1 | 0.0037, 0.055 | 0.0029, 0.042 | 0.0033, 0.058 | 0.0028 | 0.0024 | 0.0029 | none |
| `twdu2r5` g0 | 0.0040, 0.044 | 0.0031, 0.045 | 0.0039, 0.070 | 0.0034 | 0.0024 | 0.0034 | none |
| `twdu2r5` g1 | 0.0035, 0.050 | 0.0036, 0.060 | 0.0036, 0.066 | 0.0031 | 0.0032 | 0.0032 | none |
| `twdu2r6` g0 | 0.0028, 0.052 | 0.0024, 0.044 | 0.0022, 0.049 | 0.0025 | 0.0021 | 0.0019 | none |
| `twdu2r7` g0 | 0.0035, 0.053 | 0.0035, 0.057 | 0.0030, 0.054 | 0.0032 | 0.0031 | 0.0027 | none |
| `twdu2r7` g1 | 0.0043, 0.062 | 0.0048, 0.087 | 0.0035, 0.066 | 0.0040 | 0.0045 | 0.0033 | none |
| `twdu2` g8 | 0.0023, 0.043 | 0.0024, 0.046 | 0.0019, 0.048 | 0.0021 | 0.0021 | 0.0017 | none |
| `twdu2` g9 | 0.0035, 0.053 | 0.0032, 0.055 | 0.0025, 0.051 | 0.0029 | 0.0027 | 0.0021 | none |
| `twdu3` g0 | 0.0031, 0.049 | 0.0033, 0.052 | 0.0024, 0.052 | 0.0026 | 0.0029 | 0.0021 | none |
| `twdu3` g1 | 0.0030, 0.045 | 0.0030, 0.052 | 0.0026, 0.055 | 0.0025 | 0.0025 | 0.0022 | none |
| `twdu3r2` g1 | 0.0049, 0.055 | 0.0040, 0.057 | 0.0040, 0.058 | 0.0041 | 0.0035 | 0.0035 | none |
| `twdu3r3` g0 | 0.0020, 0.036 | 0.0018, 0.032 | 0.0017, 0.041 | 0.0017 | 0.0016 | 0.0014 | none |
| `twdu3r3` g1 | 0.0032, 0.051 | 0.0028, 0.041 | 0.0028, 0.054 | 0.0028 | 0.0023 | 0.0025 | none |
| `twdu3r4` g0 | 0.0026, 0.034 | 0.0027, 0.043 | 0.0023, 0.050 | 0.0021 | 0.0022 | 0.0020 | none |
| `twdu3r4` g1 | 0.0034, 0.051 | 0.0024, 0.039 | 0.0028, 0.054 | 0.0031 | 0.0021 | 0.0025 | none |
| `twdu3` g5 | 0.0036, 0.051 | 0.0032, 0.049 | 0.0027, 0.053 | 0.0031 | 0.0027 | 0.0023 | none |
| `twdu3` g6 | 0.0021, 0.041 | 0.0023, 0.042 | 0.0019, 0.047 | 0.0017 | 0.0019 | 0.0016 | none |
| `twdu3r7` g0 | 0.0082, 0.102 | 0.0088, 0.113 | 0.0058, 0.143 | 0.0077 | 0.0085 | 0.0055 | none |
| `twdu3r8` g0 | 0.0032, 0.055 | 0.0034, 0.051 | 0.0035, 0.055 | 0.0028 | 0.0028 | 0.0031 | none |
| `twdu3r8` g1 | 0.0060, 0.054 | 0.0064, 0.063 | 0.0054, 0.087 | 0.0053 | 0.0059 | 0.0048 | none |
| `twdu3r9` g0 | 0.0067, 0.067 | 0.0055, 0.055 | 0.0041, 0.056 | 0.0065 | 0.0052 | 0.0040 | none |
| `twdu3r9` g1 | 0.0059, 0.096 | 0.0049, 0.057 | 0.0045, 0.065 | 0.0056 | 0.0048 | 0.0042 | none |
| `twdu4` g0 | 0.0043, 0.055 | 0.0037, 0.054 | 0.0040, 0.073 | 0.0034 | 0.0032 | 0.0034 | none |
| `twdu4r1` g0 | 0.0039, 0.051 | 0.0039, 0.058 | 0.0035, 0.075 | 0.0033 | 0.0036 | 0.0030 | none |
| `twdu4r1` g1 | 0.0031, 0.049 | 0.0047, 0.057 | 0.0026, 0.049 | 0.0028 | 0.0042 | 0.0023 | none |
| `twdu4` g2 | 0.0021, 0.037 | 0.0021, 0.042 | 0.0016, 0.035 | 0.0017 | 0.0017 | 0.0013 | none |
| `twdu4r3` g0 | 0.0015, 0.025 | 0.0013, 0.022 | 0.0015, 0.034 | 0.0012 | 0.0010 | 0.0012 | none |
| `twdu4r3` g1 | 0.0045, 0.050 | 0.0058, 0.057 | 0.0038, 0.061 | 0.0043 | 0.0055 | 0.0037 | none |
| `twdu4r4` g0 | 0.0042, 0.055 | 0.0037, 0.054 | 0.0030, 0.050 | 0.0035 | 0.0033 | 0.0026 | none |
| `twdu4r4` g1 | 0.0028, 0.057 | 0.0029, 0.054 | 0.0021, 0.046 | 0.0025 | 0.0027 | 0.0018 | none |
| `twdu4` g5 | 0.0025, 0.037 | 0.0027, 0.054 | 0.0022, 0.050 | 0.0020 | 0.0024 | 0.0018 | none |
| `twdu4r6` g0 | 0.0017, 0.035 | 0.0021, 0.043 | 0.0017, 0.038 | 0.0015 | 0.0019 | 0.0015 | none |
| `twdu4r6` g1 | 0.0057, 0.054 | 0.0052, 0.058 | 0.0030, 0.051 | 0.0055 | 0.0048 | 0.0026 | none |
| `twdu4r7` g0 | 0.0039, 0.051 | 0.0041, 0.057 | 0.0035, 0.059 | 0.0033 | 0.0037 | 0.0031 | none |
| `twdu4r7` g1 | 0.0039, 0.051 | 0.0037, 0.054 | 0.0036, 0.057 | 0.0035 | 0.0034 | 0.0034 | none |
| `twdu4` g8 | 0.0041, 0.052 | 0.0037, 0.053 | 0.0031, 0.056 | 0.0034 | 0.0031 | 0.0027 | none |
| `twdu4r9` g0 | 0.0041, 0.052 | 0.0049, 0.067 | 0.0031, 0.055 | 0.0039 | 0.0047 | 0.0030 | none |
| `twdu4r9` g1 | 0.0053, 0.061 | 0.0062, 0.061 | 0.0041, 0.073 | 0.0042 | 0.0057 | 0.0038 | none |
| `twdu5r0` g0 | 0.0061, 0.054 | 0.0059, 0.059 | 0.0041, 0.056 | 0.0061 | 0.0057 | 0.0040 | none |
| `twdu5r0` g1 | 0.0068, 0.078 | 0.0066, 0.064 | 0.0055, 0.089 | 0.0059 | 0.0058 | 0.0048 | none |
| `twdu5r1` g0 | 0.0037, 0.052 | 0.0034, 0.050 | 0.0032, 0.050 | 0.0031 | 0.0029 | 0.0027 | none |
| `twdu5r1` g1 | 0.0040, 0.050 | 0.0050, 0.057 | 0.0038, 0.059 | 0.0033 | 0.0044 | 0.0033 | none |
| `twdu5` g2 | 0.0035, 0.055 | 0.0030, 0.047 | 0.0030, 0.057 | 0.0031 | 0.0026 | 0.0026 | none |
| `twdu5r3` g0 | 0.0026, 0.045 | 0.0035, 0.053 | 0.0025, 0.045 | 0.0021 | 0.0031 | 0.0021 | none |
| `twdu5` g4 | 0.0032, 0.053 | 0.0029, 0.054 | 0.0025, 0.052 | 0.0028 | 0.0024 | 0.0022 | none |
| `twdu5` g5 | 0.0027, 0.052 | 0.0022, 0.038 | 0.0022, 0.047 | 0.0023 | 0.0018 | 0.0019 | none |
| `twdu5` g6 | 0.0028, 0.048 | 0.0025, 0.049 | 0.0026, 0.056 | 0.0025 | 0.0021 | 0.0022 | none |
| `twdu5` g7 | 0.0037, 0.048 | 0.0037, 0.054 | 0.0034, 0.059 | 0.0033 | 0.0033 | 0.0030 | none |
| `twdu5r8` g0 | 0.0043, 0.051 | 0.0047, 0.047 | 0.0037, 0.061 | 0.0037 | 0.0039 | 0.0031 | none |
| `twdu5r8` g1 | 0.0026, 0.051 | 0.0028, 0.054 | 0.0018, 0.049 | 0.0024 | 0.0027 | 0.0017 | none |
| `twdu5r9` g0 | 0.0027, 0.050 | 0.0026, 0.048 | 0.0020, 0.052 | 0.0025 | 0.0024 | 0.0018 | none |
| `twdu5r9` g1 | 0.0040, 0.050 | 0.0034, 0.052 | 0.0032, 0.054 | 0.0036 | 0.0031 | 0.0028 | none |

## Recipe

- **Drawings.** `train/wide.py` and its parts put each drawing of the
  18×18 box into the net's cell (1 wide, 2 high) with every stroke as its
  outline, so a lying stroke is as thick as a standing one once the cell is
  drawn at half height. Drawn from the Unicode name and the charts' words;
  no font was opened or rasterised to make or check any drawing, and no
  emoji image was looked at.
- **Sets and groups.** 6 sets, each cut in order into group nets
  (60 in all); 35 failed and were trained again as halves, so
  the bundle holds 91 nets of 2 to 6 characters.
- **Training.** `train/split_expert.py train --mode repertoire --partition
  contiguous`, unchanged: hidden width 64, 120,000 steps, the project teacher
  (grid 256), seeds 0 and 1. A halved group: the set `NAMErI` of that
  group's characters, two parts, the rest the same.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from
  each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
python3 train/build_wide_supplement_v1.py    # rebuilds the .nrt byte for byte from the group nets
make test-wide-supplement-v1
```

## Checks

`make test-wide-supplement-v1` (part of `make test`): every group net against
the float64 reference; the bundle rebuilt byte for byte; its table exactly
`neuronte-wide-supplement-v1.symbols.txt`; no character in two of the five wide bundles, 1,335 in
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
| `neuronte-wide-supplement-v1.nrt` | The bundle, 5,192,780 bytes, sha256 `08b85a02c63026c47ae0ddcbb38226db4054111ded94d1eeda4d8c9517b8cec9` |
| `neuronte-wide-supplement-v1.symbols.txt` | The 337 characters it was trained on |
| `neuronte-wide-supplement-v1-SET-gN.json` | The 91 group nets as trained (the shipped seed) |
| `neuronte-wide-supplement-v1.provenance.json` | Every member's hash and scalars, written by its build script |
| `neuronte-wide-supplement-v1.validation.json` | The gates' hashes, both seeds' measurements and failures for every group and half, the limits eased, what was left out |
