# Neuronte video experiment

This tool consumes RGB24 raw frames on standard input, usually from ffmpeg.
Frame width and height are mandatory; dimensions must divide by the cell
size exactly. No implicit resizing or cropping is performed.

`python3 tools/neuronte-video.py --width 640 --height 384 --level two
--mode portable --cell 8x16 --output ansi` writes cursor-addressed truecolour
terminal cells. `--output rgb` writes reconstructed RGB24 frames. Full mode
uses the loaded bundle’s explicit scalar ranges and its actual C coverage masks;
portable mode uses the 328 ideal geometric masks. Full mode must be displayed
with that same Neuronte bundle to reproduce the fitted image. Full mode requires a monochrome bundle with explicit scalar ranges; split-v5 is the
default. A standalone net without a manifest is rejected. Fixed-colour members are
also rejected, including single-layer colour nets: their palette cannot be
reproduced by an arbitrary foreground/background fit.

`--level multi --cell 2x4 --output rgb` uses three cached C neural coverage
masks (right half, middle half, lower half), eight RGB colours per cell,
and the Gray row order 0,1,3,2. The floating-point product of three masks
chooses each ink's weight. There is no mask rounding. At 2x4 this is lossless
only when the masks pass the exactness gate. `--require-exact` is valid only with `--level multi`; it checks every
one of 256 octants at all eight pixel centres and refuses output otherwise.
It also requires the three actual masks at the selected cell size to be binary.
The standalone `--check-exact` action checks the supplied weights, defaulting
to the video calibration, and produces no frame stream.
The default video-only calibrated bundle passes this gate. The existing
unmodified split-v4 does not; explicitly selecting it produces lossy output.
The calibration doubles the coverage scale of the frozen pixel and ASCII nets.
It narrows their continuous antialias transition, changes no learned layer,
and is deliberately separate from normal text rendering. Check with `--check-exact` (JSON to stdout, exit 1 on failure).

`--margin` is a nonnegative squared RGB error per channel allowed to retain
the previous character. Colours are still refitted each frame. ANSI output
sends only cells with a changed character or quantised RGB colours. The
least-squares fit is exact for continuous RGB colours constrained to [0,255];
rounding those colours to RGB8 introduces a small additional error. This is
not an exhaustive search over all RGB8 pairs. Deterministic ties prefer the
first character in the manifest. `--stats PATH` records frame count, time,
cell dimensions and reconstructed PSNR, including RGB8 quantisation.

No new library format or public C API is required. In-process multi-ink
records have shape (rows, columns, 8, 3), uint8. Plane scalars are fixed by
this version and not repeated in each cell: payload is 24 bytes/cell. A
future persistent format would additionally require dimensions, version,
weights SHA256 and length validation; this tool does not invent an implicit
unversioned on-disk cell format. RGB streams follow ffmpeg's documented
rawvideo convention. Model experiments use separate versioned JSON files.

Sources and generated experimental clips are kept in the research directory,
not this repository. No source frames are retained in model assets. Video
nets are retained only when held-out acceptance beats the exact-search
baseline under the research plan's quality, stability and speed criteria.

## Playing a file

`python3 tools/neuronte-play.py FILE` plays a video in the terminal. ffmpeg
decodes and scales it to the terminal's grid, keeping the picture's shape.
The sound is played by mpv with no picture (`kilix-mpv` when it is
installed, else `mpv`), and its playback position is the clock the picture
follows; without either, or with `--no-audio`, the wall clock is used.
Frames that cannot be shown in time are dropped, so playback never runs slow.

Keys: `q` quit, space pause, left and right 5 seconds, down and up 60 seconds,
home restart, `m` mute, `9` and `0` volume. A seek moves the sound and
restarts the decoder at the same position; a pause holds both. One row of
text under the picture shows the position (`--no-status` removes it). A
resized terminal is refitted.

The default, `--mode pixels`, gives every cell eight colours in a 2 × 4
arrangement of blocks, mixed by the three video masks drawn at 8 × 16 pixels
a cell, and sends the result with the kitty graphics protocol. The file is
scaled to one pixel a block, so the fit is exact. Pictures are presented the
way `kilix-mpv` and `kitty-framebuffer` present them: each is complete under
its own image id before the one before it is deleted, inside one synchronized
update. For a local kitty or Kilix the pixels go through three shared-memory
objects that the terminal unlinks as it reads them; if all three are still
unread the frame is skipped, not queued. Elsewhere, and with `--transport
inline`, they are compressed and sent through the terminal's own stream.

Measured once, on one laptop, in a background Kilix tab of 196 × 55 cells
with a synthetic 640 × 360 clip at 30 frames a second: shared memory showed
237 of 240 frames, median 5 ms after their time; inline showed 204, median
33 ms after, because compressing and encoding 3.8 MB a frame took 19 ms.

`--mode cells` writes one character and two colours a cell as ordinary
truecolour text, which any truecolour terminal shows in its own font; in a
Neuronte terminal the nets draw it. It is the exhaustive two-ink fit and
is far from real time: an 80 × 24 grid showed 2 frames a second with
the 328 block characters. `--characters full` searches the whole bundle and
`--helper` adds the speed helper; both are slower still than the picture
needs.

`--log FILE` writes one JSON line per source frame (its time, the clock, how
late it was shown, and the milliseconds spent reading, fitting, drawing,
packing and writing, or that it was dropped or skipped); `--stats FILE`
writes the totals. `--input-fd N` takes keys from a descriptor, for scripts.

## Optional learned helpers

`--level two --mode full --cell 8x16 --helper speed` proposes a compact
candidate shortlist, then performs the same exact bounded RGB fit on it.
`--helper quality` uses a learned temporal switch, then checks the proposed
retained cells against the source image: local SSIM loss at most0.0001,
whole-frame SSIM loss at most0.001. This is a hybrid model plus quality veto,
not a model-only fidelity guarantee. Its goal is fewer character changes;
it still performs exhaustive search. The two helpers are alternatives, not a
combined mode that has never been measured.

Both require the precise bundle they were trained against, zero `--margin`,
and 8×16 cells. A mismatched bundle is rejected. The default helpers,
`neuronte-video-speed-v1` and `neuronte-video-quality-v1`, were retrained
against split-v5, whose 1,176 scalars include the Greek and Russian letters.
The v0 helpers were trained against split-v4's 1,061 and are kept: select them
with `--weights weights/neuronte-split-v4.nrt --helper-model
weights/neuronte-video-speed-v0.json` (or `-quality-v0`). The optional
`--helper-model` explicitly selects another compatible, versioned model.
The helper JSON records the bundle SHA256, model seed, training-frame digest,
training source hash, inference policy and acceptance evidence. Playback uses
NumPy/SciPy, not torch. Training and reproducible gates are in `train/video.py`
and `train/evaluate_video_helpers.py`; `train/adopt_video_helpers.py` writes the
shipped files and refuses unless both seeds pass.

The initial helpers failed on held-out data and were not adopted. The revised
inference policy was chosen on validation clips and checked on fresh held-out
clips, with both seeds retained in research. All footage is original synthetic
material. Passing these clips does not establish general-purpose performance
on natural footage; the exhaustive and multi-ink modes remain available.

For exactly binary neural masks, decoding uses cached ink indices derived from
those masks. This avoids multiplying every pixel by eight one-hot weights.
It is enabled only after exact binary equality is established; fractional
masks use the continuous product blend. No mask is rounded. The reproducible
benchmark reports full-HD encode/decode throughput and a plain-copy reference;
the Python record-layout work still costs more than a single memory copy.

Runtime helper models must include a valid inference policy; missing or malformed
policies are rejected before the first frame is read. Policy-less training
parents remain usable by the research evaluator, which supplies its own policy.
