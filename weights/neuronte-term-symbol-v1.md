# term-symbol-v1: punctuation, currency, letterlike symbols, number forms, technical symbols and shapes

`neuronte-term-symbol-v1.nrt` draws 480 characters: the general punctuation,
superscripts and subscripts, currency signs, letterlike symbols, number forms,
technical symbols, enclosed digits and geometric shapes that DejaVu Sans Mono
covers and `neuronte-split-v9.nrt` was not trained on. DejaVu was used only
for its list of code points; every drawing is the project's own
([PROVENANCE.md](../PROVENANCE.md)).

**28 of its 48 group nets failed the gates declared for them and are in the
bundle by the owner's choice** (257 of the 480 characters; see Result below).

It is a bundle that stands alone: 48 group nets, each trained on 8 to 12
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
other of the 480 (or a twin's); none vanished; and the packed net equal to its
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

**Result.** 48 groups were trained, 480 characters. **20 passed** at width 64
with both seeds (223 characters). **28 FAILED** at width 64. A change to the
declared recipe: the retry was not run for this bundle. The arrows and
mathematical operators bundle retried 23 failing groups at width 96 and none
passed; the accented-letter bundle retried 72 and one passed; and the owner
had decided that failed groups ship at width 64. Every group that failed at
width 64 is recorded FAILED without a second attempt. 48 groups ship (480
characters): 20 that passed and 28 that failed and the owner chose; 0 are left
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
| tsym12 | 22 | 11 or 12 | 14 | 8 | 0.0055 | 0.0070 |
| tsym10 | 6 | 9 or 10 | 6 | 0 | 0.0058 | 0.0061 |
| tsym8 | 20 | 8 or 9 | 0 | 20 | 0.0084 | 0.0100 |

### FAILED, in the bundle by the owner's choice

The width 64 net of the seed named ships. "Rules missed" counts seed 0 and
seed 1 at width 64; the worst ratio is the larger of the two seeds' group mean
error over its limit, at the size where it is largest.

| Group | Characters | Seed | Rules missed | Worst mean error over its limit | 
|---|---|---:|---:|---:|
| tsym12 g0 | ⎛ ⎞ ⎟ ⎡ ⎣ ⎥ ⎨ ⎩ ⎫ ⎭ ⎮ | 1 | 2 and 2 | 1.31 at 6x12 |
| tsym12 g1 | ‧ ‱ ⁖ ⎜ ⎝ ⎠ ⎢ ⎤ ⎦ ⎧ ⎪ ⎬ | 1 | 1 and 1 | 1.12 at 6x12 |
| tsym12 g3 | ‒ ․ ‶ ‸ ‼ ⁆ ⁇ ⁋ ⁏ ⸟ ⸣ | 0 | 1 and 1 | 0.80 at 6x12 |
| tsym12 g9 | ▦ ▧ ▻ ▿ ◁ ◃ ◝ ◫ ◱ ◷ ◿ ⬡ | 0 | 1 and 1 | 1.19 at 10x20 |
| tsym12 g10 | ▤ ▨ ▵ ▹ ▽ ◊ ◜ ◳ ◴ ◹ ◺ ⭔ | 1 | 1 and 1 | 1.15 at 10x20 |
| tsym12 g11 | ▩ ▰ ▱ ► ◓ ◙ ◨ ◪ ◼ ⬓ ⬟ | 0 | 1 and 1 | 1.24 at 10x20 |
| tsym12 g12 | ▣ ▮ ◗ ◘ ◛ ◢ ◤ ◧ ◮ ⬔ ⬘ ⬢ | 0 | 1 and 1 | 1.14 at 10x20 |
| tsym12 g17 | ⁼ ⁾ ₋ ₐ ₔ ℃ ℅ ⌋ ⌝ ⎁ ⏨ ￼ | 1 | 2 and 1 | 0.92 at 8x16 |
| tsym8 g0 | ⌷ ⌺ ⌼ ⍊ ⍪ ⍫ ⍬ ⎕ | 1 | 5 and 5 | 1.26 at 10x20 |
| tsym8 g1 | ⌹ ⍉ ⍞ ⍡ ⍥ ⍩ ⍭ ⍯ | 0 | 5 and 5 | 1.33 at 16x32 |
| tsym8 g2 | ⌻ ⍖ ⍛ ⍝ ⍟ ⍢ ⍤ ⍰ | 1 | 4 and 4 | 1.11 at 10x20 |
| tsym8 g3 | ⌶ ⌸ ⍁ ⍃ ⍑ ⍒ ⍙ ⍱ | 0 | 5 and 5 | 1.36 at 16x32 |
| tsym8 g4 | ⌿ ⍄ ⍅ ⍈ ⍗ ⍜ ⍣ ⍦ ⍨ | 0 | 5 and 5 | 1.35 at 10x20 |
| tsym8 g5 | ⌾ ⍍ ⍏ ⍓ ⍕ ⍘ ⍠ ⍲ | 0 | 5 and 5 | 1.35 at 16x32 |
| tsym8 g6 | ⍂ ⍋ ⍌ ⍎ ⍔ ⍚ ⍧ ⍮ | 0 | 5 and 5 | 1.36 at 16x32 |
| tsym8 g7 | ₢ ₪ ₮ ⌽ ⍀ ⍆ ⍇ ⍐ | 1 | 6 and 6 | 1.50 at 16x32 |
| tsym8 g8 | ¤ ₠ ₡ ₥ ₱ ₲ ₹ ₺ | 0 | 4 and 4 | 1.22 at 6x12 |
| tsym8 g9 | ₣ ₤ ₦ ₧ ₫ ₭ ₰ ₵ ₸ | 0 | 5 and 6 | 1.40 at 8x16 |
| tsym8 g10 | ₩ ₯ ₳ ℚ ℝ ℽ ⅀ ⅇ | 1 | 6 and 5 | 1.37 at 10x20 |
| tsym8 g11 | ℂ ℍ ℕ ℤ ℾ ⅅ ⅈ ⅉ | 0 | 5 and 5 | 1.47 at 10x20 |
| tsym8 g12 | ℙ ℼ ℿ ⅆ ④ ⑤ ⑨ ⑩ | 0 | 5 and 6 | 1.56 at 10x20 |
| tsym8 g13 | ⅙ ⅚ ① ② ③ ⑥ ⑦ ⑧ | 0 | 2 and 2 | 1.07 at 10x20 |
| tsym8 g14 | ⅑ ⅒ ⅓ ⅔ ⅗ ⅛ ⅜ ⅞ ⅟ | 1 | 5 and 5 | 1.28 at 6x12 |
| tsym8 g15 | ⅐ ⅕ ⅖ ⅘ ⅝ Ⅰ Ⅷ ↉ | 0 | 6 and 6 | 1.46 at 6x12 |
| tsym8 g16 | Ⅲ Ⅾ ⅴ ⅶ ⅺ ⅽ ⅾ ↂ | 1 | 6 and 5 | 1.18 at 6x12 |
| tsym8 g17 | Ⅵ Ⅹ Ⅻ ⅰ ⅲ ⅹ ⅻ ⅿ | 1 | 7 and 6 | 1.25 at 10x20 |
| tsym8 g18 | Ⅱ Ⅳ Ⅶ Ⅺ Ⅼ Ⅽ ⅵ ⅸ | 1 | 4 and 4 | 1.20 at 8x16 |
| tsym8 g19 | Ⅴ Ⅸ Ⅿ ⅱ ⅳ ⅷ ⅼ ↀ ↁ | 0 | 3 and 3 | 1.17 at 6x12 |

## Rebuild

```sh
make pack-term-symbol-v1
```

`train/build_term_symbols.py symbol` writes `neuronte-term-symbol-v1.list.txt`
from the tier `tsym` of `train/glyphs.py` less the groups left out, then
applies `train/standalone_bundle.py` to the group JSON in order, with split-v9
as the bundle to stay apart from. The table sends each listed character to its
group net; there is no gate.

| File | Members | Table rows | Bytes | SHA256 |
|---|---:|---:|---:|---|
| `neuronte-term-symbol-v1.nrt` | 49 | 417 | 2,743,740 | `5c6121177da923e9c8c05cc45960715b893db2b123712eb6c3e8891924ca2480` |

## Training

`train/split_expert.py`, unchanged: repertoire groups, contiguous partition,
width 64, seeds 0 and 1, 120,000 steps, Adam 0.002 cosine, the project teacher
(grid 256, tau .15, pen .075), from the drawings in `font/term-sym.txt` and
`train/term_glyphs.py`. The groups are those of
`font/term-sym-partition.json`: characters of one shape family together, 12,
10 or 8 to a net by how much ink edge the family draws
(`tools/term-partition.py`). Trained on a rented RTX 3090.

## Checks

`make test-term-symbol-v1` checks the grouping against the drawings, packs
each group JSON and runs `tests/check_reference.py` on it (C against float64
numpy), then `tests/check_term_symbols.py` and `test_api --standalone 00A4`.
The check verifies: the bundle is rebuilt byte for byte; its table is exactly
its list and shares nothing with split-v9; every scalar from 0 to U+10FFFF is
routed to its group net or to the blank net and reported trained or untrained
accordingly; each character draws as its group net alone at 19 cell sizes;
other scalars draw an empty cell; the validation record names the shipped seed
of every group and both seeds' hashes; and the drawings are still the ones the
nets were scored against. `make test-standalone` checks that no two listed
bundles claim one character. U+FFFD is one of this bundle's characters, and
the library draws a surrogate or a value above U+10FFFF as U+FFFD: through
this bundle those values draw the replacement character and are reported
trained.

## Speed

Against split-v9's fallback for the same 480 characters: split-v9 sends each
through its gate to a net that never saw it, so this compares the time to
draw, not what is drawn. kilix-bench, one pinned core, a fresh process per
job, 1 warmup and 10 measured rounds, medians; uncached coverage in µs per
glyph.

| Host CPU | Bundle | 8x16 | 16x32 | 48x96 | open µs | route ns |
|---|---|---:|---:|---:|---:|---:|
| i7-6820HQ | split-v9 | 503.4 | 1955.1 | 4372.0 | 4698.4 | 1281.3 |
| i7-6820HQ | term-symbol-v1 | 186.2 | 712.8 | 1585.3 | 3409.9 | 43.5 |
| i7-10700F | split-v9 | 381.4 | 1468.3 | 3311.6 | 3649.3 | 929.9 |
| i7-10700F | term-symbol-v1 | 141.7 | 551.1 | 1221.1 | 2324.2 | 29.9 |

split-v9 time over term-symbol-v1 time, geometric mean over the three cells:
2.73 (i7-6820HQ), 2.69 (i7-10700F); 2.71 over both. Each bundle draws the same
pixels on both hosts; C against the float64 reference differs by at most
1.5e-05.

