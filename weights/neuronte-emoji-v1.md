# Emoji v1

`neuronte-emoji-v1.nrt` draws the same 300 single-scalar emoji as `neuronte-emoji-v0`, with the same 600 left/right half labels, drawings, palettes, six layers and half API. It is about **five times as fast**. It uses **twelve experts of width 192** in place of three of width 512, and the bundle is **4,785,292 bytes** against v0's 7,011,412. It is a separate file: v0 is unchanged and still shipped, and no default changes.

## Why it is faster

A colour net costs about two H x H matrix products per sample, so a width-192 expert does about 1/7 of a width-512 expert's work. The runtime skips zero inputs, so the real ratio also depends on sparsity, and it was measured, not assumed (below). Every glyph is drawn by exactly one expert, so twelve narrow experts cost no more per glyph than one.

## The partition

Twelve contiguous groups (the first try, recipe A) did not pass. A group made of straight-edged arrows and shapes reached only .9668 at 16 px, while other groups had easy glyphs to spare. The per-expert gate is a mean, so v1 balances difficulty instead. `tools/balance.py 12 font/emoji-partition-balanced-12.json` uses v0's published per-layer 16 px IoUs (`neuronte-emoji-v0.quality.json`, mean of both seeds) as the difficulty of each glyph. It deals the glyphs greedily, hardest first, into twelve parts of 25 glyphs (50 half labels) each, then swaps pairs while the worst part's mean improves. The script is deterministic and reproduces the committed file byte for byte. Both halves of a scalar always share an expert. `train/colour.py --partition FILE --part I` trains on exactly one part, and the partition file's hash is recorded in each model. The six-part file `font/emoji-partition-balanced-6.json` was the wider alternative (6 x 256). It passed too, but was slower, so it was not selected.

## Recipe

For each part `I` in 0..11 and each seed:

```sh
python3 train/colour.py raw.json --drawing font/emoji.txt --palette font/emoji-palette.txt --wide \
    --partition font/emoji-partition-balanced-12.json --part I --form A --layers 6 --head-width 64 \
    --width 192 --seed 0 --steps 60000 --matmul-precision high --checkpoint raw.pt --scores-out raw.scores.json
python3 train/colour_calibrate.py raw.json targets.npz --prepare-targets
python3 train/colour_calibrate.py raw.json neuronte-emoji-eI-v1.json --targets targets.npz --steps 10000 --lr .0001 \
    --margin .05 --margin-weight 100 --field-anchor .005 --batch-pixels 128 --checkpoint phase.pt
make pack-emoji-v1 test-emoji-v1
```

The first command is v0's training recipe with a width of 192 and a partition in place of a shard. The second and third are v0's separate final-layer coverage phase, with v0's expert-2 settings unchanged. Here every part gets the phase, and no part gets a bias offset or any per-part tuning. The same recipe was applied to both seeds. The raw 60,000-step models were trained on a rented RTX 3090 (PyTorch 2.6.0, CUDA 12.4). The phase freezes the trunk, so it ran on a laptop CPU with one thread (PyTorch 2.6.0). Each model keeps the hashes of its sources, partition, parent, targets and trainer. Seed 0 is published, following the rule declared before seed 1 or any 12-part gate was scored. Seed 1 passes too.

Without the phase, the raw nets were at par with v0's raw nets on the same layers (within -.0021..+.0026 per part, mean +.0001), but several parts were below the .990 bar. v0 itself needed the phase on its expert 2 for the same reason.

## Gates

The gates are v0's publication gates, unchanged, run by `tests/check_emoji.py` on the packed C bundle with `--manifest font/emoji-manifest.json --experts 12`. For every expert, the mean IoU at 16 px must be at least .990. At 12, 16 and 32 px there must be no lost layer, no zero coverage of a nonempty layer, no positive coverage in an unused or empty layer, and no wrong palette head. Mean RGB error must be at most 2/255 in both themes. The NumPy float64 cross-check must differ by less than 1e-3, and C compositing by at most 2 levels. Both NRT files must reproduce from their JSON, and the inventory must be exactly 300 scalars and 600 labels with no duplicate ownership. The sampling policy is v0's.

| 16 px mean IoU per expert | Seed 0 (published) | Seed 1 |
|---|---|---|
| e0-e5 | .9967 .9977 .9982 .9990 .9986 .9978 | .9992 .9975 .9996 .9983 .9985 .9955 |
| e6-e11 | .9955 .9978 1.0000 1.0000 .9999 .9996 | .9977 .9978 .9943 1.0000 .9997 .9992 |
| worst margin over .990 | +.0055 | +.0043 |

Every count gate is zero at every size, in both seeds. The worst mean RGB error is .76/255. The NumPy difference is at most 9.7e-7, and compositing differs by at most one level.

Whole-set macro IoU over the 1,292 nonempty half layers, against v0 (reported, not gated):

| Cell width | v1 seed 0 | v1 seed 1 | v0 seed 0 | v0 seed 1 |
|---|---:|---:|---:|---:|
| 12 | .9708 | .9706 | .9730 | .9729 |
| 16 | .9985 | .9978 | .9921 | .9909 |
| 32 | .9837 | .9825 | .9851 | .9869 |

This is **not an across-size improvement**. Like v0's expert 2, the phase trades a little 12 and 32 px overlap for 16 px. The lowest 32 px expert mean is .9756 in seed 0 (e8) and .9705 in seed 1 (e9), against v0's .9770 and .9811.

Visual review: all 300 glyphs at 16 and 32 px in both themes, as source | v1 | v0. The mean distance from the source is 0.41 channel levels at 16 px and 0.41 at 32 px, against v0's 0.37 and 0.33. The glyphs where v1 trails v0 most (a flag, a bar chart, a clipboard, a keyboard, a link, a globe, arrows) were inspected enlarged. Every difference is a single edge pixel, a rim one pixel softer or harder. No layer is missing or extra, and there is no colour error or seam. This is the maintainer's review, not user approval.

## Speed

Each case ran as a fresh process per job, pinned to one CPU, with one warmup and ten rounds, cases shuffled every round. Medians are reported. Every case also passed a float64 reference check (maximum difference 4.8e-6). Uncached means `coverage_layers_half`, or a fresh handle's `draw_half`, of all 600 halves. v0 and v1 are timed on the same 0.1.2 library build, and v0 is also timed on 0.1.1.

| CPU | v0 on 0.1.1, cold 16 px | v0 on 0.1.2 | v1 on 0.1.2 | v1 speedup over v0 on 0.1.2 (uncached 16 / cold 16 / uncached 32 / cold 32) | open | primed draw |
|---|---:|---:|---:|---|---:|---:|
| Core i7-6820HQ | 28.15 ms | 23.95 ms | 4.79 ms | 4.98 / 5.00 / 4.94 / 4.93 | 1.96x | 5.2x |
| Core i7-10700F | 21.41 ms | 18.44 ms | 3.57 ms | 5.15 / 5.16 / 5.10 / 5.09 | 2.17x | 5.3x |

Against v0 on 0.1.1, v1 on 0.1.2 draws uncached emoji 5.8 to 6.0 times as fast. Routing a scalar to its expert is 1.08-1.11x faster. Seed 1 measures within about 1% of seed 0. The full medians and ratios are in `neuronte-emoji-v1.quality.json`.

## Trials that did not pass

All of them are kept, with each gate's value against its threshold:

- Recipe A, 12 contiguous groups x 192: group 1 reached .9668 at 16 px (best output-bias offset .9680), a margin of -.022.
- Recipe B, 12 balanced parts x 192, raw or with an output-bias offset: worst parts -.0075 (seed 0) and -.0088 (seed 1).
- Recipe C, 6 balanced parts x 256, raw or with an output-bias offset: worst parts -.0055 (seed 0) and -.0074 (seed 1).
- A 256-wide pilot of one contiguous group: -.0002.

The 6 x 256 recipe with the phase passed on both seeds (worst margins +.0028 and +.0053), but it measured 3.2-3.4x faster against v1's 4.9-5.2x, so it was not selected.

Build and validate:

```sh
make all pack-emoji-v1 test-emoji-v1
```
