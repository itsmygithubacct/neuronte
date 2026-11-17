# term-scripts-v1: Lisu, on their own

`neuronte-term-scripts-v1.nrt` is a terminal bundle for 48 characters no earlier bundle was trained on: the Lisu (Fraser) alphabet, U+A4D0..U+A4FF: 40 letters, six tone marks and two punctuation marks. In `neuronte-split-v9` each of them goes to the router's gate and is drawn by a net that never saw it, so it comes out as some other shape.

It is a **standalone** bundle: 6 known-only group nets and one blank net, 343,188 bytes, with no copy of split-v9 in it. A program opens it beside split-v9 and asks it first (see "What a consumer changes"). It is not a default and replaces nothing.

**Only Lisu is here, by the owner's word.** The list for this bundle has 378
characters in six scripts. 150 were drawn: Lisu 48 of 48, Ogham 24 of 28, Old
Italic 29 of 35, Tifinagh 21 of 55, Armenian 28 of 91 (40 of the 150 marked
as unsure). Shown the counts, the owner said: "train Lisu". The 102 drawings
of Ogham, Old Italic, Tifinagh and Armenian stay in `font/term-scripts.txt` on
"held" lines, in no training set, list or bundle. Georgian (121) was not
drawn: its letterforms were not known well enough, as with the 228 left out
of the other scripts.

| Characters | Training set | Group nets | Common gates |
|---|---|---|---|
| 48: Lisu: Latin capitals, fifteen of them turned, and the marks | `tscrl` | 6×H64 | all 6 passed |

## The gates

The common gates of phases 3 to 6. `gates-v2.json`, sha256 `5bf1a3f8312c45df2a20b2e69d51ee3c690c58891ec5390cf0e41cbdf9f9b51b`, was declared before any of these nets was trained and recorded in this lane's report before training. Its limits are the worst group net the owner had already accepted on a sheet, times 1.10, counted at 6×12, 8×16, 10×20, 12×24, 16×32, 24×48 and 48×96 (mean error, 99th percentile, firm-wrong fraction, the worst character, mean and worst overlap), and with one sample a pixel at 8×16, 16×32 and 48×96; at every counted size each character must be nearer its own drawing than any other drawing of the bundle (or an exact twin of it) and none may vanish. These are scored as letters, against the teacher of all 48 characters drawn for the bundle. Both seeds must pass.

**The gates were amended twice while these nets trained, by the owner, for every lane, and not by this lane.** Another lane showed that some rules are failed by a perfect net: the drawing itself, sampled as the library samples, misses them on thin strokes. `gates-v2.1.json`, sha256 `214942e398f88110cd7c6044c194f0f274274aeedb07abcbe8e1a18dc2b323c0`, dropped the overlap of the worst character for letters. `gates-v2.2.json`, sha256 `dd3cc2ea30ccb49d001c28a905bcc6e2a2d11edfcd6a741464fda91162b10e70`, **gave the verdicts here**: it is 2.1, and for each group and size a rule that the perfect drawing of that group fails is not applied there; every other rule applies with its limit, and nearest-to-itself and none-vanished are never skipped. No limit was changed.

Of the 6 groups first trained, 4 passed with both seeds under gates-v2, 6 under 2.1 and 6 under 2.2. **Rules skipped under 2.2 because a perfect net fails them: 0** in the groups of the bundle.

The rule is automatic and nobody chose a net. A group whose two seeds pass ships the seed with the lower mean error over 8×16, 16×32 and 48×96. A group that fails is trained once more as two groups of half its characters; a half that still fails is left out.

- **6 groups trained, 6 passed with both seeds.**
- **Left out: none.** Every character drawn for the bundle is in it.
- Every group net in the bundle passes the C-against-float64 check.

**Small cells.** The gates are loose at 6×12 by their formula (a letter group passes with a mean overlap of 0.44). Here the lowest overlap of any one character at 6×12 is 0.67 (`tscrl` group 2). Below 6×12 nothing is counted.

## What a consumer changes

Nothing, until it opens this file. It does not replace split-v9 and holds none of its characters; `tests/check_bundle_lists.py` checks that it shares no trained scalar with split-v9 or any other listed bundle.

```c
neuronte_open_file("neuronte-split-v9.nrt", &base);
neuronte_open_file("neuronte-term-scripts-v1.nrt", &more);
/* for each scalar c */
font = neuronte_untrained(more, c) ? base : more;
```

`neuronte_untrained(more, c)` is 0 for exactly the 48 characters in `neuronte-term-scripts-v1.list.txt` and 1 for every other scalar. A scalar outside the list, drawn through this file anyway, comes out blank, or as the code-made hollow box after `neuronte_set_untrained(more, 1)`. The file needs the current runtime (version 2 bundles, 128-member limit). It has 7 members. Cells are the terminal's 1:2 cell; the nets were trained and measured from 6×12 to 48×96.

## Recipe

- **Drawings.** Lisu is made by rule (`as` lines of `font/term-scripts.txt`): 25 letters are this
  face's Latin capitals, 15 are capitals turned half round in the capital's
  box, and the marks are written with the full stop, comma, semicolon,
  colon, hyphen and equals sign.
  No font was opened or rasterised; DejaVu Sans Mono gave only its list of code points.
- **Sets and groups.** 1 training set of `font/term-scripts.txt`, each cut in order into group nets of 8 to 8 characters (6 in all).
- **Training.** `train/split_expert.py train --mode repertoire --partition contiguous`, unchanged: hidden width 64, 120,000 steps, the project teacher (grid 256), seeds 0 and 1. No retry at another width.
- **Selection.** As under "The gates". Only the shipped seed's JSON is in `weights/`; the other seed's hash and measurements are in the validation record.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
make pack-term-scripts-v1    # rebuilds the .nrt byte for byte from the group nets
make test-term-scripts-v1
```

## Checks

`make test-term-scripts-v1` (part of `make test`): every group net against the float64 reference; the bundle rebuilt byte for byte; its table exactly `neuronte-term-scripts-v1.list.txt`, which is its training sets in `font/term-scripts.txt` less any group left out; every scalar from U+0000 to U+10FFFF routed as the table says; pixels through the bundle equal to each group net alone at 19 cell sizes and with one sample a pixel; `test_api --standalone`; and the validation record: every shipped group passed with both seeds and ships the seed the rule selects.

## Results by group

Mean error against the teacher at 8×16, 16×32 and 48×96 and mean overlap at 6×12 and 8×16, for the shipped seed (for a group not shipped, the lower-error seed).

| Set | Group | Characters | Result | Rules missed (seed 0 / seed 1) | Mean error | Overlap 6×12, 8×16 |
|---|---:|---|---|---|---|---|
| `tscrl` | 0 | ꓐ ꓑ ꓓ ꓔ ꓖ ꓗ ꓙ ꓚ | passed; H64, seed 0 | 0 / 0 | 0.0063 0.0030 0.0015 | 0.983, 0.979 |
| `tscrl` | 1 | ꓜ ꓝ ꓟ ꓠ ꓡ ꓢ ꓣ ꓦ | passed; H64, seed 1 | 0 / 0 | 0.0066 0.0028 0.0015 | 1.000, 0.966 |
| `tscrl` | 2 | ꓧ ꓪ ꓫ ꓬ ꓮ ꓰ ꓲ ꓳ | passed; H64, seed 1 | 0 / 0 | 0.0058 0.0029 0.0014 | 0.936, 0.966 |
| `tscrl` | 3 | ꓴ ꓒ ꓕ ꓘ ꓛ ꓞ ꓤ ꓥ | passed; H64, seed 1 | 0 / 0 | 0.0057 0.0029 0.0013 | 1.000, 0.965 |
| `tscrl` | 4 | ꓨ ꓩ ꓭ ꓯ ꓱ ꓵ ꓶ ꓷ | passed; H64, seed 0 | 0 / 0 | 0.0064 0.0030 0.0014 | 0.992, 0.981 |
| `tscrl` | 5 | ꓸ ꓹ ꓺ ꓻ ꓼ ꓽ ꓾ ꓿ | passed; H64, seed 0 | 0 / 0 | 0.0015 0.0011 0.0004 | 1.000, 0.902 |

## Speed

Not measured yet.

## Files

`neuronte-term-scripts-v1.nrt` (343,188 bytes, sha256 `d18eda009dfb6a955ca0a74e0f22f74f7f314d34a036ed331be44c581fb552e6`), `neuronte-term-scripts-v1.list.txt`, `neuronte-term-scripts-v1.provenance.json`, `neuronte-term-scripts-v1.validation.json`, and 6 group nets `neuronte-term-scripts-v1-SET-gN.json`. All are in `weights/SHA256SUMS`.
