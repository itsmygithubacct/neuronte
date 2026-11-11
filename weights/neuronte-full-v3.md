# RC9 full-v3

This separate monolithic font trains all 878 current full-set targets: the 763
labels in full-v2 plus 49 Greek and 66 Russian letters. The mosaic additions
remain in the split bundles. Full-v2 and split-v4 are preserved; this file does
not change the default. The full-v3 net is width 384, 331,009 parameters and
1,324,240 packed bytes.

Both seeds 0 and 1 trained for 40,000 steps from committed source
`d05f14f6c0d0e6ed2077d6007b4a5f588e4ca802`, exported before transfer, with
unlabelled weight 1.0. The original JSON source identities are retained.
The rental used PyTorch 2.7.1/CUDA 12.8 on an RTX 5090. Both jobs finished
successfully and their fetched JSON/score hashes matched the remote files.

Both seeds pass the predeclared mean IoU >= .98 gate for every tier and
script at 16 and 48 px, with no lost nonempty glyph. These are actual packed
C scores against current source targets, using production automatic sampling:
2x2 at 16 px, 1x1 at 48 px. The reference target uses a 256-node-per-cell
float16 field, pen radius .075, tau .15 and 8x8 pixel samples. Per-model shape,
target, library and source hashes are retained in the quality report.

Seed 1 is selected for publication because its common-label and whole-set
means exceed seed 0 at both sizes. Its tier means are:

| Tier | Labels | 16 px | 48 px |
|---|---:|---:|---:|
| ASCII | 95 | .988239615 | .986314544 |
| Box drawing | 128 | .999081511 | .996783429 |
| Blocks | 29 | 1.000000000 | .999985040 |
| Shades | 3 | 1.000000000 | .998602853 |
| Braille | 256 | 1.000000000 | 1.000000000 |
| Symbols | 49 | .987517725 | .986281530 |
| Latin letters and marks | 203 | .983045536 | .984319824 |
| Greek | 49 | .984307888 | .987443146 |
| Russian | 66 | .987189269 | .987140563 |

The fair baseline comparison uses only the **763 labels trained in full-v2**.
An old-net average over all 878 would include 115 untrained outputs and is
excluded from publication summaries.

| Size | Full-v2 | New seed 0 | Selected seed 1 |
|---|---:|---:|---:|
| 16 | .991558285 | .992354653 | .993069212 |
| 48 | .989761246 | .990920862 | .992697581 |

This is not an across-board improvement. Selected seed 1 regresses on 79
common glyphs at 16 px and 121 at 48 px. Box mean16 declines from .999182355
to .999081511. The largest individual declines are spacing diaeresis U+00A8
at 16 (-.075758) and colon U+003A at 48 (-.039245). All per-glyph overlap counts
and selected-seed deltas are in `neuronte-full-v3.validation.json`.

Both packed candidates pass the C/NumPy reference and API checks. Maximum
reference differences are 2.39e-5 for seed 0 and 9.17e-6 for seed 1. Raw GPU
score files retain both seeds, but the packed C results determine acceptance.
The GPU Latin subset omits four spacing marks below U+00C0; the C Latin tier
includes all 203 previous labels.

Root reviewed all 19 pages covering all 878 glyphs, comparing source geometry,
full-v2 and both packed candidates at 16/48 px. No visual blocker was found.
The exact image/model/library hashes and selection receipt are retained in
`neuronte-full-v3.validation.json`. This is root review, not user approval.
Both seeds also pass the separate 115-letter script C/NumPy check (133
coverage cases each; maximum difference below 7.46e-6).

Reproduction (training uses the historical source commit; current validation
and packing use the scripts in this tree):

```sh
python3 train/train.py full-s0.json --set full --width 384 --seed 0 --steps 40000 --score-sizes 8,16,32,48 --scores-out full-s0.scores.json
python3 train/train.py full-s1.json --set full --width 384 --seed 1 --steps 40000 --score-sizes 8,16,32,48 --scores-out full-s1.scores.json
python3 train/pack.py weights/neuronte-full-v3.json full-v3.nrt
python3 tools/mono-compare.py --library build/libneuronte.so --baseline weights/neuronte-full-v2.json --candidate full-s0.json --other-seed full-s1.json --set full --include-new --sizes 16,48 --samples 0 --minimum-iou .98 --out both-seeds.json
make test-rc9 test-rc9-quality
```
