# Neuronte Sans Metric greyscale v1: 8 to 16 px with greyscale edges (`neuronte-metric-sans*-grey*-v1`)

The binary Neuronte Sans Metric faces (`neuronte-metric-sansN-v1`) are exact
bitmaps, so the library draws them with hard edges. These faces draw the
same letters with greyscale edges. Stems and bars stay on whole pixels.
Curves and diagonals are anti-aliased. Each face keeps the binary face's
columns, rows and spacing at its em, and its advances.

Files:

- `neuronte-metric-sansN-grey-v1.nrt`: upright, at every em N from 8 to 16 px.
- `neuronte-metric-sansN-grey-italic-v1.nrt`: italic, at the same ems.

Each covers the 192 characters of the desktop faces (printable ASCII,
U+2026 and U+00A0 to U+00FF), except that **the 8 px upright face leaves out
Æ (U+00C6) and Ç (U+00C7)** (see "Results"). Each file draws regular and
bold, the bold being the letter struck twice, one pixel apart, as in every
desktop face. There is no greyscale drawn bold. No existing file changes.

## Use

Draw a face at its own em, with blending (the library's default; not
`neuronte_set_binary`). Its advances are the binary face's, in thousandths
of an em (`font/metric-sans-N.advances.txt`, Helvetica's widths from
Adobe's Core 14 AFM files, as for every Neuronte Sans Metric face; see
[neuronte-metric-sans-v1.md](neuronte-metric-sans-v1.md#where-the-widths-come-from)).
A line takes the same pixels as in the binary face of that em.

At 8 px upright, `neuronte_untrained()` is 1 for Æ and Ç. Draw those two
with `neuronte-metric-sans8-v1`, which has the same advances.

## The drawings

The teacher for each em is drawn by `train/metric_sans_grey.py` (sets
`uiNmsg` and `uiNmsgi`). It takes the large face's strokes
(`train/metric_sans.py`) and hints them onto that em's binary face:

- a one-pixel pen (radius 0.5/N), never thinner;
- each character's ink takes the binary face's first and last ink columns
  and rows, and the face's baseline, x-height, cap height, ascender and
  descender;
- each stem and bar goes to the nearest binary column or row inked along at
  least 60% of it;
- the italic is the hinted upright sheared one column per four rows about
  the baseline row.

The rules are in the module's docstring. No font file is opened. TeX Gyre
Heros was looked at as a reference only, on sheets outside the repository.
No tool in the repository reads it, and it is not used in training.

## The gates (declared before training)

The gates were measured at the face's em, on the shipped file, through
`neuronte_coverage()` with automatic samples (2 per axis below 24 px). They
were checked against the teacher: the set's strokes, with their exact signed
distance taken through the library's own coverage formula and sample
positions. ink-MAE is the mean |error| over pixels where either side has
coverage.

- **G-GC**: every character ink-MAE <= 0.010 and worst pixel <= 0.15; the
  face's mean ink-MAE <= 0.004.
- **G-GW**: every advance, regular and bold, equals the binary face's.

For calibration, the large net drawn against its own strokes gives 0.0006
to 0.0007 at 8 to 16 px. The binary 12 px face against its traced strokes
gives 0.0087.

`tests/check_metric_grey.py` measures both gates. Its `--left-out` option takes
the characters of a group the Method left out, and each of them must be
untrained in the file.

## Method and results

The Method, declared before training:

- train both seeds;
- of the passing seeds, the one with the lower face mean ships;
- a failing group is halved once;
- a group still failing is left out and listed.

A halved group K is replaced, in the shipping seed, by nets 2K and 2K+1 of a
96-group run of the same seed. They are named `-h2K` and `-h2K+1`.

G-GW passes in every face. G-GC, at the shipping seed:

| face | first pass, seed 0 / seed 1 | halved | ships | face ink-MAE | worst character | worst pixel |
|---|---|---|---|---|---|---|
| upright 8 px | 10 fail / 7 fail | 8, 9, 31, 33, 36, 39 | seed 0 | 0.0027 | 0.0096 | 0.051 |
| upright 9 px | 1 fail / 2 fail | 8, 33 | seed 1 | 0.0025 | 0.0083 | 0.050 |
| upright 10 px | 1 fail / 1 fail | 33 | seed 1 | 0.0022 | 0.0079 | 0.050 |
| upright 11 px | 1 fail / pass | - | seed 1 | 0.0024 | 0.0073 | 0.052 |
| upright 12 px | pass / pass | - | seed 1 | 0.0028 | 0.0094 | 0.079 |
| upright 13 px | 1 fail / pass | - | seed 1 | 0.0030 | 0.0083 | 0.055 |
| upright 14 px | 1 fail / 1 fail | 33 | seed 1 | 0.0029 | 0.0097 | 0.053 |
| upright 15 px | 1 fail / 2 fail | 29, 33 | seed 1 | 0.0031 | 0.0080 | 0.046 |
| upright 16 px | 1 fail / 1 fail | 33 | seed 1 | 0.0033 | 0.0075 | 0.057 |
| italic 8 px | 3 fail / 5 fail | 8, 31, 33 | seed 0 | 0.0027 | 0.0095 | 0.062 |
| italic 9 px | 1 fail / 1 fail | 33 | seed 1 | 0.0024 | 0.0069 | 0.055 |
| italic 10 px | pass / pass | - | seed 1 | 0.0025 | 0.0075 | 0.052 |
| italic 11 px | pass / pass | - | seed 1 | 0.0026 | 0.0067 | 0.040 |
| italic 12 px | pass / pass | - | seed 1 | 0.0028 | 0.0096 | 0.078 |
| italic 13 px | pass / pass | - | seed 1 | 0.0030 | 0.0061 | 0.049 |
| italic 14 px | 1 fail / pass | - | seed 1 | 0.0032 | 0.0088 | 0.053 |
| italic 15 px | pass / pass | - | seed 1 | 0.0036 | 0.0077 | 0.057 |
| italic 16 px | 2 fail / 1 fail | 33 | seed 1 | 0.0037 | 0.0075 | 0.047 |

Group 33 (U+00C4 to U+00C7, the one holding Æ) failed on at least one seed
in 11 of the 18 faces, by up to 0.007 over the limit (Æ at 8 px). One
halving fixed every failing group except one half at 8 px upright.

**At 8 px upright one half still failed on each seed**: on seed 0, Æ at
0.0107 (half h67, Æ and Ç); on seed 1, @ at 0.0108 (half h16, @ and A). As
the Method says, the half is left out. Seed 1's face mean is lower by
0.00001 (0.002671 against 0.002681), but it would leave out @ and **A**. Seed
0 ships, leaving out Æ and Ç. This departs from the declared rule and is
for the owner to confirm. Seed 1's 48 members are kept as trained.

## Training

- `train/face_parts.py OUT --set uiNmsg[i] --band --groups 48 --width 32
  --steps 80000 --candidates 2048 --near 384 --clamp 0.25 --seeds 0,1`
  (recipe R1: the binary faces' net size, with the large face's sampling).
  The recipe was chosen by a 12 px pilot that ran R1 and a larger R2
  (`--groups 12 --width 192`). By the declared rule the cheaper recipe that
  passed on both seeds was used. R2 reached face means of 0.0008 and 0.0007,
  but at about ten times the GPU time; it was not used.
- Halvings: the same command with `--groups 96`.
- Hardware: two rented RTX 4090s, about 6 minutes of GPU per face. Vast.ai
  spend for the lane was $0.85.
- Packing: `train/pack.py --drawing-bundle neuronte-metric-sansN-grey[-italic]-v1.nrt
  font/metric-sans-N.advances.txt MEMBERS...`, whole groups then halves, each in
  `sort -V` order. Each shipped file is byte for byte the one gated, and
  `make test-metric-sans-grey` repacks and gates every one.
- Members: `...-grey[-italic]-v1-gK.json` for seed 0 and
  `.seed1-gK.json` for seed 1, 48 per seed as trained, except for the
  shipping seed. There, a halved group's whole net is not kept, its halves
  are `-hH.json`, and a half that was left out is not kept.
- Sizes: 1,016,936 bytes for a face of 48 nets, plus 21,152 for each net
  that halving adds (a halved group is two nets in place of one). The 8 px
  upright face, with six halved groups and one half left out, is 1,122,696
  bytes.

## Speed

A new handle draws a line regular then bold, as a desktop builds its cells.
Figures are the median of 10 fresh handles (two passes of 5), single thread,
each pass under the benchmark lock, on 2026-11-24. Each figure is from the
binary face of that em to the grey face (upright to upright, italic to
italic). First use is in milliseconds; cached is the two lines drawn again,
in microseconds. ASCII is the line of 96 ASCII characters; Latin-1 is
U+00A0 to U+00FF. The grey faces cost 2 to 10% more at first use, and up to
3% more cached.

### Intel i7-10700F

| em | face | ASCII first use (ms) | ASCII cached (us) | Latin-1 first use (ms) | Latin-1 cached (us) |
|---|---|---|---|---|---|
| 8 | grey | 7.11 -> 7.36 | 100.3 -> 102.5 | 7.18 -> 7.38 | 101.5 -> 101.0 |
| 8 | grey-italic | 7.33 -> 7.67 | 102.7 -> 103.5 | 7.36 -> 7.69 | 102.9 -> 103.9 |
| 9 | grey | 8.62 -> 9.08 | 110.2 -> 112.1 | 8.83 -> 9.26 | 113.3 -> 115.2 |
| 9 | grey-italic | 8.74 -> 9.45 | 112.7 -> 114.8 | 9.00 -> 9.47 | 115.5 -> 117.3 |
| 10 | grey | 10.32 -> 11.02 | 129.6 -> 130.4 | 10.68 -> 11.01 | 133.1 -> 135.1 |
| 10 | grey-italic | 10.63 -> 11.29 | 132.9 -> 134.9 | 10.78 -> 11.43 | 135.2 -> 137.3 |
| 11 | grey | 12.20 -> 12.97 | 150.4 -> 154.1 | 12.54 -> 13.28 | 153.4 -> 156.7 |
| 11 | grey-italic | 12.40 -> 13.43 | 152.8 -> 156.9 | 12.68 -> 13.59 | 156.3 -> 159.1 |
| 12 | grey | 14.04 -> 15.02 | 171.4 -> 174.4 | 14.54 -> 15.27 | 172.8 -> 177.4 |
| 12 | grey-italic | 14.74 -> 15.66 | 175.5 -> 180.3 | 15.20 -> 15.88 | 175.1 -> 180.6 |
| 13 | grey | 16.31 -> 17.40 | 191.7 -> 194.4 | 16.73 -> 17.55 | 192.9 -> 198.9 |
| 13 | grey-italic | 16.39 -> 17.94 | 195.4 -> 201.1 | 17.07 -> 18.09 | 195.4 -> 200.4 |
| 14 | grey | 18.32 -> 19.55 | 216.2 -> 217.8 | 18.74 -> 19.42 | 218.4 -> 220.6 |
| 14 | grey-italic | 18.68 -> 20.10 | 220.7 -> 225.5 | 19.14 -> 20.35 | 222.1 -> 225.8 |
| 15 | grey | 20.60 -> 21.97 | 241.2 -> 242.5 | 21.34 -> 21.71 | 243.6 -> 244.2 |
| 15 | grey-italic | 21.11 -> 22.63 | 245.8 -> 250.2 | 21.53 -> 22.53 | 246.3 -> 250.4 |
| 16 | grey | 23.57 -> 24.25 | 270.9 -> 271.6 | 23.82 -> 24.70 | 273.1 -> 274.1 |
| 16 | grey-italic | 24.05 -> 25.44 | 276.6 -> 282.6 | 24.85 -> 25.52 | 277.1 -> 281.9 |
### Intel i7-6820HQ

| em | face | ASCII first use (ms) | ASCII cached (us) | Latin-1 first use (ms) | Latin-1 cached (us) |
|---|---|---|---|---|---|
| 8 | grey | 9.90 -> 10.33 | 145.2 -> 148.0 | 10.11 -> 10.39 | 150.4 -> 150.2 |
| 8 | grey-italic | 10.09 -> 10.70 | 150.7 -> 151.9 | 10.28 -> 10.83 | 152.8 -> 154.9 |
| 9 | grey | 12.15 -> 12.75 | 163.7 -> 165.5 | 12.40 -> 13.07 | 169.2 -> 172.1 |
| 9 | grey-italic | 12.14 -> 13.35 | 167.2 -> 170.3 | 12.49 -> 13.31 | 172.6 -> 174.6 |
| 10 | grey | 14.51 -> 15.37 | 192.3 -> 193.1 | 14.99 -> 15.40 | 198.0 -> 200.7 |
| 10 | grey-italic | 14.80 -> 15.85 | 197.6 -> 201.5 | 15.01 -> 15.99 | 200.3 -> 204.4 |
| 11 | grey | 17.00 -> 18.01 | 219.4 -> 223.9 | 17.48 -> 18.48 | 225.0 -> 230.4 |
| 11 | grey-italic | 17.21 -> 18.80 | 226.6 -> 233.8 | 17.50 -> 18.99 | 230.6 -> 237.1 |
| 12 | grey | 19.56 -> 20.96 | 253.4 -> 257.6 | 20.06 -> 21.27 | 255.6 -> 263.1 |
| 12 | grey-italic | 20.45 -> 21.87 | 260.4 -> 267.7 | 21.10 -> 22.15 | 259.9 -> 268.1 |
| 13 | grey | 22.75 -> 24.32 | 283.8 -> 287.4 | 23.62 -> 24.78 | 289.7 -> 292.7 |
| 13 | grey-italic | 22.76 -> 25.09 | 290.4 -> 297.4 | 23.56 -> 25.01 | 286.6 -> 291.7 |
| 14 | grey | 25.86 -> 27.33 | 311.3 -> 317.1 | 25.93 -> 26.82 | 317.2 -> 320.5 |
| 14 | grey-italic | 26.00 -> 28.14 | 321.9 -> 329.6 | 26.57 -> 28.47 | 321.8 -> 329.2 |
| 15 | grey | 28.45 -> 30.65 | 350.0 -> 353.2 | 29.58 -> 30.27 | 353.4 -> 356.1 |
| 15 | grey-italic | 29.23 -> 31.64 | 361.3 -> 365.8 | 29.85 -> 31.47 | 359.6 -> 366.2 |
| 16 | grey | 32.45 -> 33.56 | 397.6 -> 396.4 | 32.89 -> 34.27 | 398.6 -> 403.7 |
| 16 | grey-italic | 33.17 -> 35.31 | 402.9 -> 412.6 | 34.33 -> 35.51 | 404.1 -> 407.3 |
