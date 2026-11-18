# Neuronte Sans Metric v1: the desktop faces at Helvetica's widths (`neuronte-metric-sans*-v1`)

Neuronte Sans Metric is a new face. Set in it, a line of text takes the same
width as in Helvetica, and so as in Arial, Liberation Sans and Arimo, which
share Helvetica's widths. Each character is redrawn to Helvetica's
proportions, and its strokes are this project's own.

Files:

- `neuronte-metric-sansN-v1.nrt`: the upright pixel face at every em N from 1 to 16 px.
- `neuronte-metric-sansN-italic-v1.nrt`: the italic at every em N from 3 to 16 px.
- `neuronte-metric-sans-large-v1.nrt` (33 px up) and `neuronte-metric-sans-scaled-v1.nrt` (17 to 32 px, snapped): see "The large and scaled faces" below.

Each covers the 192 characters of the desktop faces (printable ASCII,
U+2026 and U+00A0 to U+00FF), regular and bold. No existing file changes.
`neuronte-uiN-v2`, `neuronte-ui-scaled-latin1-v1` and
`neuronte-ui-large-latin1-v2` stay as they are.

## Where the widths come from

**The advances are copied from Adobe's AFM metric files for Helvetica.**
This is the one place in the project where widths are copied. Adobe's Core
14 AFM files, `Helvetica.afm` and `Helvetica-Bold.afm` (Version 002.000),
give each character's width, regular and bold, and its ink box in the
regular weight. They also give the font's cap height, x-height, ascender,
descender and stem width. Those numbers are in `font/metric-sans-widths.txt`
(made by `tools/make-metric-sans-widths.py`). The AFM files are not in this
repository. Adobe's notice is in `LICENSES/Adobe-Core14-AFM.txt`. The oblique
AFM files have the same widths, which the tool checks, so the italic faces
use the upright advances.

The statement "no font was read, and no width was copied", made for the
project's other faces, does not hold for this face. Its widths are copied
from the AFM files, as said here. No font file was opened to make it:

- **TeX Gyre Heros** (GUST Font License, LPPL 1.3c) was looked at, outside
  this repository, as a visual reference while the rules were chosen and the
  sheets were checked. Nothing was traced or copied from it, and no file of
  it is here.
- No other font was opened or rasterised.

Helvetica is a trademark of Linotype-Hell AG and/or its subsidiaries. No
face here is named Helvetica.

Each advance is held in thousandths of an em. The large and scaled faces
carry a version 8 table and the pixel faces a version 4 table at 100 units
per em. An advance of m thousandths is `(m * em + 500) / 1000` pixels.

At 1 and 2 px, Helvetica's width comes to 0 px for some characters: 51 at
1 px, and 4 at 2 px (`' i j l`). Those characters keep the least advance of
1 px, so their tables hold `ceil(500 / em)` thousandths. Every other advance
in every table is Helvetica's exact width.

## Line length

`tests/check_metric_pdf.py` takes a page that GNU groff 1.23 justified in
Helvetica and Helvetica-Bold (`tests/fixtures/metric-helvetica.pdf`). Nine
justified lines, at 9 and 11 pt, include Latin-1 letters. Their words, set
with these tables, plus groff's spaces, reach the line's end exactly: 0.0000
of 1/1000 em off, in the widths file, the large table and the 9, 12 and 16
px tables. The fixture names the standard fonts and embeds no font program,
and the test fails if it ever does.

On screen, `neuronte_draw_text()` rounds each character's advance to a whole
pixel by itself. Over a line that adds up: on four sample lines the length
changes by -5.3% to +4.2% at 6 to 10 px, by -2.2% to +1.9% at 11 to 16 px,
and by less than 1% from 20 px up. Any whole-pixel pen does this.

`neuronte_draw_text_exact()` keeps the pen in thousandths and puts each
letter at the nearest pixel of its true position, so a line ends within
half a pixel of Helvetica's length at any size. There is no exact form of
the stroke call. Text that must be exact in bold uses the packed bold
(`bold` = 1).

## The pixel faces, 1 to 16 px

Each face is redrawn by `tools/make-metric-sans-face.py` from the desktop
face of the same em, `font/ui-N-latin1.txt`:

- **Rows are kept.** Each face keeps the heights it was drawn with:
  baseline, x-height, cap height and marks. These are not Helvetica's
  heights. At 16 px and below, rows are the face's own.
- **Columns are resampled** to the AFM ink box's width at that em, row by
  row:
  - a stem stays one column wide;
  - bars and bowls grow or shrink;
  - a diagonal is kept connected.
- **Placement.** The ink starts where Helvetica's box starts. Every letter
  keeps at least one clear column inside its advance, so neighbouring
  letters never touch. No pixel face needs a shift.
- **Composed letters.** The letters with marks are composed from these by
  the rules of `tools/make-latin1-face.py`.
- **Hand drawings.** `*` (10 to 15 px) and `« »` (10 to 15 px) are drawn by
  hand, in `font/metric-sans-fixes.txt`. The rules shrank the asterisk, and
  the chevrons touched.
- **Italics** are `tools/make-italic.py`'s shear of the upright face.
- **Bold** is the letter struck twice, one pixel apart, as in every desktop
  face. The bold advance is Helvetica-Bold's.

### Characters that look the same

Helvetica is narrower than the desktop faces: on average 70.5/1000 em
narrower, and 167 of the 192 characters are narrower. At small sizes that
leaves fewer columns, so more characters share a bitmap.

Characters whose pixels are the same as another character's (advance
ignored), today's face -> this face:

| em | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9-10 | 11 | 12-16 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| today | 192 | 191 | 158 | 117 | 97 | 80 | 27 | 2 | 8 | 8 | 4 |
| metric | 192 | 192 | 186 | 176 | 131 | 92 | 41 | 27 | 8 | 6 | 4 |

At 8 px and below, the metric face is harder to read than today's face. At
9 px and up the two are the same by this count. At 12 px and up only U+00A0
and the space share a bitmap, and so do SHY and the hyphen.

### Accuracy

Gate G-MP, declared before training, is exact. Every character, regular and
bold, drawn alone by the library in binary mode at the face's em, must be
exactly its drawing. The pen must move by the table's advance. A line of
all 192 characters must be those drawings side by side.

Two checks were run, on both seeds:

- `tests/check_reference.py`: the router, every net against numpy, and
  every letter exact, on a pack with the pixel face as its table;
- `tests/check_metric_sans.py`: the shipped file with its thousandths table.

| face | seed 0 | seed 1 | ships |
|---|---|---|---|
| 1-13 px, upright and italic | exact | exact | seed 0 |
| 14 px italic | Ó off by 1-2 px | exact | **seed 1** |
| 15 px italic | exact | Â off by 1 px | seed 0 |
| 16 px italic | Ò off by 1 px | exact | **seed 1** |
| 14-16 px upright | exact | exact | seed 0 |

No group was halved. All 30 faces, as shipped, were checked again on a
second machine: every one is exact.

## Training

- Per-em faces 3 to 16 px:
  `train/face_parts.py --set uiNms[i] --band --groups 48 --width 32 --steps 80000 --seeds 0,1`.
  These are 48 band-tiled nets of 4 characters, 32 wide.
- 1 and 2 px: `--groups 2 --width 16`. 1 px uses `--pen 0.49`, because the
  trainer refuses a pen of 0.5 cell or more.
- Hardware: 4 rented RTX 4090s, about 12 minutes per face (22 minutes at 1
  and 2 px), all 30 faces at once.
- Packing:
  `train/pack.py --drawing-bundle neuronte-metric-sansN[-italic]-v1.nrt font/metric-sans-N.advances.txt MEMBERS...`.
  Each packed file was checked byte for byte against the one gated on the
  rental.
- Members: `neuronte-metric-sansN[-italic]-v1-gG.json` for seed 0 and
  `.seed1-gG.json` for seed 1. Where seed 1 ships, the file is packed from
  the `.seed1` members.
- Sizes: 1,016,948 bytes for each face from 3 to 16 px. The 1 and 2 px
  faces are 19,596 and 19,636 bytes.

## Caller notes

- A **negative shift** moves a letter's drawing left of its pen. In the
  large and scaled faces, 12 characters have one: `" / \ ^ j © ® ¯ Î Ï î ï`.
  On the first letter of a line, that ink lands left of `x`, and a caller
  whose buffer is exactly the measured width clips it. Leave a margin of
  0.07 em on the left, or start the line at `x` of 0.07 em or more.
- `neuronte_bits_compose()` has no shift yet. A face with shifts placed
  through it draws those 12 letters up to 0.07 em to the right of where they
  belong.
- A font file made from this face must take its advances from
  `neuronte_advance_milli()`, not from the hundredths, or its widths will not
  match Helvetica's.

## The large and scaled faces

Not in this release of the card. The large and scaled files are trained, and they pass the library checks. Their accuracy gate is waiting on the owner's decision. Until they ship, the 12 shifted characters listed under caller notes apply to them only.
