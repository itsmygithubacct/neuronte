# Neuronte

A neural net that is its own font. A character goes in, as ASCII or as
UTF-8. The net writes that character's pixels into a buffer the caller
owns. No font file, glyph table or bitmap atlas is consulted. The
weights are the font.

Games, the OS and `soft-raster` link the library and pass in the buffer.
The same buffer can be shown in a Kilix terminal or in a GUI window. The
library does not open the window or take the terminal.

Status: local only. No remote. There are three weight files for the one
library. Scalars a file was not trained on get a mark of their own, not
a letter.

| Weights | Use | Characters | Hidden width | Parameters | File |
|---|---|---|---:|---:|---:|
| `neuronte-split-v4` | the font to use | 1,061, over six nets and a router | 48, 128 and 192 | 329,356 | 1,319,616 bytes |
| `neuronte-full-v2` | the baseline `split` is measured against | 763 of them in one net, all but the sextants and octants | 320 | 234,881 | 939,728 bytes |
| `neuronte-ascii-v0` | the smallest file | the 95 printable ASCII characters | 128 | 44,801 | 179,408 bytes |

`neuronte-split` draws each character with one small net picked for it.
It draws ASCII, symbols, blocks and the mosaics four to seven times
faster than `neuronte-full`, Braille about sixteen times faster, and box
drawing and accented letters about twice as fast, as well or better. `neuronte-full` draws every character with one
net, which has to be as wide as its hardest characters need, and is kept
to show what the split gains. See
[Split nets and the router](#split-nets-and-the-router).

Both are for terminals and TUIs. Their characters beyond ASCII were
picked from what Kilix terminals actually showed, and the mosaics from
what terminal picture viewers emit:

- **Box drawing**, U+2500..U+257F: all 128. Light, heavy, double, dashed,
  arcs, diagonals and half lines. Lines run to the cell edges, so
  neighbouring cells join.
- **Block elements**, U+2580..U+259F: all 32. The shades ░▒▓ are squares
  a quarter of a cell wide, on a lattice that tiles across cells, at 25,
  50 and 75 percent ink.
- **Braille**, U+2800..U+28FF: all 256, with dots on a lattice of half a
  cell width, so Braille graphics keep one pitch across cells.
- **Sextants and octants**, in `neuronte-split` only: the 60 sextants
  U+1FB00..U+1FB3B, a 2 × 3 lattice; the 230 octants U+1CD00..U+1CDE5, a
  2 × 4 lattice, new in Unicode 16; and the 8 characters that Unicode
  encodes the other octant patterns as, such as U+1FB82 and U+1CEA0. With
  space, the quadrants and the other block elements, every one of the 256
  octant patterns has a character. Each sub-cell is exactly its share of
  the cell, so a picture made of them has no seams.
- **Symbols**: `… · ⋅ • — – ‘ ’ “ ” › ❯ × ° ½ © ≡ ≈ ※ ⁙ ⸬ ◆ ◈ ● ◉ ◯ ◐ ◑
  ▲ ▼ ▾ ▸ ⏵ ⎿ ← → ↑ ↓ ↗ ⇣ ✔ ☐ ☒ ✻ ✢ ✶ ✽ ✳` and U+00A0, drawn blank.
- **Accented letters**, 203: the letters of Latin-1, U+00C0..U+00FF, all
  of Latin Extended-A, U+0100..U+017F, ÷, and the spacing marks `¨ ¯ ´ ¸
  ˆ ˇ ˘ ˙ ˚ ˛ ˜ ˝`.

A letter with a mark is made from the ASCII letter and a mark, by the
Unicode decomposition: é is e and U+0301. The marks are drawn once, in
`font/marks.txt`. A capital under a mark is shortened to make room, as
is the ascender of ĥ and ĺ; i and j lose their dot; ď ľ ť Ľ take their
caron as a comma beside the stem, and ķ ļ ņ ŗ Ģ Ķ Ļ Ņ Ŗ their cedilla as
a comma below, as fonts commonly draw them. The 29 letters that are not
a letter and a mark, such as ß æ œ ð þ ø ł đ ħ ŋ ĳ, are drawn in
`font/letters.txt`.

## Layout

| Path | What it is |
|---|---|
| `font/strokes.txt` | The ASCII face: each character as pen strokes on a 10 × 20 grid. Written for this project |
| `font/symbols.txt` | The symbols of the full set, in the same form |
| `font/marks.txt` | The diacritic marks, keyed by their combining code points |
| `font/letters.txt` | The Latin letters beyond ASCII that are not a letter plus a mark, and the Greek and Russian Cyrillic letters. The Greek and Cyrillic are not yet in any weights |
| `font/icons.txt` | The icons, as colour layers back to front, each naming a palette entry. Not yet in any weights |
| `font/palette.txt` | The palette for colour glyphs: entry 0 is the cell's foreground, 1 is clear, the rest have a dark-theme and a light-theme colour |
| `font/code-masks.txt` | The 43 parity masks that turn a scalar into the net's 64 character inputs |
| `font/octants.txt` | Which cells each octant U+1CD00..U+1CDE5 fills. Made by `train/mosaics.py` from Unicode 16's `UnicodeData.txt`, whose version and sha256 it records |
| `train/strokes.py` | Reads the stroke files |
| `train/glyphs.py` | The character sets. Makes box drawing and blocks from their Unicode names, Braille from the dot bits, sextants and octants from the cells they fill, accented letters from a letter and a mark, and the target the net learns. `python3 train/glyphs.py` checks the sets |
| `train/mosaics.py` | Makes `font/octants.txt`, and checks the sextants and the octant patterns encoded elsewhere against the same Unicode data |
| `train/train.py` | Trains a net on one set. Needs torch, and wants a GPU |
| `train/colour.py` | Trains a colour net. Needs torch, and wants a GPU. No icon net has been trained |
| `train/snap.py` | The straight edges of a colour glyph, measured from the drawings when the weights are packed, and the warp that snaps them |
| `train/gate.py` | Trains the router's gate for a bundle of nets. Needs torch; a CPU is enough |
| `train/pack.py` | Packs weights JSON into the binary file the C library loads: a distance net, a colour net, a bundle, an advance table, or a drawing file. Documents the layouts. No face with advances is drawn yet |
| `weights/` | The trained weights as JSON, the packed files, the scores and `SHA256SUMS`. `neuronte-draw-v2`, `neuronte-symbol-v0`, `neuronte-accent-v1`, `neuronte-pixel-v1`, `neuronte-braille-v0` and `neuronte-gate-v3` are the parts of `neuronte-split-v4`, with `neuronte-ascii-v0`. `neuronte-full-v2` is here so that `make test` and `make bench` run from a clone |
| `include/neuronte.h`, `src/` | The C library |
| `tools/neuronte-render.c` | Draws lines of text into a PPM file |
| `tools/neuronte-bench.c` | Times a net per cell, or a full net against a bundle per class of character |
| `tests/` | UTF-8 cases, API and loader checks, a cross-check against numpy, and a check of the packed advance table against the library |
| `demo/neuronte-demo.c` | Shows the font in a Kilix terminal through `kitty-framebuffer`, with typing |
| `demo/neuronte-compare.c` | Two weight files side by side, on examples that show where they differ |
| `demo/neuronte-showcase.c` | Every class of character the bundle draws, and pictures through octant cells at three levels |
| `demo/common.c` | What the two demos share: text, typing, snapshots and the terminal |

## Build and test

```sh
make          # build/libneuronte.a, build/libneuronte.so and the tools
make test     # needs python3 with numpy
make bench
./build/neuronte-render weights/neuronte-split-v4.nrt 16 out.ppm 'Hello, café.' '╭──╮ ⣿⣶⣤⣀ ░▒▓ ✔'
```

The library is C11 with libm and nothing else. On x86-64 it builds its
inner loops twice, plain and AVX2, and picks one by CPU when it loads.
`CFLAGS=-DNEURONTE_NO_CLONES` builds the plain path only.

`make test` checks, for every weight file, that:

- the weights match `weights/SHA256SUMS`;
- UTF-8 decoding follows Unicode's maximal-subpart rule, so a bad byte
  becomes one U+FFFD and never swallows the next character;
- the loader refuses a short, long or damaged file, or one of a shape it
  does not know, and the same for bundles: overlapping or unsorted
  ranges, a range to a net that is not there, a damaged gate, and a net
  in the bundle that is itself bad;
- drawing clips at every edge and blends correctly, and the draw cache
  gives the same cell after it has turned over;
- the C library agrees with an independent float64 numpy evaluation of
  the JSON weights to 1e-3 in coverage, and the packed file is exactly
  what `train/pack.py` makes from the JSON. For the bundle, the C router
  must also send each of about 2,100 scalars, both Symbols for Legacy
  Computing blocks among them, to the net a Python router picks, with the
  gate evaluated in numpy;
- a small synthetic version 3 file round-trips its layer count, palette,
  palette head and one straight edge, the head names the right entry on
  every labelled glyph, and the dark and light composites agree with the
  numpy reference at 12 and 16 pixels, snapped and unsnapped. A
  grid-aligned icon is unchanged at 16 pixels with snapping on. The
  version 1 box-drawing checks also show that a horizontal line still
  meets a vertical one when snapping is asked for.

For `neuronte-full` and `neuronte-split` it also checks that box lines
reach the cell edges, that █ fills its cell and ▀ the top half, that
U+2800 and U+00A0 are blank, and that ⣿ carries about eight times the
ink of ⠁. For both it checks that é ä ô ñ ü š ž ć are their letter
below the x-height with a mark above it, and ç its c with a mark below.
Those checks fail on a net that was not trained on accents.

For `neuronte-split` it checks the mosaics. At 16 × 32 with 2 × 2 samples,
each sub-cell of every sextant and of all 255 octant patterns with ink
must have a mean coverage above 0.9 where its bit is set and below 0.1
where it is not, leaving out the pixels within one pixel of an inner
boundary. A full column must reach the top and bottom rows, so stacked
cells join. At a 2 × 4 cell, where each octant sub-cell is one pixel,
all 2,040 pixels of those patterns must fall on the right side of 0.5,
none further than 0.25 from 0 or 1. That is the size at which octant
cells can show a picture pixel for pixel. The check fails on
`neuronte-split-v1`, whose ▙ ▛ ▜ ▟ put 0.21 of ink in their empty
quadrant, and on `neuronte-full-v2`, which knows no mosaics.

It also runs `python3 train/glyphs.py`, which checks the targets
themselves: every box junction is distinct, every quadrant, sextant
and octant is ink over exactly its cells, with no seam where two meet,
and in every colour glyph a lower layer runs under the layer above it
wherever the two meet, so their anti-aliased edges leave no line.

## Demo

```sh
make demo
./build/neuronte-demo                 # in a Kilix terminal
./build/neuronte-demo weights/neuronte-full-v2.nrt
./build/neuronte-demo --snapshot out.ppm 1280 800
```

Every glyph on the demo's screen, its labels included, is drawn by the
net and shown through `kitty-framebuffer`, which `make demo` compiles from
`KITTYFB_DIR` (default `$HOME/gpu_terminal/kilix-modules/kitty-framebuffer`).
It loads `neuronte-split` if it can, else `neuronte-full`, else
`neuronte-ascii`. With weights that know box drawing it adds a panel of
box drawing, blocks, Braille and symbols, and two spinners that turn
while it waits for keys. Type to draw text, Tab changes its size, Esc
quits. It needs zlib.

The first screen takes about 1.8 seconds with `neuronte-split` and about
5.9 with `neuronte-full`, since every cell is new. The demo shows each part
as it is done. After that a frame takes about a millisecond.

```sh
./build/neuronte-compare                      # neuronte-ascii left, neuronte-full right
./build/neuronte-compare weights/neuronte-full-v2.nrt weights/neuronte-split-v4.nrt
./build/neuronte-compare LEFT.nrt RIGHT.nrt   # any two weight files
./build/neuronte-compare --snapshot out.ppm 1280 800
```

```sh
./build/neuronte-showcase                      # in a Kilix terminal; Tab changes page
./build/neuronte-showcase --snapshot out.ppm 1280 800   # also writes out-pictures.ppm
```

`neuronte-showcase` shows everything `neuronte-split` draws, on two
pages. The first has every class of character, each with the net that
draws it, the blocks up close, and an area chart in octants that joins
across cells. The second is a moving scene made by code, drawn four
ways side by side, each with its time and its PSNR against the scene:

| Panel | A cell holds | Where it can be shown | One frame, 536 × 304 |
|---|---|---|---|
| the scene | | | |
| level 1 | one octant and two colours per 8 × 16 cell, the best of all 256 patterns in least squares | any terminal | 44 ms, 17.5 dB |
| level 2 | eight colours per 8 × 16 cell, three octants used as bit planes | a screen Neuronte draws | 8 ms, 17.8 dB |
| level 2 | eight colours per 2 × 4 cell, one pixel per sub-cell | a screen Neuronte draws | 9 ms, 59.5 dB |

Every cell's shape is the net's coverage of an octant character at that
size. At 2 × 4 the net's coverage is within about 0.01 of 0 or 1, so the
picture is the scene to within a level or two of 255; rounding the masks
would make it exact. At 8 × 16, level 1 keeps sharper edges and level 2
truer colour, at about the same PSNR: the scene's 1- to 3-pixel bars and
checkerboard are finer than either can show.

`neuronte-compare` splits the screen in two, and each half is drawn only
by its own net, labels included. The rows are ASCII at three sizes, a
TUI panel and file tree in box drawing with a spinner, a progress bar,
sparkline and Braille wave, punctuation beyond ASCII next to the ASCII
it stands in for, accented letters, and characters neither set was
trained on. Each row
says, in that net's own drawing, whether the net was trained on it.
Typing goes to both halves. Each half shows its net's size and how long
it took to draw one cell, the whole half, and the last keypress.

## Use

```c
#include "neuronte.h"

neuronte *font;
if (neuronte_open_file("neuronte-split-v4.nrt", &font) != NEURONTE_OK)
    return 1;
/* pixels: row-major 0xAARRGGBB, stride in pixels. */
neuronte_draw_utf8(font, pixels, stride, width, height,
                   x, y, 16, 32, "Hello", 5, 0xFFFFFFFF);
neuronte_close(font);
```

Every weight file works with the same calls. The file states its
hidden width, or for a bundle its nets and router, and
`neuronte_parameters()` reports the size of what was loaded.
`neuronte_nets()` and `neuronte_route()` say how many nets a file holds
and which one draws a given scalar. `neuronte_coverage()` returns a cell's coverage without
drawing it. `neuronte_open()` takes the weights from memory instead of a
file. The draw calls keep up to 1,024 cells, dropping the least recently
used, so a handle should not be shared between threads without a lock.

A colour weight file is version 3. It holds K layers that share one
hidden vector, a palette head that runs once per glyph, and the straight
edges of the drawings. `neuronte_layers()` is that K (a distance file
returns 1). `neuronte_set_theme()` selects the dark palette, which the
handle starts on, or the light one. `neuronte_palette()` copies one
theme's 32 colours, 96 bytes of R, G, B. `neuronte_set_snap()` snaps a
colour glyph's straight edges when the cell is narrower than the given
width. The file stores 14. Passing -1 restores that number, and 0 turns
snapping off. `neuronte_coverage_layers()` returns each layer's coverage
and its palette index. The two draw calls composite the layers back to
front: entry 1 clears, entry 0 uses the colour of the call, and any
other entry uses the theme's palette. The call's alpha then scales the
whole glyph. A pixel the glyph left clear is left as it was. Snapping
applies to a colour glyph that has an edge record. Letters and box
drawing have none, so a horizontal line still meets a vertical one.

No icon net has been trained. `make test` builds a small synthetic
version 3 file, with a hand-written field and a palette head that
remembers the labelled glyphs, and checks that. `font/icons.txt` is still
waiting for a trained net.

## The net

Input: 26 features of a point in the cell (x, y, and sines and cosines
at 1 to 32 cycles per cell width) and 64 features of the scalar (its 21
bits and 43 parity bits). Any two scalars differ in at least 13 of those
64. Three hidden layers, ReLU: 128 wide for `ascii`, 320 for `full`, 128
or 192 for the nets in `split`.
Output: the distance to the edge of the ink, clamped. Coverage is a ramp
one sample wide across that edge, so the same weights draw a sharp
letter in a large cell and a correctly softened one in a small cell.
Cells narrower than 24 pixels take 2 × 2 samples per pixel.

The trainer learns the signed distance to the ink edge, which
`train/glyphs.py` works out on a grid of nodes 1/256 cell width apart
and the trainer reads between nodes. A glyph there is a short list of
shapes applied in order: pen strokes, filled polygons, and cuts, which
open the channel of a double line.

```sh
python3 train/train.py out.json --set full --width 320   # 44 minutes on an RTX 3090 shared by five runs
python3 train/pack.py out.json out.nrt
```

`neuronte-ascii-v0` came from the earlier trainer at commit `0cd2a25`,
which measured the exact distance to each stroke. Retrained with the
grid at width 128 it scores 0.953, 0.990 and 0.993 at 8, 16 and 48
pixels, against 0.948, 0.990 and 0.992 for the shipped file.

## Split nets and the router

`neuronte-split-v4` is a bundle of nets that each know one part of the
set, with a router in front:

| Net | Characters | Hidden width | Parameters |
|---|---|---:|---:|
| `neuronte-ascii-v0` | the 95 printable ASCII characters | 128 | 44,801 |
| `neuronte-draw-v2` | 131: box drawing and the shades | 192 | 91,777 |
| `neuronte-symbol-v0` | the 49 symbols | 128 | 44,801 |
| `neuronte-accent-v1` | the 203 accented letters and marks | 192 | 91,777 |
| `neuronte-pixel-v1` | 327: the other 29 block elements, the 60 sextants, the 230 octants and the 8 octant substitutes | 128 | 44,801 |
| `neuronte-braille-v0` | the 256 Braille patterns | 48 | 9,121 |
| `neuronte-gate-v3` | the router's gate: 64 inputs, 32 hidden, 6 outputs | | 2,278 |

The router is in the file. It first looks the scalar up in a table of
ranges, made from the characters each net was trained on: 62 ranges, a
binary search. A scalar no net was trained on goes to the gate, a small
net over the same 64 code features the font nets take. It picks the net
trained on most of the characters in that scalar's Unicode block, or the
ASCII net for blocks none of them knows, so 中 is drawn by the ASCII net
and ↔ by the symbol net. The gate agrees with that rule on all 1,061
trained characters, on all 2,187 others in their blocks, and on 99.97%
of a sample of 199,044 from the rest. It learns from Unicode's
`Blocks.txt`, which `train/gate.py` reads at training time; the block
list is not in the repository. `neuronte-gate-v3` used version 16.0,
the first with the octants' block.

Braille has a net of its own because it needs so little. Its dots are
the low eight bits of the scalar, which the net reads directly, so a net
48 wide draws all 256 patterns exactly: 1.0000 at every size scored, with
both seeds, where one of two seeds at 32 wide did not. In
`neuronte-split-v2` Braille shared the 128-wide pixel net, which costs
about three times as much per cell. The same was tried per character for
the mosaics and did not pay: a 64-wide net matches the 128-wide one on
only about one mosaic in ten.

Language-model routers were set aside: the smallest considered had 45
million parameters, hundreds of times the font, and routing is a
function of the code point that a table answers exactly.

```sh
python3 train/train.py pixel.json --set pixel --width 128   # also ascii, symbol, accent; draw is --set boxshade --width 192, braille --width 48
python3 train/gate.py gate.json ascii.json draw.json symbol.json accent.json pixel.json braille.json --blocks Blocks.txt
python3 train/pack.py --bundle split.nrt ascii.json draw.json symbol.json accent.json pixel.json braille.json --gate gate.json
```

`make bench` runs `neuronte-bench FULL BUNDLE`, which times each class of
characters drawn by `neuronte-full` alone and by the bundle, whose time
includes its router. One thread, no cache, on a machine with a load
average of about 8 from other work, so times move by about 20 percent
from run to run and the ratios by less. Milliseconds per cell, one run:

| Class | Drawn in the bundle by | Cell | `full` | `split` | Faster |
|---|---|---|---:|---:|---:|
| ASCII, 95 | `ascii`, 128 | 8 × 16, 2 × 2 samples | 3.46 | 0.85 | 4.1× |
| | | 16 × 32, 2 × 2 | 13.4 | 2.9 | 4.6× |
| | | 48 × 96, 1 | 30.3 | 6.6 | 4.6× |
| box drawing and shades, 131 | `draw`, 192 | 8 × 16, 2 × 2 | 3.15 | 1.53 | 2.1× |
| | | 16 × 32, 2 × 2 | 12.5 | 5.8 | 2.1× |
| | | 48 × 96, 1 | 28.1 | 13.9 | 2.0× |
| symbols, 49 | `symbol`, 128 | 8 × 16, 2 × 2 | 3.21 | 0.84 | 3.8× |
| | | 16 × 32, 2 × 2 | 12.9 | 3.2 | 4.1× |
| | | 48 × 96, 1 | 29.3 | 7.3 | 4.0× |
| accented, 191 | `accent`, 192 | 8 × 16, 2 × 2 | 3.21 | 1.56 | 2.1× |
| | | 16 × 32, 2 × 2 | 12.8 | 6.1 | 2.1× |
| | | 48 × 96, 1 | 29.5 | 13.3 | 2.2× |
| blocks and mosaics, 327 | `pixel`, 128 | 8 × 16, 2 × 2 | 4.31 | 0.65 | 6.7× |
| | | 16 × 32, 2 × 2 | 17.6 | 2.5 | 7.0× |
| | | 48 × 96, 1 | 38.7 | 6.0 | 6.5× |
| Braille, 256 | `braille`, 48 | 8 × 16, 2 × 2 | 3.64 | 0.23 | 15.9× |
| | | 16 × 32, 2 × 2 | 14.3 | 0.72 | 19.9× |
| | | 48 × 96, 1 | 31.2 | 1.9 | 16.4× |

ASCII and the mosaics are drawn by nets of the same width, and the
difference between them is mostly noise; an earlier run under heavier
load gave 3.8 to 4.9 times for ASCII and 4.8 to 7.6 for the mosaics.
`neuronte-full` was not trained on the mosaics; it is timed on them, not
scored.

A net's hidden layers cost about the square of its width: 128 does a
sixth of the work of 320, and 192 a little over a third. The measured
gain is smaller than that because the first layer and the per-cell work
cost the same in both. The router takes 15 to 36 nanoseconds per call
through the table, and about a microsecond when the gate has to answer,
both far under a millisecond cell, and the draw calls route only on a
cache miss.

The trainer's scores, with 2 × 2 samples per pixel, for each class drawn
by the net the bundle sends it to and by `neuronte-full`, both against
the targets `train/glyphs.py` makes now:

| Class | Net in the bundle | 8 px | 16 px | 48 px | `full` 8 px | 16 px | 48 px |
|---|---|---:|---:|---:|---:|---:|---:|
| ASCII | `ascii`, 128 | 0.9477 | 0.9900 | 0.9921 | 0.9514 | 0.9881 | 0.9850 |
| box drawing | `draw`, 192 | 0.9748 | 0.9990 | 0.9988 | 0.9491 | 0.9992 | 0.9946 |
| shades | `draw`, 192 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9933 |
| blocks | `pixel`, 128 | 1.0000 | 1.0000 | 0.9999 | 0.9945 | 0.9945 | 0.9944 |
| Braille | `braille`, 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| sextants and octants | `pixel`, 128 | 1.0000 | 0.9998 | 0.9992 | | | |
| symbols | `symbol`, 128 | 0.9828 | 0.9908 | 0.9952 | 0.9778 | 0.9856 | 0.9838 |
| accented | `accent`, 192 | 0.9786 | 0.9849 | 0.9886 | 0.9748 | 0.9786 | 0.9798 |

The bundle is level with `full` or ahead of it everywhere but ASCII at 8
pixels, where it is behind by 0.004, and box drawing at 16, by 0.0002.
`full`'s blocks fall short of 1 because of the three-quadrant blocks
(see [Quality](#quality)); its own score file, against the targets it
was trained on, has them at 1.0000, 1.0000 and 0.9993 with the shades.
The weakest accented characters are the spacing mark ¨ alone, whose
dots are small enough that a pixel off costs much of their overlap, Œ,
and ĳ at 8 pixels. `neuronte-accent-v1` is the training of v0, same
seed, run again after the capital Ĳ was redrawn without serifs: at 12
and 16 pixels the I's serifs ran into the J's bar and the pair read as
a box. It scores within 0.001 of v0 at each size. `neuronte-full-v2`
was trained on the earlier Ĳ, which costs it 0.0024 at each size here.

### The pixel net and the new draw net

How the nets are grouped was decided by measurement. Three ways to
split the blocks, Braille, mosaics, box drawing and shades were trained
at several widths, each twice with different seeds, side by side on one
GPU. A grouping was kept if the mean of its two seeds was within the
spread between seeds (at least 0.002) of the bundle before it on every
class at 8, 16 and 48 pixels. Of those kept, the one with the smallest
widths was taken. Means of two seeds:

| Set | Width | 8 px | 16 px | 48 px |
|---|---:|---|---|---|
| blocks and mosaics | 64 | blocks .953, mosaics .999 | .953, .996 | .951, .992 |
| | 128 | 1, 1 | 1, .9999 | .9999, .9992 |
| | 192 | 1, 1 | 1, 1 | 1, .9999 |
| the same and Braille | 64 | Braille .990 | .990 | .990 |
| | 128 | Braille 1 | 1 | 1 |
| box drawing and shades | 128 | box .950 | .9992 | .9972 |
| | 192 | box .973 | .9989 | .9985 |

At 64 the eighth blocks ▏ ▕ fail and Braille loses its exactness. Box
drawing at 128 falls behind the old draw net at 8 pixels (0.950 against
0.963). So `neuronte-split-v2` had the blocks, mosaics and Braille in one
net 128 wide, and box drawing with the shades in one 192 wide. The seed
kept for each is the better of its two.

A later measurement scored the 64-wide net character by character
against the 128-wide one. Within 0.002 at all three sizes it matched on
240 of the 256 Braille patterns, but on only 28 of the 298 mosaics and 12
of the 29 blocks. So Braille was the one class a narrower net could
take. Trained alone, twice each: at 48 and at 64 wide it is exact with
both seeds; at 32 one seed is exact and the other scores 0.976.
`neuronte-split-v3` therefore gives Braille a 48-wide net,
`neuronte-braille-v0`, and the blocks and mosaics keep a 128-wide net
trained without it, `neuronte-pixel-v1`.

Every candidate at 128 or 192 is exact at a 2 × 4 cell: all 2,040 pixels
of the octant patterns are on the right side of 0.5, none further than
0.08 from 0 or 1. At 5 pixels wide every run scores about 0.81 on the
mosaics, at any width: a sub-cell edge falls on half a pixel there, so
even the target is half-covered. A sub-cell edge falls on a pixel edge
when the cell width is even and the height a multiple of 4 for octants
or of 3 for sextants, as at 8 × 16 for octants or 9 × 18 for sextants.
Elsewhere the pixel row or column on that edge is drawn half-covered,
which is what exact geometry gives; the edges are not snapped to pixels.

### The width of neuronte-full

`neuronte-full-v1` was 256 wide and knew 560 characters, without the
accented letters. Adding the 203 accented letters at the same width
cost it quality on the classes it already knew, so the whole set was
trained at five widths, side by side on one GPU, same steps and seed.
With 2 × 2 samples at 8, 16 and 48 pixels:

| Net | Parameters | ASCII | box drawing | symbols | accented |
|---|---:|---|---|---|---|
| `full-v1`, 256, 560 characters | 155,137 | .951 .990 .988 | .934 .9995 .996 | .979 .987 .987 | |
| 128 | 44,801 | .921 .939 .928 | .815 .989 .970 | .921 .934 .928 | .912 .904 .899 |
| 192 | 91,777 | .948 .977 .969 | .866 .998 .989 | .963 .968 .961 | .969 .967 .963 |
| 256 | 155,137 | .951 .985 .980 | .909 .999 .993 | .977 .980 .978 | .976 .978 .977 |
| 320, `full-v2` | 234,881 | .951 .988 .985 | .949 .999 .995 | .978 .986 .984 | .977 .981 .982 |
| 384 | 331,009 | .948 .988 .989 | .928 .998 .996 | .981 .984 .987 | .977 .983 .985 |
| the bundle, `split-v4` | 329,356 | .948 .990 .992 | .975 .999 .999 | .983 .991 .995 | .979 .985 .989 |

Blocks score 0.993 or better and Braille 1.000 at 192 and above. 320 is
the narrowest width that comes back to v1 on the classes v1 knew: it is
behind by at most 0.0034, on ASCII at 48 pixels, and ahead on box
drawing at 8. 384 is ahead of 320 on some classes and behind on others,
by under 0.021, at 1.4 times the cost. These differences are small
next to the spread between runs: the same 256-wide training, run on a
different GPU, scored 0.889 on box drawing at 8 pixels instead of
0.909. A single net for all 763 characters needs 320 wide, while the
bundle draws each of them with a net no wider than 192.

Other widths were tried. The first draw net, with box drawing, all the
blocks and Braille, was 3.3 times faster than `full` at 128 wide but
blurred the medium shade ▒, a checkerboard of 4-pixel squares in a
16-pixel cell, to grey, and scored 0.9359, 0.9986 and 0.9939 on box
drawing; at 64 wide it fell to 0.754 at 8 pixels. Box drawing and the
shades alone at 128 do better, 0.950 and 0.9992, but not well enough
(see [The pixel net and the new draw net](#the-pixel-net-and-the-new-draw-net)). An accent net 128
wide scores 0.9749, 0.9765 and 0.9770. The symbol net loses little at 64
wide (0.9782, 0.9851, 0.9843 with 14,209 parameters), so the bundle could
be smaller still there.

## Speed

One thread, i7-9850H, AVX2 path, no cache, with a load average of 14 to
15 from other work. Milliseconds per cell, one run of `neuronte-bench`
on each file:

| Cell | Samples per pixel | `ascii`, 128 | `full`, 320 |
|---|---|---:|---:|
| 8 × 16 | 2 × 2 | 1.28 | 5.00 |
| 16 × 32 | 2 × 2 | 4.71 | 19.8 |
| 32 × 64 | 1 | 4.94 | 20.2 |
| 48 × 96 | 1 | 11.1 | 45.9 |

The nets of `neuronte-split` that are 128 wide cost what `ascii` does,
and those 192 wide about twice that; see the table above. Earlier
measurements found the plain path about 2.2 times slower than AVX2 for
a net 128 wide and 1.7 times for one 256 wide. A terminal should draw
each character once per cell size and reuse it. The draw calls' cache
does that.

## Quality

`weights/*.scores.json` is the trainer's own scoring: the net's ink
against the target's ink, mean over the characters, 1.0 being exact,
with 2 × 2 samples per pixel. With 2 × 2 samples every character is
closer to its own target than to any other at every size scored; with
one sample at 8 pixels, 2 of the 763 in `full` are not. Characters whose
targets are all but the same, such as space, U+00A0 and U+2800, count
as one.

| Weights | 8 px | 16 px | 48 px |
|---|---:|---:|---:|
| `ascii` | 0.948 | 0.990 | 0.992 |
| `full`, all 763 | 0.978 | 0.992 | 0.991 |

For each class in `split` and `full`, see
[Split nets and the router](#split-nets-and-the-router).

The weakest in `ascii` is `"` at 8 pixels, whose two marks are about one
pixel wide there. In `full` the weakest at 8 pixels are `"`, `:` and
`ĳ`, at 16 the ogonek `˛`, `✳` and `Ĕ`, and at 48 the dashes `┈ ┄` and
the asterisk `✽`.

The history of `neuronte-full`: v0 knew 557 characters at 256 wide; v1
added the shades, within 0.006 of v0 on each class with 2 × 2 samples;
v2 added the 203 accented letters and is 320 wide, for the reasons in
[The width of neuronte-full](#the-width-of-neuronte-full).

The three-quadrant blocks ▙ ▛ ▜ ▟ in `neuronte-full-v2`, and in the
retired `neuronte-draw-v1`, were trained on targets with a square of ink
a quarter of a cell wide in the corner of the empty quadrant, so those
nets draw that corner as a step. The scores could not show it, since
they compare a net with its own targets. `train/glyphs.py` now makes
the quadrants and the mosaics by one rule and checks that each fills
exactly its cells. `neuronte-pixel-v1`, trained from it, draws the
corner square, and `test_api --pixel` checks that it does. Scored
against today's targets, the blocks of `neuronte-draw-v1` come to 0.9945
at every size, against 1.0000 for `neuronte-pixel-v1`.

Box lines are not snapped to pixels. A line's centre falls on a pixel
edge at even cell sizes, so at 8 pixels a light line is two grey rows,
not one dark one. With one sample per pixel at 8 pixels, the light
dashed lines can fade to almost nothing; the default there is 2 × 2.

## Licence

MIT. See [LICENSE](LICENSE). The weights are part of the project and are
under the same licence.
