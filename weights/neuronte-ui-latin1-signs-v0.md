# All of Latin-1 in the scaled and large desktop faces (`neuronte-ui-latin1-signs-v0`)

Two nets that draw the 38 Latin-1 characters that are not a letter with a mark:

    ¡ ¢ £ ¤ ¥ ¦ § © ª « ¬ SHY ® ° ± ² ³ µ ¶ · ¹ º » ¼ ½ ¾ ¿ Æ Ð × Ø Þ ß æ ð ÷ ø þ

They go in three new files beside the nets already shipped:

- `neuronte-ui-scaled-latin1-v1.nrt`, 17 to 32 px, snapped below 33 px.
  - Members: the 16 `neuronte-ui-scaled-v0` nets, the two `neuronte-ui-latin1-v0` nets (the 58 composed letters) and these two.
  - 3,250,312 bytes.
  - Advances: `font/ui-scaled-latin1-full-advances.txt`.
  - Letter edges: set `uilargexx`.
- `neuronte-ui-large-latin1-v2.nrt`, 33 px up.
  - Members: the four `neuronte-ui-large-v1` nets, the same two Latin-1 nets and these two.
  - 2,946,196 bytes.
  - Advances: `font/ui-large-latin1-full-advances.txt`.
- `neuronte-ui-scaled-latin1-italic-advances-v1.nrt`: the italic advance table, 1,568 bytes.

Each file covers printable ASCII, U+2026 and U+00A0 to U+00FF (192 characters), regular and bold. Their ASCII and their 58 composed letters draw byte for byte as `neuronte-ui-scaled-latin1-v0` and `neuronte-ui-large-latin1-v1` do (17-32 px binary and blended; 33, 48 and 64 px blended). No older file changes.

## The drawings

`font/ui-large-latin1-signs.txt` holds strokes in the ui-large grid, drawn from the Unicode names and from ui-large's own letters:

| Characters | Drawn from |
|---|---|
| Æ | A and E |
| Ð | D with a bar |
| Ø ø | O and o with a stroke |
| Þ | P |
| þ | b and p |
| æ | a and e |
| ¢ | c |
| ¥ | Y |
| µ | u |
| ¡ ¿ | ! and ? turned |
| superscripts, ordinals | digits and a/o at 0.6 size |
| fractions | digits at 0.5 size |

The small parts (superscripts, ordinals and fractions) use pen radius 0.036 em.

U+00AD SOFT HYPHEN is drawn as the hyphen. A terminal or desktop that shows it draws a hyphen.

Advances:

- Large face: the drawn width; bold is 0.2 wider.
- Scaled face and its italic: the drawn width, moved as the fitted tables moved an ASCII character of the same shape.

## Accuracy

Gate G-L1, declared before training: per net (19 characters), the IoU of the net's coverage against the exact strokes must have mean >= 0.98 and min >= 0.90 at each of 48, 64 and 96 px. The coverage was evaluated in numpy at 1 sample per pixel, against 8 x 8 samples per pixel for the truth. Both nets passed on both seeds.

The table gives IoU mean / min, beside the shipped nets of the 58 composed letters (`neuronte-ui-latin1-v0`, scored the same way by the trainer over all 58):

| px | 38 signs g0, seed 0 | 38 signs g1, seed 0 | 38 signs g0, seed 1 | 38 signs g1, seed 1 | 58 letters, seed 0 | 58 letters, seed 1 |
|---|---|---|---|---|---|---|
| 48 | **0.9894** / 0.945 | 0.9910 / 0.931 | **0.9897** / 0.945 | 0.9902 / 0.931 | **0.9896** / 0.942 | 0.9904 / 0.944 |
| 64 | **0.9896** / 0.948 | 0.9961 / 0.989 | **0.9895** / 0.944 | 0.9960 / 0.989 | 0.9955 / 0.976 | 0.9959 / 0.976 |
| 96 | 0.9951 / 0.980 | 0.9937 / 0.970 | 0.9952 / 0.977 | 0.9933 / 0.958 | 0.9959 / 0.944 | 0.9956 / 0.903 |

Means under 0.99 are in bold.

- Net g0 (¡ to ¹) is just under 0.99 at 48 and 64 px. Its worst letters are ª (48 px) and ¢ (64 px).
- The 58 letters' seed 0 is under 0.99 at 48 px too.
- At 32 px, which is not gated: g0 0.977 / 0.879 (¶), g1 0.979 / 0.903 (Æ).

Seed 0 ships, by the declared rule: fewer summed wrong pixels at 48 px, 113 against 114.

Wrong pixels per letter through the library, mean over each set, seed 0. Each letter is drawn alone and its blended coverage is cut at 1/2, against the exact strokes at 8 x 8 samples. Below 33 px snapping moves edges off the strokes by design, so this compares the sets with each other:

| em | ASCII | 58 letters | 38 signs | worst sign |
|---|---|---|---|---|
| 17 | 7.31 | 8.86 | 6.95 | ß 23 |
| 20 | 0.47 | 1.79 | 4.47 | ± 20 |
| 24 | 2.99 | 5.76 | 5.24 | æ 25 |
| 28 | 12.24 | 9.72 | 13.08 | £ 38 |
| 32 | 6.00 | 5.69 | 8.68 | ® 29 |
| 33 | 2.01 | 2.91 | 2.55 | ® 9 |
| 48 | 1.33 | 2.83 | 2.92 | ® 18 |
| 64 | 2.23 | 2.07 | 3.29 | ¢ 26 |

Seed 1 is within 0.1 of these at every em. The sheet of both seeds is in the lane's evidence.

## Speed

A new handle draws a line regular then bold, as a desktop builds its cells. Figures are milliseconds, median of 5 fresh handles, single thread, under the benchmark lock.

| file | em | i7-10700F ASCII, old -> new | i7-10700F Latin-1 line | i7-6820HQ ASCII, old -> new | i7-6820HQ Latin-1 line |
|---|---|---|---|---|---|
| scaled | 17 | 95.3 -> 95.4 | 133.1 | 132.5 -> 134.1 | 176.4 |
| scaled | 24 | 51.0 -> 50.5 | 68.2 | 71.3 -> 70.6 | 90.8 |
| scaled | 32 | 87.6 -> 88.2 | 108.0 | 122.2 -> 122.1 | 142.1 |
| large | 33 | 116.2 -> 121.6 | 116.2 | 153.3 -> 160.7 | 151.9 |
| large | 48 | 252.8 -> 250.9 | 234.8 | 330.7 -> 327.6 | 312.2 |
| large | 64 | 418.4 -> 450.2 | 411.3 | 548.0 -> 581.2 | 555.5 |

- ASCII line: the 96 ASCII characters. "Old" is the older Latin-1 file at that em.
- Latin-1 line: U+00A0..U+00FF.
- Cached redraws are the same for old and new (within 4%).

## Training and checks

Trained on one RTX 3070, seeds 0 and 1 together, in 705 seconds. The recipe is the 58 letters' recipe, unchanged:

    python3 train/face_parts.py OUT --set uilargel1s --band --groups 2 --width 192 --steps 80000 \
        --candidates 2048 --near 384 --clamp 0.25 --name X38-bg2w192-80k-n384-c25

`make test-ui-latin1-full` is part of `make test`. It does the following:

1. Repacks both seeds of both faces.
2. Runs `tests/check_letter_snap.py` on the scaled file and `tests/check_reference.py --drawing-bundle` on the large file.
3. Checks that seed 0 repacks to the shipped files byte for byte.
4. Runs `tests/check_latin1_faces.py`: ASCII and the 58 letters draw as in the older Latin-1 files.
