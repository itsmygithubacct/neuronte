# term-letters-v1: 812 more letters of Latin, Greek and Cyrillic, on their own

`neuronte-term-letters-v1.nrt` is a terminal bundle for 812 characters no earlier bundle was trained on: the letters
of scripts Neuronte already draws that `neuronte-split-v9` and `neuronte-term-latin-v1` do not hold. They are the
rest of Latin Extended-B, the IPA Extensions, the Phonetic Extensions and their supplement, the Spacing Modifier
Letters and Modifier Tone Letters, Latin Extended-C and -D, the rest of Greek and Coptic, the rest of Cyrillic
with its Supplement and Extended-B, and the Latin ligatures. In split-v9 each of them goes to the router's gate
and is drawn by a net that never saw it, so it comes out as some other shape (over these characters split-v9's
mean overlap with the drawing is 0.13 at 8×16 and 0.14 at 16×32; this bundle's is
0.95 and 0.99).

It is a **standalone** bundle: 103 known-only group nets and one blank net, 5,882,132 bytes, with no copy
of split-v9 or term-latin-v1 in it. A program opens it beside them and asks each in turn (see "What a consumer
changes").

| Characters | Training set | Group nets in the bundle | Gates |
|---|---|---|---|
| 76 IPA letters: ɐ ɑ ɒ ɓ ɔ ɕ ɖ ɗ ɘ ə ɚ ɛ ɜ ɝ ... | `tletip` | 10×H64 | 10 of 10 groups passed |
| 103 Latin capitals: Ɓ Ƃ Ƅ Ɔ Ƈ Ɖ Ɗ Ƌ Ǝ Ə Ɛ Ƒ Ɠ Ɣ ... | `tletlu` | 13×H64 | 13 of 13 groups passed |
| 89 Latin smalls: ƀ ƃ ƅ ƈ ƌ ƍ ƒ ƕ ƙ ƚ ƛ ƞ ƣ ƥ ... | `tletll` | 11×H64 | 11 of 11 groups passed |
| 42 two and three letters in one cell (digraphs, ligatures): Ǆ ǅ ǆ Ǉ ǈ ǉ Ǌ ǋ ǌ Ǳ ǲ ǳ ȸ ȹ ... | `tletdg` | 6×H64 | 6 of 6 groups passed |
| 96 Cyrillic capitals: Ѡ Ѣ Ѥ Ѧ Ѩ Ѫ Ѭ Ѯ Ѱ Ѳ Ѵ Ѷ Ѹ Ѻ ... | `tletcu` | 12×H64 | 12 of 12 groups passed |
| 96 Cyrillic smalls: ѡ ѣ ѥ ѧ ѩ ѫ ѭ ѯ ѱ ѳ ѵ ѷ ѹ ѻ ... | `tletcl` | 12×H64 | 12 of 12 groups passed |
| 27 Greek and Coptic capitals: Ͱ Ͳ Ͷ Ϳ Ϗ ϒ ϓ ϔ Ϙ Ϛ Ϝ Ϟ Ϡ Ϣ ... | `tletgu` | 4×H64 | 4 of 4 groups passed |
| 33 Greek and Coptic smalls: ͱ ͳ ͷ ͻ ͼ ͽ ϐ ϑ ϕ ϖ ϗ ϙ ϛ ϝ ... | `tletgl` | 4×H64 | 4 of 4 groups passed |
| 60 small capitals, turned and sideways letters: ɢ ɪ ɴ ɶ ʀ ʁ ʏ ʙ ʛ ʜ ʟ ᴀ ᴁ ᴂ ... | `tletsc` | 8×H64 | 8 of 8 groups passed |
| 30 modifier letters, raised capitals: ʶ ᴬ ᴭ ᴮ ᴰ ᴱ ᴲ ᴳ ᴴ ᴵ ᴶ ᴷ ᴸ ᴹ ... | `tletmu` | 4×H64 | 4 of 4 groups passed |
| 77 modifier letters, raised smalls: ʰ ʱ ʲ ʳ ʴ ʵ ʷ ʸ ˠ ˡ ˢ ˣ ˤ ᵃ ... | `tletml` | 10×H64 | 9 of 10 groups passed; 1 cut in two, 1 halves passed; **4 characters left out** |
| 10 modifier letters, lowered: ᵢ ᵣ ᵤ ᵥ ᵦ ᵧ ᵨ ᵩ ᵪ ⱼ | `tletsb` | 2×H64 | 0 of 1 groups passed; 1 cut in two, 2 halves passed |
| 77 spacing marks, tone bars, click letters: ˥ ˦ ˧ ˨ ˩ ꜈ ꜉ ꜊ ꜋ ꜌ ꜒ ꜓ ꜔ ꜕ ... | `tletsp` | 7×H64 | 7 of 7 groups passed |

**Not a default, and not a replacement for split-v9.** Every group net in it passed the project's shared gates
(`gates-v2.3.json`, sha256 `2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`) with both of its seeds. The limits and what happens
to a failing group were declared before any of these nets was trained, and nobody was asked about a failure.
100 of the 102 groups passed as trained. 2 did not; each of
those was cut into two halves and each half trained once more: 3 halves passed and are in
the bundle, 1 failed again and are **left out**. The 4 characters of the halves left out are in no list: this bundle reports them untrained, and split-v9 goes on drawing them through its fallback.

The gates are a floor, not a mark of quality: their limits are the worst group net the owner had already accepted
for shipping, times 1.10. A net that passes is no worse than something that already ships.

The gates file was amended three times while these nets trained, by the owner's decision and for every lane,
after another lane showed that some letters rules fail even for a perfect net (they measure the drawing against
pixel sampling, not the net): the rule on the overlap of the worst character was dropped for letters
(`gates-v2.1.json`); a rule the perfect drawing fails was switched off for that group and size (`gates-v2.2.json`);
and that switch was replaced (`gates-v2.3.json`): no limit is tighter than the perfect drawing's own score with 10%
of room, and a seed that puts every pixel on the right side at every counted size passes. Nearest-to-itself and
none-vanished always apply. Every verdict here is v2.3's.
**44 limits were eased** that way over the 103 nets in the bundle (16 × `24x48 iou_mean`, 9 × `24x48 firm`, 4 × `10x20 mae`, 3 × `s1 16x32 p99`, 2 × `s1 8x16 firm`, 2 × `8x16 iou_mean`, 2 × `s1 8x16 iou_mean`, 1 × `s1 8x16 p99`, 1 × `8x16 p99`, 1 × `16x32 mae`, 1 × `s1 16x32 mae`, 1 × `s1 16x32 firm`, 1 × `10x20 firm`); 0 seeds passed by the
pixel-exact rule. Each is listed in `neuronte-term-letters-v1.validation.json`. The earlier files: `gates-v2.json` sha256 `5bf1a3f8312c45df2a20b2e69d51ee3c690c58891ec5390cf0e41cbdf9f9b51b`; `gates-v2.1.json` sha256 `214942e398f88110cd7c6044c194f0f274274aeedb07abcbe8e1a18dc2b323c0`; `gates-v2.2.json` sha256 `dd3cc2ea30ccb49d001c28a905bcc6e2a2d11edfcd6a741464fda91162b10e70`.

## Groups trained a second time

2 groups failed the final gates as trained and were cut in two, each half trained once with the same
recipe (the remedy declared before training). A half that passes is in the bundle under a name ending in `a` or `b`.

- `tletml` g8 (8 characters, U+1DAF to U+1DB7): seed 1 `24x48 firm` 0.0008681 against 0.0008355 (the perfect drawing scores 0.0007595; the declared limit was 0.0006356). half a (4 characters) passed, half b (4 characters) **failed again and is left out**.
- `tletsb` g0 (10 characters, U+1D62 to U+2C7C): seed 0 `24x48 iou_mean` 0.934 against 0.937 (the perfect drawing scores 0.9427; the declared limit was 0.9449); seed 1 `24x48 iou_mean` 0.9346 against 0.937 (the perfect drawing scores 0.9427; the declared limit was 0.9449). half a (5 characters) passed, half b (5 characters) passed.

Both had passed `gates-v2.2.json`, which did not apply those rules to them (the perfect drawing itself misses the
declared limit); `gates-v2.3.json` applies them at the perfect drawing's score with 10% of room, and the nets miss that.

2 groups (`tletml:g4`, `tletsp:g6`) were trained again whole, because a drawing in each was corrected: the
scoring command showed that U+1D54 (raised top half o) drawn perfectly left no ink in a 6×12 cell, and U+A789
(modifier colon) none in an 8×16 cell. Both were drawn heavier, every drawing was checked the same way, the
teachers were made again and the two groups trained with the same recipe. That is a corrected drawing, not the
split-in-two remedy.

## What is left out

| Half | Characters | Seed 0 | Seed 1 |
|---|---|---|---|
| `tletml` g8b | U+1DB4 U+1DB5 U+1DB6 U+1DB7 (ᶴ ᶵ ᶶ ᶷ) | `24x48 firm` 0.0008681 against 0.0007161 (the perfect drawing scores 0.000651; the declared limit was 0.0006356) | passed |

A miss reads "size rule": `24x48 firm` is the share of pixels firmly on the wrong side at 24×48. These characters
are in no list: this bundle reports them untrained and split-v9 goes on drawing them through its fallback. Both
seeds of every group and half are in `neuronte-term-letters-v1.validation.json`.

## What a consumer changes

Open this file beside `neuronte-split-v9.nrt` (and `neuronte-term-latin-v1.nrt` if it is used). For a character, ask
`neuronte_untrained(handle, scalar)` of each standalone bundle; draw with the one that answers 0, and with split-v9
when none does. A scalar outside this bundle's list draws an empty cell through it and is reported untrained, so
it never hides a character another bundle has. No listed character is in split-v9's table or term-latin-v1's
(`tests/check_term_letters_v1.py`). Nothing else changes: no default, no pin and no existing file is touched.

## Drawings

`font/term-letters.txt` holds a line for each character and `train/term_letters.py` makes the drawing: most are a
letter the project already draws, turned, mirrored, made small, raised, or given a hook, bar or tail; the modifier
letters are their letters at 0.7 of the size, the small capitals the capitals at x-height, two or three letters in
one cell each squeezed to fit. No font file was opened or rasterised to make or check a drawing. Each shape comes
from the character's Unicode name and the code chart as remembered.
73 of the shipped shapes are marked "unsure" in the font file and on the review sheet, drawn without
certainty about what the chart shows: U+01AA U+01BA U+02AD U+0372 U+0373 U+03D0 U+03D1 U+03DE U+03DF U+03E0 U+03E1 U+03E4 U+03E5 U+03E6 U+03E7 U+03EA U+03EB U+03EC U+03ED U+047C U+047D U+04A8 U+04A9 U+0504 U+0505 U+0506 U+0507 U+1D12 U+1D1D U+1D1E U+1D1F U+1EFA U+1EFB U+A64C U+A64D U+A662 U+A663 U+A664 U+A665 U+A666 U+A667 U+A66A U+A66B U+A66C U+A66D U+A66E U+A68C U+A68D U+A694 U+A695 U+A708 U+A709 U+A70A U+A70B U+A70C U+A70D U+A70E U+A70F U+A710 U+A711 U+A724 U+A725 U+A728 U+A729 U+A72A U+A72B U+A746 U+A747 U+A752 U+A753 U+A782 U+A783 U+A7FF.
A character that looks the same as another has exactly its drawing (45 such pairs, among them the Cyrillic and
Greek lookalikes of Latin letters).

## Recipe

- Teacher: the project's (`train/split_expert.py prepare`, grid 256, tau 0.15, pen 0.075), one for each training set.
- `train/split_expert.py train --mode repertoire --partition contiguous`, unchanged: hidden width 64 a group net
  (`--budget` 64 × the number of groups), 120,000 steps, seeds 0 and 1, a set's two seeds as one batch.
- About 8 characters to a net; 11 for the spacing marks and tone bars and 10 for the lowered modifier letters.
- A failing group's halves are groups 2i and 2i+1 of the same set cut into twice as many groups: the same
  characters, the same recipe, trained once. No wider net was tried.
- The seed that ships is the gates' `selected_seed`: the lower mean of the mean error at 8×16, 16×32 and 48×96.
- Trained on rented RTX 3090 cards; scored on a laptop CPU with `gates_v2.py score --kind letters` against the
  teacher of all 816 characters as one set (the nearest-drawing rule is judged among all of them).

## Checks

`make test-term-letters-v1`: each group JSON packs and agrees with the float64 reference
(`tests/check_reference.py`); the bundle is rebuilt byte for byte from the group nets and its list; every scalar
routes as the list says; each character draws in the bundle exactly as its group net alone at 19 sizes; the
validation record matches the files; `test_api --standalone` passes. `tests/check_bundle_lists.py` checks the list
against the table with the other listed bundles.

## Results by group

Mean error of the shipped seed at 8×16, 16×32 and 48×96, and mean overlap at 8×16 and 16×32 (automatic sampling).

| Group | Characters | Result | Seed | Error 8×16 | 16×32 | 48×96 | Overlap 8×16 | 16×32 | Limits eased |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| `tletip` g0 | 7 | passed | 1 | 0.0051 | 0.0021 | 0.0012 | 0.953 | 0.994 | 0 |
| `tletip` g1 | 8 | passed | 1 | 0.0043 | 0.0023 | 0.0012 | 0.969 | 0.993 | 0 |
| `tletip` g2 | 7 | passed | 1 | 0.0054 | 0.0024 | 0.0014 | 0.951 | 0.989 | 0 |
| `tletip` g3 | 8 | passed | 0 | 0.0070 | 0.0043 | 0.0015 | 0.974 | 0.995 | 0 |
| `tletip` g4 | 8 | passed | 0 | 0.0069 | 0.0041 | 0.0015 | 0.989 | 1.000 | 0 |
| `tletip` g5 | 7 | passed | 1 | 0.0042 | 0.0015 | 0.0010 | 0.947 | 0.995 | 0 |
| `tletip` g6 | 8 | passed | 1 | 0.0059 | 0.0037 | 0.0013 | 0.963 | 0.994 | 0 |
| `tletip` g7 | 7 | passed | 1 | 0.0046 | 0.0022 | 0.0012 | 0.950 | 0.994 | 0 |
| `tletip` g8 | 8 | passed | 1 | 0.0050 | 0.0025 | 0.0013 | 0.957 | 0.983 | 0 |
| `tletip` g9 | 8 | passed | 1 | 0.0067 | 0.0034 | 0.0015 | 0.858 | 0.991 | 0 |
| `tletlu` g0 | 7 | passed | 1 | 0.0071 | 0.0032 | 0.0016 | 0.961 | 0.987 | 0 |
| `tletlu` g1 | 8 | passed | 1 | 0.0062 | 0.0030 | 0.0015 | 0.969 | 0.986 | 0 |
| `tletlu` g2 | 8 | passed | 1 | 0.0089 | 0.0047 | 0.0020 | 0.979 | 0.990 | 0 |
| `tletlu` g3 | 8 | passed | 0 | 0.0061 | 0.0036 | 0.0015 | 0.993 | 0.977 | 0 |
| `tletlu` g4 | 8 | passed | 1 | 0.0069 | 0.0034 | 0.0017 | 0.952 | 0.979 | 0 |
| `tletlu` g5 | 8 | passed | 1 | 0.0065 | 0.0032 | 0.0015 | 0.980 | 0.983 | 0 |
| `tletlu` g6 | 8 | passed | 1 | 0.0073 | 0.0035 | 0.0017 | 0.946 | 0.982 | 0 |
| `tletlu` g7 | 8 | passed | 0 | 0.0087 | 0.0040 | 0.0019 | 0.967 | 0.968 | 0 |
| `tletlu` g8 | 8 | passed | 0 | 0.0065 | 0.0027 | 0.0016 | 0.951 | 0.986 | 1 |
| `tletlu` g9 | 8 | passed | 1 | 0.0062 | 0.0027 | 0.0015 | 0.957 | 0.986 | 0 |
| `tletlu` g10 | 8 | passed | 0 | 0.0072 | 0.0031 | 0.0016 | 0.969 | 0.976 | 0 |
| `tletlu` g11 | 8 | passed | 1 | 0.0084 | 0.0029 | 0.0019 | 0.915 | 0.982 | 1 |
| `tletlu` g12 | 8 | passed | 0 | 0.0077 | 0.0033 | 0.0017 | 0.944 | 0.983 | 0 |
| `tletll` g0 | 8 | passed | 1 | 0.0060 | 0.0028 | 0.0015 | 0.934 | 0.987 | 0 |
| `tletll` g1 | 8 | passed | 1 | 0.0062 | 0.0032 | 0.0015 | 0.952 | 0.993 | 0 |
| `tletll` g2 | 8 | passed | 1 | 0.0058 | 0.0029 | 0.0016 | 0.950 | 0.999 | 0 |
| `tletll` g3 | 8 | passed | 1 | 0.0055 | 0.0029 | 0.0016 | 0.983 | 0.993 | 0 |
| `tletll` g4 | 8 | passed | 1 | 0.0060 | 0.0030 | 0.0015 | 0.969 | 0.993 | 0 |
| `tletll` g5 | 8 | passed | 1 | 0.0052 | 0.0025 | 0.0014 | 0.951 | 0.988 | 0 |
| `tletll` g6 | 8 | passed | 1 | 0.0073 | 0.0033 | 0.0017 | 0.944 | 0.992 | 0 |
| `tletll` g7 | 8 | passed | 1 | 0.0044 | 0.0022 | 0.0011 | 0.980 | 0.990 | 0 |
| `tletll` g8 | 8 | passed | 1 | 0.0051 | 0.0020 | 0.0012 | 0.970 | 0.997 | 0 |
| `tletll` g9 | 8 | passed | 0 | 0.0059 | 0.0029 | 0.0016 | 0.989 | 0.994 | 0 |
| `tletll` g10 | 9 | passed | 1 | 0.0065 | 0.0028 | 0.0016 | 0.923 | 0.996 | 0 |
| `tletdg` g0 | 7 | passed | 0 | 0.0103 | 0.0057 | 0.0023 | 0.967 | 0.947 | 3 |
| `tletdg` g1 | 7 | passed | 1 | 0.0094 | 0.0053 | 0.0025 | 0.982 | 0.980 | 2 |
| `tletdg` g2 | 7 | passed | 1 | 0.0086 | 0.0043 | 0.0023 | 0.964 | 0.995 | 2 |
| `tletdg` g3 | 7 | passed | 1 | 0.0072 | 0.0045 | 0.0018 | 0.963 | 0.989 | 0 |
| `tletdg` g4 | 7 | passed | 1 | 0.0070 | 0.0039 | 0.0016 | 0.980 | 0.989 | 2 |
| `tletdg` g5 | 7 | passed | 1 | 0.0099 | 0.0050 | 0.0021 | 0.925 | 0.984 | 5 |
| `tletcu` g0 | 8 | passed | 0 | 0.0094 | 0.0045 | 0.0022 | 0.933 | 0.992 | 1 |
| `tletcu` g1 | 8 | passed | 0 | 0.0074 | 0.0039 | 0.0019 | 0.981 | 0.987 | 0 |
| `tletcu` g2 | 8 | passed | 1 | 0.0077 | 0.0031 | 0.0018 | 0.969 | 0.980 | 0 |
| `tletcu` g3 | 8 | passed | 1 | 0.0090 | 0.0044 | 0.0021 | 0.962 | 0.978 | 0 |
| `tletcu` g4 | 8 | passed | 1 | 0.0069 | 0.0037 | 0.0016 | 0.965 | 0.980 | 0 |
| `tletcu` g5 | 8 | passed | 0 | 0.0076 | 0.0034 | 0.0017 | 0.971 | 0.989 | 0 |
| `tletcu` g6 | 8 | passed | 1 | 0.0076 | 0.0033 | 0.0019 | 0.980 | 0.962 | 0 |
| `tletcu` g7 | 8 | passed | 0 | 0.0065 | 0.0031 | 0.0016 | 0.973 | 0.984 | 0 |
| `tletcu` g8 | 8 | passed | 1 | 0.0073 | 0.0041 | 0.0018 | 0.983 | 0.978 | 0 |
| `tletcu` g9 | 8 | passed | 0 | 0.0093 | 0.0045 | 0.0022 | 0.953 | 0.963 | 0 |
| `tletcu` g10 | 8 | passed | 1 | 0.0080 | 0.0048 | 0.0020 | 0.971 | 0.993 | 0 |
| `tletcu` g11 | 8 | passed | 0 | 0.0083 | 0.0035 | 0.0019 | 0.909 | 0.990 | 0 |
| `tletcl` g0 | 8 | passed | 0 | 0.0072 | 0.0033 | 0.0017 | 0.948 | 0.996 | 0 |
| `tletcl` g1 | 8 | passed | 1 | 0.0059 | 0.0033 | 0.0016 | 0.987 | 0.989 | 0 |
| `tletcl` g2 | 8 | passed | 1 | 0.0060 | 0.0031 | 0.0016 | 0.970 | 0.975 | 0 |
| `tletcl` g3 | 8 | passed | 1 | 0.0066 | 0.0031 | 0.0016 | 0.941 | 0.978 | 0 |
| `tletcl` g4 | 8 | passed | 1 | 0.0057 | 0.0028 | 0.0014 | 0.955 | 0.990 | 0 |
| `tletcl` g5 | 8 | passed | 1 | 0.0064 | 0.0027 | 0.0015 | 0.961 | 0.991 | 0 |
| `tletcl` g6 | 8 | passed | 1 | 0.0049 | 0.0028 | 0.0015 | 0.983 | 0.993 | 0 |
| `tletcl` g7 | 8 | passed | 0 | 0.0050 | 0.0024 | 0.0014 | 0.957 | 0.999 | 0 |
| `tletcl` g8 | 8 | passed | 1 | 0.0052 | 0.0031 | 0.0015 | 0.972 | 0.998 | 0 |
| `tletcl` g9 | 8 | passed | 1 | 0.0065 | 0.0029 | 0.0016 | 0.953 | 0.979 | 0 |
| `tletcl` g10 | 8 | passed | 1 | 0.0063 | 0.0035 | 0.0015 | 0.970 | 0.994 | 0 |
| `tletcl` g11 | 8 | passed | 1 | 0.0065 | 0.0025 | 0.0016 | 0.909 | 0.994 | 0 |
| `tletgu` g0 | 6 | passed | 1 | 0.0064 | 0.0033 | 0.0014 | 0.949 | 0.985 | 0 |
| `tletgu` g1 | 7 | passed | 0 | 0.0049 | 0.0024 | 0.0013 | 0.932 | 0.990 | 0 |
| `tletgu` g2 | 7 | passed | 1 | 0.0072 | 0.0042 | 0.0017 | 0.929 | 0.987 | 0 |
| `tletgu` g3 | 7 | passed | 1 | 0.0058 | 0.0020 | 0.0013 | 0.907 | 0.970 | 0 |
| `tletgl` g0 | 8 | passed | 1 | 0.0045 | 0.0019 | 0.0012 | 0.959 | 0.994 | 0 |
| `tletgl` g1 | 8 | passed | 0 | 0.0058 | 0.0028 | 0.0015 | 0.971 | 0.996 | 0 |
| `tletgl` g2 | 8 | passed | 0 | 0.0057 | 0.0028 | 0.0014 | 0.925 | 0.986 | 0 |
| `tletgl` g3 | 9 | passed | 0 | 0.0051 | 0.0021 | 0.0013 | 0.984 | 0.996 | 0 |
| `tletsc` g0 | 7 | passed | 0 | 0.0058 | 0.0026 | 0.0013 | 0.983 | 0.999 | 0 |
| `tletsc` g1 | 8 | passed | 0 | 0.0065 | 0.0026 | 0.0014 | 0.974 | 0.997 | 0 |
| `tletsc` g2 | 7 | passed | 1 | 0.0053 | 0.0023 | 0.0011 | 0.992 | 0.976 | 0 |
| `tletsc` g3 | 8 | passed | 0 | 0.0051 | 0.0019 | 0.0011 | 0.994 | 0.994 | 0 |
| `tletsc` g4 | 7 | passed | 1 | 0.0047 | 0.0019 | 0.0012 | 0.989 | 0.991 | 0 |
| `tletsc` g5 | 8 | passed | 1 | 0.0056 | 0.0024 | 0.0012 | 0.986 | 0.990 | 0 |
| `tletsc` g6 | 7 | passed | 1 | 0.0059 | 0.0021 | 0.0011 | 0.953 | 1.000 | 0 |
| `tletsc` g7 | 8 | passed | 0 | 0.0062 | 0.0029 | 0.0013 | 0.986 | 1.000 | 0 |
| `tletmu` g0 | 7 | passed | 1 | 0.0079 | 0.0024 | 0.0013 | 1.000 | 1.000 | 2 |
| `tletmu` g1 | 8 | passed | 1 | 0.0080 | 0.0020 | 0.0013 | 0.962 | 0.994 | 2 |
| `tletmu` g2 | 7 | passed | 1 | 0.0067 | 0.0017 | 0.0012 | 0.945 | 0.998 | 1 |
| `tletmu` g3 | 8 | passed | 0 | 0.0051 | 0.0018 | 0.0009 | 0.989 | 0.978 | 2 |
| `tletml` g0 | 7 | passed | 1 | 0.0045 | 0.0014 | 0.0009 | 1.000 | 0.988 | 1 |
| `tletml` g1 | 8 | passed | 0 | 0.0028 | 0.0011 | 0.0008 | 1.000 | 0.978 | 0 |
| `tletml` g2 | 8 | passed | 1 | 0.0044 | 0.0017 | 0.0010 | 0.989 | 0.962 | 1 |
| `tletml` g3 | 7 | passed | 0 | 0.0052 | 0.0017 | 0.0010 | 0.921 | 0.991 | 1 |
| `tletml` g4 | 8 | passed | 1 | 0.0043 | 0.0015 | 0.0008 | 0.933 | 0.986 | 2 |
| `tletml` g5 | 8 | passed | 1 | 0.0048 | 0.0015 | 0.0010 | 0.978 | 0.985 | 2 |
| `tletml` g6 | 7 | passed | 0 | 0.0050 | 0.0019 | 0.0010 | 0.962 | 0.948 | 1 |
| `tletml` g7 | 8 | passed | 0 | 0.0046 | 0.0020 | 0.0010 | 0.911 | 0.976 | 1 |
| `tletml` g8 | 8 | **failed**, cut in two | (1) | 0.0046 | 0.0016 | 0.0010 | 1.000 | 0.970 | 3 |
| `tletml` g8a | 4 | passed as a half | 0 | 0.0045 | 0.0018 | 0.0010 | 1.000 | 0.972 | 2 |
| `tletml` g8b | 4 | **failed again, left out** | (0) | 0.0047 | 0.0014 | 0.0010 | 1.000 | 0.969 | 3 |
| `tletml` g9 | 8 | passed | 1 | 0.0044 | 0.0016 | 0.0011 | 0.994 | 0.955 | 1 |
| `tletsb` g0 | 10 | **failed**, cut in two | (1) | 0.0043 | 0.0015 | 0.0009 | 0.974 | 0.992 | 2 |
| `tletsb` g0a | 5 | passed as a half | 1 | 0.0046 | 0.0015 | 0.0008 | 0.981 | 0.981 | 1 |
| `tletsb` g0b | 5 | passed as a half | 0 | 0.0041 | 0.0016 | 0.0009 | 0.967 | 0.996 | 1 |
| `tletsp` g0 | 11 | passed | 1 | 0.0069 | 0.0027 | 0.0010 | 0.597 | 0.996 | 3 |
| `tletsp` g1 | 11 | passed | 1 | 0.0072 | 0.0028 | 0.0010 | 0.621 | 0.996 | 3 |
| `tletsp` g2 | 11 | passed | 1 | 0.0022 | 0.0015 | 0.0006 | 0.993 | 0.982 | 0 |
| `tletsp` g3 | 11 | passed | 1 | 0.0016 | 0.0008 | 0.0004 | 0.906 | 0.950 | 0 |
| `tletsp` g4 | 11 | passed | 0 | 0.0021 | 0.0009 | 0.0005 | 0.952 | 0.966 | 0 |
| `tletsp` g5 | 11 | passed | 1 | 0.0015 | 0.0008 | 0.0004 | 0.945 | 0.964 | 0 |
| `tletsp` g6 | 11 | passed | 1 | 0.0021 | 0.0012 | 0.0005 | 0.970 | 0.989 | 0 |

## The whole bundle against split-v9 on the same characters

Over the 812 characters in the bundle, against the teacher (automatic sampling):

| | Mean error 8×16 | 16×32 | 48×96 | Mean overlap 8×16 | 16×32 | 48×96 | Worst overlap 16×32 |
|---|---:|---:|---:|---:|---:|---:|---:|
| split-v9 (its fallback) | 0.2058 | 0.2195 | 0.2246 | 0.134 | 0.143 | 0.150 | 0.000 |
| neuronte-term-letters-v1 | 0.0060 | 0.0028 | 0.0014 | 0.951 | 0.986 | 0.994 | 0.714 |

## Speed

Measured on one Intel Core i7-6820HQ and one Intel Core i7-10700F, each on one pinned core (CPU 3) under the project's
benchmark lock, held for the whole run. kilix-bench e21e5cd: a fresh process for every job, one warmup and ten
measured rounds in shuffled order, medians, raw trials kept, every model checked against the float64 reference
first. The corpus is this bundle's 812 characters. split-v9 sends each through its gate to another of its nets,
which never saw it; term-letters-v1 looks it up in its table and runs a small group net.

| µs per character | i7-6820HQ: split-v9 | term-letters-v1 | ratio | i7-10700F: split-v9 | term-letters-v1 | ratio |
|---|---:|---:|---:|---:|---:|---:|
| Coverage, uncached, 8×16 | 801.1 | 186.1 | 4.30 | 611.3 | 155.6 | 3.93 |
| Coverage, uncached, 16×32 | 3120.5 | 717.5 | 4.35 | 2412.2 | 594.7 | 4.06 |
| Coverage, uncached, 48×96 | 6941.2 | 1582.7 | 4.39 | 5417.2 | 1320.5 | 4.10 |
| Draw, cold, 8×16 | 804.0 | 188.8 | 4.26 | 616.4 | 156.0 | 3.95 |
| Draw, cold, 16×32 | 3119.7 | 720.0 | 4.33 | 2389.0 | 598.7 | 3.99 |
| Draw, cold, 48×96 | 7069.7 | 1621.1 | 4.36 | 5437.4 | 1342.5 | 4.05 |
| Draw, warm, 8×16 | 263.9 | 61.3 | 4.31 | 201.0 | 50.9 | 3.95 |
| Draw, warm, 16×32 | 1014.8 | 233.4 | 4.35 | 780.8 | 194.2 | 4.02 |
| Draw, warm, 48×96 | 2315.8 | 534.1 | 4.34 | 1770.3 | 444.0 | 3.99 |

Uncached, term-letters-v1 draws these characters 4.2 times as fast as split-v9's fallback does
(geometric mean over both machines and the three cells; 4.3 on the Intel Core i7-6820HQ, 4.0 on the Intel Core i7-10700F;
cold draw 4.2, warm draw 4.2). A lookup in its table takes 49 ns and 34 ns
against 1272 ns and 942 ns for split-v9's gate. Opening the file takes 6.2 ms and 5.0 ms against
4.8 ms and 3.6 ms for split-v9; a program that opens both pays both. The pixels drawn are the same
on both machines.

A handle caches 1,024 drawn cells, in 256 sets of 4. The warm figures show that this corpus of 812 distinct
characters does not all stay in the cache: a warm draw costs about a third of a cold one, for both bundles. A
screen that shows more distinct cells than the cache keeps redraws some each frame, whichever bundle draws them.

## Files

- `neuronte-term-letters-v1.nrt`, sha256 `a5b23948026761ce58ed11b3542df38b842a6f1c93fd2c4971e60d9d4b7700fd`, 5,882,132 bytes: 103 group nets and the blank net.
- `neuronte-term-letters-v1.list.txt`: the 812 characters, by training set.
- `neuronte-term-letters-v1-SET-gN.json` (103 files): the group nets as trained, the shipped seed of each; a name ending
  in `a` or `b` is the first or second half of a group that was cut in two.
- `neuronte-term-letters-v1.provenance.json`: the packer's record. `neuronte-term-letters-v1.validation.json`: both seeds of every group and half
  against the gates, the hashes of both, and what was left out.
- `train/build_term_letters_v1.py` rebuilds the bundle (`make pack-term-letters-v1`); `tests/check_term_letters_v1.py`
  checks it.
