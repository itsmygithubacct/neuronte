# Symbol expert v1 (opt-in bundle)

`neuronte-split-v5-symbol-v1.nrt` is split-v5 with its 49 symbol labels drawn by four
smaller group nets instead of the single width-128 symbol expert. It is an explicitly
selected new bundle: `neuronte-split-v5.nrt` is unchanged and stays the default, so
anything bound to its SHA256 is unaffected.

## What changed

- Four repertoire groups of 12/12/12/13 labels (contiguous in scalar order), each a
  90→32→32→32→1 net (5,057 parameters each; 20,228 total vs 44,801 for the width-128
  expert; the same H=128 total width). Trained with `train/split_expert.py`
  (`--mode repertoire --partition contiguous --parts 4 --steps 80000`), seeds 0 and 1,
  from source `be17cff1b03315ba6c2c2bde8b39f3b11618f34f` (trainer SHA256 `75ca82ea0d18b138…`).
  Seed 0 is shipped (`neuronte-symbol-v1-g0..g3.json`); seed 1 is kept as
  `*.seed1.json`.
- The bundle was made with `train/known_bundle.py weights/neuronte-split-v5.nrt OUT
  g0..g3.json --expert 2`: split-v5's six members and gate rows are byte-identical,
  four members are appended, their gate outputs are suppressed, and only the 49
  symbol labels in the table move to them. Every other label, every untrained scalar
  and the fallback route exactly as in split-v5. The public API and file format are
  unchanged (the 128-member cap already allows it).

## Quality (native library, against the same teacher as symbol-v0)

Predeclared gates, relative to symbol-v0: all 49 nearest-teacher identities kept and
nothing vanishes; MAE ≤ base+.0015, p99 ≤ base+.02, firm-wrong fraction ≤ base+.0005;
per-glyph MAE ≤ base+.01; separation margin ≥ ¼ of base; plus 23 geometry sizes from
1×2 to 64×128 (including widths 23/24/25 and odd heights). Both seeds pass all of them.

| Cell | symbol-v0 MAE / p99 | seed 0 | seed 1 | seed 0 firm-wrong px |
|---|---|---|---|---|
| 8×16 | 0.00407 / 0.050 | 0.00436 / 0.053 | 0.00449 / 0.054 | 0 (base 0) |
| 16×32 | 0.00210 / 0.047 | 0.00244 / 0.049 | 0.00244 / 0.051 | 0 (base 0) |
| 48×96 | 0.00138 / 0.047 | 0.00196 / 0.063 | 0.00203 / 0.065 | 99 (base 16) |

This is a small, measured quality cost for speed: MAE rises 7–42% (largest at 48×96)
and 48×96 p99 sits close to its limit (0.063 vs 0.067). A 2×64 split
(40,000 steps) is closer to the original but only about 2.4× faster; 8×16 and 16×8
splits and a 2×2 spatial split did not pass. Full records are in
`neuronte-symbol-v1.validation.json`.

## Speed (uncached coverage, ms/glyph, 49-symbol corpus, one core)

kilix-bench `8f19228` expert experiment, 1 warmup + median of 10, 4 corpus passes;
A and B are two x86-64 hosts.

| Host | Bundle | 8×16 | 16×32 | 48×96 | open ms |
|---|---|---:|---:|---:|---:|
| A | split-v5 | 0.836 | 2.965 | 6.960 | 2.68 |
| A | 2×64 candidate (not shipped) | 0.363 | 1.232 | 2.589 | 2.77 |
| A | **split-v5-symbol-v1** | 0.165 | 0.545 | 1.123 | 2.74 |
| B | split-v5 | 0.616 | 2.207 | 5.215 | 1.80 |
| B | 2×64 candidate (not shipped) | 0.266 | 0.905 | 1.914 | 1.89 |
| B | **split-v5-symbol-v1** | 0.117 | 0.398 | 0.827 | 1.74 |

Primed (cached) draw is unchanged; first-corpus draw tracks coverage.

## Checks

`make test-symbol-v1`: packed-C vs float64 NumPy reference for each group net;
`tests/check_symbol_v1.py` (bundle rebuilds byte-for-byte; every symbol label equals
its group net bit for bit at 18 cell sizes; 1,127 other labels and ~3,000 untrained
scalars route and cover exactly as split-v5; cached draws equal first draws);
`test_api --full --accent --pixel`.

## Reproduction

```sh
python3 train/split_expert.py prepare DIR --set symbol
python3 train/split_expert.py train DIR --set symbol --mode repertoire --partition contiguous \
    --parts 4 --seeds 0,1 --steps 80000 --device cuda
# rename DIR/symbol-repertoire-contiguous-k4-pN-s0.json to weights/neuronte-symbol-v1-gN.json
cd train && python3 known_bundle.py ../weights/neuronte-split-v5.nrt \
    ../weights/neuronte-split-v5-symbol-v1.nrt ../weights/neuronte-symbol-v1-g[0-3].json --expert 2
```
