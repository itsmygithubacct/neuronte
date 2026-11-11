# RC9 Greek and Russian bundle

`neuronte-split-v5.nrt` is an explicitly selected new bundle. It adds 49 Greek
letters (including final sigma) and 66 Russian letters (including Ё/ё) to the
1,061 labels in split-v4. Greek accents, other Cyrillic alphabets and shaping
are outside these new labels. The existing split-v4 default and full-v2 are
preserved. The release owner decides default integration separately.

The new accent-v2 expert has 318 labels: the previous 203 Latin letters and
spacing marks plus these 115 letters. It uses width 256, 155,137 parameters,
and 40,000 steps. Both seeds 0 and 1 were trained from source commit
`d05f14f6c0d0e6ed2077d6007b4a5f588e4ca802`, exported before GPU transfer.
Its JSON records the training source hashes; later trainer checkpoint changes
do not change the historical source identity. Raw trials and source exports
are retained in the RC9 training run. Seed 0 is shipped.

The gate was trained at width 32 for 6,000 steps, seed 0, using Unicode 16
Blocks.txt (its hash is in the gate JSON). It is exact on all 1,176 trained
labels and 2,472 other scalars in their blocks; agreement elsewhere is
99.993% on 198,977 samples. Routing an untrained scalar does not establish
trained glyph coverage. The other five experts are unchanged.

Both seeds pass the predeclared per-script mean IoU >= .985 gates at 16 and
48 px with no lost nonempty glyph. Fresh packed-C scores are:

| Script | Seed | 16 px | 48 px |
|---|---:|---:|---:|
| Greek | 0 | .986587467 | .992292049 |
| Greek | 1 | .988584452 | .993146348 |
| Russian | 0 | .988316952 | .992848527 |
| Russian | 1 | .988858105 | .992363702 |

The 203 old labels were also compared against the current targets, using the
same packed-C sampling for all three nets. This is not an across-board
improvement: mean Latin IoU at 16 px declines slightly, and individual
letters regress at every measured size. Seed 0 has the better Latin means
of the two new seeds. The largest 16 px decline is spacing ogonek U+02DB,
-.037037 (one boundary pixel). All counts and per-glyph deltas are in
`neuronte-accent-v2.latin-comparison.json`.

| Size | Accent-v1 | New seed 0 | New seed 1 |
|---|---:|---:|---:|
| 8 | .978574971 | .979440926 | .978177257 |
| 16 | .984936529 | .984822170 | .984763439 |
| 48 | .988548340 | .990560607 | .989912720 |

Both standalone seeds pass 133 C/float64 NumPy script cases, with maximum
differences 4.28e-6 and 5.23e-6. The bundle passes 117 reference cells and
2,116 routing checks (maximum difference 5.56e-6), all 115 new script routes,
and the full/accent/pixel API checks. Root inspected source versus both seeds
at 16/48 and found no visual blocker. The exact sheet SHA256 and review are
in `neuronte-split-v5.validation.json`; this is root review, not user approval.
The score files retain both seeds and full-precision per-glyph training
counts. Their GPU Latin subset omits four below-U+00C0 spacing marks; the
fresh C comparison above includes all 203 old labels.

Reproduction (run training from the historical source commit; current packing
and validation commands work from this tree):

```sh
python3 train/train.py accent-s0.json --set accent --width 256 --seed 0 --steps 40000 --score-sizes 8,16,32,48 --scores-out accent-s0.scores.json
python3 train/train.py accent-s1.json --set accent --width 256 --seed 1 --steps 40000 --score-sizes 8,16,32,48 --scores-out accent-s1.scores.json
python3 train/pack.py weights/neuronte-accent-v2.json accent-v2.nrt
python3 train/gate.py gate.json weights/neuronte-ascii-v0.json weights/neuronte-draw-v2.json weights/neuronte-symbol-v0.json weights/neuronte-accent-v2.json weights/neuronte-pixel-v1.json weights/neuronte-braille-v0.json --steps 6000 --blocks Blocks-16.0.0.txt
python3 train/pack.py --bundle split-v5.nrt weights/neuronte-ascii-v0.json weights/neuronte-draw-v2.json weights/neuronte-symbol-v0.json weights/neuronte-accent-v2.json weights/neuronte-pixel-v1.json weights/neuronte-braille-v0.json --gate weights/neuronte-gate-v4.json
python3 tests/check_scripts.py build/libneuronte.so split-v5.nrt weights/neuronte-accent-v2.json
python3 tools/mono-compare.py --library build/libneuronte.so --baseline weights/neuronte-accent-v1.json --candidate weights/neuronte-accent-v2.json --other-seed accent-s1.json --out latin-comparison.json
python3 train/pack.py accent-s1.json accent-s1.nrt
python3 tools/scripts-preview.py scripts.png --weights split-v5.nrt --other-weights accent-s1.nrt --library build/libneuronte.so
```

The bundle is 1,573,128 bytes with six networks and 68 ranges. The standalone
accent net is 620,752 bytes. `SHA256SUMS` covers the new assets and reports as
well as the retained prior assets.
