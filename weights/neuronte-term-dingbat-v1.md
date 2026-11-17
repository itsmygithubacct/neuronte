# term-dingbat-v1: Miscellaneous Symbols and Dingbats

`neuronte-term-dingbat-v1.nrt` draws 323 characters: the Miscellaneous Symbols
and Dingbats that DejaVu Sans Mono covers and `neuronte-split-v9.nrt` was not
trained on. DejaVu was used only for its list of code points; every drawing is
the project's own ([PROVENANCE.md](../PROVENANCE.md)).

**24 of its 35 group nets failed the gates declared for them and are in the
bundle by the owner's choice** (209 of the 323 characters; see Result below).

It is a bundle that stands alone: 35 group nets, each trained on 8 to 12
characters, and one blank net. It holds no copy of split-v9. A program opens
it beside `neuronte-split-v9.nrt` and draws a character with the bundle whose
`neuronte_untrained()` is 0 for it; no character is in both, and `make test`
checks that. Every scalar outside its list goes to the blank net, which draws
an empty cell (or the mark for an untrained character after
`neuronte_set_untrained(font, 1)`).

**Not a default.** Nothing that ships changes: split-v5 stays the terminal
default, split-v9 is byte for byte what it was.

## Gates

Declared before any net was trained (`gates` in the validation record, sha256
`e29f5f97f7acf9d3…`). The reference is split-v9 measured on its own 113
symbols, the only nets of this kind the project has shipped. For each group
net, at each of the cell sizes 6x12, 8x16, 10x20, 12x24, 16x32, 24x48 and
48x96: group mean error, 99th percentile and firm-wrong fraction within a
small slack of the reference; every character's own error within 0.01 of the
reference's worst character; every character nearer its own teacher than any
other of the 323 (or a twin's); none vanished; and the packed net equal to its
float64 reference. A group passes when seed 0 and seed 1 both meet every rule;
the seed with the lower mean error over 8x16, 16x32 and 48x96 ships. One retry
was declared with the gates: a failing group is trained once more at width 96
and judged by the same rules. A group that still fails is FAILED and is left
out of the bundle unless the owner says otherwise.

| Limit | 6x12 | 8x16 | 10x20 | 12x24 | 16x32 | 24x48 | 48x96 |
|---|---:|---:|---:|---:|---:|---:|---:|
| mean error | .0094 | .0072 | .0049 | .0050 | .0041 | .0044 | .0029 |
| p99 | .0959 | .0790 | .0711 | .0705 | .0710 | .0779 | .0665 |
| firm-wrong fraction | .0005 | .0005 | .0005 | .0005 | .0005 | .0006 | .0005 |
| worst character error | .0383 | .0250 | .0214 | .0208 | .0193 | .0175 | .0134 |

**Result.** 35 groups were trained, 323 characters. **11 passed** at width 64
with both seeds (114 characters). **24 FAILED** at width 64. A change to the
declared recipe: the retry was not run for this bundle. The arrows and
mathematical operators bundle retried 23 failing groups at width 96 and none
passed; the accented-letter bundle retried 72 and one passed; and the owner
had decided that failed groups ship at width 64. Every group that failed at
width 64 is recorded FAILED without a second attempt. 35 groups ship (323
characters): 11 that passed and 24 that failed and the owner chose; 0 are left
out.

The owner decided on 2026-11-17, with the trained-net sheet of the first
bundle open, that groups failing the declared gates ship at width 64 marked
FAILED and owner-chosen, in all three bundles. The owner named no seed: of
each such group the seed with the lower mean error over 8x16, 16x32 and 48x96
ships, the rule declared for the groups that pass. They are not described as
passing anywhere: the validation record marks each `owner_chosen` with
`both_seeds_pass` false and keeps both seeds, and the retry where one was run.

Every character of every group, failed or not, is nearer its own teacher than
any other character of the bundle at every counted size, none vanished, and
every packed net equals its float64 reference: the failures are all on the
amount of error.

| Set | Groups | Characters a group | Passed | FAILED, owner-chosen | Mean error at 8x16, shipped seeds | Worst group at 8x16 |
|---|---:|---|---:|---:|---:|---:|
| tding12 | 8 | 11 or 12 | 5 | 3 | 0.0055 | 0.0065 |
| tding10 | 8 | 9 or 10 | 4 | 4 | 0.0063 | 0.0076 |
| tding8 | 19 | 8 or 9 | 2 | 17 | 0.0073 | 0.0128 |

### FAILED, in the bundle by the owner's choice

The width 64 net of the seed named ships. "Rules missed" counts seed 0 and
seed 1 at width 64; the worst ratio is the larger of the two seeds' group mean
error over its limit, at the size where it is largest.

| Group | Characters | Seed | Rules missed | Worst mean error over its limit | 
|---|---|---:|---:|---:|
| tding12 g2 | ➙ ➞ ➣ ➧ ➪ ➲ ➳ ➵ ➹ ➼ ➽ | 1 | 1 and 0 | 0.83 at 10x20 |
| tding12 g3 | ☱ ☴ ☵ ☷ ⚊ ⚍ ⚎ ❘ ❚ ➦ ➬ ➺ | 1 | 1 and 1 | 1.03 at 10x20 |
| tding12 g5 | ☎ ☙ ☚ ♛ ♝ ♞ ♟ ❐ ❝ ❫ ❲ | 1 | 1 and 1 | 0.77 at 8x16 |
| tding10 g0 | ⛁ ✙ ✚ ✛ ✜ ✝ ✞ ✟ ✠ | 1 | 4 and 5 | 1.35 at 10x20 |
| tding10 g1 | ♠ ♣ ♤ ♦ ⚁ ⚂ ⚃ ⚅ ⚉ ⛀ | 0 | 5 and 4 | 1.33 at 10x20 |
| tding10 g2 | ♥ ⚀ ⚄ ⚆ ⚇ ⚈ ⚤ ⛂ ⛃ | 1 | 1 and 1 | 1.17 at 10x20 |
| tding10 g4 | ♨ ♩ ♪ ♫ ♬ ♭ ♮ ♯ ⚦ ⚧ | 1 | 1 and 1 | 1.23 at 10x20 |
| tding8 g0 | ❶ ❷ ❿ ➅ ➉ ➌ ➍ ➏ | 1 | 2 and 1 | 1.16 at 10x20 |
| tding8 g1 | ❹ ❻ ➀ ➄ ➇ ➋ ➐ ➑ | 1 | 1 and 1 | 1.02 at 10x20 |
| tding8 g3 | ☠ ☾ ❺ ❼ ❾ ➂ ➃ ➓ | 1 | 1 and 1 | 1.07 at 10x20 |
| tding8 g4 | ☏ ☖ ♔ ⚚ ⚸ ✃ ✍ ✐ | 0 | 5 and 4 | 1.18 at 6x12 |
| tding8 g6 | ☘ ☟ ☤ ✁ ✂ ✇ ✉ ✎ | 1 | 5 and 4 | 1.35 at 10x20 |
| tding8 g7 | ☜ ♕ ♖ ♗ ⚕ ⚵ ✄ ✈ | 0 | 9 and 10 | 1.40 at 10x20 |
| tding8 g8 | ☞ ♘ ♙ ♧ ♲ ♽ ✌ ❡ | 1 | 2 and 2 | 1.22 at 6x12 |
| tding8 g9 | ♳ ♴ ♵ ♷ ♸ ♹ ♺ ♻ | 1 | 7 and 5 | 1.39 at 10x20 |
| tding8 g10 | ☧ ☨ ☬ ♶ ♼ ⚒ ⚞ ⚰ | 1 | 5 and 4 | 1.19 at 6x12 |
| tding8 g11 | ☓ ☢ ☫ ☮ ♰ ⚐ ⚜ ⚟ | 1 | 6 and 6 | 1.15 at 8x16 |
| tding8 g12 | ☡ ☥ ☭ ☸ ☹ ☻ ⚔ ⚗ | 1 | 0 and 1 | 0.99 at 10x20 |
| tding8 g13 | ☣ ☦ ☯ ♾ ⚑ ⚖ ⚘ ⚱ | 1 | 2 and 2 | 1.10 at 6x12 |
| tding8 g14 | ☩ ☺ ♱ ⚙ ✥ ✩ ✷ ✺ | 1 | 16 and 15 | 1.81 at 8x16 |
| tding8 g15 | ✡ ✭ ✰ ✴ ✸ ✹ ✼ ❅ | 0 | 6 and 7 | 1.14 at 6x12 |
| tding8 g16 | ✣ ✬ ✮ ✱ ✵ ❂ ❉ ❋ | 1 | 7 and 6 | 1.19 at 10x20 |
| tding8 g17 | ✦ ✲ ✿ ❀ ❁ ❇ ❈ ❊ | 0 | 2 and 2 | 1.03 at 10x20 |
| tding8 g18 | ✤ ✧ ✪ ✫ ✯ ✾ ❃ ❄ ❆ | 0 | 2 and 3 | 1.00 at 8x16 |

## Rebuild

```sh
make pack-term-dingbat-v1
```

`train/build_term_symbols.py dingbat` writes
`neuronte-term-dingbat-v1.list.txt` from the tier `tding` of `train/glyphs.py`
less the groups left out, then applies `train/standalone_bundle.py` to the
group JSON in order, with split-v9 as the bundle to stay apart from. The table
sends each listed character to its group net; there is no gate.

| File | Members | Table rows | Bytes | SHA256 |
|---|---:|---:|---:|---|
| `neuronte-term-dingbat-v1.nrt` | 36 | 252 | 2,000,188 | `0f2a6b1548c0b129ab127d6e23a96c3e7e631865f9bee37ead58513293eaf6b3` |

## Training

`train/split_expert.py`, unchanged: repertoire groups, contiguous partition,
width 64, seeds 0 and 1, 120,000 steps, Adam 0.002 cosine, the project teacher
(grid 256, tau .15, pen .075), from the drawings in `font/term-ding.txt` and
`train/term_glyphs.py`. The groups are those of
`font/term-ding-partition.json`: characters of one shape family together, 12,
10 or 8 to a net by how much ink edge the family draws
(`tools/term-partition.py`). Trained on a rented RTX 3090.

## Checks

`make test-term-dingbat-v1` checks the grouping against the drawings, packs
each group JSON and runs `tests/check_reference.py` on it (C against float64
numpy), then `tests/check_term_symbols.py` and `test_api --standalone 2600`.
The check verifies: the bundle is rebuilt byte for byte; its table is exactly
its list and shares nothing with split-v9; every scalar from 0 to U+10FFFF is
routed to its group net or to the blank net and reported trained or untrained
accordingly; each character draws as its group net alone at 19 cell sizes;
other scalars draw an empty cell; the validation record names the shipped seed
of every group and both seeds' hashes; and the drawings are still the ones the
nets were scored against. `make test-standalone` checks that no two listed
bundles claim one character.

## Speed

Against split-v9's fallback for the same 323 characters: split-v9 sends each
through its gate to a net that never saw it, so this compares the time to
draw, not what is drawn. kilix-bench, one pinned core, a fresh process per
job, 1 warmup and 10 measured rounds, medians; uncached coverage in µs per
glyph.

| Host CPU | Bundle | 8x16 | 16x32 | 48x96 | open µs | route ns |
|---|---|---:|---:|---:|---:|---:|
| i7-6820HQ | split-v9 | 506.8 | 1995.2 | 4426.6 | 4741.5 | 1256.6 |
| i7-6820HQ | term-dingbat-v1 | 186.8 | 716.6 | 1591.9 | 2537.4 | 24.7 |
| i7-10700F | split-v9 | 395.7 | 1516.9 | 3381.3 | 3486.2 | 935.3 |
| i7-10700F | term-dingbat-v1 | 146.3 | 565.2 | 1246.7 | 1800.6 | 17.7 |

split-v9 time over term-dingbat-v1 time, geometric mean over the three cells:
2.76 (i7-6820HQ), 2.70 (i7-10700F); 2.73 over both. Each bundle draws the same
pixels on both hosts; C against the float64 reference differs by at most
6.3e-06.

