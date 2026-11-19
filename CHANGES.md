# Changes

## 0.1.7

Every file of 0.1.6 is still here byte for byte and draws the same pixels
and advances. No default changes. The library gains calls and two advance
table forms (below) and keeps every existing call as it was.

### All of Latin-1 in every desktop face

The 1 to 16 px faces (`neuronte-uiN-v2`, `neuronte-uiN-italic-v2`), the
scaled face (`neuronte-ui-scaled-latin1-v1` with its italic advances) and
the large face (`neuronte-ui-large-latin1-v2`) draw printable ASCII, the
ellipsis and all 96 characters from U+00A0 to U+00FF. ASCII draws byte for
byte as before. Drawings: `font/ui-N-latin1.txt`, `font/ui-N-latin1-italic.txt`;
cards in `weights/`.

### Wide characters

Five bundles, `neuronte-wide-{forms,symbols,pictographs,pictographs2,supplement}-v1`,
draw 1,261 of the 1,335 East Asian Wide pictographs, symbols and fullwidth
forms for a box of two cells (a drawing twice as tall, the engine asks
W x 2H and averages row pairs, as `neuronte-kilix-chrome-v2`). 95 of their
322 nets failed the gates and ship by the owner's choice, marked FAILED on
their cards; 74 characters are left out and listed. Their sets are in
`weights/NAME.symbols.txt`. The pictographs are two files because a bundle
holds at most 127 group nets.

### Neuronte Sans Metric

A desktop face drawn to Helvetica's advances (`neuronte-metric-sansN-v1`,
1 to 16 px with italics and a drawn bold from 9 px; `-scaled-v1`;
`-large-v1`), with the library's new support: advance tables in
thousandths of an em (version 4 at 100 units, or version 8 with a shift of
each letter's drawing), `neuronte_advance_milli()`, `neuronte_advance_shift()`,
`neuronte_text_width_exact()` and `neuronte_draw_text_exact()`. The large
and scaled faces failed one gate (G-M1) and ship by the owner's ruling. Its
advances are numbers copied from Adobe's AFM files; see
[PROVENANCE.md](PROVENANCE.md) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## 0.1.6

Every file of 0.1.5 is still here byte for byte and draws the same pixels
and advances. No default changes. `src/neuronte.c` and `include/neuronte.h`
are unchanged byte for byte; the library gains one translation unit.

### New nets

Six more terminal bundles for 1,714 characters that DejaVu Sans Mono or
DejaVu Sans has and no earlier bundle was trained on. With them the
terminal set is 4,919 characters and shares 4,617 of DejaVu's 6,065, up
from 2,903; of DejaVu Sans Mono's 3,322 it shares 2,755, up from 2,174.

Each is a standalone bundle, opened beside `neuronte-split-v9` as the
bundles of 0.1.5 are, with its set as text in `weights/NAME.list.txt`.

- `neuronte-term-letters-v1`: 812 more letters of Latin, Greek and
  Cyrillic: the rest of Latin Extended-B, IPA and phonetic letters, small
  capitals, modifier letters, Latin Extended-C and -D, the rest of Greek
  and Coptic and of Cyrillic. 103 group nets, 5,882,132 bytes. Four
  characters of the list, U+1DB4 to U+1DB7, are left out: their group
  failed, and so did their half when it was trained again. 73 shapes were
  drawn from the character's name alone and are marked unsure in
  `font/term-letters.txt`. [Card](weights/neuronte-term-letters-v1.md).
- `neuronte-term-blocks-v1`: 310 characters of four blocks made by rule:
  64 Yijing hexagrams, 87 Tai Xuan Jing figures, 100 domino tiles and 59
  playing cards. Five tiled nets and one group net, 849,696 bytes.
  [Card](weights/neuronte-term-blocks-v1.md).
- `neuronte-term-mathalpha-v1`: 179 letters and digits of the sans-serif,
  monospace and double-struck mathematical alphabets. 17 group nets,
  971,056 bytes. [Card](weights/neuronte-term-mathalpha-v1.md).
- `neuronte-term-syllabics-v1`: 168 Canadian syllabics. 15 group nets,
  856,824 bytes. [Card](weights/neuronte-term-syllabics-v1.md).
- `neuronte-term-scripts-v1`: the 48 characters of Lisu. 6 group nets,
  343,188 bytes. [Card](weights/neuronte-term-scripts-v1.md).
- `neuronte-term-rest-v1`: 197 characters: Hebrew letters, presentation
  forms and punctuation, Lao letters and vowel signs, the baht sign, and
  faces and moon phases in one colour and one cell. 26 group nets,
  1,484,956 bytes. The Lao letters are drawn from memory of their general
  shape and should be checked by a reader of Lao.
  [Card](weights/neuronte-term-rest-v1.md).

Three bundles for a terminal's own bars, none of them a terminal bundle
and none in the count above:

- `neuronte-kilix-chrome-v1`: the 39 symbols the Kilix terminal prints on
  its bars, one cell each. 6 group nets, 343,224 bytes.
  [Card](weights/neuronte-kilix-chrome-v1.md).
- `neuronte-kilix-chrome-v2`: 41 of those symbols drawn for a box of two
  cells. 8 group nets, 457,336 bytes.
  [Card](weights/neuronte-kilix-chrome-v2.md).
- `neuronte-weather-colour-v1`: nine weather symbols in colour, two cells
  each, asked for by halves as an emoji is. One colour net of width 192
  behind a table, 396,956 bytes. In half cells under 14 pixels wide the
  library snaps edges, and the picture then differs from the drawing by 4
  to 6 of 255 on average. [Card](weights/neuronte-weather-colour-v1.md).

Every net in these nine files passed the limits that gave its verdict,
with both seeds, and the rule was automatic: a group that failed was
trained once more as two halves, and a half that failed again was left
out. The limits were declared before training (`gates-v2.json`) and
amended three times while the nets were scored, after a perfect drawing
was shown to fail some of the rules; the verdicts are those of
`gates-v2.3.json`, and each card says which limits were eased for its
nets and by how much.

Uncached, the new terminal characters draw 2.2 to 4.2 times as fast as
split-v9 drew them from its fallback net, measured on an Intel Core
i7-6820HQ and an Intel Core i7-10700F: 4.2 times for the letters, 2.7 for
term-rest, 2.6 for the mathematical alphabets, 2.5 for Lisu, 2.4 for the
syllabics and 2.2 for the blocks made by rule. Each card has its table.

No drawing was made by reading a font file. DejaVu was used only for its
list of code points.

### Cells files

`include/neuronte_cells.h` and `src/cells.c`, a new translation unit in
`libneuronte`: `neuronte_cells_open()`, `neuronte_cells_find()`,
`neuronte_cells_count()`, `neuronte_cells_entry()`,
`neuronte_cells_close()` and `neuronte_cells_write()`. A cells file holds
coverage exactly as `neuronte_coverage_styled()` writes it, for chosen
characters, cells and styles of one weight file, so that a process maps
it in place of asking the nets at its first use of a character.
`src/neuronte.c` and `include/neuronte.h` are unchanged byte for byte,
and no existing call behaves differently. `make test-cells` is in `make
test`.

### Tests

- The 54 checks of a hand-drawn face against its drawing are each a target
  of their own (`test-face-v0-ui1` and so on), so `make -jN test` runs
  them side by side; one after another they were most of the time of the
  whole test.
- `tests/check_emoji.py` writes its cache files under another name and
  renames them, so two targets run side by side no longer read a file the
  other is still writing.
- One test target for each new bundle, run by `make test`, and
  `tests/check_weather.py` for the bar's own call of the weather net.

## 0.1.5

Every file of 0.1.4 is still here byte for byte and draws the same pixels
and advances. No default changes, and the library's source is unchanged.

### New nets

Four terminal bundles for 1,864 characters that DejaVu Sans Mono or DejaVu
Sans has and `neuronte-split-v9` was not trained on. With them the terminal
set shares 2,903 of DejaVu's 6,065 characters, up from 1,039.

Each is a **standalone bundle**: a table, the group nets, and a blank net
for every other character. It holds no copy of split-v9 and does not
replace it. A program opens it beside split-v9 and draws a character with
the bundle whose `neuronte_untrained()` is 0 for it;
`weights/NAME.list.txt` is the same set as text.

- `neuronte-term-latin-v1`: 596 letters made of a letter Neuronte already
  had and one or more marks: Vietnamese, Latin with one or two marks above
  or a mark below, polytonic Greek, Cyrillic with breve, diaeresis or
  macron. 74 group nets, 4,280,128 bytes.
  [Card](weights/neuronte-term-latin-v1.md).
- `neuronte-term-math-v1`: 465 arrows and mathematical operators. 47 group
  nets, 2,686,120 bytes. [Card](weights/neuronte-term-math-v1.md).
- `neuronte-term-symbol-v1`: 480 punctuation marks, superscripts and
  subscripts, currency signs, letterlike symbols, number forms, technical
  symbols, enclosed digits and geometric shapes. 48 group nets, 2,743,740
  bytes. [Card](weights/neuronte-term-symbol-v1.md).
- `neuronte-term-dingbat-v1`: 323 Miscellaneous Symbols and Dingbats. 35
  group nets, 2,000,188 bytes. [Card](weights/neuronte-term-dingbat-v1.md).

**Most of these nets missed the limits declared for them before training.**
3 of the 74 letter groups passed, and 55 of the 130 symbol groups. The other
146 ship by the owner's choice after a side-by-side review of every group;
each card lists which groups missed and on which rule. In every group each
character is nearest its own drawing at every size counted, and none
vanishes.

Uncached, the new characters draw 2.7 to 3.1 times as fast as split-v9
drew them from its fallback net: 3.1 times for the letters, measured on a
rented AMD EPYC 7B13, and about 2.7 times for each symbol bundle, measured
on an i7-6820HQ and an i7-10700F. Each card has its table.

No drawing was made by reading a font file. The letters are composed by
code from the project's own strokes and marks; the symbols are the
project's own strokes in `font/term-math.txt`, `font/term-sym.txt` and
`font/term-ding.txt`, with families turned, mirrored, filled or negated by
`train/term_glyphs.py`. DejaVu was used only for its list of code points.

### Training and packing

- `train/standalone_bundle.py` packs group nets as a standalone bundle.
- `train/glyphs.py` composes a letter with several marks above, marks
  below and the Greek breathings; `font/marks.txt` has the new marks.

### Tests

- `tests/check_bundle_lists.py`: a listed bundle's table must be exactly
  its `weights/NAME.list.txt`, and no two listed bundles, nor a listed
  bundle and split-v9, may claim the same character.
- `test_api --standalone` checks a standalone bundle through a trained
  character.
- One test target for each new bundle, run by `make test`.

## 0.1.4

Every file of 0.1.3 is still here byte for byte and draws the same pixels
and advances. No default changes: `neuronte-split-v5` stays the terminal
font and the hand-drawn desktop faces stay the faces. The library's own
sha256 changes, so caches keyed by it are rebuilt once.

### New nets

- `neuronte-split-v9`: split-v8 with 165 more terminal characters on
  fourteen group nets: 113 symbols (check and cross marks, arrows, bullets
  and shapes, `± ≤ ≥ ≠`, currency, superscripts and fractions, math
  operators), 20 Greek letters with tonos and dialytika, and 32 Cyrillic
  letters beyond Russian. Every character split-v8 draws, and every
  character neither was trained on, draws exactly as in split-v8. The new
  characters draw about 4.6 times as fast as split-v8 drew them from its
  fallback. **Every new group missed the limits declared for it before
  training**; they ship by the owner's choice after a side-by-side review,
  and [the card](weights/neuronte-split-v9.md) says where each missed.
- `neuronte-ui-scaled-v0`: one desktop face for every size from 17 to
  32 px, the strokes of the large face with stems snapped to whole pixels,
  in a file of 1.8 MB. Italic is the same letters sheared as they are
  drawn, with `neuronte-ui-scaled-italic-advances-v0`. It is a different
  face from the hand-drawn ones for those sizes, not a copy: about a third
  of the advances differ, by at most 2 px.
  [Card](weights/neuronte-ui-scaled-v0.md).
- `neuronte-ui-large-v1`: the face above 32 px as four smaller nets, about
  13 times as fast the first time a size is used, with the advances of
  `neuronte-ui-large-v0`. **It missed the overlap limit declared for it**
  (at 32 px, and on its worst letter at 48 and 96 px) and ships by the
  owner's decision. [Card](weights/neuronte-ui-large-v1.md).
- `neuronte-ui-scaled-latin1-v0` and `neuronte-ui-large-latin1-v1`: the
  same two faces with the 58 accented letters from U+00C0 to U+00FF. Their
  ASCII letters are the ASCII-only files' exactly.

### Library

- A drawing file may carry a table of letter edges (format version 7);
  the library snaps those stems to whole pixels below the file's cell
  width, as it already did for colour glyphs. A file without the table
  draws as before. An older library refuses a file with one.
- `neuronte_untrained()` tells a program whether a bundle was trained on a
  character, and `neuronte_set_untrained()` makes the library draw a mark
  in place of an untrained one. It is off unless asked for: by default an
  untrained character is still drawn by whichever net the gate picks.

## 0.1.3

No weight file changed, and the code that runs the nets is unchanged: every
file draws the pixels and advances it drew in 0.1.2. The library's own
sha256 changes, so caches keyed by it are rebuilt once.

- **Packed text masks** (`src/bits.c`). `neuronte_bits_pack()` and
  `neuronte_alpha_pack()` turn drawn 32-bit pixels into 1-bit or 8-bit
  rows. `neuronte_bits_compose()` lays kept 1-bit letters into a line, bold
  or not, in one call. A program that draws the same small text over and
  over can keep each letter after the net has drawn it once and run no net
  after that. With them the Kilix 95 desktop draws a string in less time
  than DejaVu through FreeType at every size measured, from 8 to 48 px;
  laid from Python the same letters took 5 to 15 times as long. The
  measurements are in the
  [Neuronte 2 benchmarks](https://github.com/itsmygithubacct/neuronte-v2/blob/main/BENCHMARKS.md).
- `make test-bits` checks the three calls against a pixel loop.

## 0.1.2

0.1.1 is commit `4134bf9`, the Neuronte that Plebian OS 0.2.3 RC9 installs;
it was not tagged. Every weight file 0.1.1 shipped is still here byte for
byte, and this library draws each of them with exactly the pixels and
advances that 0.1.1's library draws (checked across the two builds,
including on the new AVX2 path). Consumers that bind a weight file by its
sha256 need no change; caches keyed by the library's sha256 are rebuilt
once.

### Defaults

- `neuronte-split-v5` stays the terminal font.
- The video player's full mode now draws with `neuronte-split-v6`:
  split-v5 with its Braille expert replaced by the tiled
  `neuronte-braille-v1`, every other expert, the gate and the ranges byte
  for byte split-v5. Its learned helpers stay bound to split-v5, so
  `--helper` without `--weights` still uses split-v5.
- The new complete bundles, split-v7 and split-v8, are not defaults.

### New nets

- `neuronte-split-v8`: split-v7 with three more sets of known-only group
  nets, for 49 symbols (`neuronte-symbol-v1`), 327 block, sextant and
  octant characters (`neuronte-pixel-groups-v1`) and 318 accented Latin,
  spacing-mark, Greek and Russian characters
  (`neuronte-accent-groups-v1`). Uncached coverage against split-v7 on two
  x86-64 CPUs is about 5.5 times as fast on the symbols, 2.1 times on the
  pixel characters and 1.95 times on the accent characters; ASCII and
  Braille draw exactly as split-v7. Opening costs 0.9 to 1.4 ms more than
  split-v7, once per process. The pixel and accent groups failed the strict
  gates declared before training and were selected by the owner after
  visual review; the card lists the regressions
  ([card](weights/neuronte-split-v8.md)).
- `neuronte-split-v7-symbol-v1`: split-v7 with the symbol groups only, all
  of whose gates passed in both seeds
  ([card](weights/neuronte-split-v7-symbol-v1.md)).
- Desktop faces `-v1`, 70 drawing files beside their unchanged `-v0`
  files. Both training seeds of every one reproduce all 96 glyphs, regular
  and bold, and the advances exactly at the native em. Times are for
  drawing the whole face once from a fresh handle, as a desktop does when
  it builds its letter cells, on two x86-64 CPUs:
  - ui24 to ui30 and four italics (nine files): 12 to 30 times as fast as
    v0 ([card](weights/neuronte-ui-v1.md)).
  - ui32, ui31 and three italics (five files): 6 to 18 times
    ([card](weights/neuronte-ui-wide-v1.md)).
  - ui33 to ui39 and ui43 (eight files): 32 to 48 times
    ([card](weights/neuronte-ui-v1-h512.md)).
  - ui1 to ui15, ui19 to ui21 and twelve italics (thirty files): 4 to 30
    times. These files are larger than their v0 files (most are 864,092
    bytes against 110,864), because each is a bundle of 32 or 96 small
    nets ([card](weights/neuronte-ui-v1-small.md)).
  - Eighteen faces whose v0 nets are 192 or 256 wide, as one narrower net
    each: 1.4 to 3.6 times ([card](weights/neuronte-ui-v1-192-256.md)).
  The installer and Kilix 95 still load the `-v0` files; using a `-v1`
  file means changing the consumer's weight path.
- `neuronte-emoji-v1`: the same 300 emoji, labels, palettes and half API
  as `neuronte-emoji-v0`, from twelve 192-wide experts over a
  difficulty-balanced partition in place of three 512-wide ones. It is
  4,785,292 bytes against 7,011,412. Both seeds pass v0's unchanged gates,
  and uncached drawing is about five times as fast as v0 on two x86-64
  CPUs. Overlap with the drawings is slightly lower than v0 at 12 and
  32 px and higher at 16 px. v0 is unchanged and stays the default
  ([card](weights/neuronte-emoji-v1.md)).
- Colour nets beside their unchanged 0.1.1 files, each passing the same
  gate as the file it follows in both seeds:
  - `neuronte-icon-v2`: the 167 icons as a bundle of four 96-wide nets of
    three layers; a cold draw is about four times as fast as
    `neuronte-icon-v1` and the file is 496,184 bytes instead of 650,216.
    It is less exact than icon-v1 at 12 px and equal at the 16 px bar
    ([card](weights/neuronte-icon-v2.md)).
  - `neuronte-flame-v1`: width 56 instead of 64, cold draw 10 to 17 per
    cent faster ([card](weights/neuronte-flame-v1.md)).
  - `neuronte-pointer-v1`: width 48 instead of 64, about 36 per cent
    faster ([card](weights/neuronte-pointer-v1.md)).
- `neuronte-split-v7`: split-v6 with the four ASCII character-group nets
  as known-only replacements for its ASCII expert. Pixels equal
  `neuronte-split-ascii-groups-v1` on ASCII and split-v6 on Braille.
  Uncached ASCII coverage is about 2.2 times as fast as split-v5 and
  split-v6 on two x86-64 CPUs and about 2.65 times on an ARM Cortex-A72;
  opening costs 0.1 to 0.3 ms more on x86-64 and about 1.1 ms more on the
  Cortex-A72, once per process ([card](weights/neuronte-split-v7.md)).
- `neuronte-braille-v1`: the 256 Braille patterns as one version 6 tiled
  net, 2 by 4 tiles, one 6-wide net of 637 parameters drawing every dot.
  `neuronte-split-v6` is split-v5 with it in place of `neuronte-braille-v0`
  ([card](weights/neuronte-braille-v1.md)).
- `neuronte-ascii-groups-v1` (four H64 character groups) and
  `neuronte-ascii-spatial-v1` (two H64 halves, a tiled net), with complete
  bundles `neuronte-split-ascii-groups-v1` and
  `neuronte-split-ascii-spatial-v1`. Both pass the declared quality limits
  in two seeds at 19 cell sizes ([card](weights/neuronte-ascii-next.md)).

### Library

- Tiled nets, format version 6: one monochrome net made of up to 64
  version 1 nets over up to 16 column and 16 row edges. A tiled net opens
  alone or as a bundle or drawing-file member.
- A bundle holds up to 128 nets (16 before). A drawing file still holds at
  most 16 members.
- A drawing file (version 5) may hold one bundle (version 2) as its only
  member with nets, plus its advance table; the bundle routes as it does
  alone. Drawing-file members may be tiled nets.
- Dense layers of hidden width 64, 128, 192 and 256 use an AVX2 kernel on
  CPUs that have it. It keeps the portable loop's accumulation order and
  ReLU behaviour, so the pixels are the same; other widths and CPUs keep
  the portable loop.
- The loader tests separate a valid width with an inconsistent payload
  (`NEURONTE_ERR_FORMAT`) from an unsupported width (`NEURONTE_ERR_SHAPE`).

### Training and packing

- `train/known_bundle.py` appends known-only replacements for one expert
  of a version 2 bundle and reassigns only their range-table entries. The
  original expert stays the gate's choice for everything else, so unknown
  characters draw as before, and successive replacements compose.
- `train/decompose.py` and `train/decompose_pack.py` train and pack
  decomposed experts (character groups, spatial tiles) in batches;
  `train/DECOMPOSITION.md` describes the recipes.
- `train/pack.py --drawing-bundle OUT FACE.txt NET.json...` packs a face
  as one bundle of nets with its advances; `train/face_parts.py` trains a
  face as character groups that draw only the face's em rows;
  `tests/check_reference.py --drawing-bundle` is the exact gate for such
  files.
- `tools/braille-tiled.py` assembles a tiled Braille expert from trained
  tile nets without changing any weight.

### Video

- The default pixels mode (`kilix video --neuronte`) draws each frame by
  copying decoded samples into their blocks once the player has checked
  that the masks' drawn ink map is the block layout. The bytes are the
  same as before and a frame draws 4.5 to 6.8 times as fast on two x86-64
  CPUs. Cells mode with the speed helper is about 1.18 times as fast, with
  identical output.
- No video weight changed. Narrower masks and narrower speed helpers were
  trained and failed their declared two-seed gates, so
  `neuronte-video-masks-v0` and the `-v1` helpers stay.
- Known limit: `neuronte-video-speed-v1`, the opt-in `--helper`, loses 0.18
  to 0.25 dB on newly generated held-out clips, above the 0.1 dB bar it
  passed on its original clips.
- Full mode accepts tiled monochrome experts.
- Playback checks time keys and deadlines from the frame, screen or log
  line they measure, keep one monotonic deadline, and fail a player that
  exits before a required milestone.

### Tests

- New make targets, all part of `make test`: `test-tiled`,
  `test-known-bundle`, `test-ascii-next`, `test-split-v7`,
  `test-symbol-v1`, `test-split-v7-symbol`, `test-split-v8`,
  `test-face-bundle`, `test-faces-v1`, `test-faces-v1-192-256`,
  `test-faces-wide-v1`, `test-faces-v1-h512`, `test-faces-v1-small`, `test-colour-marks`, `test-emoji-v1`.
