# ASCII decomposition experiments

`decompose.py` trains independent four-layer scalar-field models for the
95 printable ASCII characters. It compares a total hidden-width budget of
128 split into 4×32, 8×16, 16×8 or 64×2. Spatial grids are respectively
2×2, 2×4, 4×4 and 8×8. Each tile receives the original scalar and learns
its region of every glyph. Repertoire groups divide the ordered 95
characters into contiguous groups whose sizes differ by at most one;
one group draws a complete glyph.

Prepare the immutable FP16 teacher and coverage masks once:

```sh
python3 train/decompose.py prepare /tmp/ascii-experiment
python3 train/test_decompose.py
python3 train/decompose.py train /tmp/ascii-experiment --mode spatial --parts 4 --seeds 0,1 --batch-models 8
```

Choose a directory on suitable active storage. Training requires NumPy
and PyTorch. The teacher records source and asset SHA256 digests; prepared
coverage masks use eight samples per pixel dimension at 8×16, 16×32 and
48×96. Training retains the original 20,000-step Adam/cosine recipe,
256 labelled samples per glyph, near-edge sampling, 64 unlabelled
scalars and the area/diversity loss. TF32 is disabled. Spatial target
fields retain their original distance units; exported tau is divided by
the tile's horizontal span so coverage uses the whole glyph's scale.

`--start` and `--batch-models` select a slice of the seed-major model
inventory. Each model has independent parameters and Adam state. The
sum of per-model losses preserves independent gradient scale. Models
within a seed and padded glyph-count group share random draws; changing
batch boundaries may change that group and therefore the trajectory.
Padded glyphs are excluded from loss and scalar matching.

`--stop-after N` checkpoints and exits at an absolute step, retaining the
full cosine schedule. `--resume` validates the teacher, trainer digest,
model inventory, schedule, loss, device and software identity before
restoring parameters, optimizer and per-seed RNG state. It refuses a
different experiment. Completed checkpoints can regenerate exports.
Checkpoints are written by atomic replacement and no intermediate
checkpoint is exported as a completed model.

`test_decompose.py` compares batched losses, gradients and Adam updates
against individual networks with the original broadcast distance loss.
It also checks geometric interpolation, disjoint complete character
groups and exact interrupted/resumed CPU training. Set
`DECOMPOSE_TEST_DEVICE=cuda` to run the independent-gradient comparison
on CUDA. Timing, quality and production selection belong to the
experiment's external research record, not the trainer's output loss.
