# Neuronte Sans Metric v1: the desktop faces at Helvetica's widths (`neuronte-metric-sans*-v1`)

Neuronte Sans Metric is a new face. Set in it, a line of text takes the same
width as in Helvetica, and so as in Arial, Liberation Sans and Arimo, which
share Helvetica's widths. Each character is redrawn to Helvetica's
proportions, and its strokes are this project's own.

Files:

- `neuronte-metric-sansN-v1.nrt`: the upright pixel face at every em N from 1 to 16 px.
- `neuronte-metric-sansN-italic-v1.nrt`: the italic at every em N from 3 to 16 px.
- `neuronte-metric-sansN-bold-v1.nrt` and `neuronte-metric-sansN-bold-italic-v1.nrt`:
  a bold drawn at Helvetica-Bold's widths, upright and italic, at every em N
  from 9 to 16 px. These files are the bold: draw them with `bold` = 0 (see
  "The drawn bold" below).
- `neuronte-metric-sans-large-v1.nrt` (33 px up) and `neuronte-metric-sans-scaled-v1.nrt` (17 to 32 px, snapped): see "The large and scaled faces" below.

Each covers the 192 characters of the desktop faces (printable ASCII,
U+2026 and U+00A0 to U+00FF). The upright, italic, large and scaled files draw
regular and bold; their bold (`bold` = 1) is the letter struck twice, one
pixel apart, as in every desktop face. No existing file changes.
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
- **Placement.** The ink starts where Helvetica's box starts. The rules
  keep a clear column inside each advance where the width allows. Where it
  does not, the ink reaches the next letter (see "Letters that touch"). No
  pixel face needs a shift.
- **Composed letters.** The letters with marks are composed from these by
  the rules of `tools/make-latin1-face.py`.
- **Hand drawings.** `*` (10 to 15 px) and `« »` (10 to 15 px) are drawn by
  hand, in `font/metric-sans-fixes.txt`. The rules shrank the asterisk, and
  the chevrons touched.
- **Italics** are the upright face sheared about the baseline at the slope
  of `tools/make-italic.py`, but without that tool's move that keeps each
  letter's left side bearing (`pure_shear()` in
  `tools/make-metric-sans-face.py`). The move slides a round letter, whose
  leftmost ink is at mid-height, into the letter before it, because these
  advances, the upright's, have no room for it. Without it every row keeps
  the gap it had. The desktop faces' italics and their tool are unchanged.
- **Bold** (`bold` = 1) is the letter struck twice, one pixel apart, as in
  every desktop face. The bold advance is Helvetica-Bold's. At 9 to 16 px
  there is also a bold drawn for those widths (below).

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

### Letters that touch

Of the 188 adjacent pairs of the 189 printed characters in code order
(printable ASCII without the space, U+2026 and U+00A1 to U+00FF without
U+00AD), the number whose inks touch, drawn binary by the library: touching
at least at a corner (eight neighbours) / touching edge to edge.
`tests/check_touching.py` counts them, and `tests/metric-sans-touching.txt`
holds these counts of every metric face as limits, so that a drawing that
makes more letters touch fails `make test-metric-sans-touching`. Today's
figures are those of the `neuronte-uiN-v2` files and, from 17 px, of the
scaled and large Latin-1 files.

Upright:

| em | today regular | metric regular | today bold | metric bold (struck) | metric drawn bold |
|---|---|---|---|---|---|
| 16 | 2 / 1 | 0 / 0 | 2 / 1 | 58 / 43 | 0 / 0 |
| 15 | 2 / 1 | 0 / 0 | 2 / 1 | 58 / 46 | 0 / 0 |
| 14 | 2 / 1 | 0 / 0 | 2 / 1 | 56 / 45 | 0 / 0 |
| 13 | 3 / 1 | 1 / 1 | 3 / 1 | 80 / 62 | 1 / 1 |
| 12 | 3 / 1 | 5 / 3 | 3 / 1 | 90 / 75 | 5 / 3 |
| 11 | 4 / 3 | 3 / 1 | 4 / 3 | 101 / 81 | 3 / 1 |
| 10 | 4 / 3 | 5 / 2 | 4 / 3 | 127 / 110 | 6 / 3 |
| 9 | 4 / 3 | 5 / 2 | 4 / 3 | 151 / 126 | 6 / 3 |
| 8 | 6 / 3 | 9 / 5 | 6 / 3 | 128 / 113 | none |
| 7 | 15 / 10 | 10 / 6 | 15 / 10 | 171 / 160 | none |
| 6 | 15 / 9 | 24 / 12 | 15 / 9 | 161 / 148 | none |
| 5 | 27 / 19 | 34 / 31 | 27 / 19 | 173 / 168 | none |
| 4 | 175 / 167 | 63 / 55 | 175 / 167 | 184 / 183 | none |
| 3 | 177 / 163 | 77 / 66 | 177 / 163 | 184 / 182 | none |
| 2 | 188 / 183 | 168 / 164 | 188 / 183 | 188 / 188 | none |
| 1 | 188 / 188 | 188 / 188 | 188 / 188 | 188 / 188 | none |

Italic:

| em | today italic | metric italic | today bold italic | metric bold italic (struck) | metric drawn bold italic |
|---|---|---|---|---|---|
| 16 | 1 / 1 | 30 / 4 | 1 / 1 | 87 / 47 | 34 / 5 |
| 15 | 1 / 1 | 31 / 4 | 1 / 1 | 91 / 48 | 34 / 5 |
| 14 | 1 / 1 | 31 / 3 | 1 / 1 | 92 / 51 | 35 / 3 |
| 13 | 0 / 0 | 29 / 6 | 0 / 0 | 106 / 68 | 32 / 8 |
| 12 | 0 / 0 | 33 / 6 | 0 / 0 | 115 / 79 | 48 / 10 |
| 11 | 1 / 1 | 72 / 6 | 1 / 1 | 143 / 87 | 74 / 5 |
| 10 | 0 / 0 | 81 / 8 | 0 / 0 | 139 / 114 | 97 / 13 |
| 9 | 2 / 1 | 77 / 6 | 2 / 1 | 158 / 128 | 85 / 8 |
| 8 | 2 / 2 | 97 / 11 | 2 / 2 | 159 / 118 | none |
| 7 | 12 / 9 | 104 / 6 | 12 / 9 | 173 / 163 | none |
| 6 | 10 / 7 | 127 / 12 | 10 / 7 | 179 / 148 | none |
| 5 | 26 / 15 | 146 / 31 | 26 / 15 | 182 / 169 | none |
| 4 | 169 / 107 | 131 / 58 | 169 / 107 | 184 / 183 | none |
| 3 | 172 / 124 | 148 / 76 | 172 / 124 | 184 / 182 | none |

Scaled and large (regular; bold is the packed bold):

| size | today regular | metric regular | today bold | metric bold |
|---|---|---|---|---|
| 17 px | 4 / 3 | 19 / 16 | 4 / 3 | 72 / 70 |
| 24 px | 2 / 1 | 14 / 13 | 2 / 2 | 32 / 28 |
| 32 px | 2 / 2 | 9 / 7 | 2 / 2 | 10 / 10 |
| 33 px | 2 / 2 | 12 / 10 | 2 / 2 | 11 / 10 |
| 48 px | 2 / 2 | 5 / 4 | 2 / 2 | 8 / 7 |

- **Regular, upright.** From 13 px up at most 1 pair touches, and from 14
  px up none; at 9 to 12 px 3 to 5 pairs touch,
  as in today's faces (3 to 4). At 8 px and below the counts differ from
  today's both ways: more at 5, 6 and 8 px (34, 24 and 9, against 27, 15 and
  6), fewer at 3, 4 and 7 px (77, 63 and 10, against 177, 175 and 15). At 1
  and 2 px almost every pair touches, in today's faces too: there is no room
  for a gap.
- **Bold, struck.** 56 to 151 pairs touch at 9 to 16 px, and 128 to 188 at 1 to 8
  px. Bold is the letter struck twice, so its ink is a column wider, and
  today's faces give it one more pixel of advance. Helvetica-Bold is on
  average only 18.5/1000 em wider than regular, so at these sizes most bold
  advances come to the same pixels as regular (180 of 192 at 9 px, 134 at
  16 px), and the extra column fills the gap. **Bold pixel text set with
  `bold` = 1 is crowded; below 9 px there is no other bold.**
- **Drawn bold, 9 to 16 px.** 0 to 6 pairs touch (6 6 3 5 1 0 0 0 from 9 to 16 px). This
  is the regular face's level.
- **Italic.** The slant moves the top of a letter toward the next one, so
  corners meet: 29 to 81 pairs touch at 9 to 16 px, and today's italics
  0 to 2. Edge to edge, 3 to 8 pairs touch (today's 0 to 1), and the
  drawn bold italic has 3 to 13. The other italic rule, `tools/make-italic.py`'s, which
  moves each letter to keep its left bearing, gave 21 to 37 edge-to-edge
  pairs at these sizes. Its figures were measured on drawings before it was
  rejected, not by the library.
- **Scaled and large.** The strokes there are the large face's, which keep
  their gaps better, but bold is struck as well: 72 bold pairs touch at 17
  px, 32 at 24 px, 10 at 32 px and 8 at 48 px.

### Accuracy

Gate G-MP, declared before training, is exact. Every character, regular and
bold, drawn alone by the library in binary mode at the face's em, must be
exactly its drawing. The pen must move by the table's advance. A line of
all 192 characters must be those drawings side by side. (For a drawn bold
face "bold" is the same letter struck once more, as the checker draws it.)

Two checks were run, on both seeds of every face:

- `tests/check_reference.py`: the router, every net against numpy, and
  every letter exact, on a pack with the pixel face as its table;
- `tests/check_metric_sans.py`: the shipped file with its thousandths table.

A face ships its lower-error seed: seed 0 if it is exact, else seed 1. Seed 1
ships for two faces, the italics at 12 and 16 px. A seed fails on at most 3
pixels of one or two letters with a mark.

| face | seed 0 | seed 1 | ships |
|---|---|---|---|
| upright, 1 to 16 px | exact | exact | seed 0 |
| italic, 3 to 11 px, 14 px | exact | exact | seed 0 |
| italic 12 px | Ê off by 1 px | exact | **seed 1** |
| italic 13 px | exact | Ó off by 3 px | seed 0 |
| italic 15 px | exact | Â off by 1 px | seed 0 |
| italic 16 px | Ù off by 2 px | exact | **seed 1** |
| drawn bold, 9 to 14 px and 16 px | exact | exact | seed 0 |
| drawn bold 15 px | Ò off by 2 px | ó and ô off by 1 px each | **halved**, seed 0 |
| drawn bold italic, 9 to 12 px | exact | exact | seed 0 |
| drawn bold italic 13 px | exact | Ã off by 1 px | seed 0 |
| drawn bold italic 14 px | exact | ù off by 2 px | seed 0 |
| drawn bold italic 15 px | Ò off by 1 px | É, Ò and Ô off by 1 px each | **halved**, seed 0 |
| drawn bold italic 16 px | Ó and Ô off by 1 px each | Ê and Ó off by 1 px each | **halved**, seed 0 |

Three faces failed on both seeds, each on a single group of 4 characters (seed
0's group 36, U+00D1 to U+00D4). As the Method says, that group was halved
once, into two nets of 2 characters (`--groups 96`, both seeds trained, the
halves of group 36 used from seed 0). **Every halved face then passed, and
no character is left out of any face.** The faces carry 49 nets, not 48.

## Speed

A new handle draws a line regular then bold, as a desktop builds its cells.
Figures are the median of 10 fresh handles (two passes of 5), single thread,
each pass under the benchmark lock. Each figure is from -> to:

- regular: today's `neuronte-uiN-v2` -> `neuronte-metric-sansN-v1`;
- italic: today's `neuronte-uiN-italic-v2` -> the metric italic;
- bold and bold italic (9 to 16 px): the metric regular, or italic, face of
  the same em -> its drawn bold, drawing the same two lines;
- scaled: `neuronte-ui-scaled-latin1-v1` -> the metric scaled face; large:
  `neuronte-ui-large-latin1-v2` -> the metric large face.

First use is in milliseconds. Cached is the two lines drawn again on the
same handle, in microseconds. ASCII is the line of 96 ASCII characters, and
Latin-1 the line of U+00A0 to U+00FF. The two passes agree to a median of
1.1% (Intel i7-10700F) and 0.4% (Intel i7-6820HQ) per figure.

Machines: an Intel i7-10700F, and an Intel i7-6820HQ on a fresh Debian 13
install (with Kilix 0.2.3, kernel 6.12.117+deb13-amd64, before its NVIDIA
driver was installed), both on 2026-11-19.

### Intel i7-10700F

| em | face | from | ASCII first use | ASCII cached | Latin-1 first use | Latin-1 cached |
|---|---|---|---|---|---|---|
| 16 | metric-sans16 | ui16 | 151.71 -> 22.57 | 268.6 -> 270.4 | 23.24 -> 23.70 | 269.1 -> 277.7 |
| 16 | metric-sans16-italic | ui16-italic | 168.84 -> 24.08 | 268.9 -> 281.2 | 23.93 -> 24.72 | 276.4 -> 282.2 |
| 16 | metric-sans16-bold | metric-sans16 | 22.57 -> 23.09 | 270.4 -> 284.9 | 23.70 -> 24.14 | 277.7 -> 293.1 |
| 16 | metric-sans16-bold-italic | metric-sans16-italic | 24.08 -> 23.57 | 281.2 -> 292.8 | 24.72 -> 24.33 | 282.2 -> 294.0 |
| 15 | metric-sans15 | ui15 | 13.39 -> 20.71 | 244.7 -> 244.3 | 20.94 -> 21.39 | 242.3 -> 247.5 |
| 15 | metric-sans15-italic | ui15-italic | 10.76 -> 21.27 | 245.6 -> 248.0 | 20.98 -> 21.85 | 245.4 -> 254.2 |
| 15 | metric-sans15-bold | metric-sans15 | 20.71 -> 20.96 | 244.3 -> 249.8 | 21.39 -> 20.94 | 247.5 -> 252.2 |
| 15 | metric-sans15-bold-italic | metric-sans15-italic | 21.27 -> 21.16 | 248.0 -> 253.3 | 21.85 -> 21.61 | 254.2 -> 255.9 |
| 14 | metric-sans14 | ui14 | 9.36 -> 18.27 | 220.8 -> 220.9 | 18.17 -> 18.55 | 217.4 -> 222.6 |
| 14 | metric-sans14-italic | ui14-italic | 9.37 -> 18.89 | 225.1 -> 226.4 | 18.68 -> 19.08 | 216.8 -> 223.7 |
| 14 | metric-sans14-bold | metric-sans14 | 18.27 -> 18.78 | 220.9 -> 233.4 | 18.55 -> 19.01 | 222.6 -> 234.6 |
| 14 | metric-sans14-bold-italic | metric-sans14-italic | 18.89 -> 19.08 | 226.4 -> 233.7 | 19.08 -> 19.37 | 223.7 -> 230.6 |
| 13 | metric-sans13 | ui13 | 8.43 -> 16.04 | 200.8 -> 190.3 | 16.10 -> 16.97 | 192.1 -> 199.3 |
| 13 | metric-sans13-italic | ui13-italic | 110.74 -> 16.16 | 194.5 -> 194.9 | 16.92 -> 17.04 | 198.1 -> 199.0 |
| 13 | metric-sans13-bold | metric-sans13 | 16.04 -> 16.33 | 190.3 -> 202.0 | 16.97 -> 16.58 | 199.3 -> 200.0 |
| 13 | metric-sans13-bold-italic | metric-sans13-italic | 16.16 -> 16.47 | 194.9 -> 206.2 | 17.04 -> 16.79 | 199.0 -> 203.2 |
| 12 | metric-sans12 | ui12 | 9.18 -> 13.70 | 178.8 -> 170.7 | 14.23 -> 14.61 | 172.2 -> 176.6 |
| 12 | metric-sans12-italic | ui12-italic | 9.19 -> 14.58 | 182.4 -> 177.6 | 14.69 -> 15.14 | 179.1 -> 179.1 |
| 12 | metric-sans12-bold | metric-sans12 | 13.70 -> 14.20 | 170.7 -> 180.9 | 14.61 -> 14.77 | 176.6 -> 183.2 |
| 12 | metric-sans12-bold-italic | metric-sans12-italic | 14.58 -> 14.38 | 177.6 -> 181.9 | 15.14 -> 15.15 | 179.1 -> 186.2 |
| 11 | metric-sans11 | ui11 | 6.15 -> 12.10 | 154.6 -> 150.7 | 12.12 -> 12.35 | 154.2 -> 154.6 |
| 11 | metric-sans11-italic | ui11-italic | 6.35 -> 12.40 | 161.2 -> 152.8 | 12.60 -> 12.58 | 155.2 -> 157.8 |
| 11 | metric-sans11-bold | metric-sans11 | 12.10 -> 12.22 | 150.7 -> 156.4 | 12.35 -> 12.61 | 154.6 -> 164.3 |
| 11 | metric-sans11-bold-italic | metric-sans11-italic | 12.40 -> 12.62 | 152.8 -> 161.9 | 12.58 -> 12.68 | 157.8 -> 163.6 |
| 10 | metric-sans10 | ui10 | 5.22 -> 10.39 | 135.4 -> 132.0 | 10.32 -> 10.73 | 134.4 -> 136.9 |
| 10 | metric-sans10-italic | ui10-italic | 5.34 -> 10.70 | 139.1 -> 134.1 | 10.92 -> 10.79 | 137.0 -> 137.4 |
| 10 | metric-sans10-bold | metric-sans10 | 10.39 -> 10.45 | 132.0 -> 133.2 | 10.73 -> 10.76 | 136.9 -> 140.6 |
| 10 | metric-sans10-bold-italic | metric-sans10-italic | 10.70 -> 10.66 | 134.1 -> 138.9 | 10.79 -> 10.88 | 137.4 -> 143.1 |
| 9 | metric-sans9 | ui9 | 4.39 -> 8.71 | 117.9 -> 111.8 | 8.55 -> 8.79 | 114.8 -> 115.2 |
| 9 | metric-sans9-italic | ui9-italic | 4.45 -> 8.89 | 120.2 -> 115.2 | 8.93 -> 8.97 | 118.7 -> 117.4 |
| 9 | metric-sans9-bold | metric-sans9 | 8.71 -> 8.76 | 111.8 -> 113.4 | 8.79 -> 8.84 | 115.2 -> 118.2 |
| 9 | metric-sans9-bold-italic | metric-sans9-italic | 8.89 -> 8.87 | 115.2 -> 116.7 | 8.97 -> 8.97 | 117.4 -> 119.0 |
| 8 | metric-sans8 | ui8 | 3.81 -> 7.04 | 104.5 -> 101.1 | 7.19 -> 7.17 | 104.2 -> 103.2 |
| 8 | metric-sans8-italic | ui8-italic | 3.82 -> 7.36 | 108.1 -> 103.2 | 7.41 -> 7.25 | 104.5 -> 102.9 |
| 7 | metric-sans7 | ui7 | 3.06 -> 5.80 | 84.2 -> 82.8 | 6.06 -> 5.84 | 87.8 -> 84.0 |
| 7 | metric-sans7-italic | ui7-italic | 3.02 -> 6.00 | 91.8 -> 84.8 | 6.03 -> 6.13 | 88.7 -> 86.8 |
| 6 | metric-sans6 | ui6 | 2.32 -> 4.38 | 69.8 -> 64.8 | 4.55 -> 4.47 | 69.0 -> 67.0 |
| 6 | metric-sans6-italic | ui6-italic | 2.37 -> 4.45 | 69.2 -> 64.5 | 4.60 -> 4.66 | 69.2 -> 68.2 |
| 5 | metric-sans5 | ui5 | 1.81 -> 3.27 | 54.0 -> 52.0 | 3.40 -> 3.35 | 55.0 -> 53.2 |
| 5 | metric-sans5-italic | ui5-italic | 1.81 -> 3.43 | 58.8 -> 51.5 | 3.45 -> 3.45 | 56.7 -> 53.6 |
| 4 | metric-sans4 | ui4 | 1.26 -> 2.08 | 48.3 -> 38.0 | 2.34 -> 2.20 | 46.5 -> 40.0 |
| 4 | metric-sans4-italic | ui4-italic | 1.29 -> 2.17 | 44.2 -> 37.9 | 2.31 -> 2.20 | 45.0 -> 39.5 |
| 3 | metric-sans3 | ui3 | 0.88 -> 1.31 | 36.2 -> 29.9 | 1.70 -> 1.70 | 37.7 -> 32.6 |
| 3 | metric-sans3-italic | ui3-italic | 0.89 -> 1.41 | 36.5 -> 29.9 | 1.69 -> 1.71 | 37.2 -> 32.6 |
| 2 | metric-sans2 | ui2 | 0.47 -> 0.43 | 24.0 -> 21.6 | 0.44 -> 0.41 | 23.5 -> 21.4 |
| 1 | metric-sans1 | ui1 | 0.22 -> 0.22 | 15.1 -> 15.6 | 0.23 -> 0.23 | 16.2 -> 16.6 |
| 17 | metric-sans-scaled | ui-scaled-latin1 | 94.36 -> 115.77 | 323.6 -> 332.3 | 130.37 -> 115.05 | 329.1 -> 336.4 |
| 24 | metric-sans-scaled | ui-scaled-latin1 | 50.57 -> 58.74 | 622.8 -> 639.8 | 66.35 -> 58.63 | 632.7 -> 648.6 |
| 32 | metric-sans-scaled | ui-scaled-latin1 | 86.46 -> 112.10 | 1048.6 -> 1067.6 | 106.34 -> 116.78 | 1069.2 -> 1097.1 |
| 33 | metric-sans-large | ui-large-latin1 | 119.61 -> 114.09 | 1102.5 -> 1123.4 | 127.06 -> 110.05 | 1134.1 -> 1149.0 |
| 48 | metric-sans-large | ui-large-latin1 | 245.56 -> 236.13 | 2213.8 -> 2248.4 | 231.38 -> 227.42 | 2287.4 -> 2292.1 |
| 64 | metric-sans-large | ui-large-latin1 | 457.93 -> 415.03 | 3770.6 -> 3856.7 | 461.93 -> 403.31 | 3861.7 -> 3945.2 |

### Intel i7-6820HQ

| em | face | from | ASCII first use | ASCII cached | Latin-1 first use | Latin-1 cached |
|---|---|---|---|---|---|---|
| 16 | metric-sans16 | ui16 | 203.20 -> 31.51 | 387.2 -> 399.2 | 32.08 -> 32.77 | 392.6 -> 403.4 |
| 16 | metric-sans16-italic | ui16-italic | 229.11 -> 33.25 | 396.8 -> 408.4 | 32.91 -> 34.37 | 399.4 -> 409.4 |
| 16 | metric-sans16-bold | metric-sans16 | 31.51 -> 32.13 | 399.2 -> 416.6 | 32.77 -> 32.79 | 403.4 -> 418.7 |
| 16 | metric-sans16-bold-italic | metric-sans16-italic | 33.25 -> 32.50 | 408.4 -> 424.1 | 34.37 -> 33.66 | 409.4 -> 426.1 |
| 15 | metric-sans15 | ui15 | 18.46 -> 28.65 | 356.1 -> 355.9 | 29.20 -> 29.45 | 351.2 -> 358.9 |
| 15 | metric-sans15-italic | ui15-italic | 14.94 -> 29.38 | 362.6 -> 364.1 | 29.35 -> 29.79 | 357.6 -> 363.2 |
| 15 | metric-sans15-bold | metric-sans15 | 28.65 -> 29.09 | 355.9 -> 368.4 | 29.45 -> 29.52 | 358.9 -> 372.2 |
| 15 | metric-sans15-bold-italic | metric-sans15-italic | 29.38 -> 29.24 | 364.1 -> 375.3 | 29.79 -> 29.83 | 363.2 -> 376.6 |
| 14 | metric-sans14 | ui14 | 12.97 -> 25.36 | 319.2 -> 315.4 | 25.35 -> 26.00 | 315.9 -> 323.1 |
| 14 | metric-sans14-italic | ui14-italic | 13.00 -> 25.83 | 321.9 -> 321.6 | 26.20 -> 26.59 | 322.2 -> 327.6 |
| 14 | metric-sans14-bold | metric-sans14 | 25.36 -> 25.58 | 315.4 -> 327.4 | 26.00 -> 25.90 | 323.1 -> 335.4 |
| 14 | metric-sans14-bold-italic | metric-sans14-italic | 25.83 -> 26.22 | 321.6 -> 332.9 | 26.59 -> 27.03 | 327.6 -> 338.2 |
| 13 | metric-sans13 | ui13 | 11.58 -> 22.28 | 286.8 -> 280.1 | 22.61 -> 23.06 | 286.2 -> 286.9 |
| 13 | metric-sans13-italic | ui13-italic | 151.87 -> 22.58 | 283.9 -> 291.1 | 23.20 -> 23.50 | 287.1 -> 291.9 |
| 13 | metric-sans13-bold | metric-sans13 | 22.28 -> 22.65 | 280.1 -> 294.4 | 23.06 -> 23.34 | 286.9 -> 297.9 |
| 13 | metric-sans13-bold-italic | metric-sans13-italic | 22.58 -> 22.80 | 291.1 -> 302.2 | 23.50 -> 23.70 | 291.9 -> 302.8 |
| 12 | metric-sans12 | ui12 | 12.80 -> 19.22 | 255.8 -> 249.1 | 19.86 -> 20.40 | 256.5 -> 255.0 |
| 12 | metric-sans12-italic | ui12-italic | 12.82 -> 20.17 | 262.0 -> 255.8 | 20.59 -> 21.82 | 257.2 -> 253.1 |
| 12 | metric-sans12-bold | metric-sans12 | 19.22 -> 19.67 | 249.1 -> 258.1 | 20.40 -> 20.70 | 255.0 -> 258.1 |
| 12 | metric-sans12-bold-italic | metric-sans12-italic | 20.17 -> 20.26 | 255.8 -> 264.8 | 21.82 -> 20.91 | 253.1 -> 263.3 |
| 11 | metric-sans11 | ui11 | 8.58 -> 16.80 | 225.2 -> 219.7 | 17.07 -> 17.09 | 222.3 -> 220.9 |
| 11 | metric-sans11-italic | ui11-italic | 8.69 -> 17.23 | 232.2 -> 227.1 | 17.55 -> 17.37 | 228.4 -> 226.1 |
| 11 | metric-sans11-bold | metric-sans11 | 16.80 -> 17.02 | 219.7 -> 228.2 | 17.09 -> 17.49 | 220.9 -> 235.8 |
| 11 | metric-sans11-bold-italic | metric-sans11-italic | 17.23 -> 17.47 | 227.1 -> 236.8 | 17.37 -> 17.47 | 226.1 -> 237.0 |
| 10 | metric-sans10 | ui10 | 7.30 -> 14.51 | 196.2 -> 192.0 | 14.57 -> 14.85 | 194.2 -> 197.3 |
| 10 | metric-sans10-italic | ui10-italic | 7.45 -> 14.86 | 202.8 -> 198.2 | 15.08 -> 14.84 | 197.7 -> 197.4 |
| 10 | metric-sans10-bold | metric-sans10 | 14.51 -> 14.66 | 192.0 -> 198.2 | 14.85 -> 14.74 | 197.3 -> 201.2 |
| 10 | metric-sans10-bold-italic | metric-sans10-italic | 14.86 -> 14.93 | 198.2 -> 203.8 | 14.84 -> 15.02 | 197.4 -> 204.9 |
| 9 | metric-sans9 | ui9 | 6.14 -> 12.07 | 174.2 -> 163.9 | 12.15 -> 12.26 | 171.2 -> 168.8 |
| 9 | metric-sans9-italic | ui9-italic | 6.15 -> 12.22 | 178.3 -> 168.2 | 12.52 -> 12.51 | 174.8 -> 172.1 |
| 9 | metric-sans9-bold | metric-sans9 | 12.07 -> 12.14 | 163.9 -> 166.6 | 12.26 -> 12.29 | 168.8 -> 172.6 |
| 9 | metric-sans9-bold-italic | metric-sans9-italic | 12.22 -> 12.29 | 168.2 -> 171.6 | 12.51 -> 12.56 | 172.1 -> 174.8 |
| 8 | metric-sans8 | ui8 | 5.32 -> 9.80 | 153.1 -> 145.9 | 10.16 -> 10.00 | 152.4 -> 149.2 |
| 8 | metric-sans8-italic | ui8-italic | 5.30 -> 10.12 | 158.1 -> 150.7 | 10.44 -> 10.29 | 155.9 -> 152.4 |
| 7 | metric-sans7 | ui7 | 4.26 -> 8.04 | 122.2 -> 118.5 | 8.45 -> 8.23 | 126.8 -> 124.9 |
| 7 | metric-sans7-italic | ui7-italic | 4.15 -> 8.30 | 131.4 -> 121.6 | 8.52 -> 8.46 | 131.6 -> 126.9 |
| 6 | metric-sans6 | ui6 | 3.22 -> 6.05 | 97.9 -> 90.9 | 6.44 -> 6.21 | 100.6 -> 96.3 |
| 6 | metric-sans6-italic | ui6-italic | 3.29 -> 6.24 | 99.3 -> 92.4 | 6.45 -> 6.42 | 101.7 -> 98.2 |
| 5 | metric-sans5 | ui5 | 2.54 -> 4.58 | 78.8 -> 74.5 | 4.77 -> 4.64 | 80.8 -> 77.0 |
| 5 | metric-sans5-italic | ui5-italic | 2.50 -> 4.74 | 84.3 -> 75.0 | 4.79 -> 4.74 | 82.7 -> 77.1 |
| 4 | metric-sans4 | ui4 | 1.73 -> 2.94 | 68.5 -> 54.2 | 3.31 -> 3.12 | 67.0 -> 57.8 |
| 4 | metric-sans4-italic | ui4-italic | 1.79 -> 3.08 | 63.5 -> 54.2 | 3.28 -> 3.10 | 64.9 -> 57.8 |
| 3 | metric-sans3 | ui3 | 1.22 -> 1.80 | 50.3 -> 41.5 | 2.38 -> 2.36 | 53.0 -> 46.0 |
| 3 | metric-sans3-italic | ui3-italic | 1.23 -> 1.94 | 50.5 -> 41.5 | 2.31 -> 2.35 | 52.3 -> 45.5 |
| 2 | metric-sans2 | ui2 | 0.61 -> 0.55 | 32.3 -> 29.1 | 0.60 -> 0.55 | 33.3 -> 30.3 |
| 1 | metric-sans1 | ui1 | 0.30 -> 0.30 | 21.3 -> 21.7 | 0.31 -> 0.30 | 22.8 -> 23.3 |
| 17 | metric-sans-scaled | ui-scaled-latin1 | 130.77 -> 154.75 | 470.4 -> 480.7 | 175.76 -> 152.27 | 478.4 -> 491.1 |
| 24 | metric-sans-scaled | ui-scaled-latin1 | 70.61 -> 78.76 | 898.2 -> 921.5 | 90.37 -> 78.29 | 921.5 -> 941.7 |
| 32 | metric-sans-scaled | ui-scaled-latin1 | 120.27 -> 150.22 | 1501.0 -> 1535.2 | 141.80 -> 157.46 | 1534.8 -> 1572.4 |
| 33 | metric-sans-large | ui-large-latin1 | 159.01 -> 152.15 | 1585.5 -> 1588.1 | 171.02 -> 149.06 | 1620.2 -> 1652.4 |
| 48 | metric-sans-large | ui-large-latin1 | 328.17 -> 314.19 | 3126.4 -> 3194.3 | 313.55 -> 303.07 | 3209.1 -> 3277.8 |
| 64 | metric-sans-large | ui-large-latin1 | 619.19 -> 556.04 | 5373.4 -> 5464.6 | 627.00 -> 538.76 | 5494.8 -> 5618.4 |

On both machines:

- **Pixel faces, regular and italic.** Every metric face draws all 192
  characters with one kind of net, 48 of them for 4 characters each. Today's
  faces keep the older nets for ASCII.
  - So a metric face's ASCII line costs about what its Latin-1 line does: its
    first use is 1.5 to 2.0 times today's at 3 to 15 px.
  - Where today's ASCII is one large net (16 px, 16 px italic and 13 px
    italic), the metric face's first use is 6.4 to 7.0 times faster.
  - 1 and 2 px: 0.22 -> 0.22 ms and 0.47 -> 0.43 ms on the Intel i7-10700F.
  - The Latin-1 line's first use is from 8% faster to 6% slower, and its
    cached redraws from 14% faster to 4% slower. The ASCII line's cached
    redraws are from 21% faster (4 px) to 5% slower. The cached redraws are
    faster at 3 to 8 px.
- **Drawn bold and bold italic.** A drawn bold costs about what the regular
  face of the same em does: first use from 4.2% faster to 3.6% slower, and
  cached redraws 0.3% to 6.8% slower.
- **Scaled face.** ASCII first use is 12% to 30% slower than today's.
  Latin-1 first use is from 13% faster to 11% slower, and cached redraws are
  1.8% to 2.7% slower.
- **Large face.** ASCII first use is 3.8% to 10% faster, Latin-1 first use
  1.7% to 14% faster, and cached redraws 0.2% to 2.3% slower.

## Training

- Per-em faces 3 to 16 px, regular, italic and drawn bold:
  `train/face_parts.py OUT --set uiNms[i|b|bi] --band --groups 48 --width 32 --steps 80000 --seeds 0,1`.
  These are 48 band-tiled nets of 4 characters, 32 wide. The sets are `uiNms`
  (upright), `uiNmsi` (italic), `uiNmsb` (drawn bold) and `uiNmsbi` (drawn
  bold italic).
- 1 and 2 px: `--groups 2 --width 16`. 1 px uses `--pen 0.49`, because the
  trainer refuses a pen of 0.5 cell or more.
- Halved groups (15 px drawn bold, 15 px drawn bold italic and 16 px drawn
  bold italic): the same command with `--groups 96`, and from seed 0 only
  the two halves of group 36, `...-v1-g72.json` and `...-v1-g73.json`. Seed
  0's own group-36 net failed and is not kept. The halves sort after the
  other members, which fixes the order the file is packed in. Seed 1's
  members are kept as trained and are not repaired.
- Hardware: rented RTX 4090s, eight sets at a time on each, about 9 to 13
  minutes per set (22 minutes at 1 and 2 px); the three halvings took about
  5 minutes together on one.
- Packing:
  `train/pack.py --drawing-bundle neuronte-metric-sansN[-bold][-italic]-v1.nrt font/metric-sans-N[-bold].advances.txt MEMBERS...`.
  Each packed file was checked byte for byte against the one gated on the
  rental, and `make test-metric-sans-faces` repacks every one.
- Members: `neuronte-metric-sansN[-bold][-italic]-v1-gG.json` for seed 0 and
  `.seed1-gG.json` for seed 1. Where seed 1 ships, the file is packed from
  the `.seed1` members.
- Sizes: 1,016,948 bytes for each face from 3 to 16 px, 1,038,100 for the
  three halved faces. The 1 and 2 px faces are 19,596 and 19,636 bytes.

## The drawn bold, 9 to 16 px

The struck bold touches (above). Where the widths allow, a bold is drawn
instead: `tools/make-metric-sans-bold.py` makes
`font/metric-sans-N-bold.txt`, `font/metric-sans-N-bold-italic.txt` and
`font/metric-sans-N-bold.advances.txt` for N = 9 to 16 from the same source
as the regular face, `font/ui-N-latin1.txt`, with these rules (the regular
tool's `rowmap()` is imported, not changed):

- The advance is Helvetica-Bold's, round(width * N / 1000), from the AFM
  numbers in `font/metric-sans-widths.txt`.
- A base character's bold ink is the regular AFM box's width plus the extra of
  the bold width, in pixels, but at most the bold advance less its left
  side bearing and one clear column. The source's ink is resampled to one
  column less than that, placed at the regular box's left side bearing, and
  then struck: each pixel also inks the pixel to its right, except where that
  would close a one-column gap between two inked pixels of the row, so the
  counters of m, w, M, W and # stay open. Stems become two columns.
- Characters that would turn into a bar or lose a counter are not struck but
  drawn at the full bold width in one-column strokes; a few characters are
  drawn by hand (`font/metric-sans-bold-fixes.txt`: « » at 9 to 15 px and ° at
  9 to 11 px); and a mark wider than the room keeps no clear column, as in
  the regular face. The table:

| em | drawn at the full bold width, not struck | drawn by hand | no clear column (a mark wider than the room) |
|---|---|---|---|
| 9 | # ( ) , - / 1 ; [ \ ] ` f j t ¤ ª SHY ² ³ ¹ º | « ° » | ¨ ¯ Î Ï î ï |
| 10 | # ( ) , - / ; @ [ \ ] ` f j t ¤ SHY ² ³ ¹ | « ° » | ¨ ¯ Î Ï î ï |
| 11 | # , / ; @ \ ` j ¤ ¹ | « ° » | ¯ Î Ï î ï |
| 12 | / \ ` j ¹ | « » | ¨ ¯ Î Ï î ï |
| 13 | ¹ | « » | ¨ ¯ Ï ï |
| 14 | , ; | « » | Ï ï |
| 15 | , ; | « » | Ï ï |
| 16 | , | none | Ï ï |

- The letters with marks are composed from the unstruck bases by the rules
  of `tools/make-latin1-face.py` and then struck alike.
- The italic is the upright bold sheared about the baseline, as the regular
  italic is.
- Rows are not resampled: each drawn bold keeps its face's heights.
- Helvetica-Bold's widths were copied from the AFM files, as the card's first
  section says; TeX Gyre Heros was looked at as a reference, and no font
  file was opened.

Below 9 px there is no drawn bold: a bold advance there is mostly the
regular one, and a column wider ink leaves no room. **At 1 to 8 px the struck
bold touches in 128 to 188 of 188 pairs** (table above), and the regular face
itself touches in 9 to 188 pairs at 1 to 8 px. Text that must read at those
sizes should not rely on bold. The 8 px and smaller faces are also
harder to read than today's, because more characters share a bitmap (above).

## Caller notes

- To draw a bold at 9 to 16 px, open `neuronte-metric-sansN-bold-v1.nrt` (or
  the `-bold-italic-v1.nrt`) beside the regular file and draw bold text
  with `bold` = 0 from the bold file. The bold file's table holds
  Helvetica-Bold's width for both weights, so `neuronte_advance()`,
  `neuronte_text_width()` and the exact calls measure the bold text as
  Helvetica-Bold does. `bold` = 1 on a bold file strikes the bold again and
  is not meant to be used.
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
