# Neuronte video experiment

This tool consumes RGB24 raw frames on standard input, usually from ffmpeg.
Frame width and height are mandatory; dimensions must divide by the cell
size exactly. No implicit resizing or cropping is performed.

`python3 tools/neuronte-video.py --width 640 --height 384 --level two
--mode portable --cell 8x16 --output ansi` writes cursor-addressed truecolour
terminal cells. `--output rgb` writes reconstructed RGB24 frames. Full mode
uses the trained scalar manifest of split-v4 and its actual C coverage masks;
portable mode uses the 328 ideal geometric masks. Full mode must be displayed
with that same Neuronte bundle to reproduce the fitted image. The present
manifest is fixed to split-v4: passing a different bundle is experimental.

`--level multi --cell 2x4 --output rgb` uses three cached C neural coverage
masks (right half, middle half, lower half), eight RGB colours per cell,
and the Gray row order 0,1,3,2. The floating-point product of three masks
chooses each ink's weight. There is no mask rounding. At 2x4 this is lossless
only when the masks pass the exactness gate. `--require-exact` checks every
one of 256 octants at all eight pixel centres and refuses output otherwise.
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
