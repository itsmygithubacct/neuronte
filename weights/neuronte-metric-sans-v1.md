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

## Speed

A new handle draws a line regular then bold, as a desktop builds its cells.
Figures are the median of 5 fresh handles, single thread, under the
benchmark lock. Each figure is today's face -> this face:

- pixel faces: against `neuronte-uiN-v2`;
- scaled: against `neuronte-ui-scaled-latin1-v1`;
- large: against `neuronte-ui-large-latin1-v2`.

First use is in milliseconds. Cached is the two lines drawn again on the
same handle, in microseconds. ASCII is the line of 96 ASCII characters, and
Latin-1 the line of U+00A0 to U+00FF.

### Intel i7-10700F

| em | face | ASCII first use | ASCII cached | Latin-1 first use | Latin-1 cached |
|---|---|---|---|---|---|
| 16 | metric-sans16 | 151.83 -> 23.38 | 273.1 -> 281.2 | 23.66 -> 23.93 | 276.1 -> 278.0 |
| 16 | metric-sans16-italic | 169.65 -> 24.55 | 280.3 -> 282.3 | 24.34 -> 25.05 | 283.0 -> 283.3 |
| 15 | metric-sans15 | 13.66 -> 21.29 | 251.0 -> 250.5 | 21.54 -> 21.62 | 247.3 -> 247.7 |
| 15 | metric-sans15-italic | 10.90 -> 21.74 | 255.2 -> 255.3 | 21.81 -> 21.81 | 251.9 -> 251.3 |
| 14 | metric-sans14 | 9.41 -> 18.34 | 221.4 -> 221.5 | 18.70 -> 19.13 | 222.5 -> 224.2 |
| 14 | metric-sans14-italic | 9.80 -> 19.46 | 230.4 -> 231.1 | 19.45 -> 19.82 | 226.5 -> 231.6 |
| 13 | metric-sans13 | 8.57 -> 16.50 | 203.6 -> 197.9 | 16.61 -> 16.89 | 199.7 -> 197.0 |
| 13 | metric-sans13-italic | 119.44 -> 16.55 | 195.0 -> 199.8 | 17.19 -> 17.28 | 195.9 -> 199.5 |
| 12 | metric-sans12 | 9.39 -> 14.17 | 183.4 -> 178.4 | 14.41 -> 15.02 | 176.2 -> 181.3 |
| 12 | metric-sans12-italic | 9.47 -> 14.59 | 187.9 -> 182.5 | 15.22 -> 15.29 | 183.0 -> 181.9 |
| 11 | metric-sans11 | 6.28 -> 12.52 | 158.4 -> 155.3 | 12.51 -> 12.85 | 158.1 -> 158.2 |
| 11 | metric-sans11-italic | 6.51 -> 12.87 | 163.9 -> 159.5 | 13.04 -> 12.83 | 161.1 -> 160.4 |
| 10 | metric-sans10 | 5.40 -> 10.64 | 140.3 -> 135.6 | 10.55 -> 10.86 | 138.1 -> 138.9 |
| 10 | metric-sans10-italic | 5.53 -> 10.95 | 144.4 -> 138.5 | 11.04 -> 10.96 | 141.0 -> 141.0 |
| 9 | metric-sans9 | 7.07 -> 13.60 | 203.3 -> 197.3 | 13.59 -> 9.02 | 204.1 -> 118.2 |
| 9 | metric-sans9-italic | 4.58 -> 9.11 | 124.0 -> 118.5 | 9.19 -> 9.08 | 121.9 -> 120.6 |
| 8 | metric-sans8 | 6.07 -> 10.88 | 179.2 -> 172.2 | 11.10 -> 11.05 | 181.0 -> 176.8 |
| 8 | metric-sans8-italic | 6.03 -> 11.24 | 181.6 -> 175.6 | 11.45 -> 11.32 | 181.8 -> 178.0 |
| 7 | metric-sans7 | 4.85 -> 8.77 | 141.6 -> 140.0 | 9.07 -> 9.00 | 148.7 -> 148.3 |
| 7 | metric-sans7-italic | 4.79 -> 9.01 | 151.3 -> 142.5 | 9.22 -> 9.18 | 153.7 -> 148.5 |
| 6 | metric-sans6 | 3.75 -> 6.65 | 119.6 -> 107.2 | 5.06 -> 6.96 | 120.3 -> 116.6 |
| 6 | metric-sans6-italic | 3.71 -> 6.84 | 117.5 -> 112.9 | 7.19 -> 6.99 | 121.8 -> 116.7 |
| 5 | metric-sans5 | 2.90 -> 5.01 | 92.6 -> 88.8 | 5.15 -> 5.07 | 98.7 -> 92.5 |
| 5 | metric-sans5-italic | 2.85 -> 5.14 | 98.4 -> 88.6 | 5.23 -> 5.17 | 96.6 -> 93.2 |
| 4 | metric-sans4 | 2.12 -> 3.32 | 90.9 -> 73.9 | 3.65 -> 3.41 | 88.2 -> 71.5 |
| 4 | metric-sans4-italic | 2.15 -> 3.69 | 86.5 -> 77.2 | 3.50 -> 3.41 | 76.1 -> 69.7 |
| 3 | metric-sans3 | 1.46 -> 2.01 | 65.5 -> 49.0 | 2.50 -> 2.47 | 71.7 -> 64.2 |
| 3 | metric-sans3-italic | 1.48 -> 2.17 | 68.3 -> 51.5 | 2.48 -> 2.49 | 71.4 -> 62.4 |
| 2 | metric-sans2 | 0.73 -> 0.69 | 42.5 -> 36.0 | 0.74 -> 0.69 | 42.1 -> 40.6 |
| 1 | metric-sans1 | 0.22 -> 0.39 | 15.2 -> 26.3 | 0.38 -> 0.38 | 28.5 -> 27.7 |
| 17 | metric-sans-scaled | 96.87 -> 119.00 | 332.5 -> 340.6 | 133.68 -> 114.76 | 337.6 -> 347.4 |
| 24 | metric-sans-scaled | 51.97 -> 61.20 | 636.9 -> 661.6 | 68.23 -> 58.78 | 653.7 -> 669.3 |
| 32 | metric-sans-scaled | 88.80 -> 114.04 | 1075.9 -> 1096.2 | 108.12 -> 119.12 | 1095.7 -> 1121.0 |
| 33 | metric-sans-large | 122.93 -> 121.23 | 1131.0 -> 1162.9 | 128.79 -> 112.19 | 1155.0 -> 1179.2 |
| 48 | metric-sans-large | 254.67 -> 246.87 | 2305.4 -> 2324.4 | 232.52 -> 233.12 | 2315.0 -> 2384.1 |
| 64 | metric-sans-large | 490.51 -> 426.06 | 4152.4 -> 3955.3 | 464.84 -> 407.81 | 3976.5 -> 4111.2 |

### Intel i7-6820HQ

Measured on 2026-11-18 from 11:31 to 11:32 UTC, on a fresh Debian 13 install
(with Kilix 0.2.3, kernel 6.12.117+deb13-amd64), before that machine's NVIDIA driver was installed and it
rebooted at 13:50 UTC. The run is single-thread CPU only, so the driver does
not enter it. The figures earlier lanes recorded on this machine were taken
on its previous install.

| em | face | ASCII first use | ASCII cached | Latin-1 first use | Latin-1 cached |
|---|---|---|---|---|---|
| 16 | metric-sans16 | 205.96 -> 32.14 | 387.8 -> 400.2 | 32.25 -> 33.06 | 392.5 -> 403.6 |
| 16 | metric-sans16-italic | 233.27 -> 35.18 | 409.7 -> 422.1 | 33.45 -> 34.09 | 400.5 -> 409.5 |
| 15 | metric-sans15 | 18.69 -> 29.05 | 355.7 -> 357.2 | 31.01 -> 30.06 | 366.3 -> 359.2 |
| 15 | metric-sans15-italic | 14.81 -> 29.42 | 362.6 -> 362.2 | 30.22 -> 29.75 | 356.9 -> 373.8 |
| 14 | metric-sans14 | 13.21 -> 25.46 | 320.7 -> 319.7 | 25.98 -> 26.16 | 316.3 -> 331.4 |
| 14 | metric-sans14-italic | 14.47 -> 26.62 | 354.7 -> 326.3 | 27.03 -> 27.00 | 322.4 -> 327.2 |
| 13 | metric-sans13 | 12.40 -> 22.86 | 291.7 -> 284.0 | 22.76 -> 24.87 | 285.6 -> 298.5 |
| 13 | metric-sans13-italic | 163.49 -> 23.69 | 286.9 -> 302.1 | 23.94 -> 23.99 | 288.8 -> 292.0 |
| 12 | metric-sans12 | 12.96 -> 19.81 | 259.9 -> 252.4 | 19.86 -> 20.19 | 255.7 -> 263.7 |
| 12 | metric-sans12-italic | 13.63 -> 19.88 | 275.2 -> 260.0 | 20.76 -> 20.75 | 261.3 -> 260.2 |
| 11 | metric-sans11 | 8.69 -> 17.17 | 225.8 -> 220.5 | 17.23 -> 18.46 | 225.0 -> 231.9 |
| 11 | metric-sans11-italic | 9.76 -> 17.56 | 251.4 -> 226.9 | 18.02 -> 17.63 | 232.0 -> 229.6 |
| 10 | metric-sans10 | 7.56 -> 15.91 | 202.7 -> 197.8 | 14.50 -> 16.33 | 196.6 -> 207.6 |
| 10 | metric-sans10-italic | 7.66 -> 15.06 | 203.9 -> 197.4 | 15.46 -> 15.04 | 202.6 -> 200.8 |
| 9 | metric-sans9 | 6.14 -> 12.33 | 174.6 -> 164.3 | 12.17 -> 12.32 | 171.1 -> 168.5 |
| 9 | metric-sans9-italic | 6.40 -> 12.51 | 183.8 -> 168.5 | 12.76 -> 12.42 | 175.1 -> 171.9 |
| 8 | metric-sans8 | 5.47 -> 9.89 | 158.1 -> 145.4 | 10.20 -> 10.17 | 154.3 -> 154.1 |
| 8 | metric-sans8-italic | 5.80 -> 10.33 | 164.0 -> 151.8 | 10.66 -> 10.50 | 156.0 -> 152.7 |
| 7 | metric-sans7 | 4.30 -> 8.04 | 120.9 -> 118.3 | 8.45 -> 8.46 | 127.1 -> 127.7 |
| 7 | metric-sans7-italic | 4.26 -> 8.41 | 132.6 -> 121.9 | 8.64 -> 8.59 | 131.9 -> 125.9 |
| 6 | metric-sans6 | 3.31 -> 6.73 | 99.7 -> 94.3 | 6.69 -> 6.53 | 103.0 -> 99.3 |
| 6 | metric-sans6-italic | 3.37 -> 6.45 | 98.9 -> 91.9 | 6.67 -> 6.48 | 101.2 -> 97.7 |
| 5 | metric-sans5 | 2.57 -> 4.60 | 77.7 -> 74.1 | 4.76 -> 4.67 | 80.7 -> 76.8 |
| 5 | metric-sans5-italic | 2.59 -> 4.89 | 84.5 -> 74.3 | 4.88 -> 5.05 | 82.2 -> 80.0 |
| 4 | metric-sans4 | 1.72 -> 2.98 | 68.8 -> 54.6 | 3.47 -> 3.12 | 71.9 -> 58.4 |
| 4 | metric-sans4-italic | 1.88 -> 3.15 | 63.3 -> 54.3 | 3.43 -> 3.18 | 68.4 -> 58.0 |
| 3 | metric-sans3 | 1.22 -> 1.89 | 52.2 -> 42.6 | 2.36 -> 2.34 | 53.0 -> 46.3 |
| 3 | metric-sans3-italic | 1.23 -> 1.96 | 50.0 -> 41.7 | 2.38 -> 2.40 | 53.2 -> 46.2 |
| 2 | metric-sans2 | 0.62 -> 0.56 | 32.3 -> 29.7 | 0.61 -> 0.55 | 33.5 -> 30.3 |
| 1 | metric-sans1 | 0.33 -> 0.33 | 21.3 -> 21.6 | 0.29 -> 0.30 | 22.6 -> 23.1 |
| 17 | metric-sans-scaled | 135.20 -> 158.77 | 469.9 -> 480.6 | 181.17 -> 155.39 | 488.3 -> 491.2 |
| 24 | metric-sans-scaled | 71.28 -> 84.96 | 900.7 -> 922.0 | 90.80 -> 79.78 | 948.2 -> 943.0 |
| 32 | metric-sans-scaled | 122.89 -> 153.27 | 1535.1 -> 1539.3 | 144.56 -> 165.55 | 1534.8 -> 1573.0 |
| 33 | metric-sans-large | 165.32 -> 157.43 | 1586.4 -> 1613.7 | 173.78 -> 151.16 | 1622.9 -> 1681.6 |
| 48 | metric-sans-large | 335.37 -> 322.89 | 3150.4 -> 3200.2 | 315.36 -> 320.44 | 3214.1 -> 3333.1 |
| 64 | metric-sans-large | 683.78 -> 584.12 | 5494.8 -> 5576.9 | 640.73 -> 552.36 | 5608.1 -> 5653.2 |

On both machines:

- **Pixel faces.** Every metric face draws all 192 characters with one kind
  of net, 48 of them for 4 characters each. Today's faces keep the older
  nets for ASCII.
  - So a metric face's ASCII line costs about what its Latin-1 line does:
    1.5 to 2 times today's ASCII line at 3 to 15 px.
  - Where today's ASCII is one large net (ui16, ui16-italic, ui13-italic),
    the metric face is 5 to 7 times faster.
  - The Latin-1 line and cached redraws are at most 5% slower than today's.
    At 9 px and below, cached redraws are faster, by up to 21%.
- **Scaled face.**
  - ASCII first use is 17% to 29% slower than today's.
  - Latin-1 first use is 12% to 14% faster at 17 and 24 px, and 10% to 15%
    slower at 32 px.
  - Cached redraws are within 4%.
- **Large face.**
  - ASCII first use is 1% to 15% faster.
  - Latin-1 first use is 13% to 14% faster at 33 and 64 px, and within 2% at
    48 px.
  - Cached redraws are within 5%.

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

**These two files FAILED their accuracy gate, G-M1, as it was declared.
They ship by the owner's ruling of 2026-11-18, on a revised measurement
chosen after the results were known. Read this section before you rely on
them.**

- `neuronte-metric-sans-large-v1.nrt`: the face from 33 px up, drawn
  blended. 4,418,804 bytes.
- `neuronte-metric-sans-scaled-v1.nrt`: the same nets with letter edges
  (`--letter-edges uilargems --snap-below 33`), for 17 to 32 px. 4,423,128
  bytes.
- Both carry a version 8 table: Helvetica's advances in thousandths, and a
  shift for 12 characters whose ink would otherwise start left of the pen
  or cross the advance (`" / \ ^ j © ® ¯ Î Ï î ï`, -0.062 to +0.028 em). A shift moves the drawing, not the pen.

### The drawings

`train/metric_sans.py` redraws the strokes of the large desktop face
(`font/ui-large.txt`, its Latin-1 signs and composed letters) to Helvetica's
proportions:

- **Heights.** The x-height, cap height and descender move to the AFM's.
  Unlike the pixel faces, this face takes Helvetica's heights. Ascenders stay
  at the top of the cell's ink band: 0.75 em, against Helvetica's 0.718.
- **Widths.** Each letter is moved and scaled across so that its ink spans
  the AFM box. The pen is not scaled, so stems keep the face's weight (3/32
  em, against the AFM's 88/1000).
- **Composed letters** are composed again from the new letters.
- **Bold** is the packed bold, as in the other large faces.

### Gate G-M1, as declared: FAILED

G-M1 was declared before training. Per net, at 48, 64 and 96 px, the IoU of
the net's coverage (1 sample per pixel) against the exact strokes sampled 8 x
8 per pixel and cut at 1/2 must have mean >= 0.98 and min >= 0.90.

- **8 of the 12 groups failed, on both seeds.**
- As the Method says, the failing groups were halved once (24 groups, both
  seeds). **13 of the 16 halves still failed, with the same minima.**
  Halving changed nothing.
- Worst letters: I and | at 48 px (0.809), ¦ (0.827), T (0.843) and F
  (0.857) at 64 px.

### Why, and what the owner ruled

Helvetica's box edges are in thousandths of an em. At 48, 64 and 96 px many
of them fall within 1/16 px of a pixel centre. There, the 8 x 8 reference
rounds a whole column of a stem or a bar to one side, and a drawing sampled
once per pixel rounds it to the other. That is not an error in the net.

The exact strokes themselves, sampled once per pixel, score the same as the
nets against that reference: the "ceiling" column. On I at 48 px both are
0.809. The project's other large faces have no such edges and score about
1.0 on the same letters.

The owner ruled, on 2026-11-18, that these files ship gated instead on the
**net against its own strokes, both sampled once per pixel**, at the same
bar (mean >= 0.98, min >= 0.90 at 48, 64 and 96 px). The ruling had one
condition, checked group by group: wherever G-M1 failed, the ceiling had to
fail the same way, minimum below 0.90. It does in every failing group, on
both seeds. In one case the gate failed on its mean as well and the ceiling
did not: group 7 seed 0 at 48 px, gate mean 0.9793, ceiling mean 0.9802 (its
min is 0.893, below the bar). That seed does not ship for group 7 (see the
table).

This is not a pass of G-M1. It is the owner's ruling on a measurement chosen
after the results.

Shipped groups, the range of each group's mean / the lowest min:

| em | G-M1 as declared | ceiling (exact strokes) | net vs strokes, the ruled gate |
|---|---|---|---|
| 48 | 0.9703-0.9940 / 0.809 (7 groups fail) | 0.9707-0.9932 / 0.809 | 0.9975-0.9995 / 0.971 |
| 64 | 0.9731-0.9967 / 0.844 (5 groups fail) | 0.9713-0.9969 / 0.843 | 0.9925-0.9993 / 0.979 |
| 96 | 0.9854-0.9984 / 0.902 | 0.9852-0.9985 / 0.902 | 0.9975-0.9992 / 0.986 |

Beside them, the Latin-1 large face's two newest nets scored, under G-L1, the
same declared measure: 0.9894 to 0.9961 mean, 0.903 to 0.989 min
(`neuronte-ui-latin1-signs-v0.md`).

Every group, seed and em:

| group | seed | em | G-M1 as declared (mean / min) | ceiling: exact strokes at 1 sample per pixel (mean / min) | net vs strokes (mean / min) | ships |
|---|---|---|---|---|---|---|
| 0 | 0 | 48 | 0.9878 / 0.9552 (*) pass | 0.9876 / 0.9509 (*) | 0.9976 / 0.9800 ($) |  |
| 0 | 0 | 64 | 0.9871 / 0.9379 (+) pass | 0.9862 / 0.9379 (+) | 0.9980 / 0.9863 (') |  |
| 0 | 0 | 96 | 0.9951 / 0.9546 (+) pass | 0.9950 / 0.9546 (+) | 0.9990 / 0.9950 (,) |  |
| 0 | 1 | 48 | 0.9871 / 0.9552 (*) pass | 0.9876 / 0.9509 (*) | 0.9975 / 0.9714 ($) | yes |
| 0 | 1 | 64 | 0.9865 / 0.9379 (+) pass | 0.9862 / 0.9379 (+) | 0.9989 / 0.9943 (() | yes |
| 0 | 1 | 96 | 0.9949 / 0.9534 (+) pass | 0.9950 / 0.9546 (+) | 0.9989 / 0.9961 (/) | yes |
| 1 | 0 | 48 | 0.9920 / 0.9737 (;) pass | 0.9932 / 0.9832 (9) | 0.9984 / 0.9868 (;) |  |
| 1 | 0 | 64 | 0.9852 / 0.9357 (7) pass | 0.9854 / 0.9357 (7) | 0.9983 / 0.9936 (3) |  |
| 1 | 0 | 96 | 0.9938 / 0.9287 (1) pass | 0.9940 / 0.9298 (1) | 0.9987 / 0.9967 (;) |  |
| 1 | 1 | 48 | 0.9928 / 0.9832 (9) pass | 0.9932 / 0.9832 (9) | 0.9989 / 0.9953 (<) | yes |
| 1 | 1 | 64 | 0.9855 / 0.9378 (7) pass | 0.9854 / 0.9357 (7) | 0.9991 / 0.9962 (8) | yes |
| 1 | 1 | 96 | 0.9937 / 0.9298 (1) pass | 0.9940 / 0.9298 (1) | 0.9987 / 0.9951 (:) | yes |
| 2 | 0 | 48 | 0.9738 / 0.8090 (I) **fail** | 0.9738 / 0.8090 (I) | 0.9980 / 0.9909 (O) | yes |
| 2 | 0 | 64 | 0.9740 / 0.8556 (F) **fail** | 0.9741 / 0.8571 (F) | 0.9970 / 0.9788 (E) | yes |
| 2 | 0 | 96 | 0.9984 / 0.9943 (@) pass | 0.9985 / 0.9947 (@) | 0.9992 / 0.9978 (J) | yes |
| 2 | 1 | 48 | 0.9733 / 0.8090 (I) **fail** | 0.9738 / 0.8090 (I) | 0.9982 / 0.9932 (G) |  |
| 2 | 1 | 64 | 0.9739 / 0.8556 (F) **fail** | 0.9741 / 0.8571 (F) | 0.9963 / 0.9736 (F) |  |
| 2 | 1 | 96 | 0.9984 / 0.9958 (@) pass | 0.9985 / 0.9947 (@) | 0.9993 / 0.9978 (J) |  |
| 3 | 0 | 48 | 0.9877 / 0.8661 ([) **fail** | 0.9876 / 0.8661 ([) | 0.9985 / 0.9946 (U) |  |
| 3 | 0 | 64 | 0.9713 / 0.8450 (T) **fail** | 0.9713 / 0.8429 (T) | 0.9965 / 0.9726 (P) |  |
| 3 | 0 | 96 | 0.9881 / 0.9024 (_) pass | 0.9882 / 0.9024 (_) | 0.9984 / 0.9954 (Y) |  |
| 3 | 1 | 48 | 0.9881 / 0.8661 ([) **fail** | 0.9876 / 0.8661 ([) | 0.9988 / 0.9940 (Q) | yes |
| 3 | 1 | 64 | 0.9731 / 0.8450 (T) **fail** | 0.9713 / 0.8429 (T) | 0.9965 / 0.9846 (P) | yes |
| 3 | 1 | 96 | 0.9879 / 0.9024 (_) pass | 0.9882 / 0.9024 (_) | 0.9987 / 0.9954 (Y) | yes |
| 4 | 0 | 48 | 0.9921 / 0.9695 (d) pass | 0.9918 / 0.9671 (d) | 0.9989 / 0.9946 (a) |  |
| 4 | 0 | 64 | 0.9971 / 0.9872 (`) pass | 0.9969 / 0.9872 (`) | 0.9987 / 0.9952 (c) |  |
| 4 | 0 | 96 | 0.9961 / 0.9773 (m) pass | 0.9961 / 0.9784 (m) | 0.9992 / 0.9979 (c) |  |
| 4 | 1 | 48 | 0.9920 / 0.9671 (d) pass | 0.9918 / 0.9671 (d) | 0.9995 / 0.9971 (h) | yes |
| 4 | 1 | 64 | 0.9966 / 0.9872 (`) pass | 0.9969 / 0.9872 (`) | 0.9993 / 0.9970 (j) | yes |
| 4 | 1 | 96 | 0.9961 / 0.9784 (m) pass | 0.9961 / 0.9784 (m) | 0.9989 / 0.9969 (e) | yes |
| 5 | 0 | 48 | 0.9841 / 0.8117 (\|) **fail** | 0.9842 / 0.8117 (\|) | 0.9990 / 0.9926 (x) |  |
| 5 | 0 | 64 | 0.9945 / 0.9843 (~) pass | 0.9944 / 0.9803 (~) | 0.9985 / 0.9959 (u) |  |
| 5 | 0 | 96 | 0.9856 / 0.9436 ({) pass | 0.9852 / 0.9425 (t) | 0.9986 / 0.9947 (s) |  |
| 5 | 1 | 48 | 0.9842 / 0.8117 (\|) **fail** | 0.9842 / 0.8117 (\|) | 0.9995 / 0.9963 (x) | yes |
| 5 | 1 | 64 | 0.9945 / 0.9803 (~) pass | 0.9944 / 0.9803 (~) | 0.9992 / 0.9954 (p) | yes |
| 5 | 1 | 96 | 0.9854 / 0.9412 (t) pass | 0.9852 / 0.9425 (t) | 0.9980 / 0.9956 (s) | yes |
| 6 | 0 | 48 | 0.9781 / 0.8267 (¦) **fail** | 0.9773 / 0.8267 (¦) | 0.9975 / 0.9880 (¯) |  |
| 6 | 0 | 64 | 0.9817 / 0.9048 (¬) pass | 0.9822 / 0.9048 (¬) | 0.9988 / 0.9921 (¢) |  |
| 6 | 0 | 96 | 0.9883 / 0.9127 (¡) pass | 0.9886 / 0.9109 (¡) | 0.9985 / 0.9934 (ª) |  |
| 6 | 1 | 48 | 0.9775 / 0.8267 (¦) **fail** | 0.9773 / 0.8267 (¦) | 0.9989 / 0.9933 (¬) | yes |
| 6 | 1 | 64 | 0.9825 / 0.9048 (¬) pass | 0.9822 / 0.9048 (¬) | 0.9989 / 0.9950 (¤) | yes |
| 6 | 1 | 96 | 0.9886 / 0.9073 (¡) pass | 0.9886 / 0.9109 (¡) | 0.9976 / 0.9882 (¡) | yes |
| 7 | 0 | 48 | 0.9793 / 0.8929 (·) **fail** | 0.9802 / 0.8929 (·) | 0.9987 / 0.9878 (¹) | yes |
| 7 | 0 | 64 | 0.9820 / 0.8443 (¹) **fail** | 0.9811 / 0.8443 (¹) | 0.9977 / 0.9841 (À) | yes |
| 7 | 0 | 96 | 0.9922 / 0.9659 (µ) pass | 0.9923 / 0.9651 (µ) | 0.9982 / 0.9936 (º) | yes |
| 7 | 1 | 48 | 0.9803 / 0.8929 (·) **fail** | 0.9802 / 0.8929 (·) | 0.9981 / 0.9878 (¹) |  |
| 7 | 1 | 64 | 0.9813 / 0.8443 (¹) **fail** | 0.9811 / 0.8443 (¹) | 0.9978 / 0.9793 (À) |  |
| 7 | 1 | 96 | 0.9914 / 0.9629 (µ) pass | 0.9923 / 0.9651 (µ) | 0.9983 / 0.9947 (´) |  |
| 8 | 0 | 48 | 0.9703 / 0.8588 (Ì) **fail** | 0.9707 / 0.8588 (Ì) | 0.9992 / 0.9932 (Ï) | yes |
| 8 | 0 | 64 | 0.9777 / 0.9489 (Æ) **fail** | 0.9766 / 0.9480 (Æ) | 0.9925 / 0.9861 (Ã) | yes |
| 8 | 0 | 96 | 0.9978 / 0.9940 (Ç) pass | 0.9976 / 0.9946 (Ç) | 0.9990 / 0.9974 (Å) | yes |
| 8 | 1 | 48 | 0.9708 / 0.8588 (Ì) **fail** | 0.9707 / 0.8588 (Ì) | 0.9987 / 0.9905 (Î) |  |
| 8 | 1 | 64 | 0.9771 / 0.9480 (Æ) **fail** | 0.9766 / 0.9480 (Æ) | 0.9900 / 0.9764 (È) |  |
| 8 | 1 | 96 | 0.9974 / 0.9935 (Å) pass | 0.9976 / 0.9946 (Ç) | 0.9992 / 0.9974 (Å) |  |
| 9 | 0 | 48 | 0.9939 / 0.9881 (à) pass | 0.9932 / 0.9880 (Ü) | 0.9979 / 0.9941 (Ú) | yes |
| 9 | 0 | 64 | 0.9924 / 0.9494 (Þ) pass | 0.9926 / 0.9495 (Þ) | 0.9972 / 0.9788 (Þ) | yes |
| 9 | 0 | 96 | 0.9958 / 0.9749 (Ý) pass | 0.9958 / 0.9749 (Ý) | 0.9985 / 0.9963 (Ý) | yes |
| 9 | 1 | 48 | 0.9939 / 0.9904 (Ò) pass | 0.9932 / 0.9880 (Ü) | 0.9977 / 0.9935 (Õ) |  |
| 9 | 1 | 64 | 0.9913 / 0.9336 (Þ) pass | 0.9926 / 0.9495 (Þ) | 0.9965 / 0.9656 (Þ) |  |
| 9 | 1 | 96 | 0.9957 / 0.9739 (Ý) pass | 0.9958 / 0.9749 (Ý) | 0.9986 / 0.9969 (×) |  |
| 10 | 0 | 48 | 0.9862 / 0.8910 (î) **fail** | 0.9860 / 0.8910 (î) | 0.9977 / 0.9903 (ç) | yes |
| 10 | 0 | 64 | 0.9967 / 0.9899 (ï) pass | 0.9965 / 0.9899 (ï) | 0.9993 / 0.9973 (á) | yes |
| 10 | 0 | 96 | 0.9966 / 0.9938 (ë) pass | 0.9969 / 0.9932 (ë) | 0.9987 / 0.9970 (ì) | yes |
| 10 | 1 | 48 | 0.9876 / 0.8910 (î) **fail** | 0.9860 / 0.8910 (î) | 0.9972 / 0.9920 (è) |  |
| 10 | 1 | 64 | 0.9969 / 0.9899 (ï) pass | 0.9965 / 0.9899 (ï) | 0.9986 / 0.9951 (â) |  |
| 10 | 1 | 96 | 0.9967 / 0.9932 (ë) pass | 0.9969 / 0.9932 (ë) | 0.9992 / 0.9980 (è) |  |
| 11 | 0 | 48 | 0.9945 / 0.9845 (ü) pass | 0.9929 / 0.9845 (ü) | 0.9977 / 0.9938 (ý) |  |
| 11 | 0 | 64 | 0.9896 / 0.8951 (÷) **fail** | 0.9895 / 0.8951 (÷) | 0.9982 / 0.9940 (ô) |  |
| 11 | 0 | 96 | 0.9883 / 0.9701 (ü) pass | 0.9897 / 0.9716 (ü) | 0.9969 / 0.9798 (…) |  |
| 11 | 1 | 48 | 0.9940 / 0.9848 (ñ) pass | 0.9929 / 0.9845 (ü) | 0.9979 / 0.9938 (ÿ) | yes |
| 11 | 1 | 64 | 0.9899 / 0.8951 (÷) **fail** | 0.9895 / 0.8951 (÷) | 0.9979 / 0.9948 (ù) | yes |
| 11 | 1 | 96 | 0.9888 / 0.9709 (ü) pass | 0.9897 / 0.9716 (ü) | 0.9975 / 0.9864 (…) | yes |

### Seeds

Each group ships its lower-error seed: the higher mean net-vs-strokes IoU
over 48, 64 and 96 px, seed 0 on a tie. Groups 0, 1, 3, 4, 5, 6 and 11 ship
seed 1, and groups 2, 7, 8, 9 and 10 ship seed 0. Both seeds' members are in
`weights/`: `neuronte-metric-sans-large-v1-gG.json` and
`neuronte-metric-sans-large-v1.seed1-gG.json`.

### Gate G-M2, as declared

The library checks, unchanged, on the shipped pack and on each seed's pack:

- `tests/check_reference.py`: the router, every net against numpy, and every
  letter, on the large pack with a hundredths table;
- `tests/check_letter_snap.py`: the scaled pack's letter edges below 33 px;
- `tests/check_metric_sans.py --large`: the shipped large and scaled files
  with their version 8 table. Advances and shifts are checked at ems 1 to
  128 and 4096. Every letter is drawn at 17, 24, 32, 33, 48 and 64 px, binary
  and blended, alone and in lines, as the reference's drawing moved by its
  shift.

All pass. `make test-metric-sans-large` repeats them.

### Training

`train/face_parts.py --set uilargems --band --groups 12 --width 192 --steps
80000 --candidates 2048 --near 384 --clamp 0.25 --seeds 0,1`, on an RTX 3070
under the benchmark lock: about 35 minutes. 12 nets of 16 characters, 192
wide, 1,102,560 parameters. The halved run used `--groups 24` and did not
ship.

Packing:

    train/pack.py --drawing-bundle neuronte-metric-sans-large-v1.nrt font/metric-sans-advances.txt MEMBERS...
    train/pack.py --drawing-bundle neuronte-metric-sans-scaled-v1.nrt font/metric-sans-advances.txt MEMBERS... --letter-edges uilargems --snap-below 33
