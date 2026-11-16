# Changes

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
