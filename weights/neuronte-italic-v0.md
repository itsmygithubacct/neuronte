# RC9 completion of the desktop italic sizes

This adds the 17 previously missing native italic sizes and preserves all 13 existing italic models. Native italic nets now cover every size from 3 through 32 px. Sizes 1 and 2 retain their documented fallback. These assets do not change the split/full defaults.

Both seeds of one matching recipe pass every one of the 96 source glyphs, regular and bold, through the packed C renderer and independently through desktop/PIL masks and advances:6528 exact comparisons. The published seed is consistently 0. C/NumPy differences and model/target hashes are retained in `neuronte-italic-v0.validation.json`; raw score records from both seeds accompany each model.

| Size | Width | Training | Distinct source masks |
|---|---:|---|---:|
|3|96|20000 steps|46|
|4|96|20000 steps|69|
|5|96|20000 steps|74|
|6|96|20000 steps|75|
|7|96|20000 steps|89|
|8|128|40000 steps|96|
|9|96|20000 steps|96|
|13|192|40000 steps|96|
|15|128|30000 steps|96|
|17|256|40000 steps|96|
|19|256|40000 steps|96|
|21|256|40000 steps|96|
|23|256|40000 steps|96|
|25|256|40000 steps|96|
|27|512|60k +20k restarted phase, then shared bias -.05|96|
|29|384|40000 steps|96|
|31|512|40000 steps|96|

The 3–7 px sources deliberately reuse some pixel shapes because those grids are small. Exact reproduction is not a claim that every glyph is distinct or easy to read. All alias groups and advances are recorded.

The 27 px pair first trained at width 512 for 60,000 steps. Seed 1 retained one extra dollar-sign pixel. Both seeds then resumed the same completed parent checkpoints for a **separate 20,000-step cosine phase**, starting at LR 0.0002 and retaining Adam and CPU/CUDA RNG state. This is not fresh 80,000-step cosine training. The extra pixel remained, so both continued models received the same normalized output bias offset **-.05**. The feasible common interval was[-.069203,-.036058]; targets, rendering and thresholds stayed unchanged. Both derived artifacts then passed all 192 actual C and desktop/PIL regular/bold comparisons. Their score files clearly distinguish the failed pre-calibration scores from the final packed C acceptance. Parent checkpoint/source identities and calibration hashes remain in each model.

Earlier failed same-recipe pairs remain in the research receipts:8px96/20k,13px128/30k,27px384/40k,512/60k and uncalibrated60k+20k. No seed was combined with a different recipe to close acceptance.

Root reviewed representative source/both-seed regular/bold text at3/4/8/13/17/25/31px, and a separate27px sheet including the dollar sign. No visual blocker was found. This review covers the stated samples; exhaustive pixel acceptance covers all 96 glyphs. It is root review, not user approval.

All targets use grid 256, tau .15 and the size-specific pen radius. Below 24 px the established consumer uses 2x2 samples; at 24 px and above it uses 1x1. Source and trained bytes were verified before rental teardown.

Repack with `make pack-rc9-italics`; validate the selected inventory with `make test-rc9-italics`. Ordinary training uses `python3 train/train.py OUT.json --set uiEMi --width WIDTH --steps STEPS --seed SEED --unlabelled 0 --score-sizes EM --scores-out SCORES.json`. Historical source hashes in every model bind the recipe. For 27 px, use the source-bound `--continue-from`, `--continue-source`, `--continue-lr .0002`, `--steps 80000` options, then `tools/calibrate-output-bias.py` with `--offsets=-.05`.
