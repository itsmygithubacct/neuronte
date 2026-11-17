# term-syllabics-v1: Canadian syllabics made by rule, on their own

`neuronte-term-syllabics-v1.nrt` is a terminal bundle for 168 characters no earlier bundle was trained on: Unified Canadian Aboriginal Syllabics: the vowels and the p, t, k, c, m and n series with their long and w forms, their finals, the finals that are marks, and the full stop. In `neuronte-split-v9` each of them goes to the router's gate and is drawn by a net that never saw it, so it comes out as some other shape.

It is a **standalone** bundle: 15 known-only group nets and one blank net, 856,824 bytes, with no copy of split-v9 in it. A program opens it beside split-v9 and asks it first (see "What a consumer changes"). It is not a default and replaces nothing.

**236 of the 404 syllabics in the list are not here.** They were never drawn:
the l, s, sh, y, r, f, th, q, ng, nng and lh series, the aai forms, and the
Carrier, Naskapi, Nunavik, Sayisi, South Slavey and Th-Cree forms. Their
shapes were not known well enough to draw without looking at a font, which
this work does not do. They stay untrained in every bundle.

| Characters | Training set | Group nets | Common gates |
|---|---|---|---|
| 132: the vowels, p, t, k, c and m, 22 each, two nets a series | `tscrsa` | 12×H64 | all 12 passed |
| 36: n; the rest of n, the small finals and the full stop; the finals that are marks | `tscrsb` | 3×H64 | all 3 passed |

## The gates

The common gates of phases 3 to 6. `gates-v2.json`, sha256 `5bf1a3f8312c45df2a20b2e69d51ee3c690c58891ec5390cf0e41cbdf9f9b51b`, was declared before any of these nets was trained and recorded in this lane's report before training. Its limits are the worst group net the owner had already accepted on a sheet, times 1.10, counted at 6×12, 8×16, 10×20, 12×24, 16×32, 24×48 and 48×96 (mean error, 99th percentile, firm-wrong fraction, the worst character, mean and worst overlap), and with one sample a pixel at 8×16, 16×32 and 48×96; at every counted size each character must be nearer its own drawing than any other drawing of the bundle (or an exact twin of it) and none may vanish. These are scored as letters, against the teacher of all 168 characters drawn for the bundle. Both seeds must pass.

**The gates were amended twice while these nets trained, by the owner, for every lane, and not by this lane.** Another lane showed that some rules are failed by a perfect net: the drawing itself, sampled as the library samples, misses them on thin strokes. `gates-v2.1.json`, sha256 `214942e398f88110cd7c6044c194f0f274274aeedb07abcbe8e1a18dc2b323c0`, dropped the overlap of the worst character for letters. `gates-v2.2.json`, sha256 `dd3cc2ea30ccb49d001c28a905bcc6e2a2d11edfcd6a741464fda91162b10e70`, **gave the verdicts here**: it is 2.1, and for each group and size a rule that the perfect drawing of that group fails is not applied there; every other rule applies with its limit, and nearest-to-itself and none-vanished are never skipped. No limit was changed.

Of the 15 groups first trained, 14 passed with both seeds under gates-v2, 15 under 2.1 and 15 under 2.2. **Rules skipped under 2.2 because a perfect net fails them: 0** in the groups of the bundle.

The rule is automatic and nobody chose a net. A group whose two seeds pass ships the seed with the lower mean error over 8×16, 16×32 and 48×96. A group that fails is trained once more as two groups of half its characters; a half that still fails is left out.

- **15 groups trained, 15 passed with both seeds.**
- **Left out: none.** Every character drawn for the bundle is in it.
- Every group net in the bundle passes the C-against-float64 check.

**Small cells.** The gates are loose at 6×12 by their formula (a letter group passes with a mean overlap of 0.44). Here the lowest overlap of any one character at 6×12 is 0.60 (`tscrsa` group 8). Below 6×12 nothing is counted.

## What a consumer changes

Nothing, until it opens this file. It does not replace split-v9 and holds none of its characters; `tests/check_bundle_lists.py` checks that it shares no trained scalar with split-v9 or any other listed bundle.

```c
neuronte_open_file("neuronte-split-v9.nrt", &base);
neuronte_open_file("neuronte-term-syllabics-v1.nrt", &more);
/* for each scalar c */
font = neuronte_untrained(more, c) ? base : more;
```

`neuronte_untrained(more, c)` is 0 for exactly the 168 characters in `neuronte-term-syllabics-v1.list.txt` and 1 for every other scalar. A scalar outside the list, drawn through this file anyway, comes out blank, or as the code-made hollow box after `neuronte_set_untrained(more, 1)`. The file needs the current runtime (version 2 bundles, 128-member limit). It has 16 members. Cells are the terminal's 1:2 cell; the nets were trained and measured from 6×12 to 48×96.

## Recipe

- **Drawings.** A syllabic is its consonant's shape turned for its vowel, made by
  `train/term_scripts.py` from the Unicode names and seven shapes in
  `font/term-scripts.txt`: a dot above for a long vowel, a dot at mid height
  before the shape for w (after it in the West Cree forms), the a form small
  and raised for a final. Fifteen marks and finals are drawn one by one.
  Marked as unsure on the drawing sheet: the n series (the hook's size is
  from memory), the Y-Cree long oo, the West Cree final m, the full stop.
  No font was opened or rasterised; DejaVu Sans Mono gave only its list of code points.
- **Sets and groups.** 2 training sets of `font/term-scripts.txt`, each cut in order into group nets of 11 to 12 characters (15 in all).
- **Training.** `train/split_expert.py train --mode repertoire --partition contiguous`, unchanged: hidden width 64, 120,000 steps, the project teacher (grid 256), seeds 0 and 1. No retry at another width.
- **Selection.** As under "The gates". Only the shipped seed's JSON is in `weights/`; the other seed's hash and measurements are in the validation record.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
make pack-term-syllabics-v1    # rebuilds the .nrt byte for byte from the group nets
make test-term-syllabics-v1
```

## Checks

`make test-term-syllabics-v1` (part of `make test`): every group net against the float64 reference; the bundle rebuilt byte for byte; its table exactly `neuronte-term-syllabics-v1.list.txt`, which is its training sets in `font/term-scripts.txt` less any group left out; every scalar from U+0000 to U+10FFFF routed as the table says; pixels through the bundle equal to each group net alone at 19 cell sizes and with one sample a pixel; `test_api --standalone`; and the validation record: every shipped group passed with both seeds and ships the seed the rule selects.

## Results by group

Mean error against the teacher at 8×16, 16×32 and 48×96 and mean overlap at 6×12 and 8×16, for the shipped seed (for a group not shipped, the lower-error seed).

| Set | Group | Characters | Result | Rules missed (seed 0 / seed 1) | Mean error | Overlap 6×12, 8×16 |
|---|---:|---|---|---|---|---|
| `tscrsa` | 0 | ᐁ ᐌ ᐍ ᐃ ᐄ ᐎ ᐏ ᐐ ᐑ ᐅ ᐆ | passed; H64, seed 1 | 0 / 0 | 0.0051 0.0026 0.0014 | 1.000, 0.952 |
| `tscrsa` | 1 | ᐇ ᐒ ᐓ ᐔ ᐕ ᐊ ᐋ ᐗ ᐘ ᐙ ᐚ | passed; H64, seed 1 | 0 / 0 | 0.0069 0.0030 0.0017 | 0.921, 0.960 |
| `tscrsa` | 2 | ᐯ ᐺ ᐻ ᐱ ᐲ ᐼ ᐽ ᐾ ᐿ ᐳ ᐴ | passed; H64, seed 1 | 0 / 0 | 0.0034 0.0016 0.0011 | 1.000, 0.945 |
| `tscrsa` | 3 | ᐵ ᑀ ᑁ ᑂ ᑃ ᐸ ᐹ ᑄ ᑅ ᑆ ᑇ | passed; H64, seed 1 | 0 / 0 | 0.0041 0.0020 0.0013 | 0.980, 0.961 |
| `tscrsa` | 4 | ᑌ ᑗ ᑘ ᑎ ᑏ ᑙ ᑚ ᑛ ᑜ ᑐ ᑑ | passed; H64, seed 1 | 0 / 0 | 0.0058 0.0027 0.0014 | 0.915, 0.948 |
| `tscrsa` | 5 | ᑒ ᑝ ᑞ ᑟ ᑠ ᑕ ᑖ ᑡ ᑢ ᑣ ᑤ | passed; H64, seed 1 | 0 / 0 | 0.0049 0.0027 0.0013 | 0.903, 0.938 |
| `tscrsa` | 6 | ᑫ ᑴ ᑵ ᑭ ᑮ ᑶ ᑷ ᑸ ᑹ ᑯ ᑰ | passed; H64, seed 1 | 0 / 0 | 0.0061 0.0024 0.0014 | 0.948, 0.973 |
| `tscrsa` | 7 | ᑱ ᑺ ᑻ ᑼ ᑽ ᑲ ᑳ ᑾ ᑿ ᒀ ᒁ | passed; H64, seed 0 | 0 / 0 | 0.0058 0.0027 0.0015 | 0.845, 0.975 |
| `tscrsa` | 8 | ᒉ ᒒ ᒓ ᒋ ᒌ ᒔ ᒕ ᒖ ᒗ ᒍ ᒎ | passed; H64, seed 1 | 0 / 0 | 0.0047 0.0020 0.0011 | 0.901, 0.933 |
| `tscrsa` | 9 | ᒏ ᒘ ᒙ ᒚ ᒛ ᒐ ᒑ ᒜ ᒝ ᒞ ᒟ | passed; H64, seed 0 | 0 / 0 | 0.0051 0.0025 0.0012 | 0.927, 0.980 |
| `tscrsa` | 10 | ᒣ ᒬ ᒭ ᒥ ᒦ ᒮ ᒯ ᒰ ᒱ ᒧ ᒨ | passed; H64, seed 1 | 0 / 0 | 0.0060 0.0025 0.0013 | 0.921, 0.968 |
| `tscrsa` | 11 | ᒩ ᒲ ᒳ ᒴ ᒵ ᒪ ᒫ ᒶ ᒷ ᒸ ᒹ | passed; H64, seed 1 | 0 / 0 | 0.0066 0.0039 0.0013 | 0.868, 0.923 |
| `tscrsb` | 0 | ᓀ ᓂ ᓃ ᓄ ᓅ ᓆ ᓇ ᓈ ᓉ ᓊ ᓋ ᓌ | passed; H64, seed 1 | 0 / 0 | 0.0044 0.0023 0.0012 | 0.902, 0.992 |
| `tscrsb` | 1 | ᓍ ᓎ ᑉ ᑊ ᑦ ᒃ ᒄ ᒡ ᒻ ᒼ ᓐ ᙮ | passed; H64, seed 1 | 0 / 0 | 0.0034 0.0017 0.0009 | 0.974, 0.989 |
| `tscrsb` | 2 | ᐟ ᐠ ᐡ ᐢ ᐣ ᐤ ᐥ ᐦ ᐧ ᐨ ᐩ ᐪ | passed; H64, seed 1 | 0 / 0 | 0.0019 0.0011 0.0006 | 0.944, 1.000 |

## Speed

Not measured yet.

## Files

`neuronte-term-syllabics-v1.nrt` (856,824 bytes, sha256 `bb992b61ed2c31a6ae81240e5504a9adb95bf19d8a933f4066c149f37de5f5af`), `neuronte-term-syllabics-v1.list.txt`, `neuronte-term-syllabics-v1.provenance.json`, `neuronte-term-syllabics-v1.validation.json`, and 15 group nets `neuronte-term-syllabics-v1-SET-gN.json`. All are in `weights/SHA256SUMS`.
