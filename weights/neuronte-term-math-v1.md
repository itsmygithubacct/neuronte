# term-math-v1: arrows and mathematical operators

`neuronte-term-math-v1.nrt` draws 465 characters: the arrows, mathematical
operators and mathematical brackets that DejaVu Sans Mono covers and
`neuronte-split-v9.nrt` was not trained on: the rest of Arrows and
Mathematical Operators, and parts of Supplemental Arrows-A and -B,
Miscellaneous Mathematical Symbols-A and -B, Supplemental Mathematical
Operators and Miscellaneous Symbols and Arrows. DejaVu was used only for its
list of code points; every drawing is the project's own
([PROVENANCE.md](../PROVENANCE.md)).

**23 of its 47 group nets failed the gates declared for them and are in the
bundle by the owner's choice** (220 of the 465 characters; see Result below).

It is a bundle that stands alone: 47 group nets, each trained on 8 to 12
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
other of the 465 (or a twin's); none vanished; and the packed net equal to its
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

**Result.** 47 groups were trained, 465 characters. **24 passed** at width 64
with both seeds (245 characters). **23 FAILED** at width 64. All 23 were
retried at width 96 as declared; 0 of them then passed. 47 groups ship (465
characters): 24 that passed and 23 that failed and the owner chose; 0 are left
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
| tmath12 | 18 | 11 or 12 | 12 | 6 | 0.0058 | 0.0075 |
| tmath10 | 12 | 9 or 10 | 4 | 8 | 0.0064 | 0.0074 |
| tmath8 | 17 | 8 or 9 | 8 | 9 | 0.0075 | 0.0119 |

### FAILED, in the bundle by the owner's choice

The width 64 net of the seed named ships. "Rules missed" counts seed 0 and
seed 1 at width 64; the worst ratio is the larger of the two seeds' group mean
error over its limit, at the size where it is largest. The last column is what
the retry at width 96 did.

| Group | Characters | Seed | Rules missed | Worst mean error over its limit | Retry at width 96 |
|---|---|---:|---:|---:|---|
| tmath12 g0 | ↧ ↯ ↱ ↸ ↹ ⇀ ⇞ ⇷ ⇿ ⟿ ⬑ | 1 | 1 and 0 | 1.03 at 6x12 | failed again (1 and 1 rules) |
| tmath12 g3 | ↡ ↥ ↬ ↲ ↽ ⇅ ⇥ ⇲ ⇹ ⇻ ⬎ | 1 | 3 and 3 | 1.12 at 6x12 | failed again (3 and 3 rules) |
| tmath12 g4 | ↞ ↤ ↭ ↾ ⇂ ⇄ ⇉ ⇜ ⇠ ⇴ ⇵ ⇸ | 1 | 1 and 1 | 1.07 at 6x12 | failed again (1 and 1 rules) |
| tmath12 g5 | ↟ ↦ ↮ ↳ ↶ ↼ ⇇ ⇊ ⇟ ⇡ ⇾ ⟴ | 0 | 4 and 3 | 1.06 at 6x12 | failed again (4 and 4 rules) |
| tmath12 g6 | ↣ ↫ ↰ ↿ ⇆ ⇈ ⇤ ⇱ ⇺ ⥁ ⬍ ⬐ | 1 | 1 and 1 | 1.08 at 6x12 | failed again (1 and 1 rules) |
| tmath12 g9 | ∀ ∐ ∔ ∢ ∣ ∴ ∷ ∸ ∻ ⋮ ⋯ ⋰ | 1 | 1 and 1 | 0.69 at 6x12 | failed again (1 and 1 rules) |
| tmath10 g0 | ⟆ ⟧ ⟩ ⟪ ⦃ ⦈ ⦗ ⧒ ⧕ | 1 | 1 and 1 | 1.01 at 6x12 | failed again (1 and 1 rules) |
| tmath10 g1 | ⋶ ⋿ ⟅ ⟦ ⟨ ⟫ ⦄ ⦇ ⦘ ⧐ | 1 | 3 and 2 | 1.11 at 6x12 | failed again (1 and 2 rules) |
| tmath10 g3 | ≑ ≒ ≔ ≙ ≚ ≛ ≝ ⋵ ⋺ ⋽ | 1 | 2 and 3 | 1.15 at 10x20 | failed again (2 and 3 rules) |
| tmath10 g4 | ≐ ≓ ≕ ≖ ≗ ≘ ≞ ≢ ≣ | 0 | 3 and 3 | 1.21 at 10x20 | failed again (3 and 3 rules) |
| tmath10 g8 | ⊄ ⊌ ⊏ ⊐ ⋁ ⋃ ⋒ ⋔ ⋥ ⪸ | 0 | 1 and 2 | 1.00 at 8x16 | failed again (2 and 1 rules) |
| tmath10 g9 | ⊉ ⊋ ⊍ ⊎ ⊑ ⊔ ⋏ ⋓ ⋢ | 1 | 3 and 2 | 1.04 at 6x12 | failed again (2 and 2 rules) |
| tmath10 g10 | ⊈ ⊊ ⊒ ⊓ ⋀ ⋂ ⋎ ⋐ ⋣ ⋤ | 1 | 1 and 1 | 1.00 at 6x12 | failed again (1 and 1 rules) |
| tmath10 g11 | ⊅ ⊲ ⊳ ⊴ ⊵ ⋑ ⋪ ⋫ ⋬ ⋭ | 1 | 2 and 2 | 1.09 at 6x12 | failed again (2 and 2 rules) |
| tmath8 g0 | ⇍ ⇏ ⇗ ⇙ ⇚ ⇛ ⟰ ⤊ | 1 | 7 and 7 | 1.50 at 8x16 | failed again (7 and 7 rules) |
| tmath8 g1 | ⇎ ⇕ ⇖ ⇘ ⟱ ⤆ ⤇ ⤋ | 1 | 7 and 7 | 1.49 at 8x16 | failed again (7 and 7 rules) |
| tmath8 g2 | ⇦ ⇮ ⇯ ⇰ ⇳ ⬀ ⬂ ⬄ | 0 | 6 and 6 | 1.53 at 10x20 | failed again (6 and 6 rules) |
| tmath8 g3 | ⇨ ⇩ ⇪ ⇫ ⇬ ⇭ ⬁ ⬃ | 0 | 6 and 6 | 1.68 at 8x16 | failed again (6 and 6 rules) |
| tmath8 g4 | ⊘ ⊙ ⊚ ⊝ ⊞ ⊡ ⨀ ⨂ | 0 | 1 and 1 | 1.17 at 10x20 | failed again (1 and 1 rules) |
| tmath8 g5 | ⊕ ⊖ ⊗ ⊛ ⊜ ⊟ ⊠ ⨁ ⨌ | 1 | 7 and 7 | 1.33 at 10x20 | failed again (7 and 7 rules) |
| tmath8 g6 | ∰ ⨎ ⨐ ⨑ ⨓ ⨗ ⨙ ⨜ | 1 | 6 and 7 | 1.48 at 6x12 | failed again (7 and 7 rules) |
| tmath8 g7 | ∯ ∱ ∲ ⨍ ⨏ ⨒ ⨖ ⨚ | 0 | 7 and 7 | 1.56 at 6x12 | failed again (7 and 7 rules) |
| tmath8 g8 | ∬ ∭ ∮ ∳ ⨔ ⨕ ⨘ ⨛ | 1 | 6 and 6 | 1.70 at 6x12 | failed again (6 and 6 rules) |

## Rebuild

```sh
make pack-term-math-v1
```

`train/build_term_symbols.py math` writes `neuronte-term-math-v1.list.txt`
from the tier `tmath` of `train/glyphs.py` less the groups left out, then
applies `train/standalone_bundle.py` to the group JSON in order, with split-v9
as the bundle to stay apart from. The table sends each listed character to its
group net; there is no gate.

| File | Members | Table rows | Bytes | SHA256 |
|---|---:|---:|---:|---|
| `neuronte-term-math-v1.nrt` | 48 | 369 | 2,686,120 | `cf30e22efe80b233c73ca2f0c78490c153e172995187cdc1798206db647b1f77` |

## Training

`train/split_expert.py`, unchanged: repertoire groups, contiguous partition,
width 64, seeds 0 and 1, 120,000 steps, Adam 0.002 cosine, the project teacher
(grid 256, tau .15, pen .075), from the drawings in `font/term-math.txt` and
`train/term_glyphs.py`. The groups are those of
`font/term-math-partition.json`: characters of one shape family together, 12,
10 or 8 to a net by how much ink edge the family draws
(`tools/term-partition.py`). Trained on a rented RTX 3090.

## Checks

`make test-term-math-v1` checks the grouping against the drawings, packs each
group JSON and runs `tests/check_reference.py` on it (C against float64
numpy), then `tests/check_term_symbols.py` and `test_api --standalone 219A`.
The check verifies: the bundle is rebuilt byte for byte; its table is exactly
its list and shares nothing with split-v9; every scalar from 0 to U+10FFFF is
routed to its group net or to the blank net and reported trained or untrained
accordingly; each character draws as its group net alone at 19 cell sizes;
other scalars draw an empty cell; the validation record names the shipped seed
of every group and both seeds' hashes; and the drawings are still the ones the
nets were scored against. `make test-standalone` checks that no two listed
bundles claim one character.

## Speed

Against split-v9's fallback for the same 465 characters: split-v9 sends each
through its gate to a net that never saw it, so this compares the time to
draw, not what is drawn. kilix-bench, one pinned core, a fresh process per
job, 1 warmup and 10 measured rounds, medians; uncached coverage in µs per
glyph.

| Host CPU | Bundle | 8x16 | 16x32 | 48x96 | open µs | route ns |
|---|---|---:|---:|---:|---:|---:|
| i7-6820HQ | split-v9 | 500.4 | 1960.5 | 4372.6 | 4741.5 | 1276.4 |
| i7-6820HQ | term-math-v1 | 187.3 | 717.9 | 1594.6 | 3392.9 | 40.7 |
| i7-10700F | split-v9 | 385.6 | 1510.8 | 3352.1 | 3453.5 | 932.6 |
| i7-10700F | term-math-v1 | 145.3 | 553.1 | 1241.2 | 2244.4 | 28.1 |

split-v9 time over term-math-v1 time, geometric mean over the three cells:
2.71 (i7-6820HQ), 2.70 (i7-10700F); 2.70 over both. Each bundle draws the same
pixels on both hosts; C against the float64 reference differs by at most
8.5e-06.

