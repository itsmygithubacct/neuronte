# wide-symbols-v1: 195 wide characters drawn for a box of two cells

`neuronte-wide-symbols-v1.nrt` draws the wide signs of the blocks below U+1F300 (watch, hourglass, weather, zodiac and the like), the game tiles, enclosed and squared signs, emoticons, transport and map symbols and the large coloured shapes: characters that a terminal gives two cells
(East Asian Width W or F), 324 of the 1,335 that the four neuronte-wide
bundles draw between them, with no character in two of them. Each is this
project's own drawing for the **box of two cells**, made from its Unicode
name and the charts' description of it in words, on a grid of 18 by 18
units with pens of 2 units (1/9 of the box).

It is a **standalone** bundle: 44 known-only group nets and one blank net,
2,511,496 bytes. It is not a default and replaces nothing; the one-cell
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

`neuronte_untrained(wide, c)` is 0 for exactly the 195 characters of
`neuronte-wide-symbols-v1.symbols.txt` and 1 for every other scalar.

**This file is not a listed bundle.** Some of its code points are drawn for
one cell in a terminal bundle (for instance by `neuronte-term-rest-v1`), and
this file draws them again for another box, so the rule that no two listed
bundles claim one character (`tests/check_bundle_lists.py`) cannot hold for
it. Its list is `neuronte-wide-symbols-v1.symbols.txt`; `tests/check_wide.py` holds the table
to it exactly and holds the four wide bundles apart from each other.

## Colour twins, by the owner's choice

Unicode tells 12 of these characters apart from a sibling only by
colour. A one-colour font has no way to show that, and the owner chose
(2026-11-18) **identical twins**: each shape is drawn once and every colour
of it the same, as in a one-colour font. They are in the bundle as twins on
purpose, and the gates allow identical drawings.

U+1F7E0 U+1F7E1 U+1F7E2 U+1F7E3 U+1F7E4 U+1F7E5 U+1F7E6 U+1F7E7 U+1F7E8 U+1F7E9 U+1F7EA U+1F7EB

## Left out

**129 drawn characters are not in the bundle.** Their nets failed the
gates twice (as a group, then as a half) and were left out by rule; the
characters stay untrained:
U+26F3 U+26F5 U+26FA U+1F0CF U+1F18E U+1F191 U+1F192 U+1F193 U+1F194 U+1F195 U+1F196 U+1F197 U+1F198 U+1F199 U+1F19A U+1F200 U+1F201 U+1F202 U+1F210 U+1F211 U+1F212 U+1F213 U+1F214 U+1F215 U+1F216 U+1F217 U+1F218 U+1F219 U+1F21A U+1F21B U+1F21C U+1F21D U+1F21E U+1F21F U+1F220 U+1F221 U+1F222 U+1F223 U+1F224 U+1F225 U+1F226 U+1F227 U+1F228 U+1F229 U+1F22A U+1F22B U+1F22C U+1F22D U+1F22E U+1F22F U+1F230 U+1F231 U+1F232 U+1F233 U+1F234 U+1F235 U+1F236 U+1F237 U+1F238 U+1F239 U+1F23A U+1F23B U+1F240 U+1F244 U+1F245 U+1F246 U+1F247 U+1F248 U+1F250 U+1F251 U+1F260 U+1F261 U+1F262 U+1F263 U+1F264 U+1F265 U+1F600 U+1F601 U+1F638 U+1F639 U+1F63A U+1F64A U+1F64B U+1F64C U+1F680 U+1F681 U+1F682 U+1F683 U+1F684 U+1F685 U+1F689 U+1F68A U+1F68B U+1F68C U+1F68D U+1F68E U+1F68F U+1F690 U+1F691 U+1F692 U+1F693 U+1F694 U+1F698 U+1F699 U+1F69A U+1F69B U+1F69C U+1F69D U+1F69E U+1F69F U+1F6A0 U+1F6AD U+1F6AE U+1F6AF U+1F6B3 U+1F6B4 U+1F6B5 U+1F6B9 U+1F6BA U+1F6BB U+1F6BC U+1F6BD U+1F6BE U+1F6BF U+1F6C0 U+1F6C1 U+1F6C2 U+1F6C3 U+1F6C4.

Across the four wide bundles, the halves that failed again missed
error-amount rules (the 99th percentile, the mean error, firm wrong pixels),
mostly at 24×48 and 48×96. No group or half failed the rule that each
character is nearest its own drawing, and none vanished. These width-64
nets draw the detailed pictographs recognisably but not exactly enough at
the large boxes. Whether to ship them as failed, or to train them again
wider, is the owner's decision; it was not made for this version.

## Gates

Declared before any net of this bundle was trained (2026-11-18T00:25Z):
every group is judged as symbols by gates v2.3 (`gates-v2.3.json`, sha256
`2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`), unchanged, by the unchanged scoring command
(sha256 `572d573b643f5f7074ceca1fd4505eee9cc8da05bbebdf5e391d1689a9d31f2c`), at its counted cells 6×12, 8×16,
10×20, 12×24, 16×32, 24×48 and 48×96, against a teacher of all
324 drawings of the bundle (sha256 `6091071b84124cc0d358d5aac03f6f2f9dd1d1d4d93ad59743e78d3afaacf031`): mean error,
99th percentile error and firm wrong pixels for the group and mean error for
each character; every character nearest its own drawing; none vanished. The
cell W×2W is what a program asks for a box W×W, so 12×24 to 48×96 judge the
boxes 12×12 to 48×48.

Gates v2.3 is gates v2 with no limit tighter than what the group's own
drawing scores when sampled as the library samples it (a perfect net), with
10 % of room, and a seed that puts every pixel on the right side at every
counted size passing the error-amount rules. Nearest-to-itself and
none-vanished are never eased. **208 limits were eased** for the nets in this
bundle; each is in the validation record with the declared limit, the
perfect drawing's score and the limit applied.

A group whose two seeds pass ships the seed with the lower mean error at
8×16, 16×32 and 48×96. A group that fails is trained once more as two nets
of half its characters each; a half that fails is left out. Nothing that failed ships.

- 54 groups trained; 21 passed with both seeds.
- 33 failed and were halved; of the 66 halves 23 passed.
- 43 halves failed again and are left out (129 characters).

## Results by net

Mean error against the teacher and mean overlap at counted cells, for the shipped seed (for a net not in the bundle: seed 0).

| Net | Characters | Gates v2.3 | Rules missed (seed 0 / seed 1) | Limits eased | In the bundle | Mean error 12×24 / 16×32 / 24×48 / 48×96 | Overlap 16×32 | Overlap 24×48 |
|---|---|---|---|---:|---|---|---:|---:|
| `twds0` g0 | U+231A..U+23EA (6) | passed | 0 / 0 | 1 | seed 1 | 0.0038 0.0032 0.0033 0.0016 | 1.000 | 0.947 |
| `twds0` g1 | U+23EB..U+25FE (6) | passed | 0 / 0 | 3 | seed 0 | 0.0041 0.0032 0.0039 0.0015 | 0.998 | 0.902 |
| `twds0` g2 | U+2614..U+264B (6) | **failed** | 0 / 1: 8x16 p99 | 1 | no: halved | 0.0048 0.0039 0.0044 0.0019 | 0.985 | 0.954 |
| `twds0r2` g0 (half) | U+2614..U+2648 (3) | passed | 0 / 0 | 2 | seed 0 | 0.0050 0.0049 0.0046 0.0016 | 0.991 | 0.977 |
| `twds0r2` g1 (half) | U+2649..U+264B (3) | passed | 0 / 0 | 2 | seed 1 | 0.0047 0.0030 0.0041 0.0019 | 0.984 | 0.933 |
| `twds0` g3 | U+264C..U+2651 (6) | **failed** | 1 / 0: 6x12 p99 | 1 | no: halved | 0.0056 0.0038 0.0048 0.0018 | 0.943 | 0.963 |
| `twds0r3` g0 (half) | U+264C..U+264E (3) | passed | 0 / 0 | 0 | seed 0 | 0.0056 0.0038 0.0047 0.0016 | 0.946 | 0.974 |
| `twds0r3` g1 (half) | U+264F..U+2651 (3) | passed | 0 / 0 | 5 | seed 1 | 0.0057 0.0039 0.0045 0.0017 | 0.954 | 0.951 |
| `twds0` g4 | U+2652..U+26AA (6) | passed | 0 / 0 | 3 | seed 0 | 0.0043 0.0028 0.0039 0.0016 | 0.978 | 0.985 |
| `twds0` g5 | U+26AB..U+26CE (6) | passed | 0 / 0 | 1 | seed 1 | 0.0051 0.0033 0.0041 0.0020 | 0.965 | 0.988 |
| `twds0` g6 | U+26D4..U+26FA (6) | **failed** | 1 / 1: 10x20 p99 | 7 | no: halved | 0.0056 0.0049 0.0050 0.0022 | 0.965 | 0.988 |
| `twds0r6` g0 (half) | U+26D4..U+26F2 (3) | passed | 0 / 0 | 0 | seed 1 | 0.0055 0.0042 0.0039 0.0017 | 0.965 | 0.991 |
| `twds0r6` g1 (half) | U+26F3..U+26FA (3) | **failed** | 0 / 1: 24x48 p99 | 9 | **no: left out** | 0.0060 0.0056 0.0062 0.0024 | 0.965 | 0.989 |
| `twds0` g7 | U+26FD..U+274C (6) | passed | 0 / 0 | 3 | seed 1 | 0.0057 0.0052 0.0045 0.0024 | 0.958 | 0.966 |
| `twds0` g8 | U+274E..U+2795 (6) | passed | 0 / 0 | 1 | seed 1 | 0.0036 0.0038 0.0033 0.0015 | 0.983 | 0.938 |
| `twds1` g0 | U+2796..U+2B1C (6) | passed | 0 / 0 | 1 | seed 1 | 0.0035 0.0038 0.0027 0.0014 | 0.998 | 0.947 |
| `twds1` g1 | U+2B50..U+1F191 (6) | **failed** | 2 / 2: 24x48 mae, 48x96 mae | 17 | no: halved | 0.0093 0.0081 0.0070 0.0034 | 0.963 | 0.984 |
| `twds1r1` g0 (half) | U+2B50..U+1F004 (3) | passed | 0 / 0 | 6 | seed 0 | 0.0070 0.0065 0.0056 0.0022 | 0.970 | 0.993 |
| `twds1r1` g1 (half) | U+1F0CF..U+1F191 (3) | **failed** | 2 / 2: 24x48 mae, 48x96 mae | 17 | **no: left out** | 0.0116 0.0094 0.0078 0.0039 | 0.965 | 0.977 |
| `twds1` g2 | U+1F192..U+1F197 (6) | **failed** | 4 / 3: 12x24 p99, 24x48 mae, 48x96 mae, 48x96 p99 | 24 | no: halved | 0.0120 0.0114 0.0082 0.0041 | 0.925 | 0.988 |
| `twds1r2` g0 (half) | U+1F192..U+1F194 (3) | **failed** | 2 / 2: 24x48 mae, 48x96 mae | 21 | **no: left out** | 0.0120 0.0107 0.0082 0.0035 | 0.920 | 0.986 |
| `twds1r2` g1 (half) | U+1F195..U+1F197 (3) | **failed** | 4 / 3: 12x24 p99, 24x48 firm, 24x48 mae, 48x96 mae, 6x12 p99 | 18 | **no: left out** | 0.0117 0.0122 0.0076 0.0040 | 0.935 | 0.990 |
| `twds1` g3 | U+1F198..U+1F202 (6) | **failed** | 3 / 4: 12x24 mae, 24x48 mae, 48x96 mae, 48x96 p99 | 23 | no: halved | 0.0099 0.0129 0.0084 0.0043 | 0.955 | 0.991 |
| `twds1r3` g0 (half) | U+1F198..U+1F19A (3) | **failed** | 3 / 2: 24x48 firm, 24x48 mae, 48x96 mae | 17 | **no: left out** | 0.0110 0.0113 0.0078 0.0042 | 0.932 | 0.987 |
| `twds1r3` g1 (half) | U+1F200..U+1F202 (3) | **failed** | 3 / 3: 24x48 mae, 48x96 mae, 6x12 glyph_mae, 6x12 mae | 17 | **no: left out** | 0.0084 0.0144 0.0084 0.0038 | 0.979 | 0.996 |
| `twds1` g4 | U+1F210..U+1F215 (6) | **failed** | 3 / 3: 24x48 mae, 48x96 mae, 6x12 mae | 17 | no: halved | 0.0082 0.0132 0.0078 0.0032 | 0.977 | 0.985 |
| `twds1r4` g0 (half) | U+1F210..U+1F212 (3) | **failed** | 2 / 3: 24x48 mae, 48x96 mae, 6x12 mae | 13 | **no: left out** | 0.0084 0.0139 0.0079 0.0030 | 0.954 | 0.982 |
| `twds1r4` g1 (half) | U+1F213..U+1F215 (3) | **failed** | 2 / 1: 24x48 mae, 6x12 mae | 11 | **no: left out** | 0.0076 0.0123 0.0068 0.0027 | 0.994 | 0.989 |
| `twds1` g5 | U+1F216..U+1F21B (6) | **failed** | 7 / 6: 10x20 glyph_mae, 12x24 mae, 16x32 p99, 24x48 mae, 48x96 mae, 48x96 p99 | 24 | no: halved | 0.0117 0.0152 0.0123 0.0062 | 0.977 | 0.975 |
| `twds1r5` g0 (half) | U+1F216..U+1F218 (3) | **failed** | 6 / 3: 16x32 p99, 24x48 firm, 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 17 | **no: left out** | 0.0101 0.0144 0.0098 0.0043 | 0.984 | 0.983 |
| `twds1r5` g1 (half) | U+1F219..U+1F21B (3) | **failed** | 6 / 4: 12x24 p99, 24x48 firm, 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 19 | **no: left out** | 0.0118 0.0147 0.0125 0.0050 | 0.977 | 0.963 |
| `twds1` g6 | U+1F21C..U+1F221 (6) | **failed** | 7 / 6: 12x24 mae, 12x24 p99, 16x32 p99, 24x48 mae, 48x96 mae, 48x96 p99 | 24 | no: halved | 0.0124 0.0154 0.0131 0.0065 | 0.975 | 0.984 |
| `twds1r6` g0 (half) | U+1F21C..U+1F21E (3) | **failed** | 5 / 5: 12x24 mae, 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 18 | **no: left out** | 0.0117 0.0153 0.0115 0.0054 | 0.976 | 0.985 |
| `twds1r6` g1 (half) | U+1F21F..U+1F221 (3) | **failed** | 7 / 7: 12x24 mae, 12x24 p99, 24x48 firm, 24x48 mae, 48x96 mae, 48x96 p99 | 21 | **no: left out** | 0.0115 0.0145 0.0113 0.0050 | 0.983 | 0.982 |
| `twds1` g7 | U+1F222..U+1F227 (6) | **failed** | 8 / 7: 12x24 mae, 12x24 p99, 16x32 p99, 24x48 firm, 24x48 mae, 48x96 mae | 22 | no: halved | 0.0123 0.0157 0.0125 0.0060 | 0.963 | 0.981 |
| `twds1r7` g0 (half) | U+1F222..U+1F224 (3) | **failed** | 5 / 4: 24x48 firm, 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 18 | **no: left out** | 0.0103 0.0154 0.0097 0.0044 | 0.937 | 0.985 |
| `twds1r7` g1 (half) | U+1F225..U+1F227 (3) | **failed** | 4 / 3: 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 16 | **no: left out** | 0.0105 0.0145 0.0107 0.0048 | 0.991 | 0.977 |
| `twds1` g8 | U+1F228..U+1F22D (6) | **failed** | 4 / 6: 12x24 firm, 12x24 mae, 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 17 | no: halved | 0.0097 0.0138 0.0089 0.0043 | 0.955 | 0.981 |
| `twds1r8` g0 (half) | U+1F228..U+1F22A (3) | **failed** | 2 / 3: 24x48 mae, 48x96 mae, 6x12 mae | 12 | **no: left out** | 0.0087 0.0123 0.0072 0.0033 | 0.985 | 0.979 |
| `twds1r8` g1 (half) | U+1F22B..U+1F22D (3) | **failed** | 3 / 4: 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 16 | **no: left out** | 0.0104 0.0149 0.0095 0.0042 | 0.937 | 0.982 |
| `twds2` g0 | U+1F22E..U+1F233 (6) | **failed** | 5 / 4: 12x24 mae, 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 25 | no: halved | 0.0120 0.0150 0.0109 0.0054 | 0.954 | 0.980 |
| `twds2r0` g0 (half) | U+1F22E..U+1F230 (3) | **failed** | 3 / 3: 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 18 | **no: left out** | 0.0102 0.0142 0.0091 0.0043 | 0.950 | 0.972 |
| `twds2r0` g1 (half) | U+1F231..U+1F233 (3) | **failed** | 4 / 3: 12x24 p99, 24x48 mae, 48x96 mae, 6x12 mae | 20 | **no: left out** | 0.0122 0.0147 0.0101 0.0046 | 0.961 | 0.985 |
| `twds2` g1 | U+1F234..U+1F239 (6) | **failed** | 6 / 6: 12x24 mae, 12x24 p99, 24x48 firm, 24x48 mae, 48x96 mae, 48x96 p99 | 25 | no: halved | 0.0129 0.0153 0.0122 0.0062 | 0.973 | 0.983 |
| `twds2r1` g0 (half) | U+1F234..U+1F236 (3) | **failed** | 4 / 5: 24x48 firm, 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 18 | **no: left out** | 0.0115 0.0149 0.0108 0.0048 | 0.984 | 0.977 |
| `twds2r1` g1 (half) | U+1F237..U+1F239 (3) | **failed** | 3 / 4: 24x48 mae, 48x96 mae, 48x96 p99, 6x12 mae | 19 | **no: left out** | 0.0121 0.0150 0.0095 0.0044 | 0.961 | 0.985 |
| `twds2` g2 | U+1F23A..U+1F243 (6) | **failed** | 5 / 5: 16x32 p99, 24x48 glyph_mae, 24x48 mae, 48x96 mae, 48x96 p99 | 23 | no: halved | 0.0135 0.0151 0.0113 0.0059 | 0.962 | 0.972 |
| `twds2r2` g0 (half) | U+1F23A..U+1F240 (3) | **failed** | 4 / 4: 24x48 glyph_mae, 24x48 mae, 48x96 mae, 48x96 p99 | 24 | **no: left out** | 0.0157 0.0179 0.0134 0.0063 | 0.935 | 0.987 |
| `twds2r2` g1 (half) | U+1F241..U+1F243 (3) | passed | 0 / 0 | 7 | seed 1 | 0.0105 0.0122 0.0069 0.0045 | 0.992 | 0.952 |
| `twds2` g3 | U+1F244..U+1F250 (6) | **failed** | 8 / 6: 10x20 glyph_mae, 10x20 p99, 12x24 p99, 16x32 p99, 24x48 mae, 24x48 p99 | 21 | no: halved | 0.0130 0.0145 0.0119 0.0066 | 0.970 | 0.958 |
| `twds2r3` g0 (half) | U+1F244..U+1F246 (3) | **failed** | 0 / 1: 48x96 p99 | 16 | **no: left out** | 0.0124 0.0138 0.0091 0.0054 | 0.959 | 0.957 |
| `twds2r3` g1 (half) | U+1F247..U+1F250 (3) | **failed** | 2 / 2: 48x96 mae, 48x96 p99 | 21 | **no: left out** | 0.0133 0.0141 0.0123 0.0062 | 0.982 | 0.964 |
| `twds2` g4 | U+1F251..U+1F264 (6) | **failed** | 10 / 9: 10x20 firm, 10x20 p99, 12x24 mae, 12x24 p99, 16x32 mae, 16x32 p99 | 27 | no: halved | 0.0139 0.0130 0.0143 0.0073 | 0.963 | 0.982 |
| `twds2r4` g0 (half) | U+1F251..U+1F261 (3) | **failed** | 3 / 2: 16x32 p99, 48x96 mae, 48x96 p99 | 19 | **no: left out** | 0.0128 0.0109 0.0117 0.0053 | 0.958 | 0.988 |
| `twds2r4` g1 (half) | U+1F262..U+1F264 (3) | **failed** | 2 / 2: 48x96 mae, 48x96 p99 | 21 | **no: left out** | 0.0125 0.0123 0.0118 0.0053 | 0.979 | 0.983 |
| `twds2` g5 | U+1F265..U+1F604 (6) | **failed** | 3 / 2: 24x48 mae, 24x48 p99, 48x96 mae | 14 | no: halved | 0.0079 0.0062 0.0075 0.0032 | 0.972 | 0.970 |
| `twds2r5` g0 (half) | U+1F265..U+1F601 (3) | **failed** | 1 / 1: 48x96 mae | 16 | **no: left out** | 0.0090 0.0081 0.0088 0.0037 | 0.971 | 0.965 |
| `twds2r5` g1 (half) | U+1F602..U+1F604 (3) | passed | 0 / 0 | 3 | seed 0 | 0.0068 0.0044 0.0053 0.0024 | 0.984 | 0.976 |
| `twds2` g6 | U+1F605..U+1F60A (6) | passed | 0 / 0 | 7 | seed 0 | 0.0064 0.0045 0.0063 0.0028 | 0.977 | 0.983 |
| `twds2` g7 | U+1F60B..U+1F610 (6) | passed | 0 / 0 | 4 | seed 1 | 0.0067 0.0043 0.0061 0.0026 | 0.975 | 0.979 |
| `twds2` g8 | U+1F611..U+1F616 (6) | passed | 0 / 0 | 4 | seed 0 | 0.0061 0.0042 0.0057 0.0026 | 0.971 | 0.984 |
| `twds3` g0 | U+1F617..U+1F61C (6) | passed | 0 / 0 | 4 | seed 1 | 0.0063 0.0041 0.0055 0.0023 | 0.969 | 0.981 |
| `twds3` g1 | U+1F61D..U+1F622 (6) | passed | 0 / 0 | 8 | seed 0 | 0.0065 0.0045 0.0062 0.0027 | 0.975 | 0.978 |
| `twds3` g2 | U+1F623..U+1F628 (6) | passed | 0 / 0 | 8 | seed 1 | 0.0066 0.0049 0.0066 0.0031 | 0.969 | 0.986 |
| `twds3` g3 | U+1F629..U+1F62E (6) | **failed** | 1 / 2: 10x20 p99, 24x48 p99, 48x96 mae | 8 | no: halved | 0.0068 0.0053 0.0066 0.0030 | 0.964 | 0.982 |
| `twds3r3` g0 (half) | U+1F629..U+1F62B (3) | passed | 0 / 0 | 6 | seed 1 | 0.0070 0.0049 0.0064 0.0029 | 0.976 | 0.984 |
| `twds3r3` g1 (half) | U+1F62C..U+1F62E (3) | passed | 0 / 0 | 9 | seed 0 | 0.0064 0.0056 0.0063 0.0028 | 0.968 | 0.983 |
| `twds3` g4 | U+1F62F..U+1F634 (6) | passed | 0 / 0 | 4 | seed 0 | 0.0063 0.0042 0.0058 0.0027 | 0.975 | 0.980 |
| `twds3` g5 | U+1F635..U+1F63A (6) | **failed** | 1 / 0: 48x96 mae | 9 | no: halved | 0.0076 0.0050 0.0072 0.0031 | 0.982 | 0.985 |
| `twds3r5` g0 (half) | U+1F635..U+1F637 (3) | passed | 0 / 0 | 7 | seed 1 | 0.0071 0.0045 0.0064 0.0026 | 0.978 | 0.983 |
| `twds3r5` g1 (half) | U+1F638..U+1F63A (3) | **failed** | 0 / 1: 10x20 p99 | 9 | **no: left out** | 0.0080 0.0054 0.0078 0.0030 | 0.998 | 0.990 |
| `twds3` g6 | U+1F63B..U+1F640 (6) | passed | 0 / 0 | 10 | seed 1 | 0.0080 0.0051 0.0079 0.0031 | 0.997 | 0.988 |
| `twds3` g7 | U+1F641..U+1F646 (6) | **failed** | 1 / 1: 12x24 firm, 24x48 mae | 6 | no: halved | 0.0063 0.0043 0.0066 0.0027 | 0.971 | 0.983 |
| `twds3r7` g0 (half) | U+1F641..U+1F643 (3) | passed | 0 / 0 | 2 | seed 0 | 0.0053 0.0038 0.0048 0.0021 | 0.968 | 0.985 |
| `twds3r7` g1 (half) | U+1F644..U+1F646 (3) | passed | 0 / 0 | 8 | seed 1 | 0.0069 0.0047 0.0075 0.0028 | 0.978 | 0.988 |
| `twds3` g8 | U+1F647..U+1F64C (6) | **failed** | 4 / 0: 10x20 p99, 12x24 p99, 24x48 mae, 24x48 p99 | 9 | no: halved | 0.0072 0.0043 0.0070 0.0028 | 0.965 | 0.985 |
| `twds3r8` g0 (half) | U+1F647..U+1F649 (3) | passed | 0 / 0 | 9 | seed 1 | 0.0068 0.0042 0.0069 0.0025 | 0.952 | 0.978 |
| `twds3r8` g1 (half) | U+1F64A..U+1F64C (3) | **failed** | 3 / 1: 10x20 p99, 12x24 p99, 24x48 p99 | 5 | **no: left out** | 0.0070 0.0040 0.0061 0.0024 | 0.976 | 0.993 |
| `twds4` g0 | U+1F64D..U+1F682 (6) | **failed** | 1 / 2: 10x20 p99, 24x48 p99 | 7 | no: halved | 0.0058 0.0044 0.0056 0.0023 | 0.966 | 0.977 |
| `twds4r0` g0 (half) | U+1F64D..U+1F64F (3) | passed | 0 / 0 | 3 | seed 1 | 0.0043 0.0032 0.0048 0.0017 | 0.945 | 0.994 |
| `twds4r0` g1 (half) | U+1F680..U+1F682 (3) | **failed** | 0 / 1: 24x48 firm | 7 | **no: left out** | 0.0071 0.0056 0.0061 0.0026 | 0.985 | 0.958 |
| `twds4` g1 | U+1F683..U+1F688 (6) | **failed** | 4 / 2: 24x48 mae, 24x48 p99, 48x96 mae, 6x12 p99 | 10 | no: halved | 0.0083 0.0069 0.0070 0.0030 | 0.981 | 0.974 |
| `twds4r1` g0 (half) | U+1F683..U+1F685 (3) | **failed** | 2 / 2: 12x24 p99, 24x48 mae, 24x48 p99 | 9 | **no: left out** | 0.0076 0.0074 0.0068 0.0028 | 0.979 | 0.967 |
| `twds4r1` g1 (half) | U+1F686..U+1F688 (3) | passed | 0 / 0 | 7 | seed 0 | 0.0087 0.0063 0.0064 0.0026 | 0.979 | 0.981 |
| `twds4` g2 | U+1F689..U+1F68E (6) | **failed** | 3 / 4: 10x20 p99, 24x48 mae, 48x96 mae, 48x96 p99, 8x16 p99 | 12 | no: halved | 0.0096 0.0082 0.0082 0.0038 | 0.981 | 0.940 |
| `twds4r2` g0 (half) | U+1F689..U+1F68B (3) | **failed** | 1 / 1: 24x48 p99, 8x16 p99 | 11 | **no: left out** | 0.0107 0.0080 0.0088 0.0035 | 0.979 | 0.923 |
| `twds4r2` g1 (half) | U+1F68C..U+1F68E (3) | **failed** | 2 / 0: 24x48 firm, 24x48 p99 | 11 | **no: left out** | 0.0082 0.0080 0.0069 0.0031 | 0.981 | 0.951 |
| `twds4` g3 | U+1F68F..U+1F694 (6) | **failed** | 3 / 3: 24x48 mae, 48x96 mae, 48x96 p99, 6x12 firm | 9 | no: halved | 0.0075 0.0063 0.0079 0.0032 | 0.967 | 0.963 |
| `twds4r3` g0 (half) | U+1F68F..U+1F691 (3) | **failed** | 2 / 3: 10x20 p99, 12x24 firm, 24x48 mae | 7 | **no: left out** | 0.0070 0.0060 0.0076 0.0029 | 0.969 | 0.970 |
| `twds4r3` g1 (half) | U+1F692..U+1F694 (3) | **failed** | 1 / 3: 24x48 mae, 24x48 p99, 6x12 p99 | 10 | **no: left out** | 0.0077 0.0065 0.0073 0.0031 | 0.966 | 0.956 |
| `twds4` g4 | U+1F695..U+1F69A (6) | **failed** | 1 / 2: 24x48 mae, 6x12 firm | 10 | no: halved | 0.0073 0.0066 0.0072 0.0029 | 0.961 | 0.955 |
| `twds4r4` g0 (half) | U+1F695..U+1F697 (3) | passed | 0 / 0 | 9 | seed 1 | 0.0071 0.0056 0.0066 0.0027 | 0.965 | 0.953 |
| `twds4r4` g1 (half) | U+1F698..U+1F69A (3) | **failed** | 2 / 2: 10x20 p99, 24x48 mae | 10 | **no: left out** | 0.0072 0.0072 0.0071 0.0029 | 0.958 | 0.958 |
| `twds4` g5 | U+1F69B..U+1F6A0 (6) | **failed** | 3 / 3: 24x48 mae, 24x48 p99, 48x96 mae | 8 | no: halved | 0.0077 0.0069 0.0076 0.0033 | 0.954 | 0.962 |
| `twds4r5` g0 (half) | U+1F69B..U+1F69D (3) | **failed** | 2 / 2: 24x48 mae, 24x48 p99 | 10 | **no: left out** | 0.0080 0.0071 0.0071 0.0033 | 0.986 | 0.971 |
| `twds4r5` g1 (half) | U+1F69E..U+1F6A0 (3) | **failed** | 2 / 2: 24x48 mae, 24x48 p99 | 4 | **no: left out** | 0.0061 0.0065 0.0068 0.0027 | 0.921 | 0.952 |
| `twds4` g6 | U+1F6A1..U+1F6A6 (6) | passed | 0 / 0 | 7 | seed 0 | 0.0067 0.0054 0.0053 0.0024 | 0.890 | 0.983 |
| `twds4` g7 | U+1F6A7..U+1F6AC (6) | passed | 0 / 0 | 6 | seed 1 | 0.0078 0.0055 0.0056 0.0023 | 0.973 | 0.976 |
| `twds4` g8 | U+1F6AD..U+1F6B2 (6) | **failed** | 2 / 3: 48x96 mae, 8x16 firm, 8x16 p99 | 10 | no: halved | 0.0071 0.0046 0.0072 0.0029 | 0.950 | 0.981 |
| `twds4r8` g0 (half) | U+1F6AD..U+1F6AF (3) | **failed** | 1 / 1: 10x20 p99, 8x16 firm | 7 | **no: left out** | 0.0063 0.0040 0.0059 0.0024 | 0.953 | 0.987 |
| `twds4r8` g1 (half) | U+1F6B0..U+1F6B2 (3) | passed | 0 / 0 | 11 | seed 1 | 0.0078 0.0049 0.0080 0.0027 | 0.954 | 0.971 |
| `twds5` g0 | U+1F6B3..U+1F6B8 (6) | **failed** | 5 / 5: 24x48 mae, 24x48 p99, 48x96 mae, 48x96 p99, 6x12 firm, 8x16 firm | 12 | no: halved | 0.0089 0.0059 0.0092 0.0038 | 0.961 | 0.976 |
| `twds5r0` g0 (half) | U+1F6B3..U+1F6B5 (3) | **failed** | 5 / 2: 12x24 p99, 24x48 mae, 48x96 mae, 48x96 p99, 6x12 firm, 8x16 firm | 16 | **no: left out** | 0.0112 0.0069 0.0122 0.0043 | 0.957 | 0.969 |
| `twds5r0` g1 (half) | U+1F6B6..U+1F6B8 (3) | passed | 0 / 0 | 3 | seed 0 | 0.0064 0.0047 0.0054 0.0025 | 0.972 | 0.982 |
| `twds5` g1 | U+1F6B9..U+1F6BE (6) | **failed** | 3 / 2: 48x96 mae, 6x12 p99, 8x16 firm | 9 | no: halved | 0.0083 0.0061 0.0062 0.0032 | 0.957 | 0.963 |
| `twds5r1` g0 (half) | U+1F6B9..U+1F6BB (3) | **failed** | 0 / 1: 8x16 firm | 6 | **no: left out** | 0.0083 0.0059 0.0051 0.0029 | 0.938 | 0.946 |
| `twds5r1` g1 (half) | U+1F6BC..U+1F6BE (3) | **failed** | 1 / 0: 24x48 mae | 10 | **no: left out** | 0.0082 0.0061 0.0065 0.0028 | 0.980 | 0.979 |
| `twds5` g2 | U+1F6BF..U+1F6C4 (6) | **failed** | 1 / 1: 24x48 p99 | 9 | no: halved | 0.0089 0.0062 0.0062 0.0024 | 0.976 | 0.980 |
| `twds5r2` g0 (half) | U+1F6BF..U+1F6C1 (3) | **failed** | 0 / 1: 24x48 firm | 6 | **no: left out** | 0.0072 0.0060 0.0058 0.0021 | 0.972 | 0.991 |
| `twds5r2` g1 (half) | U+1F6C2..U+1F6C4 (3) | **failed** | 2 / 1: 24x48 p99, 8x16 p99 | 8 | **no: left out** | 0.0106 0.0062 0.0057 0.0025 | 0.978 | 0.969 |
| `twds5` g3 | U+1F6C5..U+1F6D5 (6) | **failed** | 3 / 3: 24x48 mae, 48x96 mae, 48x96 p99 | 17 | no: halved | 0.0101 0.0082 0.0076 0.0037 | 0.986 | 0.989 |
| `twds5r3` g0 (half) | U+1F6C5..U+1F6D0 (3) | passed | 0 / 0 | 16 | seed 0 | 0.0097 0.0101 0.0061 0.0034 | 0.998 | 0.989 |
| `twds5r3` g1 (half) | U+1F6D1..U+1F6D5 (3) | passed | 0 / 0 | 13 | seed 1 | 0.0100 0.0059 0.0085 0.0034 | 0.979 | 0.990 |
| `twds5` g4 | U+1F6D6..U+1F6DF (6) | passed | 0 / 0 | 3 | seed 1 | 0.0066 0.0055 0.0049 0.0024 | 0.938 | 0.991 |
| `twds5` g5 | U+1F6EB..U+1F6F7 (6) | passed | 0 / 0 | 0 | seed 1 | 0.0048 0.0035 0.0039 0.0020 | 0.952 | 0.965 |
| `twds5` g6 | U+1F6F8..U+1F7E0 (6) | **failed** | 0 / 1: 8x16 firm | 0 | no: halved | 0.0044 0.0035 0.0041 0.0019 | 0.984 | 0.984 |
| `twds5r6` g0 (half) | U+1F6F8..U+1F6FA (3) | passed | 0 / 0 | 0 | seed 1 | 0.0046 0.0035 0.0037 0.0019 | 0.993 | 0.991 |
| `twds5r6` g1 (half) | U+1F6FB..U+1F7E0 (3) | passed | 0 / 0 | 1 | seed 0 | 0.0040 0.0035 0.0041 0.0017 | 0.982 | 0.984 |
| `twds5` g7 | U+1F7E1..U+1F7E6 (6) | passed | 0 / 0 | 0 | seed 0 | 0.0026 0.0031 0.0025 0.0011 | 1.000 | 0.963 |
| `twds5` g8 | U+1F7E7..U+1F7F0 (6) | passed | 0 / 0 | 1 | seed 0 | 0.0040 0.0050 0.0036 0.0018 | 1.000 | 0.907 |

## The boxes in use that the gates do not count (information)

The shipped seed of each net at the cell a program asks for the boxes
18×18, 20×20 and 36×36, by the scorer's own metric code against the bundle
teacher, and in the box itself (each pair of rows averaged) against the
teacher's area coverage of the box. Declared as information before
training; it decides nothing.

| Net | 18×36: error, 99th pct | 20×40 | 36×72 | Box 18×18: error | Box 20×20 | Box 36×36 | Not nearest or vanished |
|---|---|---|---|---:|---:|---:|---|
| `twds0` g0 | 0.0023, 0.045 | 0.0019, 0.043 | 0.0022, 0.051 | 0.0022 | 0.0018 | 0.0018 | none |
| `twds0` g1 | 0.0030, 0.051 | 0.0026, 0.054 | 0.0022, 0.050 | 0.0028 | 0.0024 | 0.0020 | none |
| `twds0r2` g0 | 0.0040, 0.052 | 0.0023, 0.030 | 0.0024, 0.050 | 0.0036 | 0.0020 | 0.0021 | none |
| `twds0r2` g1 | 0.0032, 0.051 | 0.0021, 0.029 | 0.0026, 0.053 | 0.0029 | 0.0018 | 0.0023 | none |
| `twds0r3` g0 | 0.0036, 0.051 | 0.0033, 0.056 | 0.0023, 0.049 | 0.0032 | 0.0030 | 0.0020 | none |
| `twds0r3` g1 | 0.0037, 0.052 | 0.0030, 0.055 | 0.0026, 0.051 | 0.0034 | 0.0027 | 0.0023 | none |
| `twds0` g4 | 0.0026, 0.038 | 0.0021, 0.034 | 0.0025, 0.053 | 0.0022 | 0.0018 | 0.0021 | none |
| `twds0` g5 | 0.0031, 0.041 | 0.0031, 0.045 | 0.0027, 0.051 | 0.0025 | 0.0025 | 0.0022 | none |
| `twds0r6` g0 | 0.0038, 0.051 | 0.0031, 0.055 | 0.0021, 0.047 | 0.0034 | 0.0028 | 0.0018 | none |
| `twds0` g7 | 0.0037, 0.053 | 0.0044, 0.057 | 0.0025, 0.052 | 0.0034 | 0.0042 | 0.0023 | none |
| `twds0` g8 | 0.0026, 0.048 | 0.0032, 0.044 | 0.0020, 0.047 | 0.0022 | 0.0028 | 0.0017 | none |
| `twds1` g0 | 0.0028, 0.051 | 0.0021, 0.039 | 0.0020, 0.051 | 0.0026 | 0.0020 | 0.0019 | none |
| `twds1r1` g0 | 0.0043, 0.051 | 0.0043, 0.056 | 0.0031, 0.050 | 0.0037 | 0.0037 | 0.0028 | none |
| `twds2r2` g1 | 0.0076, 0.053 | 0.0057, 0.045 | 0.0050, 0.058 | 0.0074 | 0.0054 | 0.0047 | none |
| `twds2r5` g1 | 0.0037, 0.032 | 0.0031, 0.033 | 0.0034, 0.058 | 0.0032 | 0.0026 | 0.0030 | none |
| `twds2` g6 | 0.0039, 0.035 | 0.0034, 0.036 | 0.0037, 0.060 | 0.0032 | 0.0029 | 0.0031 | none |
| `twds2` g7 | 0.0038, 0.037 | 0.0033, 0.037 | 0.0034, 0.056 | 0.0031 | 0.0027 | 0.0028 | none |
| `twds2` g8 | 0.0036, 0.038 | 0.0033, 0.036 | 0.0034, 0.056 | 0.0030 | 0.0028 | 0.0028 | none |
| `twds3` g0 | 0.0035, 0.034 | 0.0032, 0.036 | 0.0031, 0.052 | 0.0029 | 0.0026 | 0.0026 | none |
| `twds3` g1 | 0.0038, 0.034 | 0.0036, 0.040 | 0.0034, 0.053 | 0.0031 | 0.0030 | 0.0029 | none |
| `twds3` g2 | 0.0042, 0.047 | 0.0038, 0.048 | 0.0039, 0.059 | 0.0034 | 0.0032 | 0.0032 | none |
| `twds3r3` g0 | 0.0038, 0.039 | 0.0038, 0.045 | 0.0036, 0.054 | 0.0032 | 0.0032 | 0.0030 | none |
| `twds3r3` g1 | 0.0045, 0.049 | 0.0043, 0.053 | 0.0037, 0.057 | 0.0039 | 0.0036 | 0.0032 | none |
| `twds3` g4 | 0.0036, 0.037 | 0.0034, 0.036 | 0.0036, 0.056 | 0.0029 | 0.0028 | 0.0029 | none |
| `twds3r5` g0 | 0.0041, 0.049 | 0.0038, 0.051 | 0.0035, 0.056 | 0.0034 | 0.0032 | 0.0030 | none |
| `twds3` g6 | 0.0042, 0.043 | 0.0046, 0.051 | 0.0041, 0.069 | 0.0033 | 0.0036 | 0.0034 | none |
| `twds3r7` g0 | 0.0031, 0.032 | 0.0026, 0.030 | 0.0028, 0.047 | 0.0025 | 0.0021 | 0.0023 | none |
| `twds3r7` g1 | 0.0040, 0.044 | 0.0038, 0.043 | 0.0038, 0.054 | 0.0032 | 0.0032 | 0.0032 | none |
| `twds3r8` g0 | 0.0044, 0.060 | 0.0036, 0.057 | 0.0036, 0.058 | 0.0039 | 0.0031 | 0.0032 | none |
| `twds4r0` g0 | 0.0031, 0.049 | 0.0029, 0.043 | 0.0029, 0.053 | 0.0029 | 0.0027 | 0.0027 | none |
| `twds4r1` g1 | 0.0043, 0.050 | 0.0044, 0.057 | 0.0034, 0.055 | 0.0039 | 0.0041 | 0.0031 | none |
| `twds4r4` g0 | 0.0048, 0.052 | 0.0047, 0.057 | 0.0037, 0.060 | 0.0045 | 0.0042 | 0.0034 | none |
| `twds4` g6 | 0.0037, 0.052 | 0.0047, 0.058 | 0.0027, 0.056 | 0.0034 | 0.0044 | 0.0025 | none |
| `twds4` g7 | 0.0040, 0.053 | 0.0042, 0.060 | 0.0034, 0.059 | 0.0036 | 0.0039 | 0.0032 | none |
| `twds4r8` g1 | 0.0044, 0.053 | 0.0037, 0.049 | 0.0039, 0.063 | 0.0037 | 0.0032 | 0.0034 | none |
| `twds5r0` g1 | 0.0035, 0.040 | 0.0029, 0.039 | 0.0033, 0.051 | 0.0027 | 0.0024 | 0.0026 | none |
| `twds5r3` g0 | 0.0075, 0.059 | 0.0077, 0.060 | 0.0052, 0.066 | 0.0072 | 0.0071 | 0.0050 | none |
| `twds5r3` g1 | 0.0054, 0.063 | 0.0055, 0.064 | 0.0048, 0.065 | 0.0050 | 0.0051 | 0.0044 | none |
| `twds5` g4 | 0.0040, 0.052 | 0.0044, 0.056 | 0.0031, 0.056 | 0.0037 | 0.0040 | 0.0028 | none |
| `twds5` g5 | 0.0031, 0.048 | 0.0035, 0.055 | 0.0027, 0.057 | 0.0027 | 0.0031 | 0.0023 | none |
| `twds5r6` g0 | 0.0025, 0.049 | 0.0025, 0.039 | 0.0020, 0.045 | 0.0022 | 0.0022 | 0.0018 | none |
| `twds5r6` g1 | 0.0026, 0.037 | 0.0028, 0.044 | 0.0023, 0.051 | 0.0023 | 0.0023 | 0.0021 | none |
| `twds5` g7 | 0.0021, 0.049 | 0.0014, 0.028 | 0.0014, 0.049 | 0.0020 | 0.0012 | 0.0013 | none |
| `twds5` g8 | 0.0040, 0.050 | 0.0024, 0.042 | 0.0026, 0.050 | 0.0040 | 0.0024 | 0.0025 | none |

## Recipe

- **Drawings.** `train/wide.py` and its parts put each drawing of the
  18×18 box into the net's cell (1 wide, 2 high) with every stroke as its
  outline, so a lying stroke is as thick as a standing one once the cell is
  drawn at half height. Drawn from the Unicode name and the charts' words;
  no font was opened or rasterised to make or check any drawing, and no
  emoji image was looked at.
- **Sets and groups.** 6 sets, each cut in order into group nets
  (54 in all); 33 failed and were trained again as halves, so
  the bundle holds 44 nets of 3 to 6 characters.
- **Training.** `train/split_expert.py train --mode repertoire --partition
  contiguous`, unchanged: hidden width 64, 120,000 steps, the project teacher
  (grid 256), seeds 0 and 1. A halved group: the set `NAMErI` of that
  group's characters, two parts, the rest the same.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from
  each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
python3 train/build_wide_symbols_v1.py    # rebuilds the .nrt byte for byte from the group nets
make test-wide-symbols-v1
```

## Checks

`make test-wide-symbols-v1` (part of `make test`): every group net against
the float64 reference; the bundle rebuilt byte for byte; its table exactly
`neuronte-wide-symbols-v1.symbols.txt`; no character in two of the four wide bundles, 1,335 in
all; every scalar from U+0000 to U+10FFFF routed as the table says; pixels
through the bundle equal to each group net alone at 19 cell sizes, at the
five cells asked for two-cell boxes and with one sample a pixel; every
character with ink in its 18×18 box; `test_api --standalone`; and the
validation record: only nets whose two seeds passed gates v2.3 are in the
bundle, each as the selected seed.

## Speed

Measured on the two x86 hosts other cards use, an Intel Core i7-6820HQ and an
Intel Core i7-10700F, each under the shared benchmark lock, at commit 2938cbc
(the bundle there is byte for byte the one here). kilix-bench e21e5cd: one
pinned core, a fresh process for every job, one warmup and ten measured
rounds in shuffled order, medians, raw trials kept, every model checked
against the float64 reference first. The corpus is this bundle's 195
characters. The cells 8×16, 16×32 and 48×96 are what a program asks for
the two-cell boxes 8×8, 16×16 and 48×48. split-v9, which was not trained
on these characters, sends each through its gate to one of its nets and
draws something else; this bundle looks it up in its table and runs a
small group net.

| µs per character | split-v9, i7-6820HQ | wide-symbols-v1, i7-6820HQ | ratio | split-v9, i7-10700F | wide-symbols-v1, i7-10700F | ratio |
|---|---:|---:|---:|---:|---:|---:|
| Coverage, uncached, 8×16 | 504.2 | 181.4 | 2.78 | 390.1 | 140.9 | 2.77 |
| Coverage, uncached, 16×32 | 1968.3 | 692.0 | 2.84 | 1524.4 | 563.9 | 2.70 |
| Coverage, uncached, 48×96 | 4373.2 | 1533.8 | 2.85 | 3956.9 | 1206.8 | 3.28 |
| Draw, cold, 8×16 | 511.0 | 184.4 | 2.77 | 405.1 | 142.4 | 2.84 |
| Draw, cold, 16×32 | 1966.0 | 701.3 | 2.80 | 1504.1 | 540.4 | 2.78 |
| Draw, cold, 48×96 | 4399.5 | 1583.0 | 2.78 | 3373.9 | 1219.3 | 2.77 |
| Draw, warm, 8×16 | 3.9 | 1.2 | 3.33 | 2.9 | 0.9 | 3.35 |
| Draw, warm, 16×32 | 6.7 | 3.8 | 1.78 | 5.0 | 2.8 | 1.78 |
| Draw, warm, 48×96 | 27.4 | 27.9 | 0.98 | 20.0 | 20.3 | 0.99 |

Uncached, wide-symbols-v1 draws these characters 2.9 times as fast as
split-v9 does (geometric mean over the three cells and both hosts:
2.83 on the i7-6820HQ, 2.91 on the i7-10700F; cold draw 2.8,
warm draw 1.8). A lookup in its table takes 13 ns and 8 ns against
1241 ns and 919 ns for split-v9's gate. Opening the file takes 2.9 ms and
2.2 ms against 4.7 ms and 3.4 ms for split-v9.

A two-cell box costs the samples of the cell W×2H a program asks for it:
twice those of a one-cell character of the same height. A handle caches
1,024 drawn cells.

## Files

| File | What |
|---|---|
| `neuronte-wide-symbols-v1.nrt` | The bundle, 2,511,496 bytes, sha256 `8b922014fb953403dd8b161bffb22299aa52aa5afc16f3d35b4a3dd4d5768478` |
| `neuronte-wide-symbols-v1.symbols.txt` | The 195 characters it was trained on |
| `neuronte-wide-symbols-v1-SET-gN.json` | The 44 group nets as trained (the shipped seed) |
| `neuronte-wide-symbols-v1.provenance.json` | Every member's hash and scalars, written by its build script |
| `neuronte-wide-symbols-v1.validation.json` | The gates' hashes, both seeds' measurements and failures for every group and half, the limits eased, what was left out |
