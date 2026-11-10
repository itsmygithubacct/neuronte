# Neuronte

A neural net that is its own font. A character goes in, as ASCII or as
UTF-8. The net writes that character's pixels into a buffer the caller
owns. No font file, glyph table or bitmap atlas is consulted. The
weights are the font.

Games, the OS and `soft-raster` link the library and pass in the buffer.
The same buffer can be shown in a Kilix terminal or in a GUI window. The
library does not open the window or take the terminal.

Status: local only. No remote. There are two weight files for the one
library. Scalars a file was not trained on get a mark of their own, not
a letter.

| Weights | Characters | Hidden width | Parameters | File |
|---|---|---:|---:|---:|
| `neuronte-ascii-v0` | the 95 printable ASCII characters | 128 | 44,801 | 179,408 bytes |
| `neuronte-full-v0` | 557: ASCII, box drawing, blocks, Braille and 49 symbols | 256 | 155,137 | 620,752 bytes |

`neuronte-full` is for terminals and TUIs. Its characters beyond ASCII
were picked from what Kilix terminals actually showed:

- **Box drawing**, U+2500..U+257F: all 128. Light, heavy, double, dashed,
  arcs, diagonals and half lines. Lines run to the cell edges, so
  neighbouring cells join.
- **Block elements**, U+2580..U+259F, apart from the shades ░▒▓, which
  are dither patterns and do not scale.
- **Braille**, U+2800..U+28FF: all 256, with dots on a lattice of half a
  cell width, so Braille graphics keep one pitch across cells.
- **Symbols**: `… · ⋅ • — – ‘ ’ “ ” › ❯ × ° ½ © ≡ ≈ ※ ⁙ ⸬ ◆ ◈ ● ◉ ◯ ◐ ◑
  ▲ ▼ ▾ ▸ ⏵ ⎿ ← → ↑ ↓ ↗ ⇣ ✔ ☐ ☒ ✻ ✢ ✶ ✽ ✳` and U+00A0, drawn blank.

It has no accented letters yet. Text with é gets a mark in that cell.

## Layout

| Path | What it is |
|---|---|
| `font/strokes.txt` | The ASCII face: each character as pen strokes on a 10 × 20 grid. Written for this project |
| `font/symbols.txt` | The symbols of the full set, in the same form |
| `font/code-masks.txt` | The 43 parity masks that turn a scalar into the net's 64 character inputs |
| `train/strokes.py` | Reads the two stroke files |
| `train/glyphs.py` | The two character sets. Makes box drawing and blocks from their Unicode names, Braille from the dot bits, and the target the net learns |
| `train/train.py` | Trains the net. Needs torch, and wants a GPU |
| `train/pack.py` | Packs the weights JSON into the binary file the C library loads. Documents the layout |
| `weights/` | The trained weights, as JSON and packed, with scores and `SHA256SUMS` |
| `include/neuronte.h`, `src/` | The C library |
| `tools/neuronte-render.c` | Draws lines of text into a PPM file |
| `tools/neuronte-bench.c` | Times the net per cell |
| `tests/` | UTF-8 cases, API and loader checks, and a cross-check against numpy |
| `demo/neuronte-demo.c` | Shows the font in a Kilix terminal through `kitty-framebuffer`, with typing |

## Build and test

```sh
make          # build/libneuronte.a, build/libneuronte.so and the tools
make test     # needs python3 with numpy
make bench
./build/neuronte-render weights/neuronte-full-v0.nrt 16 out.ppm 'Hello.' '╭──╮ ⣿⣶⣤⣀ ✔'
```

The library is C11 with libm and nothing else. On x86-64 it builds its
inner loops twice, plain and AVX2, and picks one by CPU when it loads.
`CFLAGS=-DNEURONTE_NO_CLONES` builds the plain path only.

`make test` checks, for both weight files, that:

- the weights match `weights/SHA256SUMS`;
- UTF-8 decoding follows Unicode's maximal-subpart rule, so a bad byte
  becomes one U+FFFD and never swallows the next character;
- the loader refuses a short, long or damaged file, or one of a shape it
  does not know;
- drawing clips at every edge and blends correctly, and the draw cache
  gives the same cell after it has turned over;
- the C library agrees with an independent float64 numpy evaluation of
  the JSON weights to 1e-3 in coverage, and the packed file is exactly
  what `train/pack.py` makes from the JSON.

For `neuronte-full` it also checks that box lines reach the cell edges,
that █ fills its cell and ▀ the top half, that U+2800 and U+00A0 are
blank, and that ⣿ carries about eight times the ink of ⠁.

## Demo

```sh
make demo
./build/neuronte-demo                 # in a Kilix terminal
./build/neuronte-demo weights/neuronte-ascii-v0.nrt
./build/neuronte-demo --snapshot out.ppm 1280 800
```

Every glyph on the demo's screen, its labels included, is drawn by the
net and shown through `kitty-framebuffer`, which `make demo` compiles from
`KITTYFB_DIR` (default `$HOME/gpu_terminal/kilix-modules/kitty-framebuffer`).
It loads `neuronte-full` if it can, else `neuronte-ascii`. With the full
weights it adds a panel of box drawing, blocks, Braille and symbols, and
two spinners that turn while it waits for keys. Type to draw text, Tab
changes its size, Esc quits. It needs zlib.

The first screen takes about 5 seconds with the full weights, since
every cell is new. The demo shows each part as it is done. After that
a frame takes about a millisecond.

## Use

```c
#include "neuronte.h"

neuronte *font;
if (neuronte_open_file("neuronte-full-v0.nrt", &font) != NEURONTE_OK)
    return 1;
/* pixels: row-major 0xAARRGGBB, stride in pixels. */
neuronte_draw_utf8(font, pixels, stride, width, height,
                   x, y, 16, 32, "Hello", 5, 0xFFFFFFFF);
neuronte_close(font);
```

Either weight file works with the same calls. The file states its
hidden width, and `neuronte_parameters()` reports the size of the net
that was loaded. `neuronte_coverage()` returns a cell's coverage without
drawing it. `neuronte_open()` takes the weights from memory instead of a
file. The draw calls keep up to 1,024 cells, dropping the least recently
used, so a handle should not be shared between threads without a lock.

## The net

Input: 26 features of a point in the cell (x, y, and sines and cosines
at 1 to 32 cycles per cell width) and 64 features of the scalar (its 21
bits and 43 parity bits). Any two scalars differ in at least 13 of those
64. Three hidden layers, ReLU: 128 wide for `ascii`, 256 for `full`.
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
python3 train/train.py out.json --set full --width 256   # 24 minutes on a shared RTX 3070
python3 train/pack.py out.json out.nrt
```

`neuronte-ascii-v0` came from the earlier trainer at commit `0cd2a25`,
which measured the exact distance to each stroke. Retrained with the
grid at width 128 it scores 0.953, 0.990 and 0.993 at 8, 16 and 48
pixels, against 0.948, 0.990 and 0.992 for the shipped file.

## Speed

One thread, i7-9850H, AVX2 path, no cache, while the machine was
otherwise busy. Milliseconds per cell, over several runs:

| Cell | Samples per pixel | `ascii` (load 17) | `full` (load 7 to 8) |
|---|---|---:|---:|
| 8 × 16 | 2 × 2 | 1.0 to 1.2 | 3.1 to 4.4 |
| 16 × 32 | 2 × 2 | 3.5 to 3.8 | 13 to 17 |
| 32 × 64 | 1 | 3.5 to 3.8 | 13 to 17 |
| 48 × 96 | 1 | 7.9 to 8.1 | 29 to 38 |

The plain path measured about 2.2 times slower for `ascii` and 1.7
times for `full`. Twice the width costs about four times the work in
the hidden layers. A
terminal should draw each character once per cell size and reuse it.
The draw calls' cache does that.

## Quality

`weights/*.scores.json` is the trainer's own scoring: the net's ink
against the target's ink, mean over the characters, 1.0 being exact,
with 2 × 2 samples per pixel. With 2 × 2 samples every character is
closer to its own target than to any other at every size scored; with
one sample at 8 pixels, 2 of the 557 in `full` are not. Characters whose
targets are all but the same, such as space, U+00A0 and U+2800, count
as one.

| Weights | 8 px | 16 px | 48 px |
|---|---:|---:|---:|
| `ascii` | 0.948 | 0.990 | 0.992 |
| `full`, all 557 | 0.976 | 0.997 | 0.996 |
| `full`, its ASCII | 0.952 | 0.989 | 0.988 |
| `full`, box drawing | 0.940 | 0.999 | 0.997 |
| `full`, blocks and Braille | 1.000 | 1.000 | 1.000 |
| `full`, symbols | 0.976 | 0.987 | 0.986 |

The weakest in `ascii` is `"` at 8 pixels, whose two marks are about one
pixel wide there. In `full` the weakest at 8 pixels are `├`, `"` and
`~`, and at 16 and 48 the asterisks `✳ ✶ ✽` and the dashed lines `┇ ┈`.

A width-384 net trained the same way scored 0.993 on its ASCII at 48
pixels, level with `ascii`, and 0.998 over all 557. The difference from
256 could not be seen in renders at 40 pixels, while 384 measured about
1.6 times slower per cell and makes a file twice the size, so `full` is
256.

Box lines are not snapped to pixels. A line's centre falls on a pixel
edge at even cell sizes, so at 8 pixels a light line is two grey rows,
not one dark one. With one sample per pixel at 8 pixels, the light
dashed lines can fade to almost nothing; the default there is 2 × 2.

## Licence

MIT. See [LICENSE](LICENSE). The weights are part of the project and are
under the same licence.
