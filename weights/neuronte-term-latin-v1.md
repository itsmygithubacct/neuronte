# term-latin-v1: 596 accented Latin, Greek and Cyrillic letters, on their own

`neuronte-term-latin-v1.nrt` is a terminal bundle for 596 characters no earlier bundle
was trained on: letters `neuronte-split-v9` already has, carrying one to three
marks (Vietnamese, Latin letters with one or two marks above or a mark
below, polytonic Greek, Cyrillic with a breve, diaeresis or macron), and
fourteen Greek marks that stand alone in a cell.
In split-v9 each of them goes to the router's gate and is drawn by a net
that never saw it, so it comes out as some other shape (over these
characters split-v9's mean overlap with the drawing is
0.02 to 0.21 at 8×16; this bundle's is
0.94 to 1.00).

It is a **standalone** bundle: 74 known-only group nets and one blank net,
4,280,128 bytes, with no copy of split-v9 in it. A program opens it beside
split-v9 and asks it first (see "What a consumer changes").

| Characters | Training set | Group nets | Declared gates |
|---|---|---|---|
| 47 Vietnamese capitals: Ạ Ả Ấ Ầ Ẩ Ẫ Ậ Ắ Ằ Ẳ Ẵ Ặ Ẹ Ẻ ... | `tlvu` | 6×H64/96 | 2 of 6 passed; the failed groups chosen by the owner |
| 47 Vietnamese smalls: ạ ả ấ ầ ẩ ẫ ậ ắ ằ ẳ ẵ ặ ẹ ẻ ... | `tlvl` | 6×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 52 Latin capitals, one mark above: Ȧ Ȯ Ḃ Ḋ Ḟ Ḣ Ṁ Ṅ Ṗ Ṙ Ṡ Ṫ Ẇ Ẋ ... | `tlau` | 6×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 56 Latin smalls, one mark above: ȧ ȯ ḃ ḋ ḟ ḣ ṁ ṅ ṗ ṙ ṡ ṫ ẇ ẋ ... | `tlal` | 6×H64 | 1 of 6 passed; the failed groups chosen by the owner |
| 21 Latin capitals, two marks above: Ṥ Ṍ Ṹ Ȭ Ṏ Ḕ Ṑ Ḗ Ṓ Ṻ Ǡ Ȱ Ǜ Ǘ ... | `tl2u` | 3×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 21 Latin smalls, two marks above: ṥ ṍ ṹ ȭ ṏ ḕ ṑ ḗ ṓ ṻ ǡ ȱ ǜ ǘ ... | `tl2l` | 3×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 45 Latin capitals, a mark below: Ḅ Ḍ Ḥ Ḳ Ḷ Ḹ Ṃ Ṇ Ṛ Ṝ Ṣ Ṩ Ṭ Ṿ ... | `tlbu` | 5×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 46 Latin smalls, a mark below: ḅ ḍ ḥ ḳ ḷ ḹ ṃ ṇ ṛ ṝ ṣ ṩ ṭ ṿ ... | `tlbl` | 5×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 15 Cyrillic capitals: Ӂ Ӑ Ӓ Ӗ Ӝ Ӟ Ӣ Ӥ Ӧ Ӭ Ӯ Ӱ Ӳ Ӵ ... | `tlcu` | 2×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 15 Cyrillic smalls: ӂ ӑ ӓ ӗ ӝ ӟ ӣ ӥ ӧ ӭ ӯ ӱ ӳ ӵ ... | `tlcl` | 2×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 96 Greek capitals: Ἀ Ἁ Ἂ Ἃ Ἄ Ἅ Ἆ Ἇ ᾈ ᾉ ᾊ ᾋ ᾌ ᾍ ... | `tlgu` | 12×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 121 Greek smalls: ἀ ἁ ἂ ἃ ἄ ἅ ἆ ἇ ὰ ά ᾀ ᾁ ᾂ ᾃ ... | `tlgl` | 16×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |
| 14 Greek marks alone in the cell: U+0385 U+1FBD U+1FBF U+1FC0 ... | `tlgs` | 2×H64 | **failed**, every group, both seeds; the failed groups chosen by the owner |

**Not a default, and not a replacement for split-v9.** 3 of the 74 groups
passed the rules declared before training; 71 failed them with both
seeds or one, at width 64 and again on the one declared retry at width 96.
The owner was shown failing groups side by side (teacher, split-v9 today,
both seeds, at 8×16, 12×24 and 16×32; twenty groups at that time), said
"they all look good", was asked what to do with groups that still fail, and
chose "Ship them, width 64": each ships its width 64 net, the seed with the
lower error. The final sheet shows all 74 groups; the owner's words on it,
as relayed afterwards, were "the screens look good". None of this changes a
measurement or turns a failure into a pass. Every failure is in `neuronte-term-latin-v1.validation.json`.

## How the gates failed

The gates take their limits from split-v9's own letter groups: its 20 Greek
letters with tonos for the three Greek sets, its 32 Cyrillic letters for the
others. Each limit is that set's figure plus a small slack (mean error
+0.0015, 99th percentile +0.02, mean overlap −0.005), counted at 6×12, 8×16,
10×20, 12×24, 16×32, 24×48 and 48×96, and with one sample a pixel at 8×16,
16×32 and 48×96. Both seeds have to pass. Smaller cells are measured and
never counted.

These limits are strict: split-v9's own five letter groups do not meet them
either, each being held to the average of its set. That was found in a dry
run before any result was in, and the gates were left as declared. A second
line was fixed then, for information only: "no worse, at any counted size,
than the worst letter group net split-v9 ships". 4 of the 74 groups
meet that line with both seeds.

Every group net passes the C-against-float64 check. Of the 71 failing
groups:

- **41 Latin and Cyrillic groups.** 33 of them pass mean error at every
  counted size. What fails there is mean overlap (coverage cut at one
  half) at one or more counted sizes, or the one-sample rules at 8×16.
- **30 Greek groups.** 17 of them pass mean error at every counted size;
  the capitals, which carry a breathing or an accent beside the letter,
  miss the most rules (up to 18 in one group).
- **Rules missed, by number of groups** (either seed; `s1` is one sample a
  pixel, `iou_mean` mean overlap, `firm` pixels on the wrong
  side of one half where the drawing is at least 0.1 from it):
  s1 8x16 mae 37, 12x24 iou_mean 30, s1 8x16 iou_mean 29, s1 8x16 firm 27, s1 8x16 p99 26, 24x48 iou_mean 26, 6x12 iou_mean 24, 10x20 iou_mean 20, s1 16x32 iou_mean 18, s1 16x32 mae 18, 16x32 iou_mean 16, 8x16 iou_mean 15.
  Overlap rules are 206 of the 403 group-rule misses.
- **Width was not the limit.** The retry at width 96 (half again the
  hidden units, same characters, seeds and steps) moved mean error by a
  few percent and passed 1 group; elsewhere the same rules failed.
  Overlap is measured after cutting coverage at one half, and it fails
  where mean error passes. That is the pattern pixels near one half give;
  it was not measured pixel by pixel here.

**Small cells.** At every counted size every character is nearest its own drawing and none vanishes, in every group and both seeds. Ӹ and ӹ (yeru with diaeresis) overlap their drawing at 6×12 by 0.44 and
0.40 in both seeds, the lowest of any character. Below 6×12 nothing is
counted; the validation record has every group's measurements down to 1×2.

## What a consumer changes

Nothing, until it opens this file. It does not replace split-v9 and holds
none of its characters; `tests/check_bundle_lists.py` checks that the two
share no trained scalar.

```c
neuronte_open_file("neuronte-split-v9.nrt", &base);
neuronte_open_file("neuronte-term-latin-v1.nrt", &latin);
/* for each scalar c */
font = neuronte_untrained(latin, c) ? base : latin;
```

`neuronte_untrained(latin, c)` is 0 for exactly the 596 characters in
`neuronte-term-latin-v1.list.txt` and 1 for every other scalar. A scalar outside
the list, drawn through this file anyway, comes out blank (the file's
fallback is a net that draws nothing), or as the code-made hollow box after
`neuronte_set_untrained(latin, 1)`. The file needs the current runtime
(version 2 bundles, 128-member limit). It has 75 members.

Cells are the terminal's 1:2 cell; the nets were trained and measured from
6×12 to 48×96.

## Recipe

- **Drawings.** `train/glyphs.py` composes each character from a letter
  split-v9 already has and one to three marks of `font/marks.txt`, by the
  Unicode decomposition. No font was read; DejaVu Sans Mono 2.37 gave only
  its list of code points. The list is `font/term-latin.txt`. The owner
  approved the drawings on a sheet before training.
- **Sets and groups.** Thirteen sets by script, case and kind of marking;
  each cut in order into group nets of 7 to 10 characters (74 in all).
- **Training.** `train/split_expert.py train --mode repertoire --partition
  contiguous`, unchanged: hidden width 64, 120,000 steps, the project
  teacher (grid 256), seeds 0 and 1. The retry: width 96, the rest the same.
- **Selection.** Declared: a group whose two seeds pass ships the seed with
  the lower mean error over 8×16, 16×32 and 48×96. By the owner's choice: a
  group that still fails ships its width 64 net, the lower-error seed.
  Only the shipped seed's JSON is in `weights/`; the other seed's hash and
  measurements are in the validation record.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from
  each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
make pack-term-latin-v1    # rebuilds the .nrt byte for byte from the group nets
make test-term-latin-v1
```

## Checks

`make test-term-latin-v1` (part of `make test`): every group net against
the float64 reference; the bundle rebuilt byte for byte; its table exactly
`neuronte-term-latin-v1.list.txt`, which is `font/term-latin.txt`;
every scalar from U+0000 to U+10FFFF routed as the table says; pixels through
the bundle equal to each group net alone at 19 cell sizes and with one
sample a pixel; `test_api --standalone`; and the validation record's hashes.

## Results by group

Mean error against the teacher at 8×16, 16×32 and 48×96, and mean overlap at 8×16, for the shipped net. "B" marks the groups that meet the information-only second line.

| Set | Group | Characters | Net | Declared gates | Rules missed (seed 0 / seed 1) | Mean error | Overlap 8×16 |
|---|---:|---|---|---|---|---|---:|
| `tlvu` | 0 | Ạ Ả Ấ Ầ Ẩ Ẫ Ậ | H64, seed 0 | **failed**; owner's choice | 4 / 4 | 0.0047 0.0025 0.0015 | 0.923 |
| `tlvu` | 1 | Ắ Ằ Ẳ Ẵ Ặ Ẹ Ẻ Ẽ | H64, seed 0 | **failed**; owner's choice | 4 / 5 | 0.0070 0.0038 0.0018 | 0.948 |
| `tlvu` | 2 | Ế Ề Ể Ễ Ệ Ỉ Ị Ơ | H64, seed 1 | **failed**; owner's choice | 11 / 10 | 0.0087 0.0051 0.0020 | 0.985 |
| `tlvu` | 3 | Ọ Ỏ Ố Ồ Ổ Ỗ Ộ Ớ | H96, seed 1 | passed on the retry · B | 0 / 0 | 0.0057 0.0027 0.0016 | 0.996 |
| `tlvu` | 4 | Ờ Ở Ỡ Ợ Ư Ụ Ủ Ứ | H64, seed 1 | **failed**; owner's choice · B | 1 / 1 | 0.0063 0.0027 0.0018 | 0.987 |
| `tlvu` | 5 | Ừ Ử Ữ Ự Ỳ Ỵ Ỷ Ỹ | H64, seed 1 | passed · B | 0 / 0 | 0.0061 0.0030 0.0017 | 0.987 |
| `tlvl` | 0 | ạ ả ấ ầ ẩ ẫ ậ | H64, seed 0 | **failed**; owner's choice | 7 / 8 | 0.0066 0.0036 0.0020 | 0.996 |
| `tlvl` | 1 | ắ ằ ẳ ẵ ặ ẹ ẻ ẽ | H64, seed 1 | **failed**; owner's choice | 9 / 7 | 0.0063 0.0034 0.0020 | 0.993 |
| `tlvl` | 2 | ế ề ể ễ ệ ỉ ị ơ | H64, seed 1 | **failed**; owner's choice | 6 / 6 | 0.0061 0.0035 0.0018 | 1.000 |
| `tlvl` | 3 | ọ ỏ ố ồ ổ ỗ ộ ớ | H64, seed 0 | **failed**; owner's choice | 1 / 1 | 0.0043 0.0025 0.0016 | 1.000 |
| `tlvl` | 4 | ờ ở ỡ ợ ư ụ ủ ứ | H64, seed 0 | **failed**; owner's choice | 1 / 2 | 0.0047 0.0023 0.0014 | 0.977 |
| `tlvl` | 5 | ừ ử ữ ự ỳ ỵ ỷ ỹ | H64, seed 1 | **failed**; owner's choice · B | 1 / 0 | 0.0046 0.0022 0.0015 | 0.975 |
| `tlau` | 0 | Ȧ Ȯ Ḃ Ḋ Ḟ Ḣ Ṁ Ṅ | H64, seed 1 | **failed**; owner's choice | 3 / 3 | 0.0066 0.0031 0.0016 | 0.958 |
| `tlau` | 1 | Ṗ Ṙ Ṡ Ṫ Ẇ Ẋ Ẏ Ǹ Ẁ | H64, seed 0 | **failed**; owner's choice | 1 / 0 | 0.0055 0.0027 0.0015 | 0.972 |
| `tlau` | 2 | Ǵ Ǽ Ǿ Ḱ Ḿ Ṕ Ẃ Ẑ Ṽ | H64, seed 1 | **failed**; owner's choice | 2 / 3 | 0.0068 0.0033 0.0020 | 0.976 |
| `tlau` | 3 | Ǣ Ȳ Ḡ Ḧ Ẅ Ẍ Å Ǎ | H64, seed 0 | **failed**; owner's choice | 10 / 11 | 0.0063 0.0034 0.0017 | 0.965 |
| `tlau` | 4 | Ǐ Ǒ Ǔ Ǧ Ǩ Ȟ Ȁ Ȅ Ȉ | H64, seed 1 | **failed**; owner's choice | 3 / 3 | 0.0075 0.0040 0.0021 | 0.969 |
| `tlau` | 5 | Ȍ Ȑ Ȕ Ȃ Ȇ Ȋ Ȏ Ȓ Ȗ | H64, seed 0 | **failed**; owner's choice | 2 / 2 | 0.0076 0.0034 0.0019 | 0.969 |
| `tlal` | 0 | ȧ ȯ ḃ ḋ ḟ ḣ ṁ ṅ ṗ | H64, seed 1 | **failed**; owner's choice | 6 / 7 | 0.0053 0.0025 0.0014 | 0.949 |
| `tlal` | 1 | ṙ ṡ ṫ ẇ ẋ ẏ ẛ ǹ ẁ | H64, seed 1 | **failed**; owner's choice | 3 / 3 | 0.0043 0.0020 0.0013 | 0.943 |
| `tlal` | 2 | ǵ ǽ ǿ ḱ ḿ ṕ ẃ ẑ ṽ ǣ | H64, seed 0 | **failed**; owner's choice | 2 / 4 | 0.0066 0.0032 0.0020 | 0.981 |
| `tlal` | 3 | ȳ ḡ ḧ ẅ ẍ ẗ ẘ ẙ ǎ | H64, seed 1 | **failed**; owner's choice | 1 / 1 | 0.0056 0.0025 0.0017 | 0.969 |
| `tlal` | 4 | ǐ ǒ ǔ ǧ ǩ ǰ ȟ ȁ ȅ | H64, seed 1 | passed | 0 / 0 | 0.0065 0.0034 0.0020 | 0.974 |
| `tlal` | 5 | ȉ ȍ ȑ ȕ ȃ ȇ ȋ ȏ ȓ ȗ | H64, seed 0 | **failed**; owner's choice | 2 / 1 | 0.0051 0.0028 0.0016 | 0.981 |
| `tl2u` | 0 | Ṥ Ṍ Ṹ Ȭ Ṏ Ḕ Ṑ | H64, seed 1 | **failed**; owner's choice | 4 / 3 | 0.0076 0.0038 0.0019 | 0.992 |
| `tl2u` | 1 | Ḗ Ṓ Ṻ Ǡ Ȱ Ǜ Ǘ | H64, seed 0 | **failed**; owner's choice | 5 / 5 | 0.0074 0.0037 0.0018 | 0.973 |
| `tl2u` | 2 | Ḯ Ǖ Ǟ Ȫ Ǚ Ǻ Ṧ | H64, seed 0 | **failed**; owner's choice | 8 / 7 | 0.0068 0.0032 0.0018 | 0.978 |
| `tl2l` | 0 | ṥ ṍ ṹ ȭ ṏ ḕ ṑ | H64, seed 1 | **failed**; owner's choice | 5 / 5 | 0.0060 0.0032 0.0018 | 0.965 |
| `tl2l` | 1 | ḗ ṓ ṻ ǡ ȱ ǜ ǘ | H64, seed 0 | **failed**; owner's choice | 5 / 5 | 0.0067 0.0032 0.0017 | 0.976 |
| `tl2l` | 2 | ḯ ǖ ǟ ȫ ǚ ǻ ṧ | H64, seed 1 | **failed**; owner's choice | 4 / 4 | 0.0072 0.0033 0.0018 | 0.966 |
| `tlbu` | 0 | Ḅ Ḍ Ḥ Ḳ Ḷ Ḹ Ṃ Ṇ Ṛ | H64, seed 0 | **failed**; owner's choice | 5 / 3 | 0.0083 0.0036 0.0019 | 0.961 |
| `tlbu` | 1 | Ṝ Ṣ Ṩ Ṭ Ṿ Ẉ Ẓ Ṳ Ḁ | H64, seed 0 | **failed**; owner's choice | 1 / 1 | 0.0059 0.0033 0.0016 | 0.976 |
| `tlbu` | 2 | Ș Ț Ȩ Ḉ Ḑ Ḝ Ḩ Ǫ Ǭ | H64, seed 1 | **failed**; owner's choice | 9 / 9 | 0.0086 0.0040 0.0021 | 0.982 |
| `tlbu` | 3 | Ḓ Ḙ Ḽ Ṋ Ṱ Ṷ Ḫ Ḛ Ḭ | H64, seed 1 | **failed**; owner's choice | 7 / 7 | 0.0094 0.0046 0.0022 | 0.984 |
| `tlbu` | 4 | Ṵ Ḇ Ḏ Ḵ Ḻ Ṉ Ṟ Ṯ Ẕ | H64, seed 0 | **failed**; owner's choice | 9 / 8 | 0.0092 0.0049 0.0022 | 0.977 |
| `tlbl` | 0 | ḅ ḍ ḥ ḳ ḷ ḹ ṃ ṇ ṛ | H64, seed 1 | **failed**; owner's choice | 4 / 4 | 0.0063 0.0034 0.0016 | 0.944 |
| `tlbl` | 1 | ṝ ṣ ṩ ṭ ṿ ẉ ẓ ṳ ḁ | H64, seed 1 | **failed**; owner's choice | 2 / 2 | 0.0049 0.0024 0.0014 | 0.972 |
| `tlbl` | 2 | ș ț ȩ ḉ ḑ ḝ ḩ ǫ ǭ | H64, seed 1 | **failed**; owner's choice | 4 / 5 | 0.0060 0.0026 0.0018 | 0.975 |
| `tlbl` | 3 | ḓ ḙ ḽ ṋ ṱ ṷ ḫ ḛ ḭ | H64, seed 0 | **failed**; owner's choice | 6 / 5 | 0.0068 0.0033 0.0018 | 0.951 |
| `tlbl` | 4 | ṵ ḇ ḏ ḵ ḻ ṉ ṟ ṯ ẕ ẖ | H64, seed 1 | **failed**; owner's choice | 5 / 7 | 0.0073 0.0039 0.0018 | 0.953 |
| `tlcu` | 0 | Ӂ Ӑ Ӓ Ӗ Ӝ Ӟ Ӣ | H64, seed 1 | **failed**; owner's choice | 12 / 10 | 0.0078 0.0038 0.0020 | 0.960 |
| `tlcu` | 1 | Ӥ Ӧ Ӭ Ӯ Ӱ Ӳ Ӵ Ӹ | H64, seed 1 | **failed**; owner's choice | 5 / 5 | 0.0063 0.0033 0.0018 | 0.981 |
| `tlcl` | 0 | ӂ ӑ ӓ ӗ ӝ ӟ ӣ | H64, seed 0 | **failed**; owner's choice | 6 / 6 | 0.0078 0.0030 0.0020 | 0.982 |
| `tlcl` | 1 | ӥ ӧ ӭ ӯ ӱ ӳ ӵ ӹ | H64, seed 1 | **failed**; owner's choice | 2 / 2 | 0.0058 0.0027 0.0016 | 0.982 |
| `tlgu` | 0 | Ἀ Ἁ Ἂ Ἃ Ἄ Ἅ Ἆ Ἇ | H64, seed 1 | **failed**; owner's choice | 5 / 5 | 0.0042 0.0025 0.0012 | 0.996 |
| `tlgu` | 1 | ᾈ ᾉ ᾊ ᾋ ᾌ ᾍ ᾎ ᾏ | H64, seed 1 | **failed**; owner's choice | 7 / 7 | 0.0058 0.0030 0.0015 | 0.969 |
| `tlgu` | 2 | Ᾰ Ᾱ Ὰ Ά ᾼ Ἐ Ἑ Ἒ | H64, seed 1 | **failed**; owner's choice | 10 / 10 | 0.0065 0.0038 0.0017 | 0.967 |
| `tlgu` | 3 | Ἓ Ἔ Ἕ Ὲ Έ Ἠ Ἡ Ἢ | H64, seed 0 | **failed**; owner's choice | 13 / 13 | 0.0108 0.0055 0.0022 | 0.985 |
| `tlgu` | 4 | Ἣ Ἤ Ἥ Ἦ Ἧ ᾘ ᾙ ᾚ | H64, seed 1 | **failed**; owner's choice | 16 / 16 | 0.0128 0.0052 0.0025 | 0.987 |
| `tlgu` | 5 | ᾛ ᾜ ᾝ ᾞ ᾟ Ὴ Ή ῌ | H64, seed 0 | **failed**; owner's choice | 17 / 18 | 0.0130 0.0050 0.0026 | 0.948 |
| `tlgu` | 6 | Ἰ Ἱ Ἲ Ἳ Ἴ Ἵ Ἶ Ἷ | H64, seed 1 | **failed**; owner's choice | 10 / 10 | 0.0090 0.0049 0.0017 | 0.730 |
| `tlgu` | 7 | Ῐ Ῑ Ὶ Ί Ὀ Ὁ Ὂ Ὃ | H64, seed 0 | **failed**; owner's choice | 7 / 8 | 0.0069 0.0038 0.0015 | 0.920 |
| `tlgu` | 8 | Ὄ Ὅ Ὸ Ό Ῥ Ὑ Ὓ Ὕ | H64, seed 0 | **failed**; owner's choice | 5 / 5 | 0.0062 0.0030 0.0015 | 0.927 |
| `tlgu` | 9 | Ὗ Ῠ Ῡ Ὺ Ύ Ὠ Ὡ Ὢ | H64, seed 0 | **failed**; owner's choice | 4 / 3 | 0.0060 0.0034 0.0018 | 0.909 |
| `tlgu` | 10 | Ὣ Ὤ Ὥ Ὦ Ὧ ᾨ ᾩ ᾪ | H64, seed 0 | **failed**; owner's choice | 12 / 12 | 0.0074 0.0040 0.0024 | 0.958 |
| `tlgu` | 11 | ᾫ ᾬ ᾭ ᾮ ᾯ Ὼ Ώ ῼ | H64, seed 1 | **failed**; owner's choice | 13 / 13 | 0.0077 0.0043 0.0025 | 0.965 |
| `tlgl` | 0 | ἀ ἁ ἂ ἃ ἄ ἅ ἆ | H64, seed 0 | **failed**; owner's choice | 4 / 4 | 0.0055 0.0026 0.0017 | 0.990 |
| `tlgl` | 1 | ἇ ὰ ά ᾀ ᾁ ᾂ ᾃ ᾄ | H64, seed 0 | **failed**; owner's choice | 4 / 4 | 0.0060 0.0029 0.0019 | 0.988 |
| `tlgl` | 2 | ᾅ ᾆ ᾇ ᾰ ᾱ ᾲ ᾳ | H64, seed 0 | **failed**; owner's choice | 3 / 3 | 0.0060 0.0029 0.0019 | 0.990 |
| `tlgl` | 3 | ᾴ ᾶ ᾷ ἐ ἑ ἒ ἓ ἔ | H64, seed 0 | **failed**; owner's choice | 4 / 4 | 0.0055 0.0024 0.0016 | 0.987 |
| `tlgl` | 4 | ἕ ὲ έ ἠ ἡ ἢ ἣ | H64, seed 0 | **failed**; owner's choice | 5 / 4 | 0.0064 0.0023 0.0015 | 0.974 |
| `tlgl` | 5 | ἤ ἥ ἦ ἧ ὴ ή ᾐ ᾑ | H64, seed 0 | **failed**; owner's choice | 4 / 4 | 0.0080 0.0027 0.0018 | 0.952 |
| `tlgl` | 6 | ᾒ ᾓ ᾔ ᾕ ᾖ ᾗ ῂ | H64, seed 1 | **failed**; owner's choice | 7 / 7 | 0.0092 0.0032 0.0020 | 0.956 |
| `tlgl` | 7 | ῃ ῄ ῆ ῇ ἰ ἱ ἲ ἳ | H64, seed 1 | **failed**; owner's choice | 4 / 3 | 0.0058 0.0025 0.0014 | 0.942 |
| `tlgl` | 8 | ἴ ἵ ἶ ἷ ὶ ί ῐ ῑ | H64, seed 0 | **failed**; owner's choice | 5 / 4 | 0.0041 0.0023 0.0012 | 0.933 |
| `tlgl` | 9 | ῒ ΐ ῖ ῗ ὀ ὁ ὂ | H64, seed 1 | **failed**; owner's choice | 2 / 2 | 0.0037 0.0024 0.0013 | 0.944 |
| `tlgl` | 10 | ὃ ὄ ὅ ὸ ό ῤ ῥ ὐ | H64, seed 0 | **failed**; owner's choice | 3 / 3 | 0.0040 0.0022 0.0014 | 1.000 |
| `tlgl` | 11 | ὑ ὒ ὓ ὔ ὕ ὖ ὗ | H64, seed 0 | **failed**; owner's choice | 2 / 2 | 0.0063 0.0027 0.0015 | 0.994 |
| `tlgl` | 12 | ὺ ύ ῠ ῡ ῢ ΰ ῦ ῧ | H64, seed 0 | **failed**; owner's choice | 1 / 1 | 0.0060 0.0026 0.0015 | 1.000 |
| `tlgl` | 13 | ὠ ὡ ὢ ὣ ὤ ὥ ὦ | H64, seed 0 | **failed**; owner's choice | 10 / 10 | 0.0092 0.0049 0.0019 | 1.000 |
| `tlgl` | 14 | ὧ ὼ ώ ᾠ ᾡ ᾢ ᾣ ᾤ | H64, seed 0 | **failed**; owner's choice | 10 / 10 | 0.0094 0.0053 0.0021 | 1.000 |
| `tlgl` | 15 | ᾥ ᾦ ᾧ ῲ ῳ ῴ ῶ ῷ | H64, seed 0 | **failed**; owner's choice | 10 / 10 | 0.0099 0.0054 0.0022 | 1.000 |
| `tlgs` | 0 | U+0385 U+1FBD U+1FBF U+1FC0 U+1FC1 U+1FCD U+1FCE | H64, seed 1 | **failed**; owner's choice | 3 / 3 | 0.0015 0.0007 0.0005 | 1.000 |
| `tlgs` | 1 | U+1FCF U+1FDD U+1FDE U+1FDF U+1FED U+1FEE U+1FFE | H64, seed 1 | **failed**; owner's choice | 1 / 1 | 0.0022 0.0009 0.0006 | 1.000 |

## The whole bundle against split-v9 on the same characters

Mean error and mean overlap against the teacher, automatic sampling. split-v9 draws each of these through its gate, with a net that never saw it.

| Set | Characters | split-v9 8×16 | term-latin-v1 8×16 | split-v9 16×32 | term-latin-v1 16×32 | split-v9 48×96 | term-latin-v1 48×96 |
|---|---:|---|---|---|---|---|---|
| Vietnamese capitals | 47 | 0.243, 0.06 | 0.0064, 0.972 | 0.267, 0.11 | 0.0033, 0.975 | 0.276, 0.12 | 0.0017, 0.993 |
| Vietnamese smalls | 47 | 0.244, 0.05 | 0.0054, 0.990 | 0.266, 0.10 | 0.0029, 0.988 | 0.275, 0.11 | 0.0017, 0.994 |
| Latin capitals, one mark above | 52 | 0.237, 0.12 | 0.0067, 0.968 | 0.256, 0.14 | 0.0033, 0.983 | 0.263, 0.16 | 0.0018, 0.991 |
| Latin smalls, one mark above | 56 | 0.226, 0.13 | 0.0056, 0.967 | 0.246, 0.15 | 0.0028, 0.991 | 0.253, 0.16 | 0.0016, 0.995 |
| Latin capitals, two marks above | 21 | 0.223, 0.12 | 0.0073, 0.981 | 0.245, 0.15 | 0.0036, 0.964 | 0.253, 0.16 | 0.0018, 0.989 |
| Latin smalls, two marks above | 21 | 0.212, 0.17 | 0.0066, 0.969 | 0.234, 0.18 | 0.0032, 0.970 | 0.240, 0.19 | 0.0018, 0.992 |
| Latin capitals, a mark below | 45 | 0.244, 0.12 | 0.0083, 0.976 | 0.270, 0.14 | 0.0041, 0.983 | 0.281, 0.15 | 0.0020, 0.996 |
| Latin smalls, a mark below | 46 | 0.221, 0.10 | 0.0063, 0.959 | 0.240, 0.15 | 0.0031, 0.997 | 0.248, 0.16 | 0.0017, 0.996 |
| Cyrillic capitals | 15 | 0.215, 0.17 | 0.0070, 0.971 | 0.228, 0.17 | 0.0035, 0.986 | 0.234, 0.17 | 0.0019, 0.992 |
| Cyrillic smalls | 15 | 0.195, 0.21 | 0.0068, 0.982 | 0.205, 0.20 | 0.0028, 0.985 | 0.209, 0.21 | 0.0018, 0.996 |
| Greek capitals | 96 | 0.272, 0.02 | 0.0080, 0.938 | 0.295, 0.08 | 0.0040, 0.955 | 0.304, 0.09 | 0.0019, 0.985 |
| Greek smalls | 121 | 0.251, 0.04 | 0.0066, 0.978 | 0.272, 0.09 | 0.0031, 0.996 | 0.281, 0.10 | 0.0017, 0.995 |
| Greek marks alone in the cell | 14 | 0.169, 0.02 | 0.0018, 1.000 | 0.168, 0.04 | 0.0008, 0.998 | 0.168, 0.04 | 0.0005, 0.990 |

## Speed

Measured on one rented datacenter machine, an AMD EPYC 7B13 (64 cores, shared
with other tenants; load average 8 to 6 of 128 threads during the run),
at the owner's instruction, in place of the two x86 hosts other cards use.
The numbers compare the two bundles with each other on that machine; they
are not comparable with other cards' numbers.

kilix-bench e21e5cd: one pinned core, a fresh process for every job, one
warmup and ten measured rounds in shuffled order, medians, every model
checked against the float64 reference first. The corpus is this bundle's
596 characters. split-v9 sends each through its gate to another of its
nets, which never saw it; term-latin-v1 looks it up in its table and runs
a small group net.

| µs per character | split-v9 | term-latin-v1 | split-v9 / term-latin-v1 |
|---|---:|---:|---:|
| Coverage, uncached, 8×16 | 450.2 | 146.5 | 3.07 |
| Coverage, uncached, 16×32 | 1749.8 | 556.3 | 3.15 |
| Coverage, uncached, 48×96 | 3919.6 | 1227.1 | 3.19 |
| Draw, cold, 8×16 | 453.1 | 149.6 | 3.03 |
| Draw, cold, 16×32 | 1761.4 | 563.0 | 3.13 |
| Draw, cold, 48×96 | 3964.6 | 1262.0 | 3.14 |
| Draw, warm, 8×16 | 9.1 | 2.1 | 4.30 |
| Draw, warm, 16×32 | 29.1 | 7.3 | 4.00 |
| Draw, warm, 48×96 | 76.5 | 30.5 | 2.51 |

Uncached, term-latin-v1 draws these characters 3.1 times as fast as
split-v9's fallback does (geometric mean over the three cells; cold draw
3.1, warm draw 3.5). A lookup in its table takes 15 ns against
994 ns for split-v9's gate. Opening the file takes 7.5 ms against 6.8 ms
for split-v9; a program that opens both pays both.

A handle caches 1,024 drawn cells. A screen that shows more distinct cells
than that redraws some each frame, whichever bundle draws them.

## Files

| File | What |
|---|---|
| `neuronte-term-latin-v1.nrt` | The bundle, 4,280,128 bytes, sha256 `d54279bcbb190178f61a10c1d55f9840cadbd6f1b858a9993c232dc0106a473b` |
| `neuronte-term-latin-v1.list.txt` | The 596 characters it was trained on |
| `neuronte-term-latin-v1-SET-gN.json` | The 74 group nets as trained (the shipped seed) |
| `neuronte-term-latin-v1.provenance.json` | Every member's hash and scalars, written by `make pack-term-latin-v1` |
| `neuronte-term-latin-v1.validation.json` | The declared gates, both seeds' measurements and failures for every group, the retry, the second line |
