# split-v8: split-v7 with the symbol, pixel and accent groups

`neuronte-split-v8.nrt` is `neuronte-split-v7.nrt` with three more sets of
known-only group nets. Each character is drawn by one net:

| Characters | Drawn by | Gates | Card |
|---|---|---|---|
| Braille, U+2800..U+28FF (256) | `neuronte-braille-v1`, tiled, as in split-v7 | passed | [braille-v1](neuronte-braille-v1.md) |
| Printable ASCII (95) | `neuronte-ascii-groups-v1`, 4×H64, as in split-v7 | passed, both seeds | [ascii-next](neuronte-ascii-next.md) |
| 49 symbols | `neuronte-symbol-v1`, 4×H32, seed 0 | passed, both seeds | [symbol-v1](neuronte-symbol-v1.md) |
| 327 block, sextant and octant characters | `neuronte-pixel-groups-v1`, 4×H64, seed 1 | **failed** the declared strict geometry gates; selected by the owner after visual review | [pixel-groups-v1](neuronte-pixel-groups-v1.md) |
| 318 accented Latin, spacing-mark, Greek and Russian characters | `neuronte-accent-groups-v1`, H192 + H128 + H128, seed 0 | **failed** the declared strict gates; selected by the owner after visual review | [accent-groups-v1](neuronte-accent-groups-v1.md) |
| The other 131 range characters, and every character outside the table | split-v7's experts | unchanged | [split-v7](neuronte-split-v7.md) |

**Not a default.** The pixel and accent groups did not qualify under the
rules declared before they were trained. The owner reviewed the failing
glyphs side by side and chose these seeds, accepting the regressions; that
choice does not change the measurements or turn the failures into passes.
In short, from their validation records:

- Pixel, seed 1: passes all limits at 8×16, 16×32 and 48×96. It adds 296
  firm wrong pixels at six other sizes from 25×49 to 64×128 (242 at 64×128),
  and 500 at fourteen sizes with one sample per pixel (S1). It loses no
  baseline-correct nearest identity.
- Accent, seed 0: fails 16 of the 25 automatic geometries, including 8×16
  (U+03B9 and U+0421 fall below the IoU floor) and 16×32 (one pixel of
  U+00B4 crosses the binary threshold), and S1 at 16×32. The automatic sizes
  it passes are 17×35, 23×46, 23×47, 24×48, 25×49, 25×50, 32×64, 33×61 and
  48×96.

split-v7 keeps its name and its bytes (`b6e8ad1a…`). Each part above draws
exactly as in the bundle in which it was selected, so the parts' own quality
records carry over unchanged.

## Rebuild

```sh
make pack-split-v8
```

`train/build_split_v8.py` applies `train/known_bundle.py` to split-v7 once per
entry of its `REPLACEMENTS` list, in order: the symbol groups for expert 2,
the pixel groups for expert 4, the accent groups for expert 3. Adding a
replacement is one more entry. `neuronte-split-v8.provenance.json` holds each
step's known_bundle record (source hashes, rewritten ranges, gate bounds,
original member hashes) and how its part was chosen.

split-v7's ten members are kept byte for byte, including the original symbol,
accent and pixel experts. The gate still chooses among them for characters
outside the range table, so unknown characters draw exactly as in split-v7.
Each step appends its members and constant, suppressed gate outputs, and
reassigns only its own expert's table entries.

| File | Members | Net parameters | Bytes | SHA256 |
|---|---:|---:|---:|---|
| `neuronte-split-v7.nrt` | 10 | 441,068 | 1,768,128 | `b6e8ad1ac6fbc2370fbacc14727180954b4fc6d23cf7c0506a93116853f92f1f` |
| `neuronte-split-v8.nrt` | 21 | 699,511 | 2,805,688 | `445b53caa40c6cd02a1b324458bf5ae549b1ab304043ac0eeb3d4871e6461168` |

The new nets add 20,228 (symbol), 56,836 (pixel) and 181,379 (accent)
parameters. A replaced character evaluates one smaller net (or, for Latin
accents, H192 instead of H256); the file grows because the original experts
stay for unknown characters. Twenty-one members need the current runtime's
128-member limit; the earlier 16-member runtime cannot open this file.

## Checks

`make test-split-v8` runs `tests/check_split_v8.py` and `test_api` with
`--full --accent --pixel`. The check verifies:

- split-v7 is `b6e8ad1a…`; the file is rebuilt byte for byte from it and the
  group JSON, and its provenance is the rebuild's.
- The first ten members are split-v7's; members 10–20 are the group JSON,
  packed, in order; the header and gate are split-v7's with eleven zero rows
  and suppressed biases appended.
- The selected sources are rebuilt from split-v7 and bound by hash:
  `neuronte-split-v7-symbol-v1.nrt` (`b98a5b05…`), the reviewed pixel bundle
  (`a45671b6…`) and the reviewed pixel+accent bundle (`924ddff9…`). The pixel
  and accent validation records still record their seeds and failed gates.
- Every scalar 0..0x10FFFF and 0xFFFFFFFF routes as in split-v7, except the
  694 replaced characters, each of which was on its expert and now goes to
  the group trained on it.
- ASCII draws split-v7's pixels at its 19 qualification sizes and Braille at
  8×16, 16×32, 25×49 and 48×96. The 49 symbols draw split-v7-symbol-v1's at
  13 sizes from 1×2 to 64×128, and in S1 at three. The 327 pixel characters
  draw `a45671b6`'s at all 22 reviewed sizes, automatic and S1. The 318
  accent characters draw `924ddff9`'s, and match the reviewed native buffer
  hashes, at all 28 reviewed geometries. The other 131 range characters draw
  split-v7's at 5×10, 8×16 and 16×32, and about a thousand unknown and
  invalid scalars at 9×17 and 25×49, automatic and S1.
- `tests/check_braille_v1.py` passes against a control with the same
  replacements and the previous Braille member.

These are integration checks: they prove each part is the reviewed one and
that nothing else moved. They do not assert the strict pixel or accent gates.

## Speed

Measured as a whole bundle with kilix-bench `e21e5cd`, against split-v5 and
split-v7 in the same runs, on two x86 hosts, an Intel i7-10700F and an
i7-6820HQ (on mains power), each on one pinned core with the benchmark lock
held for the whole run. Five corpora: ASCII (95), Braille (256), the 49
symbols, the 327 pixel characters and the 318 accent characters. One warmup
and ten measured rounds, a fresh process per job, rounds shuffled; 3,828
trials in all. ARM was not measured, and no figure here is carried over from
the parts' own campaigns.

Uncached `neuronte_coverage()`, geometric mean over cells of (other bundle /
split-v8); above 1 means split-v8 is faster. Cells are 8x16, 16x32 and 48x96,
and also 25x49 for Braille. Figures are i7-10700F / i7-6820HQ.

| Corpus | split-v5 | split-v7 |
|---|---:|---:|
| Symbols (49) | 5.51 / 5.40 | 5.58 / 5.43 |
| Pixel characters (327) | 2.11 / 2.09 | 2.11 / 2.10 |
| Accent characters (318) | 1.95 / 1.94 | 1.96 / 1.95 |
| Printable ASCII (95) | 2.26 / 2.23 | 1.01 / 1.00 |
| Braille (256) | 11.47 / 11.50 | 1.00 / 1.00 |

Median µs per glyph at 16x32, uncached coverage:

| CPU | Corpus | split-v5 | split-v7 | split-v8 |
|---|---|---:|---:|---:|
| i7-10700F | symbols | 2,210.3 | 2,223.5 | 401.6 |
| i7-10700F | pixel | 1,713.1 | 1,708.7 | 803.4 |
| i7-10700F | accent | 6,251.9 | 6,186.9 | 3,098.0 |
| i7-10700F | ASCII | 2,051.9 | 916.1 | 905.2 |
| i7-10700F | Braille | 539.2 | 32.6 | 32.8 |
| i7-6820HQ | symbols | 2,977.3 | 2,973.0 | 551.3 |
| i7-6820HQ | pixel | 2,285.7 | 2,290.0 | 1,082.5 |
| i7-6820HQ | accent | 8,282.9 | 8,200.3 | 4,162.6 |
| i7-6820HQ | ASCII | 2,731.1 | 1,222.6 | 1,224.6 |
| i7-6820HQ | Braille | 727.7 | 44.1 | 44.0 |

Pixels are identical on both hosts, and split-v8 draws ASCII and Braille
exactly as split-v7, so those two cost the same. A first draw tracks
coverage, and a primed (cached) draw costs the same for all three bundles.

**Opening is the cost.** One model open, including the first 8x16 buffer,
ranges over the five corpus runs:

| CPU | split-v5 ms | split-v7 ms | split-v8 ms |
|---|---:|---:|---:|
| i7-10700F | 1.68–1.82 | 1.84–1.97 | 2.88–3.05 |
| i7-6820HQ | 2.59–2.61 | 2.81–2.84 | 3.72–4.27 |

That is 0.9 to 1.4 ms more than split-v7, paid once per process; the eleven
appended members are the likely cause. Table routing is within 0.4 ns of
split-v7 on the ASCII, Braille and symbol corpora, and 0.6 to 1.8 ns faster
on the pixel and accent corpora.

## Status

Not a default. The video player still draws full mode with split-v6, no
release pins this file, and split-v7 still names the ASCII/Braille bundle.
