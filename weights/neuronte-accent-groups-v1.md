# Accent script groups: selected seed 0

Three independent networks replace known accent labels in
`neuronte-split-v8.nrt` ([recipe, checks and speed](neuronte-split-v8.md)):

| Member | Repertoire | Labels | Hidden width | Parameters |
|---|---|---:|---:|---:|
| 0 | Latin, diacritics and spacing marks | 203 | 192 | 91,777 |
| 1 | Greek | 49 | 128 | 44,801 |
| 2 | Russian | 66 | 128 | 44,801 |

Each glyph runs one network. The new networks total 181,379 parameters,
16.92% more than the original H256 expert's 155,137. The original expert
remains in the full bundle for unknown fallback; total storage increases.

## Training and selection

Both seeds 0 and 1 completed 120,000 Adam/cosine steps with the original
teacher, unknown regularization weight 1 and independent per-model losses.
Trainer revision: `79ef666df956c0718c87f0719ccda7ddead223e5`.
Teacher SHA256: `770525efe59bb69a465b91a87305212555186e60c941e17a2f56318e34a781c4`.

The owner selected seed 0 for the combined bundle, now `neuronte-split-v8`,
after reviewing the regressions.
It has fewer failed automatic geometries (16 versus 17), fewer new lost
binary-overlap glyph/size events (13 versus 14), and fewer failing glyphs
at 8x16 (2 versus 4). It is also slightly faster. Seed 1 has lower average
coverage error and the stronger explicit S1 result. This selection accepts
known regressions; **the original quality gates did not pass**.

## Geometry exceptions

Automatic sampling was evaluated at 25 geometries for both seeds. Selected
seed 0 fails 1x1, 1x2, 2x3, 3x5, 5x9, 7x13, 8x16, 9x17, 16x32, 16x16,
12x40, 3x6, 4x8, 5x10, 6x12 and 12x24. All remaining tested automatic
geometries pass, including 48x96. Explicit S1 passes 8x16 and 48x96 but
fails 16x32. Exact script metrics and failures are retained in
`neuronte-accent-groups-v1.validation.json`.

At 16x32 the sole failing glyph is U+00B4, the spacing acute accent. One
pixel's coverage changes from 0.501898 to 0.499445, crossing the 0.5 binary
threshold. IoU becomes 16/17 (0.941176), below the original-relative floor
of 0.95, despite the subtle antialiased difference. At 3x6, eight glyphs
newly lose all thresholded overlap with their teacher. This definition of
lost overlap does not necessarily mean a blank output. Tiny geometries
also contain nearest-identity regressions. At 48x96, average coverage error
and mean IoU improve and all declared checks pass.

Per-glyph limits: MAE no more than baseline +0.01, IoU no less than baseline
−0.05, no new lost overlap or baseline-correct nearest-identity regression.
Per-script limits: MAE +0.0015, p99 +0.02, firm-error fraction +0.0005,
mean IoU −0.005. Both seeds were required for the original recipe gate;
selecting this specific asset does not change that recorded result.

## Native performance

On a Core i7-6820HQ, selected seed 0 has uncached coverage medians of
1.1391 / 4.1838 / 9.1889 ms per glyph at 8x16 / 16x32 / 48x96. The fresh
original baseline is 2.1139 / 8.1754 / 18.4085 ms: geometric mean speedup
1.9367x. Warm draw at 16x32 is essentially unchanged (3.5783 versus
3.5802 microseconds). The selected accent-only full bundle opens in
3.6633 ms versus 2.6084 ms for the baseline.

These measurements used the complete 318-label repertoire, one warmup,
ten measured repetitions, four passes for coverage and warm draw, one cold
pass, a single core and an exclusive host lock. All 605 trials in the
five-case experiment and all 15 independent packed pixel-reference checks
were audited. Those opening figures describe the measured accent-only
bundle, not split-v8, whose own measurements are in its card.

## Assets and integration

The three `neuronte-accent-groups-v1-p*.json` files are byte-identical to
the selected training exports. `neuronte-accent-groups-v1.nrt` is the
726,336-byte direct bundle, SHA256
`998ffdd2c1f4d74cee03d38d169f0b1fe5e15ce2ef2508243b8b727020537bce`.
The reviewed full accent-only seed-0 bundle has SHA256
`feb7a42495fc4914be7015506195dafd2541aa80a2f9cac06e7461dced5cb983`.

`make pack-split-v8` appends these networks after the symbol and pixel groups,
rewriting only expert 3's 318 labelled routes. Existing members, gate rows,
ASCII/Braille/pixel choices and unknown fallback are retained. Integration
checks compare every selected glyph with the direct networks and the saved
native coverage hashes at all 25 automatic and three S1 sizes. The checks
prove faithful packaging; they do not relabel the geometry exceptions.
