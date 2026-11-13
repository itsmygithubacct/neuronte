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

The accent expert is available with `--expert accent` on both preparation
and training. Its default hidden-width sum is 256. Repertoire splits assign
half the models to Latin letters/spacing marks, one quarter to Greek, and
one quarter to Russian, partitioning each script in scalar order. All 318
labels are retained. Spatial models see all labels. The teacher inventory
maps sparse Unicode values to field rows explicitly; it is verified before
training. `--width-budget` permits an explicitly different divisible budget
for follow-up recipes; use a separate directory for each budget to preserve
checkpoints and exports. Accent's original baseline used 40,000 steps; pass
`--steps 40000` to match that schedule. No teacher equivalence or quality
improvement is implied by trainer support.

`--expert accent --mode repertoire --parts 3` assigns the complete Latin,
Greek and Russian inventories to widths 128, 64 and 64, respectively. This
also sums to 256 but spends more of the width on the larger Latin repertoire.
For seeds `0,1`, train homogeneous slices `(start,batch-models)` of `(0,1)`,
`(1,2)`, `(3,1)` and `(4,2)`. Mixed-width batches fail explicitly. A separate
`--unlabelled 0` experiment can focus capacity on known glyphs; it must keep
the original expert for unknown-scalar rendering. The accent packager does
so for both spatial and repertoire designs, retaining all original gate rows
and routing only labelled accent scalars to appended members.

`known_bundle.py BASE.nrt OUT.nrt REPLACEMENT.json... --expert INDEX`
appends complete known-character replacements to an existing version2 bundle.
Original members remain byte-identical for unknown and unrelated glyphs.
Only the selected expert's table entries move. The packer preserves original
gate rows and appends suppressed outputs after establishing conservative
activation/output bounds. `--allow-partial` explicitly permits mixed-width
fallback. The provenance sidecar binds the original bytes, replacements,
new ranges and output hash. Validate resulting quality before deployment.

## Explicit script capacities

For the three-member accent repertoire, `--script-widths 192,128,128` selects
independent Latin/diacritic, Greek and Russian widths in that order. It is mutually
exclusive with `--width-budget`. The same option must be supplied to
`tools/pack-accent-experiment.py`; packing verifies each trained member's width
and complete scalar partition. Widths remain part of checkpoint identity.

Use a new experiment directory for each recipe. Train equal-width slices with
`--start` and `--batch-models`; for seeds `0,1`, starts `0` and `3` select the two
Latin models individually, while starts `1` and `4` with batch size `2` select
each seed's Greek/Russian pair. The existing default H128/H64/H64 recipe and all
prior checkpoints retain their interpretation. Explicit widths are a training
configuration, not a quality or performance claim.

