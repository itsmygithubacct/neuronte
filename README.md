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
| `neuronte-split-v1` | the font to use | 763, over four nets and a router | 128 and 192 | 275,368 | 1,103,104 bytes |
| `neuronte-full-v2` | the baseline `split` is measured against | the same 763 in one net | 320 | 234,881 | 939,728 bytes |
| `neuronte-ascii-v0` | the smallest file | the 95 printable ASCII characters | 128 | 44,801 | 179,408 bytes |

`neuronte-split` draws each character with one small net picked for it.
It draws ASCII and symbols about four times faster than `neuronte-full`
and box drawing, blocks, Braille and accented letters about twice as
fast, as well or better. `neuronte-full` draws every character with one
net, which has to be as wide as its hardest characters need, and is kept
to show what the split gains. See
[Split nets and the router](#split-nets-and-the-router).

Both are for terminals and TUIs. Their characters beyond ASCII were
picked from what Kilix terminals actually showed:

- **Box drawing**, U+2500..U+257F: all 128. Light, heavy, double, dashed,
  arcs, diagonals and half lines. Lines run to the cell edges, so
  neighbouring cells join.
- **Block elements**, U+2580..U+259F: all 32. The shades ░▒▓ are squares
  a quarter of a cell wide, on a lattice that tiles across cells, at 25,
  50 and 75 percent ink.
- **Braille**, U+2800..U+28FF: all 256, with dots on a lattice of half a
  cell width, so Braille graphics keep one pitch across cells.
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
| `font/letters.txt` | The Latin letters beyond ASCII that are not a letter plus a mark |
| `font/code-masks.txt` | The 43 parity masks that turn a scalar into the net's 64 character inputs |
| `train/strokes.py` | Reads the stroke files |
| `train/glyphs.py` | The character sets. Makes box drawing and blocks from their Unicode names, Braille from the dot bits, accented letters from a letter and a mark, and the target the net learns |
| `train/train.py` | Trains a net on one set. Needs torch, and wants a GPU |
| `train/gate.py` | Trains the router's gate for a bundle of nets. Needs torch; a CPU is enough |
| `train/pack.py` | Packs weights JSON into the binary file the C library loads, one net or a bundle. Documents both layouts |
| `weights/` | The trained weights as JSON, the packed files, the scores and `SHA256SUMS`. `neuronte-draw-v1`, `neuronte-symbol-v0`, `neuronte-accent-v0` and `neuronte-gate-v1` are the parts of `neuronte-split-v1`, with `neuronte-ascii-v0`. `neuronte-full-v2` is here so that `make test` and `make bench` run from a clone |
| `include/neuronte.h`, `src/` | The C library |
| `tools/neuronte-render.c` | Draws lines of text into a PPM file |
| `tools/neuronte-bench.c` | Times a net per cell, or a full net against a bundle per class of character |
| `tests/` | UTF-8 cases, API and loader checks, and a cross-check against numpy |
| `demo/neuronte-demo.c` | Shows the font in a Kilix terminal through `kitty-framebuffer`, with typing |
| `demo/neuronte-compare.c` | Two weight files side by side, on examples that show where they differ |
| `demo/common.c` | What the two demos share: text, typing, snapshots and the terminal |

## Build and test

```sh
make          # build/libneuronte.a, build/libneuronte.so and the tools
make test     # needs python3 with numpy
make bench
./build/neuronte-render weights/neuronte-split-v1.nrt 16 out.ppm 'Hello, café.' '╭──╮ ⣿⣶⣤⣀ ░▒▓ ✔'
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
  must also send each of about 1,800 scalars to the net a Python router
  picks, with the gate evaluated in numpy.

For `neuronte-full` and `neuronte-split` it also checks that box lines
reach the cell edges, that █ fills its cell and ▀ the top half, that
U+2800 and U+00A0 are blank, and that ⣿ carries about eight times the
ink of ⠁. For both it checks that é ä ô ñ ü š ž ć are their letter
below the x-height with a mark above it, and ç its c with a mark below.
Those checks fail on a net that was not trained on accents.

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
./build/neuronte-compare weights/neuronte-full-v2.nrt weights/neuronte-split-v1.nrt
./build/neuronte-compare LEFT.nrt RIGHT.nrt   # any two weight files
./build/neuronte-compare --snapshot out.ppm 1280 800
```

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
if (neuronte_open_file("neuronte-split-v1.nrt", &font) != NEURONTE_OK)
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

`neuronte-split-v1` is a bundle of nets that each know one part of the
set, with a router in front:

| Net | Characters | Hidden width | Parameters |
|---|---|---:|---:|
| `neuronte-ascii-v0` | the 95 printable ASCII characters | 128 | 44,801 |
| `neuronte-draw-v1` | 416: box drawing, blocks with the shades, Braille | 192 | 91,777 |
| `neuronte-symbol-v0` | the 49 symbols | 128 | 44,801 |
| `neuronte-accent-v0` | the 203 accented letters and marks | 192 | 91,777 |
| `neuronte-gate-v1` | the router's gate: 64 inputs, 32 hidden, 4 outputs | | 2,212 |

The router is in the file. It first looks the scalar up in a table of
ranges, made from the characters each net was trained on: 50 ranges, a
binary search. A scalar no net was trained on goes to the gate, a small
net over the same 64 code features the font nets take. It picks the net
trained on most of the characters in that scalar's Unicode block, or the
ASCII net for blocks none of them knows, so 中 is drawn by the ASCII net
and ↔ by the symbol net. The gate agrees with that rule on all 763
trained characters, on all 1,525 others in their blocks, and on 99.981%
of a sample of 199,206 from the rest. It learns from Unicode's
`Blocks.txt` (15.1), which `train/gate.py` reads at training time; the
block list is not in the repository.

Language-model routers were set aside: the smallest considered had 45
million parameters, hundreds of times the font, and routing is a
function of the code point that a table answers exactly.

```sh
python3 train/train.py draw.json --set draw --width 192     # also ascii, symbol, accent
python3 train/gate.py gate.json ascii.json draw.json symbol.json accent.json
python3 train/pack.py --bundle split.nrt ascii.json draw.json symbol.json accent.json --gate gate.json
```

`make bench` runs `neuronte-bench FULL BUNDLE`, which times each class of
characters drawn by `neuronte-full` alone and by the bundle, whose time
includes its router. One thread, no cache, on a machine with a load
average of 13 to 15 from other work, so times move by about 20 percent
from run to run and the ratios by less. Milliseconds per cell, one run:

| Class | Drawn in the bundle by | Cell | `full` | `split` | Faster |
|---|---|---|---:|---:|---:|
| ASCII, 95 | `ascii`, 128 | 8 × 16, 2 × 2 samples | 4.89 | 1.05 | 4.7× |
| | | 16 × 32, 2 × 2 | 19.0 | 4.5 | 4.2× |
| | | 48 × 96, 1 | 46.6 | 10.3 | 4.5× |
| drawing, 416 | `draw`, 192 | 8 × 16, 2 × 2 | 4.73 | 2.49 | 1.9× |
| | | 16 × 32, 2 × 2 | 18.3 | 9.5 | 1.9× |
| | | 48 × 96, 1 | 39.6 | 20.6 | 1.9× |
| symbols, 49 | `symbol`, 128 | 8 × 16, 2 × 2 | 4.31 | 1.09 | 4.0× |
| | | 16 × 32, 2 × 2 | 17.7 | 4.7 | 3.8× |
| | | 48 × 96, 1 | 41.6 | 10.6 | 3.9× |
| accented, 191 | `accent`, 192 | 8 × 16, 2 × 2 | 4.46 | 2.33 | 1.9× |
| | | 16 × 32, 2 × 2 | 18.7 | 8.7 | 2.1× |
| | | 48 × 96, 1 | 41.2 | 21.3 | 1.9× |

A net's hidden layers cost about the square of its width: 128 does a
sixth of the work of 320, and 192 a little over a third. The measured
gain is smaller than that because the first layer and the per-cell work
cost the same in both. The router takes 20 to 30 nanoseconds per call
through the table, and about a microsecond when the gate has to answer,
both far under a millisecond cell, and the draw calls route only on a
cache miss.

The trainer's scores, with 2 × 2 samples per pixel, for each class drawn
by the net the bundle sends it to and by `neuronte-full`:

| Class | Net in the bundle | 8 px | 16 px | 48 px | `full` 8 px | 16 px | 48 px |
|---|---|---:|---:|---:|---:|---:|---:|
| ASCII | `ascii`, 128 | 0.9477 | 0.9900 | 0.9921 | 0.9514 | 0.9881 | 0.9850 |
| box drawing | `draw`, 192 | 0.9633 | 0.9990 | 0.9970 | 0.9491 | 0.9992 | 0.9946 |
| blocks and shades | `draw`, 192 | 1.0000 | 1.0000 | 0.9999 | 1.0000 | 1.0000 | 0.9993 |
| Braille | `draw`, 192 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| symbols | `symbol`, 128 | 0.9828 | 0.9908 | 0.9952 | 0.9778 | 0.9856 | 0.9838 |
| accented | `accent`, 192 | 0.9795 | 0.9846 | 0.9881 | 0.9772 | 0.9810 | 0.9822 |

The bundle is level with `full` or ahead of it everywhere but ASCII at 8
pixels, where it is behind by 0.004, and box drawing at 16, by 0.0002.
The weakest accented characters are the spacing marks alone, ¨ and ˙,
whose dots are small enough that a pixel off costs much of their
overlap, and ĳ at 8 pixels.

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
| the bundle | 275,368 | .948 .990 .992 | .963 .999 .997 | .983 .991 .995 | .980 .985 .988 |

Blocks score 0.993 or better and Braille 1.000 at 192 and above. 320 is
the narrowest width that comes back to v1 on the classes v1 knew: it is
behind by at most 0.0034, on ASCII at 48 pixels, and ahead on box
drawing at 8. 384 is ahead of 320 on some classes and behind on others,
by under 0.021, at 1.4 times the cost. These differences are small
next to the spread between runs: the same 256-wide training, run on a
different GPU, scored 0.889 on box drawing at 8 pixels instead of
0.909. A single net for all 763 characters needs 320 wide, while the
bundle draws each of them with a net no wider than 192.

Other widths were tried. A draw net 128 wide is 3.3 times faster than
`full` but blurs the medium shade ▒, a checkerboard of 4-pixel squares
in a 16-pixel cell, to grey, and scores 0.9359, 0.9986 and 0.9939 on box
drawing; at 64 wide it falls to 0.754 at 8 pixels. An accent net 128
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

Box lines are not snapped to pixels. A line's centre falls on a pixel
edge at even cell sizes, so at 8 pixels a light line is two grey rows,
not one dark one. With one sample per pixel at 8 pixels, the light
dashed lines can fade to almost nothing; the default there is 2 × 2.

## Licence

MIT. See [LICENSE](LICENSE). The weights are part of the project and are
under the same licence.
