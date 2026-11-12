# RC9 original emoji v0

This explicit, separate colour bundle covers **300 single Unicode scalars**, represented by 600 left/right half labels across three experts. It occupies **7,011,412 bytes**. Each glyph spans two cells, uses at most six layers, and carries fixed colours for dark and light themes. The source manifest is `font/emoji-manifest.json`. Existing fonts, icons, split-v4 and full-v2 are preserved; this asset does not change a default.

The drawings and palette are original project geometry, with no external artwork or font tracing. The set contains 100 faces, 30 hands, 24 clocks, 20 controls, 18 shapes, 18 hearts and 90 objects. Two source pairs intentionally share geometry: U+2709/U+1F4E7 and U+270A/U+1F44A. This first set covers individual scalars; joined sequences, flags and skin-tone sequences are outside its inventory. Call the half API with the original Unicode scalar and half 0 or 1.

All three experts use form A, width 512 and a 64-wide palette head. Both seeds originally trained for 60,000 steps from the committed `ba5a171` source export, with PyTorch 2.7.1/CUDA 12.8 on an RTX 5090. Both complete seed bundles pass the same publication gates. Seed 0 is selected for its stronger 16px aggregate and coherent full visual review; seed 1 has the better 32px aggregate.

The raw models required explicit calibration:

| Expert | Same recipe for both seeds | Final C mean16, seed 0 | Seed 1 |
|---|---|---:|---:|
| 0 | Add -.0024 to every output bias | .991090360 | .991240263 |
| 1 | Add -.0026 to every output bias | .990386601 | .990641296 |
| 2 | Separate 10,000-step final-layer coverage phase | .994699211 | .990835978 |

Expert 2 freezes all three hidden layers and the palette head. A **new Adam optimizer** trains only the final layer, using unchanged 16px source coverage, a binary margin and a penalty for departures from the parent model's predicted field. Its settings are LR .0001 with a new cosine horizon, margin .05, margin weight 100, field penalty .005 and 128 sampled pixels per glyph per step. This is a separate calibration phase, not continuation of the original optimizer or fresh 70,000-step SDF training. The trainer checkpoints its optimizer and RNG, and interrupted resume was verified byte-exact. Parent model, target, trainer and checkpoint-source hashes are retained in the model.

The earlier width384/40k expert-0 pair, all uncalibrated width512/60k models, and the weaker 5,000-step expert-2 phase remain recorded as failed trials. No passing seed was combined with a different recipe to complete a pair. The accompanying per-expert `.scores.json` and `.seed1.scores.json` files are the **raw 60k scores before calibration**. Final acceptance is the actual packed-C report in `neuronte-emoji-v0.quality.json`.

The predeclared gates require mean IoU >= .990 at 16px for every expert in both seeds, exact palette heads, no positive coverage in unused layers or layers with zero reference coverage, no lost target-positive binary layer, and no zero coverage for a source layer with nonzero reference coverage. Mean RGB error must remain <= 2/255 in both themes at 12, 16 and 32px. Every final expert passes. Intentionally empty half layers are excluded from the mean and separately required to remain empty; 1,292 nonempty half layers contribute to each aggregate.

**Sampling scope is explicit.** Quality measurements disable snapping at 12/16/32px and use 2x2/2x2/1x1 samples respectively. Source coverage comes from the unchanged grid256 float16 field, pen radius .075, tau .15 and an 8x8 reference grid, with a .5 coverage threshold. These measurements do not represent every consumer configuration. Separate checks compare 60 sampled halves per seed against float64 NumPy at 8px, 2x2 sampling, with snap settings 0 and 14. Maximum differences are 6.85e-7 and 8.76e-7. Sampled half drawing through the C compositing API at 16px differs by at most one channel level in either theme. The file's default snap threshold is 14; the complete 16/32px visual review uses that file default. Display validation at 8px with default snapping is separate.

| Cell width | Complete seed 0 mean IoU | Seed 1 |
|---|---:|---:|
| 12 | .972963856 | .972943559 |
| 16 | .992125212 | .990905053 |
| 32 | .985122353 | .986918707 |

This is **not an across-size improvement**. For selected expert 2, the calibration changes C means12/16/32 from .965747450/.985477528/.987066862 to .960768313/.994699211/.977033673. Seed 1 has the same tradeoff. Worst mean RGB error across both seeds, experts, themes and tested sizes is .623790/255, within the unchanged gate. Per-layer overlap counts and raw-parent comparisons remain available in the quality and validation reports.

Publication also verifies exactly 300 distinct source scalars and all 600 half labels across exactly three experts, with no omissions, extra labels or duplicate ownership. Both halves of each scalar belong to the same expert. Both complete NRT files reproduce from their JSON sources, and every C route is checked. Root reviewed all 26 pages covering all 300 glyphs at 16 and 32px, comparing source geometry and both seeds in dark and light themes. Exact image/model/library hashes and the review scope are retained in `neuronte-emoji-v0.validation.json`. Fine detail is coarse at small cells, and pale source colours have low contrast on white. This is root review, not user approval.

Build and validate the published inventory:

```sh
make all pack-rc9-emoji test-rc9-emoji
```

The Makefile produces each standalone expert and the complete bundle, then invokes the C verifier with `--manifest font/emoji-manifest.json`. Single-expert validation remains available without `--manifest`.

The original training recipe, repeated for each shard 0/3, 1/3 and 2/3 and seeds 0 and 1, is:

```sh
python3 train/colour.py raw.json --drawing font/emoji.txt --palette font/emoji-palette.txt --wide --shard 0/3 --form A --layers 6 --head-width 64 --width 512 --seed 0 --steps 60000 --matmul-precision high --checkpoint raw.pt --scores-out raw.scores.json
python3 tools/calibrate-output-bias.py raw.json calibrated.json --offsets=-.0024
```

Use the historical source export for original training. Expert 1 uses offset -.0026. Expert 2 instead uses the source-bound separate phase from commit `885b63a`:

```sh
python3 train/colour_calibrate.py raw-e2.json targets.npz --prepare-targets
python3 train/colour_calibrate.py raw-e2.json calibrated-e2.json --targets targets.npz --steps 10000 --lr .0001 --margin .05 --margin-weight 100 --field-anchor .005 --batch-pixels 128 --checkpoint phase.pt
```

All raw trials, source exports, phase checkpoints and remote/local SHA receipts were retained before rental teardown. Neither source geometry nor acceptance thresholds were changed to close a gate.
