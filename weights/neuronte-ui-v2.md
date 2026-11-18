# Desktop pixel faces v2: all of Latin-1 (`neuronte-uiN-v2`, `neuronte-uiN-italic-v2`)

There are 30 drawing files:

- the upright pixel face at every em from 1 to 16 px;
- the italic at every em from 3 to 16 px.

Each draws printable ASCII, U+2026 and all 96 characters from U+00A0 to U+00FF, regular and bold. Each is its `-v1` file's ASCII nets, unchanged, plus new nets for the 96 Latin-1 characters. Their ASCII draws byte for byte as the `-v1` file's, at the native em. No `-v0` or `-v1` file changes, and no default changes.

## The drawings

`font/ui-N-latin1.txt` (1 to 16 px) and `font/ui-N-latin1-italic.txt` (3 to 16 px) are new files. Each holds the face's ASCII glyphs copied byte for byte and the 96 Latin-1 glyphs. `tools/make-latin1-face.py` writes and checks them (`--check` is part of the test).

- **Letters with a mark** (the 58 composed letters and the four spacing marks): composed from the face's own letters and a mark drawn for that em range (`font/ui-latin1-marks.txt`).
  - Over a lower-case letter the mark sits one row clear of the x-height, or touching it when there is no room.
  - Over a capital the letter is lowered by dropping the inner row most like the row above it.
  - The cedilla goes below the baseline.
  - i is dotless under a mark.
- **The other 38**: drawn per em. 16 and 15 px were drawn and corrected by hand. 14 down to 3 px follow the same shapes.
- **1 and 2 px**: every Latin-1 character is the ASCII glyph it most resembles, and a letter with a mark is its base letter.
- **Italics**: tools/make-italic.py's shear of the upright, as every italic face from 3 to 16 px already is.
- **U+00AD SOFT HYPHEN**: drawn as the hyphen.

No font file was opened or rasterised to draw them.

### Characters that look the same

Small faces cannot tell every character apart. These Latin-1 characters draw the same bitmap and advance as another character of the face:

| em | Shared bitmaps |
|---|---|
| 12-16 | NBSP and space; SHY and hyphen |
| 9-11 | NBSP and space; Ì ì, Í í and Î î |
| 8 | NBSP and space |
| 7 | 10 characters, adding © ® |
| 6 | 39 characters. For example µ p; ª ° º; ¼ ½ ¾; the lower-case vowels with the same mark; ã ñ õ |
| 5 | 57 characters |
| 4 | 65 characters |
| 3 | 76 characters |
| 1-2 | all 96: at 2 px most glyphs are one of a few blocks, and at 1 px every glyph is the same dot |

## Accuracy

The gate is exact: `tests/check_reference.py --drawing-bundle` on the packed file must find every one of the 192 characters, regular and bold, exactly its drawing at the native em, with its advance. It must pass for both seeds.

Every face passes. Six faces passed only after the declared halving:

| face | the group of 4 that failed | miss |
|---|---|---|
| ui16 | À Á Â Ã | U+00C0, seed 1, 1-2 pixels |
| ui15 | À Á Â Ã | U+00C0, seed 1, 3 pixels |
| ui15-italic | À Á Â Ã and ù ú û ü | U+00C0 and U+00F9, 1-2 pixels |
| ui13-italic | à á â ã | U+00E0, seed 0, 1 pixel |
| ui11-italic | Ð Ñ Ò Ó | U+00D2 and U+00D3, 1 pixel |
| ui10-italic | è é ê ë | U+00EB, 1-2 pixels |

Each failing group of 4 was replaced by two nets of 2 characters, trained by the same recipe on both seeds. Every halved face then passed on both seeds. No character is left out of any face. Seed 0 ships, as both seeds are exact.

## What is in each file

The `-v1` members come first and are unchanged.

| Latin-1 nets | Faces |
|---|---|
| 24 (4 characters each) | the other faces from 3 to 16 px |
| 25 | ui16, ui15, ui13-italic, ui11-italic and ui10-italic |
| 26 | ui15-italic |
| 1 (all 96 characters) | ui1 and ui2 |

Nets of 3 to 16 px:
- Band-tiled distance nets 32 x 32 x 32 wide, drawing only the face's ink rows (`train/face_parts.py --band`).
- About 21 KB per net packed.
- Each face grows by about 0.5 MB.

The 1 and 2 px nets are 16 wide. The 30 files hold 33,163,952 bytes in all, against 18,760,460 for the 30 `-v1` files.

## Speed

A new handle draws a line regular then bold, as a desktop builds its cells. Figures are milliseconds, median of 5 fresh handles, single thread, under the benchmark lock.

- ASCII: the line of 96 ASCII characters, `-v1` file -> `-v2` file.
- Latin-1: the line of U+00A0..U+00FF in the `-v2` file.

| face | i7-10700F ASCII | i7-10700F Latin-1 | i7-6820HQ ASCII | i7-6820HQ Latin-1 |
|---|---|---|---|---|
| ui16 | 173.2 -> 147.6 | 23.3 | 239.2 -> 197.8 | 32.6 |
| ui16-italic | 169.1 -> 168.4 | 24.3 | 226.3 -> 226.9 | 33.4 |
| ui15 | 13.5 -> 13.5 | 21.7 | 18.6 -> 18.5 | 29.8 |
| ui14 | 9.6 -> 9.5 | 18.8 | 13.0 -> 12.9 | 25.6 |
| ui13-italic | 117.9 -> 114.6 | 16.9 | 162.1 -> 155.4 | 23.5 |
| ui12 | 9.2 -> 9.0 | 14.3 | 12.8 -> 12.7 | 20.2 |
| ui10 | 5.3 -> 5.3 | 10.4 | 7.3 -> 7.3 | 14.8 |
| ui8 | 3.8 -> 3.8 | 7.5 | 5.4 -> 5.3 | 10.3 |
| ui6 | 2.3 -> 2.3 | 4.6 | 3.2 -> 3.2 | 6.5 |
| ui4 | 1.3 -> 1.3 | 2.3 | 1.8 -> 1.7 | 3.3 |
| ui3 | 0.9 -> 0.9 | 1.5 | 1.2 -> 1.2 | 2.1 |
| ui2 | 0.5 -> 0.5 | 0.5 | 0.6 -> 0.6 | 0.6 |
| ui1 | 0.2 -> 0.2 | 0.2 | 0.3 -> 0.3 | 0.3 |

- Every other face's ASCII line is within 5% of its `-v1` figure.
- The ui16 ASCII line was faster in `-v2` on both hosts.
- Cached redraws are within 5% of `-v1`, and about 1 to 2 microseconds slower at 1 and 2 px.
- The Latin-1 line costs about twice the ASCII line where the ASCII nets are small. It costs much less in the faces whose ASCII is one large net (ui16, ui16-italic, ui13-italic).

## Training and checks

Trained on one rented RTX 4090, both seeds of a face in one job and eight jobs at a time: 9 to 13 minutes a job from 3 to 16 px, 22 minutes for the single nets of 1 and 2 px:

    python3 train/face_parts.py OUT --set uiNl1  --band --groups 24 --width 32 --steps 80000   # 3-16 px
    python3 train/face_parts.py OUT --set uiNl1i --band --groups 24 --width 32 --steps 80000   # italic
    python3 train/face_parts.py OUT --set ui2l1  --band --groups 1  --width 16 --steps 80000
    python3 train/face_parts.py OUT --set ui1l1  --band --groups 1  --width 16 --steps 80000 --pen 0.49

- **Halved groups**: the same command with `--groups 48`, keeping only the two halves of the failing group.
- **The ui1 pen**: the set's own pen at 1 px is 0.55 cell. Since the scalable-faces change, the trainer refuses a pen of 0.5 cell or more, so ui1 uses 0.49. The gate is exact either way.
- **Packing**: `train/pack.py --drawing-bundle neuronte-uiN-v2.nrt font/ui-N-latin1.txt V1-MEMBERS... LATIN1-MEMBERS...`.

`make test-faces-latin1` is part of `make test`. It does the following:

1. Checks the drawing files with `tools/make-latin1-face.py --check`.
2. Repacks both seeds of every face.
3. Runs the exact gate on both seeds.
4. Checks that seed 0 repacks to the shipped file byte for byte.
5. Checks with `tests/check_latin1_faces.py` that the ASCII draws as the `-v1` file's.
