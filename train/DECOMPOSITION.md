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

## Other monochrome experts

`--set pixel` uses the complete, sorted 327-scalar block, sextant and
octant repertoire from the unchanged teacher. Other supported sets are
`symbol`, `boxshade` and `accent`. Preparation and training must specify
the same set; the teacher identity binds both set and scalar inventory.
Counts 1 and 2 are also supported; count 2 splits left/right spatially.
`--width-budget` specifies the sum of hidden widths, default 128, and must
divide the count exactly. It is not a parameter-count budget.

```sh
python3 train/decompose.py prepare /tmp/pixel-experiment --set pixel
python3 train/decompose.py train /tmp/pixel-experiment --set pixel \
  --mode repertoire --parts 4 --seeds 0,1 --batch-models 8
python3 train/test_pixel_decompose.py
```

Mosaic bits are row-major and are not Braille dot bits. Adjacent filled
regions change the teacher distance inside an occupied tile; a tile's
occupancy bit alone is insufficient to share its distance network. The
pixel tests retain this counterexample and check every sextant and octant
pattern at tile centres. Spatial experiments retain the complete scalar
input and original distance units.

## Preserve unknown-scalar behavior when packaging

A selected narrower model need not replace the old expert's behavior on
unlabelled scalars. Append its labelled override to a new bundle:

```sh
python3 tools/override-bundle.py weights/neuronte-split-v5.nrt \
  /tmp/pixel-candidate.nrt /tmp/pixel-experiment/pixel-repertoire-k2-w64-p0-s0.json \
  /tmp/pixel-experiment/pixel-repertoire-k2-w64-p1-s0.json
python3 tests/check_bundle_override.py
```

Each new expert's labels must be disjoint and already covered by the base.
The original members, fallback and gate weights remain intact. Appended gate
outputs are constants strictly below the bound on every original logit, so
they cannot win a table miss. This retains the original model's size in
addition to the candidate weights; report that load/storage cost explicitly.
The output uses the existing version-2 bundle format and the public API.
Never overwrite a shipped model whose hash is bound by consumers.

Spatial exports can be assembled as a single version-6 member:

```sh
python3 tools/decomposition-tiled.py /tmp/pixel-spatial.json \
  /tmp/pixel-experiment/pixel-spatial-k2-w64-p0-s0.json \
  /tmp/pixel-experiment/pixel-spatial-k2-w64-p1-s0.json
python3 tests/check_decomposition_tiled.py
```

The assembler verifies row-major full-cell coverage, matching training
identities and distance scales. Tiles use the original scalar unchanged.
The native sampler dispatches each subpixel at its full-cell position,
including odd sizes and widths 23, 24 and 25. The analytic test checks
both axes, scalar identity and coverage scaling across these boundaries.

Explicit repertoire partitions may mix widths while retaining an exact
summed budget. `--specification spec.json` accepts
`{"schema":"neuronte.decomposition-spec/v1","expert":"pixel","groups":[...]}`.
Each group supplies a unique `name`, positive `width`, and sorted distinct
`scalars`; groups must cover the teacher inventory exactly once. The number
of groups must match `--parts`, and widths must sum to `--width-budget`.
The specification's hash and complete selected members are checkpoint-bound.

`--model-indices 0,1,3,4` selects noncontiguous seed-major members for one
batch. Each batch must have one width. For a three-group 32/32/64 partition
and seeds 0/1, indices 0,1,3,4 train the four width-32 models, and 2,5 train
the two width-64 models. Smaller repertoires are padded and excluded from
loss exactly as in contiguous partitioning. The pixel tests check complete
29/60/238 semantic inventories, refusal of overlaps and mixed-width batches,
and exact restart with the padded noncontiguous selection.

### Pixel refinement recipes

`pixel-semantic-spec.json` is the explicit 29-block, 60-sextant,
238-octant partition with widths 32, 32, 64. It has the same summed hidden
width as the original H128 expert, but 24,323 parameters rather than
44,801. The two homogeneous allocations have 28,418 parameters (2x64)
and 20,228 parameters (4x32). These counts exclude retained fallback
weights and routing metadata.

The following commands reproduce the semantic training configuration in a
fresh directory. Both batches use the same prepared teacher. Specify the
same pinned NumPy, PyTorch, CUDA, and device versions when comparing training
trajectories; checkpoint identities refuse changes to these inputs.

```sh
python3 train/decompose.py prepare /tmp/pixel-semantic --set pixel
python3 train/decompose.py train /tmp/pixel-semantic --set pixel \
  --mode repertoire --parts 3 --width-budget 128 \
  --specification train/pixel-semantic-spec.json --seeds 0,1 \
  --model-indices 0,1,3,4 --batch-models 4 --steps 60000 --unlabelled 0
python3 train/decompose.py train /tmp/pixel-semantic --set pixel \
  --mode repertoire --parts 3 --width-budget 128 \
  --specification train/pixel-semantic-spec.json --seeds 0,1 \
  --model-indices 2,5 --batch-models 2 --steps 60000 --unlabelled 0
```

For longer contiguous 2x64 controls, prepare separate fresh directories,
then use `--mode repertoire --parts 2 --seeds 0,1 --batch-models 4
--steps 60000`, with `--unlabelled 1` for the original regularizer or
`--unlabelled 0` for known-only training. Do not resume a completed
20,000-step cosine schedule as a 60,000-step experiment.

Training completion is not a quality or production approval. Check every
label, both seeds, odd cell geometries, and each consumer sampling mode.
Report per-glyph failures even when corpus averages pass. A partial override
retains the original H128 inference for omitted labels and the full original
bundle in storage; it is not a uniformly narrower replacement.
