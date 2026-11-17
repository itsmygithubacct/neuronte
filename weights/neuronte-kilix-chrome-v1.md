# kilix-chrome-v1: the 39 symbols Kilix prints on its bars

`neuronte-kilix-chrome-v1.nrt` holds the symbols the Kilix terminal prints on its own bars
and that no other bundle draws: the ringing bell of a pane's title bar, the
title bar's buttons and chips, the symbols of the top bar's widgets, a
battery at ten levels, and seven weather symbols. Kilix prints most of
them at private-use code points. Those code points are used here only as
numbers: every symbol is this project's own drawing, made from what the
symbol means on the bar, one cell wide, one colour, drawn to be read at
10×20.

It is a **standalone** bundle: 6 known-only group nets and one blank net,
343,224 bytes. A program opens it beside the terminal bundles and asks it
first. It is not a default and replaces nothing.

| Code point | Set | What it means on the bar | In the bundle |
|---|---|---|---|
| U+F0731 | `tchra` | split, new pane to the left: a bold arrow pointing left | yes |
| U+F0737 | `tchra` | split, new pane above: a bold arrow pointing up | yes |
| U+F072E | `tchra` | split, new pane below: a bold arrow pointing down | yes |
| U+F0734 | `tchra` | split, new pane to the right: a bold arrow pointing right | yes |
| U+EAB9 | `tchra` | maximise this pane: a small square outline | yes |
| U+F0293 | `tchra` | restore this pane: the four corner brackets of a full-screen frame | yes |
| U+F0156 | `tchra` | close this pane: a diagonal cross | yes |
| U+1F56D | `tchrb` | the bell rang in this tab: a ringing bell, a flared body with its clapper and marks of sound at both sides; not round | yes |
| U+F0219 | `tchrb` | open this pane's saved log: a sheet of paper with a folded corner and lines of text | yes |
| U+F030C | `tchrb` | type into several panes at once: a keyboard, three keys over a space bar | yes |
| U+F035B | `tchrb` | memory used: a chip, a square body with a die in it and three pins on every side | yes |
| U+F08AE | `tchrb` | graphics card use: an expansion card, a board with a fan, its bracket at the left and an edge connector below | yes |
| U+F073 | `tchrb` | date: a calendar page, two rings, a dark head and six days | yes |
| U+F2C9 | `tchrb` | temperature: a thermometer, a tube with a filled bulb and three marks beside it | yes |
| U+F028 | `tchrb` | volume: a loudspeaker with two waves of sound | yes |
| U+F05CB | `tchrb` | read the pane aloud: a head and shoulders, with two waves of sound from the mouth | yes |
| U+F036C | `tchrb` | dictation on: a microphone in its cradle, on a stand | yes |
| U+F036D | `tchrb` | dictation off: the microphone struck through | yes |
| U+F1EB | `tchrb` | network: three arcs of a wireless signal over a dot | yes |
| U+F0E7 | `tchrb` | charging: a lightning bolt | yes |
| U+F007A | `tchrp` | battery 10 percent | yes |
| U+F007B | `tchrp` | battery 20 percent | yes |
| U+F007C | `tchrp` | battery 30 percent | yes |
| U+F007D | `tchrp` | battery 40 percent | yes |
| U+F007E | `tchrp` | battery 50 percent | yes |
| U+F007F | `tchrp` | battery 60 percent | yes |
| U+F0080 | `tchrp` | battery 70 percent | yes |
| U+F0081 | `tchrp` | battery 80 percent | yes |
| U+F0082 | `tchrp` | battery 90 percent | yes |
| U+F0079 | `tchrp` | battery full | yes |
| U+F0083 | `tchrp` | battery needs attention: the outline with an exclamation mark in it | yes |
| U+F0091 | `tchrp` | battery state unknown: the outline with a question mark in it | yes |
| U+1F324 | `tchrx` | mostly clear: a sun with a small cloud before its lower right | yes |
| U+26C5 | `tchrx` | partly cloudy: a sun behind a cloud | yes |
| U+1F32B | `tchrx` | fog: four bars of mist, set off from one another | yes |
| U+1F326 | `tchrx` | showers: a sun behind a cloud with rain | yes |
| U+1F327 | `tchrx` | rain: a cloud with three strokes of rain | yes |
| U+1F328 | `tchrx` | snow: a cloud with five flakes, drawn as dots | yes |
| U+26C8 | `tchrx` | thunderstorm: a cloud with a lightning bolt and rain at both sides | yes |

**The drawings.** `font/kilix-chrome.txt` holds them; `train/kilix_chrome.py`
makes the twelve batteries from one outline and a level or a mark, and six
of the weather symbols from a sun, a cloud and what falls from it. The four
split arrows are one arrow turned. The battery stands upright with its cap
on top and fills from the bottom, a tenth of the inside for each level
(a little over one pixel a level at 10×20), so it does not fill the cell's
width.
The bell is a flared bell with a clapper and sound marks on both sides.
Where a sun stands behind a cloud, clear space is cut around the cloud so
the two do not run together. No font was opened to make or check any of
them, and nothing printed at these code points by any font was looked at.

**One drawing fix after the first training.** The battery's body first ran
from 5.8 to 15.2 of the cell's 20 units. The gates then reported a drawing
problem, not a net's: at 6×12 the full battery, drawn perfectly, was as
near the drawing of the battery at nine tenths as its own (a level was
half a pixel there). The body now runs from 4.4 to 16.6, so a level is
about 0.7 of a pixel at 6×12 and 1.1 pixels at 10×20, and the "!" and "?"
are larger. All twelve batteries changed; their two nets were trained
again on the new drawings and pass. The first battery nets are not in
the bundle.

## What a consumer changes

```c
neuronte_open_file("neuronte-kilix-chrome-v1.nrt", &chrome);
/* for each scalar c on a bar */
if (!neuronte_untrained(chrome, c))
    draw with chrome;
else
    go on to the next bundle;
```

`neuronte_untrained(chrome, c)` is 0 for exactly the 39 symbols in
`neuronte-kilix-chrome-v1.list.txt` and 1 for every other scalar, U+10FFFD among them (the
test checks it). A scalar outside the list, drawn through this file
anyway, comes out blank. `tests/check_bundle_lists.py` checks that no
listed bundle and split-v9 share a trained scalar. The file needs the
current runtime (version 2 bundles). It has 7 members.

## Gates

Every symbol is judged as a symbol by gates v2.3 (`gates-v2.3.json`, sha256
`2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`), the declaration the terminal lanes of this phase
share, against a teacher of all 39 drawings: mean error, 99th
percentile error and firm wrong pixels for the group and mean error for
each symbol at 6×12, 8×16, 10×20, 12×24, 16×32, 24×48 and 48×96; every
symbol nearest its own drawing; none vanished. Gates v2.3 is gates v2
(sha256 `5bf1a3f8312c45df2a20b2e69d51ee3c690c58891ec5390cf0e41cbdf9f9b51b`,
written before any net of this phase was trained) with two changes the
owner decided on 2026-11-17, before the nets in this bundle were scored
under it: no limit is tighter than what the group's own drawing scores
when sampled as the library samples it (a perfect net), with 10 % of room;
and a seed whose net puts every pixel on the right side at every counted
size passes the error-amount rules. Nearest-to-itself and none-vanished
are never eased. The steps between, gates v2.1 and v2.2, have sha256
`214942e398f88110cd7c6044c194f0f274274aeedb07abcbe8e1a18dc2b323c0` and
`dd3cc2ea30ccb49d001c28a905bcc6e2a2d11edfcd6a741464fda91162b10e70`.

**12 limits were eased** for the nets in this bundle: `tchrb g0` 8, `tchrp g0` 1, `tchrp g1` 3; each is in the
validation record with the declared limit, the perfect drawing's score and
the limit applied. 0 seeds passed by the pixel-exact rule.

A group whose two seeds pass ships the seed with the lower mean error at
8×16, 16×32 and 48×96. A group that fails is trained once more as two nets
of half its symbols each; a half that fails is left out. Nothing that
failed ships.

- 6 groups trained; 6 passed with both seeds.
- 0 failed and were halved; of the 0 halves 0 passed.
- 0 halves failed again and are left out (0 symbols).

## Results by net

Mean error against the teacher and mean overlap, for the shipped seed (for a net not in the bundle: seed 0).

| Net | Symbols | Gates v2.3 | Rules missed (seed 0 / seed 1) | Limits eased | In the bundle | Mean error 8×16 / 10×20 / 16×32 / 48×96 | Overlap 8×16 | Overlap 10×20 |
|---|---|---|---|---:|---|---|---:|---:|
| `tchra` g0 | U+F0731 U+F0737 U+F072E U+F0734 U+EAB9 U+F0293 U+F0156 | passed | 0 / 0 | 0 | seed 0 | 0.0064 0.0048 0.0038 0.0014 | 0.905 | 0.870 |
| `tchrb` g0 | U+1F56D U+F0219 U+F030C U+F035B U+F08AE U+F073 | passed | 0 / 0 | 8 | seed 0 | 0.0128 0.0107 0.0063 0.0028 | 0.833 | 0.937 |
| `tchrb` g1 | U+F2C9 U+F028 U+F05CB U+F036C U+F036D U+F1EB U+F0E7 | passed | 0 / 0 | 0 | seed 0 | 0.0059 0.0039 0.0026 0.0016 | 0.964 | 0.961 |
| `tchrp` g0 | U+F007A U+F007B U+F007C U+F007D U+F007E U+F007F | passed | 0 / 0 | 1 | seed 0 | 0.0142 0.0035 0.0037 0.0022 | 0.947 | 0.639 |
| `tchrp` g1 | U+F0080 U+F0081 U+F0082 U+F0079 U+F0083 U+F0091 | passed | 0 / 0 | 3 | seed 1 | 0.0145 0.0044 0.0043 0.0027 | 0.948 | 0.729 |
| `tchrx` g0 | U+1F324 U+26C5 U+1F32B U+1F326 U+1F327 U+1F328 U+26C8 | passed | 0 / 0 | 0 | seed 0 | 0.0059 0.0046 0.0032 0.0016 | 0.881 | 0.958 |

## Recipe

- **Sets and groups.** Four sets; each cut in order into group nets of 6 or
  7 symbols (6 in all).
- **Training.** `train/split_expert.py train --mode repertoire --partition
  contiguous`, unchanged: hidden width 64, 120,000 steps, the project
  teacher (grid 256), seeds 0 and 1. A halved group: the set `NAMErI` of
  that group's symbols, two parts, the rest the same.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from
  each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
make pack-kilix-chrome-v1    # rebuilds the .nrt byte for byte from the group nets
make test-kilix-chrome-v1
```

## Checks

`make test-kilix-chrome-v1` (part of `make test`): every group net against
the float64 reference; the bundle rebuilt byte for byte; its table exactly
`neuronte-kilix-chrome-v1.list.txt`; every scalar from U+0000 to U+10FFFF routed as the table
says, U+10FFFD untrained; pixels through the bundle equal to each group net
alone at 19 cell sizes and with one sample a pixel; `test_api --standalone`;
and the validation record: only nets whose two seeds passed gates v2.3 are
in the bundle, each as the selected seed.

## Speed

Not measured on its own. Its nets have the shape of
`neuronte-term-rest-v1`'s (width 64 group nets behind a table, no gate),
which was measured at 2.7 times the speed of split-v9's fallback on an
Intel Core i7-6820HQ and an Intel Core i7-10700F; see that card.

## Files

| File | What |
|---|---|
| `neuronte-kilix-chrome-v1.nrt` | The bundle, 343,224 bytes, sha256 `235e2e9d9ec83f83f72feb848df1fb1f47a7ca4d0b794cdf9d3763646cfb892c` |
| `neuronte-kilix-chrome-v1.list.txt` | The 39 symbols it was trained on |
| `neuronte-kilix-chrome-v1-SET-gN.json` | The 6 group nets as trained (the shipped seed) |
| `neuronte-kilix-chrome-v1.provenance.json` | Every member's hash and scalars, written by `make pack-kilix-chrome-v1` |
| `neuronte-kilix-chrome-v1.validation.json` | The gates' hashes, both seeds' measurements and failures for every group and half, the limits eased, what was left out |
