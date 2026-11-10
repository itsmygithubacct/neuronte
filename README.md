# Neuronte

A neural net that is its own font. A character goes in, as ASCII or as
UTF-8. The net writes that character's pixels into a buffer the caller
owns. No font file, glyph table or bitmap atlas is consulted. The 44,801
weights are the font.

Games, the OS and `soft-raster` link the library and pass in the buffer.
The same buffer can be shown in a Kilix terminal or in a GUI window. The
library does not open the window or take the terminal.

Status: local only. No remote. The C library draws the 95 printable
ASCII characters. Other scalars get a mark of their own, not a letter.

## Layout

| Path | What it is |
|---|---|
| `font/strokes.txt` | The face: each ASCII character as pen strokes on a 10 × 20 grid. Written for this project |
| `font/code-masks.txt` | The 43 parity masks that turn a scalar into the net's 64 character inputs |
| `train/train.py` | Trains the net on the stroke lists. Needs torch, and wants a GPU |
| `train/pack.py` | Packs the weights JSON into the binary file the C library loads. Documents the layout |
| `weights/` | The trained weights, as JSON and packed, with `SHA256SUMS` |
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
./build/neuronte-render weights/neuronte-ascii-v0.nrt 16 out.ppm 'Hello.'
```

The library is C11 with libm and nothing else. On x86-64 it builds its
inner loops twice, plain and AVX2, and picks one by CPU when it loads.
`CFLAGS=-DNEURONTE_NO_CLONES` builds the plain path only.

`make test` checks that:

- the weights match `weights/SHA256SUMS`;
- UTF-8 decoding follows Unicode's maximal-subpart rule, so a bad byte
  becomes one U+FFFD and never swallows the next character;
- the loader refuses a short, long, damaged or differently shaped file;
- drawing clips at every edge and blends correctly;
- the C library agrees with an independent float64 numpy evaluation of
  the JSON weights to 1e-3 in coverage, and the packed file is exactly
  what `train/pack.py` makes from the JSON.

## Demo

```sh
make demo
./build/neuronte-demo                 # in a Kilix terminal
./build/neuronte-demo --snapshot out.ppm 1280 800
```

Every glyph on the demo's screen, its labels included, is drawn by the
net and shown through `kitty-framebuffer`, which `make demo` compiles from
`KITTYFB_DIR` (default `$HOME/gpu_terminal/kilix-modules/kitty-framebuffer`).
Type to draw text, Tab changes its size, Esc quits. It needs zlib.

## Use

```c
#include "neuronte.h"

neuronte *font;
if (neuronte_open_file("neuronte-ascii-v0.nrt", &font) != NEURONTE_OK)
    return 1;
/* pixels: row-major 0xAARRGGBB, stride in pixels. */
neuronte_draw_utf8(font, pixels, stride, width, height,
                   x, y, 16, 32, "Hello", 5, 0xFFFFFFFF);
neuronte_close(font);
```

`neuronte_coverage()` returns a cell's coverage without drawing it.
`neuronte_open()` takes the weights from memory instead of a file. The
draw calls keep a small cache of cells, so a handle should not be shared
between threads without a lock.

## The net

Input: 26 features of a point in the cell (x, y, and sines and cosines
at 1 to 32 cycles per cell width) and 64 features of the scalar (its 21
bits and 43 parity bits). Any two scalars differ in at least 13 of those
64. Three hidden layers of 128, ReLU. Output: the distance to the edge of
the ink, clamped. Coverage is a ramp one sample wide across that edge, so
the same weights draw a sharp letter in a large cell and a correctly
softened one in a small cell. Cells narrower than 24 pixels take 2 × 2
samples per pixel.

## Speed

One thread, i7-9850H, AVX2 path, no cache, three runs while the machine
was otherwise busy (load average about 17 on 12 threads):

| Cell | Samples per pixel | ms per cell |
|---|---|---:|
| 8 × 16 | 2 × 2 | 1.0 to 1.2 |
| 16 × 32 | 2 × 2 | 3.5 to 3.8 |
| 32 × 64 | 1 | 3.5 to 3.8 |
| 48 × 96 | 1 | 7.9 to 8.1 |

The plain path measured about 2.2 times slower. All 95 ASCII cells at
16 × 32 take about a third of a second, so a terminal should draw each
character once per cell size and reuse it. The draw calls keep a small
cache for that.

## Quality

`weights/neuronte-ascii-v0.scores.json` is the trainer's own scoring:
the net's ink against the stroke lists' ink, mean over the 95 characters,
1.0 being exact. With 2 × 2 samples per pixel it is 0.948 at 8 pixels
wide, 0.990 at 16 and 0.992 at 48. Every character is closer to its own
target than to any other. The weakest is `"` at 8 pixels, whose two
marks are about one pixel wide there.

## Licence

MIT. See [LICENSE](LICENSE). The weights are part of the project and are
under the same licence.
