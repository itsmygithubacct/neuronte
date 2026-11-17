# term-blocks-v1: 310 characters of four blocks made by rule, on their own

`neuronte-term-blocks-v1.nrt` is a terminal bundle for the Yijing hexagrams, the Tai Xuan Jing
figures, the domino tiles and the playing cards: four Unicode blocks whose
every character is put together from a few parts by a rule. No earlier
bundle was trained on them; in `neuronte-split-v9` each goes to the
router's gate and is drawn by a net that never saw it.

It is a **standalone** bundle: 5 tiled nets, 1 group net and one blank net,
849,696 bytes, with no copy of split-v9 in it. A program opens it beside
split-v9 and asks it first (see "What a consumer changes").

| Characters | Training set | Form in the bundle | Gates (gates-v2.3) |
|---|---|---|---|
| 64 Yijing hexagrams: U+4DC0..U+4DFF | `tblkhex` | tiled, 1×6: 6 tile nets of width 32 | passed, both seeds |
| 6 Tai Xuan Jing monogram and digrams: U+1D300..U+1D305 | `tblkdig` | 1 group net of width 64 | passed, both seeds |
| 81 Tai Xuan Jing tetragrams: U+1D306..U+1D356 | `tblktet` | tiled, 1×4: 4 tile nets of width 32 | passed, both seeds |
| 50 Domino tiles, lying: U+1F030..U+1F061 | `tblkdomh` | tiled, 2×1: 2 tile nets of width 64 | passed, both seeds |
| 50 Domino tiles, standing: U+1F062..U+1F093 | `tblkdomv` | tiled, 1×2: 2 tile nets of width 64 | passed, both seeds |
| 59 Playing cards: U+1F0A0..U+1F0AE, U+1F0B1..U+1F0BE, U+1F0C1..U+1F0CF, U+1F0D1..U+1F0DF | `tblkcard` | tiled, 1×2: 2 tile nets of width 128 | passed, both seeds |

All 310 listed characters are in the bundle. Every member passed the
common gates with both seeds, as the owner amended them while the bundle
trained; three of the six pass only because of the last amendment, which
was decided after their first scores were in (see "Gates").

**Not a default, and not a replacement for split-v9.** Nothing opens this
file until a program is changed to.

## What the drawings are

`train/term_blocks.py` makes every drawing from `font/term-blocks.txt` by
rule. **No font was read or rasterised**, to make a drawing or to check
one; DejaVu Sans Mono gave only its list of code points. The shapes come
from the characters' Unicode names and the Unicode charts as remembered.

- **Hexagrams.** Six lines, the top line first, each whole or broken in
  the middle, in the King Wen order of the code points.
- **Tai Xuan Jing.** The monogram (one line broken twice), five digrams,
  and 81 tetragrams: four lines, each whole, broken once or broken twice,
  counted in threes with the top line the slowest digit.
- **Domino tiles are drawn to fill one cell.** Unicode shows them as wide
  pictures. A standing tile is the cell: a frame, a bar across the middle,
  the first number in the upper field. A lying tile is the cell cut down
  the middle: two tall fields side by side, each showing its face upright
  with the pips stretched to tall ovals.
- **Playing cards are drawn to fill one cell**: a frame, the rank above
  (A, 2 to 9, T for ten, J, C for the knight, Q, K: this project's own
  letters and digits, made small) and the suit below. Spades and clubs are
  filled, hearts and diamonds in outline. The jokers are a star, filled
  for the black joker and in outline for the white one. U+1F0BF and the
  trumps U+1F0E0..U+1F0F5 are not in the list.

**What is not certain**, as the drawing sheet said beside each block:
which line of a Tai Xuan Jing digram is the upper one, and which of its
names means which line; the order in which the tetragrams count (if the
bottom line is the slowest digit, 72 of the 81 are in the wrong places);
which diagonal a domino's two and three lie on; how the charts tell red
suits from black in one colour, and what a joker looks like there. The
two domino backs (U+1F030 and U+1F062) are one drawing. At 8×16 and below
the frame of a tile or a card is thinner than a pixel and shows grey;
these two blocks read well from about 12×24.

## The form of each block, and why

A **tiled net** cuts the cell into a fixed grid and draws each piece with
its own small net, which receives the character's own scalar
(`train/tile_member.py`; the runtime already draws tiled members inside a
bundle, so nothing in `src/` changed). It suits a block whose characters
are a fixed grid of independent parts: a piece of the cell then shows only
a few different pictures over the whole block, and a narrow net can learn
them. The declared rule was: train each such set tiled at several tile
widths, ship the smallest width whose two seeds pass the gates and agree
with the float64 reference, and fall back to ordinary group nets only if
no width passes.

| Training set | Grid | Why this grid | What was trained, and how it did | Ships as |
|---|---|---|---|---|
| `tblkhex` | 1×6 | six lines, one to each sixth of the cell's height | width 16 failed (15 and 2 failures in seeds 0 and 1); width 32 passed; width 64 passed | tiled, 1×6: 6 tile nets of width 32 |
| `tblkdig` | none | six characters of one, or two, lines: too few for a grid of its own | one group net of width 64 | 1 group net of width 64 |
| `tblktet` | 1×4 | four lines, one to each quarter of the cell's height | width 16 failed (49 and 121 failures in seeds 0 and 1); width 32 passed; width 64 passed | tiled, 1×4: 4 tile nets of width 32 |
| `tblkdomh` | 2×1 | two fields side by side, each half of the cell's width | width 32 failed (12 and 19 failures in seeds 0 and 1); width 64 passed | tiled, 2×1: 2 tile nets of width 64 |
| `tblkdomv` | 1×2 | two fields, one above the other | width 32 failed (5 and 9 failures in seeds 0 and 1); width 64 passed | tiled, 1×2: 2 tile nets of width 64 |
| `tblkcard` | 1×2 | the rank in the upper half, the suit in the lower | width 64 failed (7 and 0 failures in seeds 0 and 1); width 128 passed | tiled, 1×2: 2 tile nets of width 128 |

A tile's picture is not quite independent of its neighbours: the net
learns the true distance to the nearest ink, which near a tile's edge
depends on the line in the next tile.

## What a consumer changes

Nothing, until it opens this file. It does not replace split-v9 and holds
none of its characters; `tests/check_bundle_lists.py` checks that the two
share no trained scalar.

```c
neuronte_open_file("neuronte-split-v9.nrt", &base);
neuronte_open_file("neuronte-term-blocks-v1.nrt", &blocks);
/* for each scalar c */
font = neuronte_untrained(blocks, c) ? base : blocks;
```

`neuronte_untrained(blocks, c)` is 0 for exactly the 310 characters in
`neuronte-term-blocks-v1.list.txt` and 1 for every other scalar. A scalar outside
the list, drawn through this file anyway, comes out blank (the file's
fallback is a net that draws nothing), or as the code-made hollow box after
`neuronte_set_untrained(blocks, 1)`. The file needs the current runtime
(version 2 bundles holding tiled members). It has 7 members.

Cells are the terminal's 1:2 cell; the nets were trained and measured from
6×12 to 48×96.

## Recipe

Declared in the lane's report before training, and not changed after
results were seen. The gates were amended by the owner while it trained;
see "Gates".

- **Teacher.** The project teacher of `train/split_expert.py` (grid 256,
  tau 0.15), unchanged.
- **Tile nets.** `train/tile_expert.py COLUMNSxROWS DIR`: split_expert.py's
  own spatial training loop on the set's grid, one net a tile, every net
  seeing every character of the set; 120,000 steps, seeds 0 and 1.
  Widths trained: hexagrams and tetragrams 16, 32 and 64; dominoes 32 and
  64; cards 64 and 128.
- **Group nets.** `train/split_expert.py train --mode repertoire
  --partition contiguous`, unchanged: width 64, 120,000 steps, seeds 0 and
  1. The monogram and digrams are one group; the other sets were also
  trained as groups (hexagrams 6, tetragrams 7, dominoes 6 and 6, cards 8)
  as the fallback, and none of those is used: every set passed tiled. Only
  the cards' eight were scored (seven pass; the last fails one 99th
  percentile rule in both seeds); the others were not scored. No width 96
  retry.
- **Gates.** The common gates of phases 3 to 6, kind symbols, scored by the
  common command against the teacher of all 310 characters. Each tiled net
  is scored as one group over its whole set. A member whose two seeds pass
  ships the seed with the lower mean error over 8×16, 16×32 and 48×96.
  A failing group net gets one remedy (two halves, trained once); what
  still fails is left out. No remedy was needed.
- **Packing.** `train/standalone_bundle.py`: the members, a table from each
  listed scalar to its member, no gate, and a blank net as the fallback.

```sh
make pack-term-blocks-v1    # rebuilds the .nrt byte for byte from the members
make test-term-blocks-v1
```

## Gates

The limits are `gates-v2.json`, sha256
`5bf1a3f8312c45df2a20b2e69d51ee3c690c58891ec5390cf0e41cbdf9f9b51b`,
declared before this bundle's training. The owner amended the gates three
times while it trained; verdicts are final under `gates-v2.3.json`,
sha256 `2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`.
For symbols its declared limits are gates-v2's, every one. What it adds:
no limit is applied tighter than the score of a perfect net (the drawing
itself, sampled as the library samples) with ten per cent of room; and a
seed that puts every pixel on the right side at all seven counted sizes
passes whatever its error rules say. Both additions were decided by the
owner after the first of this bundle's nets had been scored and had failed;
the hexagrams were the case shown. So three of the six members are in the
bundle because of that amendment, and the table says which.

Under the gates as they stood before it (`gates-v2.2.json`: the same
limits, a rule skipped where the perfect net itself fails it, no room
otherwise), the shipped members score as follows. This changes no verdict
and is here so that the amendment's effect can be seen.

| Member | Under gates-v2.2 | What failed there (seed 0; seed 1) | Scored |
|---|---|---|---|
| `tblkhex` | **failed** | 8x16 mae, 16x32 mae; 8x16 mae, 16x32 mae | at the time |
| `tblkdig` | passed | nothing | afterwards, for this table |
| `tblktet` | passed | nothing | at the time |
| `tblkdomh` | **failed** | 16x32 glyph_mae U+1F030 0.0194; nothing | at the time |
| `tblkdomv` | passed | nothing | afterwards, for this table |
| `tblkcard` | **failed** | 8x16 glyph_mae U+1F0A0 0.0292; nothing | afterwards, for this table |

The three failures are small: the hexagrams' mean error at 8×16 is 0.0134
against a limit of 0.0131 that the perfect net meets by 0.00004; one
domino back and one card back exceed the worst-character limit at one
size in one seed. They are failures of the gates as declared all the
same.

The teacher's mask, which the error is measured against, is 8 by 8 samples
a pixel. A straight edge that runs along the pixel rows or columns off the
pixel lattice is rounded to an eighth of a pixel along its whole length, so
even a perfect net differs from the mask all along it. These four blocks
are made of such edges, and many of their limits were eased for that
reason:

| Member | Limits eased, of those applied | Rules eased | Largest easing |
|---|---:|---|---|
| `tblkhex` | 4 of 469 | 3 mae, 1 p99 | 10x20 mae: 0.0082 to 0.0128 |
| `tblkdig` group 0 | 0 of 63 | none |  |
| `tblktet` | 2 of 588 | 2 mae | 6x12 mae: 0.0176 to 0.0270 |
| `tblkdomh` | 221 of 371 | 210 glyph_mae, 6 mae, 4 p99, 1 firm | 6x12 firm: 0.0005 to 0.0086 |
| `tblkdomv` | 51 of 371 | 44 glyph_mae, 6 mae, 1 p99 | 12x24 mae: 0.0087 to 0.0211 |
| `tblkcard` | 121 of 434 | 114 glyph_mae, 6 mae, 1 p99 | 8x16 mae: 0.0131 to 0.0337 |

Every shipped member passed with both seeds at the limits so applied; none needed the pixel-exact rule.

## Results by member

The shipped seed against the teacher, automatic sampling, at the seven
counted sizes. "Exact" counts the characters whose every pixel is on the
right side of one half of the gates' teacher mask (not a gate by itself).
"Firm-wrong" counts wrong-side pixels only where the drawing is at least
0.1 from one half. Mean overlap is measured after cutting coverage at one
half; it is not a gate for symbols. The last column is the other seed's
mean error.

**Where the exact counts and the overlap are low, and why.** These
drawings are straight lines along the pixel rows and columns. At some
sizes a line covers exactly half of each pixel it crosses: the frame and
bar of a domino or a card at 10×20, which are half a pixel thick there,
and the edges of the Tai Xuan Jing lines at 12×24. The drawing's coverage
in those pixels is exactly one half (about half of a domino's cell at
10×20), the cut at one half is a tie, and an error of a few thousandths
decides each pixel. Firm-wrong stays at or near zero and mean error is
small there. A program that shows coverage as grey shows the same
half-grey line as the drawing; **a program that cuts coverage at one half
shows, at those sizes, a frame with pixels missing or a line one pixel
thicker or thinner than the drawing's.** The sizes where the shipped
net's mean overlap is below 0.9, with the perfect net's beside it:

| Member | Cell | Mean overlap, shipped net | Perfect net | Characters exact |
|---|---|---:|---:|---|
| `tblkhex` | 10×20 | 0.826 | 0.826 | 0 of 64 |
| `tblkdig` | 6×12 | 0.833 | 0.833 | 5 of 6 |
| `tblkdig` | 12×24 | 0.691 | 1.000 | 0 of 6 |
| `tblktet` | 12×24 | 0.686 | 1.000 | 0 of 81 |
| `tblkdomh` | 10×20 | 0.446 | 1.000 | 0 of 50 |
| `tblkdomv` | 10×20 | 0.397 | 0.895 | 0 of 50 |
| `tblkcard` | 10×20 | 0.474 | 0.997 | 0 of 59 |

| Member | Cell | Mean error | 99th percentile | Firm-wrong | Worst character | Mean overlap | Exact | Other seed |
|---|---|---:|---:|---:|---:|---:|---|---:|
| `tblkhex` tiled, seed 0 | 6×12 | 0.00024 | 0.0014 | 0.00000 | 0.0004 | 1.0000 | 64 of 64 | 0.00025 |
|  | 8×16 | 0.01337 | 0.0418 | 0.00000 | 0.0165 | 1.0000 | 64 of 64 | 0.01362 |
|  | 10×20 | 0.01177 | 0.0731 | 0.00000 | 0.0134 | 0.8263 | 0 of 64 | 0.01179 |
|  | 12×24 | 0.00083 | 0.0123 | 0.00000 | 0.0013 | 0.9850 | 31 of 64 | 0.00097 |
|  | 16×32 | 0.00690 | 0.0420 | 0.00000 | 0.0081 | 1.0000 | 64 of 64 | 0.00689 |
|  | 24×48 | 0.00095 | 0.0237 | 0.00000 | 0.0015 | 1.0000 | 64 of 64 | 0.00114 |
|  | 48×96 | 0.00044 | 0.0074 | 0.00000 | 0.0006 | 1.0000 | 64 of 64 | 0.00042 |
| `tblkdig` group 0, seed 0 | 6×12 | 0.01233 | 0.0594 | 0.00000 | 0.0156 | 0.8333 | 5 of 6 | 0.01241 |
|  | 8×16 | 0.00308 | 0.0502 | 0.00000 | 0.0049 | 1.0000 | 6 of 6 | 0.00312 |
|  | 10×20 | 0.00508 | 0.0579 | 0.00000 | 0.0067 | 1.0000 | 6 of 6 | 0.00512 |
|  | 12×24 | 0.00194 | 0.0496 | 0.00000 | 0.0032 | 0.6910 | 0 of 6 | 0.00196 |
|  | 16×32 | 0.00150 | 0.0499 | 0.00000 | 0.0024 | 1.0000 | 6 of 6 | 0.00156 |
|  | 24×48 | 0.00104 | 0.0473 | 0.00000 | 0.0017 | 1.0000 | 6 of 6 | 0.00112 |
|  | 48×96 | 0.00055 | 0.0250 | 0.00000 | 0.0008 | 1.0000 | 6 of 6 | 0.00062 |
| `tblktet` tiled, seed 1 | 6×12 | 0.02375 | 0.0613 | 0.00000 | 0.0312 | 1.0000 | 81 of 81 | 0.02361 |
|  | 8×16 | 0.00432 | 0.0505 | 0.00000 | 0.0100 | 1.0000 | 81 of 81 | 0.00488 |
|  | 10×20 | 0.00919 | 0.0597 | 0.00000 | 0.0136 | 1.0000 | 81 of 81 | 0.00914 |
|  | 12×24 | 0.00298 | 0.0498 | 0.00000 | 0.0069 | 0.6864 | 0 of 81 | 0.00301 |
|  | 16×32 | 0.00216 | 0.0502 | 0.00000 | 0.0052 | 1.0000 | 81 of 81 | 0.00212 |
|  | 24×48 | 0.00237 | 0.0504 | 0.00000 | 0.0040 | 1.0000 | 81 of 81 | 0.00221 |
|  | 48×96 | 0.00075 | 0.0329 | 0.00000 | 0.0017 | 1.0000 | 81 of 81 | 0.00075 |
| `tblkdomh` tiled, seed 1 | 6×12 | 0.03554 | 0.1171 | 0.00778 | 0.0424 | 0.9881 | 37 of 50 | 0.03564 |
|  | 8×16 | 0.03556 | 0.1750 | 0.00000 | 0.0427 | 0.9674 | 0 of 50 | 0.03560 |
|  | 10×20 | 0.00616 | 0.0406 | 0.00000 | 0.0136 | 0.4459 | 0 of 50 | 0.00606 |
|  | 12×24 | 0.02381 | 0.0964 | 0.00000 | 0.0285 | 1.0000 | 50 of 50 | 0.02369 |
|  | 16×32 | 0.01855 | 0.0505 | 0.00000 | 0.0206 | 0.9836 | 2 of 50 | 0.01858 |
|  | 24×48 | 0.01751 | 0.2259 | 0.00000 | 0.0231 | 0.9860 | 4 of 50 | 0.01743 |
|  | 48×96 | 0.00598 | 0.0523 | 0.00001 | 0.0073 | 0.9940 | 0 of 50 | 0.00598 |
| `tblkdomv` tiled, seed 0 | 6×12 | 0.02873 | 0.0993 | 0.00000 | 0.0350 | 1.0000 | 50 of 50 | 0.02873 |
|  | 8×16 | 0.02616 | 0.1340 | 0.00000 | 0.0397 | 0.9445 | 0 of 50 | 0.02641 |
|  | 10×20 | 0.00372 | 0.0277 | 0.00000 | 0.0156 | 0.3971 | 0 of 50 | 0.00379 |
|  | 12×24 | 0.01911 | 0.0508 | 0.00000 | 0.0234 | 0.9993 | 49 of 50 | 0.01917 |
|  | 16×32 | 0.01470 | 0.0508 | 0.00000 | 0.0186 | 0.9861 | 5 of 50 | 0.01484 |
|  | 24×48 | 0.01280 | 0.0627 | 0.00000 | 0.0154 | 0.9861 | 1 of 50 | 0.01278 |
|  | 48×96 | 0.00530 | 0.0527 | 0.00000 | 0.0074 | 0.9953 | 1 of 50 | 0.00531 |
| `tblkcard` tiled, seed 1 | 6×12 | 0.02228 | 0.0899 | 0.00000 | 0.0330 | 0.9839 | 38 of 59 | 0.02215 |
|  | 8×16 | 0.03046 | 0.1361 | 0.00000 | 0.0375 | 0.9962 | 46 of 59 | 0.03044 |
|  | 10×20 | 0.00555 | 0.0524 | 0.00000 | 0.0098 | 0.4741 | 0 of 59 | 0.00543 |
|  | 12×24 | 0.02008 | 0.0526 | 0.00000 | 0.0232 | 0.9928 | 35 of 59 | 0.02008 |
|  | 16×32 | 0.01415 | 0.0512 | 0.00000 | 0.0167 | 0.9909 | 19 of 59 | 0.01418 |
|  | 24×48 | 0.01271 | 0.0654 | 0.00012 | 0.0156 | 0.9972 | 17 of 59 | 0.01273 |
|  | 48×96 | 0.00575 | 0.0538 | 0.00027 | 0.0065 | 0.9968 | 1 of 59 | 0.00576 |

## Left out

Nothing. Every listed character is in the bundle.

## Checks

`make test-term-blocks-v1` (part of `make test`): the drawings' own checks
(`train/term_blocks.py`); every group net against the float64 reference
and every tiled net against it tile by tile (`tests/check_tiled.py`, also
through the streaming build); the bundle rebuilt byte for byte; its table
exactly `neuronte-term-blocks-v1.list.txt`; every scalar from U+0000 to
U+10FFFF routed as the table says; pixels through the bundle equal to each
member alone at 19 cell sizes and with one sample a pixel; scalars inside
a tiled net's range that it was not trained on drawn blank;
`test_api --standalone`; and the validation record's hashes.

## Speed

kilix-bench: one pinned core, a fresh process for every job, one warmup
and ten measured rounds in shuffled order, medians, every model checked
against the float64 reference first. The corpus is this bundle's 310
characters. split-v9 sends each through its gate to another of its nets,
which never saw it; term-blocks-v1 looks it up in its table and runs its
member.

**Intel Core i7-6820HQ**

| µs per character | split-v9 | term-blocks-v1 | split-v9 / term-blocks-v1 |
|---|---:|---:|---:|
| Coverage, uncached, 8×16 | 490.3 | 240.3 | 2.04 |
| Coverage, uncached, 16×32 | 1942.2 | 867.7 | 2.24 |
| Coverage, uncached, 48×96 | 4278.1 | 1877.3 | 2.28 |
| Draw, cold, 8×16 | 502.1 | 242.9 | 2.07 |
| Draw, cold, 16×32 | 1940.8 | 875.9 | 2.22 |
| Draw, cold, 48×96 | 4322.1 | 1921.6 | 2.25 |
| Draw, warm, 8×16 | 4.0 | 1.4 | 2.91 |
| Draw, warm, 16×32 | 6.7 | 4.5 | 1.52 |
| Draw, warm, 48×96 | 27.6 | 31.3 | 0.88 |

A lookup in the table takes 9 ns against 1244 ns for split-v9's gate; opening the file takes 1.3 ms against 4.7 ms.

**Intel Core i7-10700F**

| µs per character | split-v9 | term-blocks-v1 | split-v9 / term-blocks-v1 |
|---|---:|---:|---:|
| Coverage, uncached, 8×16 | 378.1 | 180.1 | 2.10 |
| Coverage, uncached, 16×32 | 1490.6 | 669.9 | 2.23 |
| Coverage, uncached, 48×96 | 3254.0 | 1427.2 | 2.28 |
| Draw, cold, 8×16 | 379.2 | 183.3 | 2.07 |
| Draw, cold, 16×32 | 1465.4 | 654.9 | 2.24 |
| Draw, cold, 48×96 | 3275.1 | 1438.3 | 2.28 |
| Draw, warm, 8×16 | 2.9 | 1.0 | 2.91 |
| Draw, warm, 16×32 | 5.0 | 3.3 | 1.51 |
| Draw, warm, 48×96 | 20.0 | 22.9 | 0.87 |

A lookup in the table takes 5 ns against 912 ns for split-v9's gate; opening the file takes 0.9 ms against 3.7 ms.

Uncached, term-blocks-v1 draws these characters 2.2 times as fast as
split-v9's fallback does (geometric mean over the hosts and the three
cells; cold draw 2.2, warm draw 1.6). Both hosts drew the same pixels.

It is slower than split-v9 in: warm draw at 48×96 on the Intel Core i7-6820HQ (1.13 times split-v9's time); warm draw at 48×96 on the Intel Core i7-10700F (1.14 times split-v9's time).

A handle caches 1,024 drawn cells. A program that opens both bundles pays
both openings.

## Files

| File | What |
|---|---|
| `neuronte-term-blocks-v1.nrt` | The bundle, 849,696 bytes, sha256 `8c3a73904ff0301eb96ea2a9d2ef6a926cc69406fe057298be093f248c2505c6` |
| `neuronte-term-blocks-v1.list.txt` | The 310 characters it was trained on |
| `neuronte-term-blocks-v1-SET.json` | The 5 tiled nets as trained (the shipped seed): `tblkhex`, `tblktet`, `tblkdomh`, `tblkdomv`, `tblkcard` |
| `neuronte-term-blocks-v1-SET-gN.json` | The 1 group net as trained (the shipped seed) |
| `neuronte-term-blocks-v1.provenance.json` | Every member's hash and scalars, written by `make pack-term-blocks-v1` |
| `neuronte-term-blocks-v1.validation.json` | The gates file, both seeds' measurements and failures for every member, every tile width trained and the group nets not used |
| `font/term-blocks.txt`, `train/term_blocks.py` | The list and the rules the drawings are made by |
| `train/tile_expert.py`, `train/tile_member.py` | Training the tile nets of a tiled net, and assembling them |
