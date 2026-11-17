# kilix-chrome-v2: the 41 symbols Kilix prints on its bars, drawn for two cells

`neuronte-kilix-chrome-v2.nrt` holds the symbols the Kilix terminal prints on its own bars:
the code points of `neuronte-kilix-chrome-v1` and the sun and the cloud.
Kilix prints most of them with a blank cell after them, and the symbol font
it used drew them across both cells; v1's one-cell drawings looked half
the size beside that, and their one-unit pens came out grey at a 9×18 cell.
Here 40 symbols are drawn for the **box of two cells** (the symbol's cell and
the blank one after it), with pens of 1/9 of the box; the ringing bell
stays one cell, v1's drawing unchanged, because it stands beside one-cell
marks. The private-use code points are used only as numbers: every symbol
is this project's own drawing, made from what it means on the bar.

It is a **standalone** bundle: 8 known-only group nets and one blank net,
457,336 bytes. v1 is unchanged and stays for a symbol that has no blank
cell after it. It is not a default and replaces nothing.

## How a program must ask for a two-cell symbol

A net's design cell is 1 wide and 2 high. A two-cell box W×H (W twice the
cell's width, H the cell's height) is about square, and its drawing is in
the net's cell twice as tall as it is wide. **Ask for the cell W×2H and
average each pair of rows:**

```c
/* a two-cell symbol c in a box w x h; buf holds w * 2 * h floats */
neuronte_coverage(chrome2, c, w, 2 * h, 0, buf);
for (y = 0; y < h; y++)
    for (x = 0; x < w; x++)
        box[y * w + x] = (buf[2 * y * w + x] + buf[(2 * y + 1) * w + x]) / 2;
```

Do not ask for W×H itself. The library turns distance into coverage with
the box's width alone, so in a cell squeezed to half its height the ramp
across a level edge is half a pixel deep, and an edge that falls inside a
pixel row is drawn harder than the area it covers. Measured with v1's nets
(exact drawings score the same), against the true area coverage of the
box, before v2 was drawn:

| Box | Asked as | Mean error | 99th percentile | Firm wrong pixels |
|---|---|---:|---:|---:|
| 18×18 | 18×18 | 0.0108 | 0.125 | 0.86 % |
| 18×18 | 18×36, row pairs averaged | 0.0054 | 0.057 | 0 |
| 24×24 | 24×24 | 0.0165 | 0.250 | 0.04 % |
| 24×24 | 24×48, row pairs averaged | 0.0046 | 0.058 | 0.004 % |
| 48×48 | 48×48 | 0.0081 | 0.217 | 0.01 % |
| 48×48 | 48×96, row pairs averaged | 0.0025 | 0.052 | 0 |

The half calls (`neuronte_draw_half`) are no way round it: they refuse the
plane-15 code points most of these symbols have. The one-cell bell is asked
as any character, for its cell.

| Code point | Set | Cells | What it means on the bar | In the bundle |
|---|---|---|---|---|
| U+F0731 | `tchwa` | two | split, new pane to the left: a bold arrow pointing left | yes |
| U+F0737 | `tchwa` | two | split, new pane above: a bold arrow pointing up | yes |
| U+F072E | `tchwa` | two | split, new pane below: a bold arrow pointing down | yes |
| U+F0734 | `tchwa` | two | split, new pane to the right: a bold arrow pointing right | yes |
| U+EAB9 | `tchwa` | two | maximise this pane: a square outline | yes |
| U+F0293 | `tchwa` | two | restore this pane: the four corner brackets of a full-screen frame | yes |
| U+F0156 | `tchwa` | two | close this pane: a diagonal cross | yes |
| U+1F56D | `tchwb` | one | the bell rang in this tab: the one-cell ringing bell of neuronte-kilix-chrome-v1, unchanged | yes |
| U+F0219 | `tchwb` | two | open this pane's saved log: a sheet of paper with two lines of text | yes |
| U+F030C | `tchwb` | two | type into several panes at once: a keyboard, three keys over a space bar | yes |
| U+F035B | `tchwb` | two | memory used: a chip, a square body with a window in it and two short pins on every side | yes |
| U+F08AE | `tchwb` | two | graphics card use: an expansion card, a board with a part on it, its bracket at the left and an edge connector below | yes |
| U+F2C9 | `tchwb` | two | temperature: a thermometer, a tube half full over a filled bulb | yes |
| U+F028 | `tchwb` | two | volume: a loudspeaker with two waves of sound | yes |
| U+F05CB | `tchwb` | two | read the pane aloud: a head and shoulders, with two waves of sound from the mouth | yes |
| U+F036C | `tchwb` | two | dictation on: a microphone in its cradle, on a stand | yes |
| U+F036D | `tchwb` | two | dictation off: the microphone struck through, with clear space beside the stroke | yes |
| U+F1EB | `tchwb` | two | network: three arcs of a wireless signal over a dot | yes |
| U+F073 | `tchwb` | two | date: a calendar page, two rings, a dark head and three days | yes |
| U+F0E7 | `tchwb` | two | charging: a lightning bolt | yes |
| U+F007A | `tchwp` | two | battery 10 percent | yes |
| U+F007B | `tchwp` | two | battery 20 percent | yes |
| U+F007C | `tchwp` | two | battery 30 percent | yes |
| U+F007D | `tchwp` | two | battery 40 percent | yes |
| U+F007E | `tchwp` | two | battery 50 percent | yes |
| U+F007F | `tchwp` | two | battery 60 percent | yes |
| U+F0080 | `tchwp` | two | battery 70 percent | yes |
| U+F0081 | `tchwp` | two | battery 80 percent | yes |
| U+F0082 | `tchwp` | two | battery 90 percent | yes |
| U+F0079 | `tchwp` | two | battery full | yes |
| U+F0083 | `tchwp` | two | battery needs attention: the outline with an exclamation mark in it | yes |
| U+F0091 | `tchwp` | two | battery state unknown: the outline with a question mark in it | yes |
| U+2600 | `tchwx` | two | clear: a sun, a disc with eight rays | yes |
| U+2601 | `tchwx` | two | cloudy: a cloud | yes |
| U+1F324 | `tchwx` | two | mostly clear: a sun with a small cloud before its lower right | yes |
| U+26C5 | `tchwx` | two | partly cloudy: a sun behind a cloud | yes |
| U+1F32B | `tchwx` | two | fog: four bars of mist, set off from one another | yes |
| U+1F326 | `tchwx` | two | showers: a sun behind a cloud with rain | yes |
| U+1F327 | `tchwx` | two | rain: a cloud with three strokes of rain | yes |
| U+1F328 | `tchwx` | two | snow: a cloud with five flakes, drawn as dots | yes |
| U+26C8 | `tchwx` | two | thunderstorm: a cloud with a lightning bolt and rain at both sides | yes |

**The drawings.** `font/kilix-chrome-2.txt` holds them, on a grid of 18 by
18 units for the box: one unit is one pixel when the terminal's cell is
9×18, and straight edges lie on whole units, so they fall on pixel edges
there. `train/kilix_chrome2.py` puts each drawing in the net's cell and
turns every stroke into its outline first, so a lying stroke is as thick
as a standing one once the cell is drawn at half height; it makes the
twelve batteries from one outline and a level or a mark, and eight weather
symbols from a sun, a cloud and what falls from it.

- Centred in the box both ways; all ink inside 5/6 of the box each way
  (15 of 18 pixels), most of it inside 14.
- Outlines, thin strokes, the gaps between strokes and the marks inside a
  shape are 2 units (1/9 of the box); solid shapes 4 units or more.
- Things with straight sides (the square, the sheet, the keyboard, the
  calendar, the card, the battery) are cut from solid shapes and have sharp
  corners.
- Upright things keep their proportions: the battery is 10 units wide and
  14 high with its cap, a level is 0.9 unit, and the full battery is solid.
- Where a sun stands behind a cloud, clear space is cut round the cloud
  and the sun's rays are dots.

Drawn from meaning and unsure, each of which can be changed on its own:
the "?" in the battery is a hook 4 units wide, the least legible drawing;
the card (a board, its bracket at the left, a connector below) may read as
a flag; the Wi-Fi arcs span 64 degrees so that three arcs and their gaps
fit. No font was opened to make or check any drawing, nothing printed at
these code points by any font was looked at, and the screenshots of the
symbol font that came with the request were not opened.

## What a consumer changes

```c
neuronte_open_file("neuronte-kilix-chrome-v2.nrt", &chrome2);
/* for a scalar c on a bar that Kilix prints with a blank cell after it */
if (!neuronte_untrained(chrome2, c))
    draw c across both cells, asked as above;
else
    go on to neuronte-kilix-chrome-v1 and the terminal bundles;
```

`neuronte_untrained(chrome2, c)` is 0 for exactly the 41 symbols in
`neuronte-kilix-chrome-v2.symbols.txt` and 1 for every other scalar, U+10FFFD among them (the
test checks it). Which code points are two cells wide is the program's to
know: all but U+1F56D. A two-cell symbol asked for one cell comes out
squeezed; use v1 there.

**This file is not a listed bundle.** It has v1's code points on purpose,
and U+2600 and U+2601 are also one-cell characters of a terminal bundle,
so the rule that no two listed bundles claim one character
(`tests/check_bundle_lists.py`) cannot hold for it. Its list is therefore
`neuronte-kilix-chrome-v2.symbols.txt`, not a `.list.txt`; that test and its rule are
unchanged for every other bundle, and `tests/check_kilix_chrome_v2.py`
holds this bundle to its list exactly and the list to v1's and those two.
The file needs the current runtime (version 2 bundles). It has 9
members.

## Gates

Declared before any v2 drawing was trained (2026-11-17): every group is
judged as symbols by gates v2.3 (`gates-v2.3.json`, sha256
`2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`), unchanged, by the unchanged scoring command, at its
unchanged counted cells 6×12, 8×16, 10×20, 12×24, 16×32, 24×48 and 48×96,
against a teacher of all 41 drawings: mean error, 99th percentile error
and firm wrong pixels for the group and mean error for each symbol; every
symbol nearest its own drawing; none vanished. The cell W×2W is what a
program asks for a box W×W, so 12×24, 16×32, 24×48 and 48×96 judge the
boxes 12×12, 16×16, 24×24 and 48×48; the three smallest counted cells
judge boxes nobody uses and stay counted. The cells of the boxes in use
that the gates do not count (16×34, 18×36, 20×38, 20×40, 36×72) are
reported below as information and decide nothing.

Gates v2.3 is gates v2 (sha256 `5bf1a3f8312c45df2a20b2e69d51ee3c690c58891ec5390cf0e41cbdf9f9b51b`)
with two changes the owner decided on 2026-11-17, before this bundle was
drawn: no limit is tighter than what the group's own drawing scores when
sampled as the library samples it (a perfect net), with 10 % of room; and
a seed whose net puts every pixel on the right side at every counted size
passes the error-amount rules. Nearest-to-itself and none-vanished are
never eased.

**53 limits were eased** for the nets in this bundle: `tchwa g0` 1, `tchwbr0 g0` 9, `tchwbr0 g1` 19, `tchwbr1 g1` 8, `tchwp g0` 7, `tchwp g1` 9; each is in the
validation record with the declared limit, the perfect drawing's score and
the limit applied. 0 seeds passed by the pixel-exact rule.

A group whose two seeds pass ships the seed with the lower mean error at
8×16, 16×32 and 48×96. A group that fails is trained once more as two nets
of half its symbols each; a half that fails is left out. Nothing that
failed ships.

- 6 groups trained; 4 passed with both seeds.
- 2 failed and were halved; of the 4 halves 4 passed.
- 0 halves failed again and are left out (0 symbols).

## Results by net

Mean error against the teacher and mean overlap at counted cells, for the shipped seed (for a net not in the bundle: seed 0).

| Net | Symbols | Gates v2.3 | Rules missed (seed 0 / seed 1) | Limits eased | In the bundle | Mean error 12×24 / 16×32 / 24×48 / 48×96 | Overlap 16×32 | Overlap 24×48 |
|---|---|---|---|---:|---|---|---:|---:|
| `tchwa` g0 | U+F0731 U+F0737 U+F072E U+F0734 U+EAB9 U+F0293 U+F0156 | passed | 0 / 0 | 1 | seed 1 | 0.0055 0.0038 0.0038 0.0018 | 0.875 | 0.996 |
| `tchwb` g0 | U+1F56D U+F0219 U+F030C U+F035B U+F08AE U+F2C9 | **failed** | 1 / 2: 24x48 mae, 24x48 p99 | 18 | no: halved | 0.0111 0.0085 0.0085 0.0039 | 0.945 | 0.984 |
| `tchwbr0` g0 (half) | U+1F56D U+F0219 U+F030C | passed | 0 / 0 | 9 | seed 1 | 0.0093 0.0089 0.0059 0.0026 | 0.929 | 0.972 |
| `tchwbr0` g1 (half) | U+F035B U+F08AE U+F2C9 | passed | 0 / 0 | 19 | seed 1 | 0.0125 0.0082 0.0104 0.0048 | 0.958 | 0.994 |
| `tchwb` g1 | U+F028 U+F05CB U+F036C U+F036D U+F1EB U+F073 U+F0E7 | **failed** | 1 / 0: 24x48 firm | 2 | no: halved | 0.0062 0.0041 0.0052 0.0023 | 0.956 | 0.983 |
| `tchwbr1` g0 (half) | U+F028 U+F05CB U+F036C | passed | 0 / 0 | 0 | seed 0 | 0.0049 0.0035 0.0040 0.0017 | 0.961 | 0.991 |
| `tchwbr1` g1 (half) | U+F036D U+F1EB U+F073 U+F0E7 | passed | 0 / 0 | 8 | seed 1 | 0.0072 0.0045 0.0059 0.0025 | 0.955 | 0.981 |
| `tchwp` g0 | U+F007A U+F007B U+F007C U+F007D U+F007E U+F007F | passed | 0 / 0 | 7 | seed 0 | 0.0078 0.0098 0.0047 0.0020 | 0.992 | 0.989 |
| `tchwp` g1 | U+F0080 U+F0081 U+F0082 U+F0079 U+F0083 U+F0091 | passed | 0 / 0 | 9 | seed 0 | 0.0087 0.0096 0.0057 0.0025 | 0.993 | 0.991 |
| `tchwx` g0 | U+2600 U+2601 U+1F324 U+26C5 U+1F32B U+1F326 U+1F327 U+1F328 U+26C8 | passed | 0 / 0 | 0 | seed 0 | 0.0042 0.0030 0.0038 0.0019 | 0.978 | 0.990 |

## The boxes in use that the gates do not count (information)

The shipped seed of each net at the cell a program asks, by the scorer's
own metric code, and in the box itself (each pair of rows averaged)
against the teacher's area coverage of the box. Every symbol is nearest
its own drawing and none vanishes at every one of these cells unless the
table says otherwise. Error is lowest at 18×18 and 36×36, where the
drawings' straight edges fall on pixel edges; at the other boxes those
edges fall inside pixels.

| Net | 16×34: error, 99th pct | 18×36 | 20×40 | 36×72 | Box 16×17: error | Box 18×18 | Box 20×20 | Box 36×36 | Not nearest or vanished |
|---|---|---|---|---|---:|---:|---:|---:|---|
| `tchwa` g0 | 0.0039, 0.059 | 0.0011, 0.019 | 0.0030, 0.057 | 0.0013, 0.031 | 0.0036 | 0.0010 | 0.0029 | 0.0012 | none |
| `tchwbr0` g0 | 0.0095, 0.069 | 0.0020, 0.034 | 0.0071, 0.058 | 0.0016, 0.042 | 0.0094 | 0.0019 | 0.0068 | 0.0016 | none |
| `tchwbr0` g1 | 0.0086, 0.077 | 0.0020, 0.029 | 0.0067, 0.082 | 0.0019, 0.050 | 0.0081 | 0.0018 | 0.0065 | 0.0019 | none |
| `tchwbr1` g0 | 0.0033, 0.043 | 0.0018, 0.024 | 0.0027, 0.038 | 0.0017, 0.036 | 0.0027 | 0.0014 | 0.0023 | 0.0014 | none |
| `tchwbr1` g1 | 0.0046, 0.066 | 0.0022, 0.028 | 0.0038, 0.058 | 0.0021, 0.046 | 0.0041 | 0.0020 | 0.0036 | 0.0019 | none |
| `tchwp` g0 | 0.0099, 0.078 | 0.0006, 0.011 | 0.0079, 0.057 | 0.0004, 0.008 | 0.0097 | 0.0006 | 0.0078 | 0.0004 | none |
| `tchwp` g1 | 0.0097, 0.075 | 0.0007, 0.018 | 0.0078, 0.058 | 0.0006, 0.019 | 0.0095 | 0.0007 | 0.0077 | 0.0006 | none |
| `tchwx` g0 | 0.0031, 0.045 | 0.0022, 0.033 | 0.0024, 0.040 | 0.0022, 0.047 | 0.0027 | 0.0019 | 0.0021 | 0.0018 | none |

**Seen on the sheet of the trained nets.** The full battery keeps a faint
trace of the nine-tenths level it shares a net with: one row inside it
dips to 0.93 of full at 20×20 and to 0.81 at 24×24 and 48×48 (1.00 at
16×17, 0.99 at 18×18, 0.95 at 36×36). It passes the gates, which count it
as error and not as a wrong pixel.

## Recipe

- **Sets and groups.** Four sets; each cut in order into group nets of 6 to
  9 symbols (6 in all). 2 of them failed and were trained again as
  halves, so the bundle holds 8 nets of 3 to 9 symbols. The one-cell
  bell shares its net with two-cell symbols.
- **Training.** `train/split_expert.py train --mode repertoire --partition
  contiguous`, unchanged: hidden width 64, 120,000 steps, the project
  teacher (grid 256), seeds 0 and 1. A halved group: the set `NAMErI` of
  that group's symbols, two parts, the rest the same.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from
  each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
make pack-kilix-chrome-v2    # rebuilds the .nrt byte for byte from the group nets
make test-kilix-chrome-v2
```

## Checks

`make test-kilix-chrome-v2` (part of `make test`): every group net against
the float64 reference; the bundle rebuilt byte for byte; its table exactly
`neuronte-kilix-chrome-v2.symbols.txt`, and that list exactly v1's and U+2600 and U+2601;
every scalar from U+0000 to U+10FFFF routed as the table says, U+10FFFD
untrained; pixels through the bundle equal to each group net alone at 19
cell sizes, at the five cells asked for two-cell boxes and with one sample
a pixel; every two-cell symbol with ink in both cells of its 18×18 box and
none on the box's edge; `test_api --standalone`; and the validation record:
only nets whose two seeds passed gates v2.3 are in the bundle, each as the
selected seed.

## Speed

Not measured on the benchmark hosts. The nets have the shape of
`neuronte-term-rest-v1`'s (width 64 group nets behind a table, no gate);
a two-cell box costs four times the samples of one cell of the same
height: twice the width and, by the way it is asked, twice the rows. A
rough figure, not a benchmark: on one busy laptop core a symbol for an
18×18 box took about 1.7 ms asked as 18×36, with v1's nets, before v2 was
trained. A program should keep the box it gets.

## Files

| File | What |
|---|---|
| `neuronte-kilix-chrome-v2.nrt` | The bundle, 457,336 bytes, sha256 `8583eadf252d499fe5b8b3ae5c28c4716cdd502c6f509f5a5c473dd033e9519c` |
| `neuronte-kilix-chrome-v2.symbols.txt` | The 41 symbols it was trained on |
| `neuronte-kilix-chrome-v2-SET-gN.json` | The 8 group nets as trained (the shipped seed) |
| `neuronte-kilix-chrome-v2.provenance.json` | Every member's hash and scalars, written by `make pack-kilix-chrome-v2` |
| `neuronte-kilix-chrome-v2.validation.json` | The gates' hashes, both seeds' measurements and failures for every group and half, the limits eased, what was left out |
