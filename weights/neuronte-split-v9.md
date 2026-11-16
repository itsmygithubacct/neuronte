# split-v9: split-v8 with 165 terminal characters

`neuronte-split-v9.nrt` is `neuronte-split-v8.nrt` with fourteen more
known-only group nets for characters that terminals print often and no
earlier bundle was trained on. In split-v8 these characters went to the
router's gate, which handed each to a net that had never seen it, so ✓ came
out as a small arrow and ά as dots. Each is now drawn by a net trained on it:

| Characters | Drawn by | Gates |
|---|---|---|
| 113 symbols: ✓ ✕ ✖ ✗ ✘ ☑; 19 arrows and triangles (↔ ↕ ↖ ↘ ↙ ↩ ↪ ↵ ⇐ ⇑ ⇒ ⇓ ⇔ ➜ ➤ ▶ ◀ ▴ ◂); ◦ ‣ ○ ◇ ■ □ ▪ ▫ ★ ☆; ± − ≤ ≥ ≠; ¢ £ ¥ € ₽ ₴ µ ® ™; ⁰¹²³⁴⁵⁶⁷⁸⁹ ₀₁₂₃₄₅₆₇₈₉ ¼ ¾ ª º; ‹ « » † ‡ § ¶ ¡ ¿ ¦ ¬ „; ∞ √ ∑ ∏ ∫ ∂ ∆ ∇ ∈ ∉ ∩ ∪ ⊂ ⊃ ⊆ ⊇ ∧ ∨; ⎇ ☰ ⏎ ⌘ ⌥ ⇧ ⌃ ⏱ ⚠ № | `neuronte-tsymbol-v1`, 9×H64, seed 0 | **failed** the declared gates, both seeds; chosen by the owner after review |
| 20 Greek letters with tonos and dialytika (Ά Έ Ή Ί Ό Ύ Ώ ΐ Ϊ Ϋ ά έ ή ί ΰ ϊ ϋ ό ύ ώ) | `neuronte-tgreek-v1`, 2×H64, seed 0 | **failed**, both seeds; chosen by the owner after review |
| 32 Cyrillic letters beyond Russian, for Ukrainian, Belarusian, Serbian, Macedonian and Bulgarian (Ѐ Ђ Ѓ Є Ѕ І Ї Ј Љ Њ Ћ Ќ Ѝ Ў Џ, their smalls, Ґ ґ) | `neuronte-tcyrillic-v1`, 3×H64, seed 0 | **failed**, both seeds; chosen by the owner after review |
| Every other character, trained or not | split-v8's members, unchanged | as in [split-v8](neuronte-split-v8.md) |

**Not a default.** split-v5 stays the terminal default and split-v8 is
unchanged. No group qualified under the rules declared before it was
trained. The owner looked at every group side by side (teacher, split-v8,
both seeds, at 4×8 to 16×32) and chose seed 0 of all fourteen; that choice
does not change the measurements or turn the failures into passes. Seed 1
of each group is kept beside it (`…-gN.seed1.json`). Every failure is in
`neuronte-split-v9.validation.json`.

## How the gates failed

The gates, written before training, take their numbers from the nets the
project's own gates were written against: split-v5's symbol expert on its 49
symbols for the symbols, and the H256 accent expert on its Greek and Russian
letters for the letters. Every group net passes the C-versus-float64 check.
In short:

- **Symbols** (recipe 2, after recipe 1 — nine H32 nets, 80k steps — failed
  every group by more): five of the nine groups miss the 8×16 mean-error
  limit (0.00557), g4 (↖..⇧) by the most (0.0086); several miss mean error
  at sizes from 2×4 to 13×27; and nearest-glyph identity fails at the
  smallest cells: at 1×2, ∩ ∪ ○ ✕ are nearest ∏; at 2×4, ¥ is nearest ∇
  (and, in seed 0, ⇐ nearest ✖); at 3×6, ⁰→³, ₄→₃ and ↔→∞; at 4×8, ₀→₈.
  g6 (∪..⌥) and g7 (⎇..○) fail only that 1×2 identity rule; g2 (‹..₃) only
  at 3×6 and 4×8. At 8×16, 16×32 and 48×96 everything else passes: mean
  error at 16×32 and 48×96, p99, firm-wrong pixels, every glyph's own error,
  identity and margin.
- **Greek and Cyrillic**: mean error and p99 pass at 8×16, 16×32 and 48×96
  in every group (Greek capitals 0.0063 at 8×16 against 0.0075). What fails
  is mostly binary IoU — coverage cut at one half — at 8×16 or 16×32 (drawn
  normally, with one sample per pixel, or both) and at 6 to 13 of the 26 other
  cell sizes. The Greek capitals also miss firm, vanished, identity, p99 and
  mean-error rules at sizes from 1×2 to 6×12; the other letter groups miss
  firm or vanished rules at 1×2 to 3×6. Most misses are pixels the teacher leaves just under one half: at 8×16 Ί inks
  25 pixels where the teacher inks 17, in both seeds, with no firm-wrong
  pixel.

**Small cells.** At 8×16, ΐ and ΰ (dialytika and tonos together) merge into
one mark, and ∉ and ⇔ are crowded. Below about 6×12 several symbols lose the
detail that tells them apart (see above). These are limits of the drawings at
that size as much as of the nets.

## What a consumer changes

Load `neuronte-split-v9.nrt` where it now loads split-v8 or split-v5. No
call changes. The 1,176 characters split-v8 was trained on draw split-v8's
exact pixels, and every character outside the table draws exactly as before;
only the 165 above change. The file is larger and has 35 members, so it
needs the current runtime (128-member limit) and opens a little slower (see
Speed).

To stop drawing invented shapes for characters no net was trained on, also
call `neuronte_set_untrained(font, 1)`: such a scalar is then drawn as a
hollow box with a small square inside, made by code. `neuronte_untrained()`
says whether a scalar is outside the trained table. Both are opt-in; the
default draws as before.

## Rebuild

```sh
make pack-split-v9
```

`train/build_split_v9.py` applies `known_bundle.add_known` to split-v8 once,
with the fourteen group JSON in order (symbols, Greek, Cyrillic). The added
scalars were in no table row of split-v8; each gets a row to its group net.
split-v8's 21 members, 75 table rows and gate are kept byte for byte; the
gate gets fourteen zero rows and suppressed biases, so it never picks a new
member. `neuronte-split-v9.provenance.json` holds the add_known record
(source hashes, rows, gate bounds, original member hashes).

| File | Members | Net parameters | Bytes | SHA256 |
|---|---:|---:|---:|---|
| `neuronte-split-v8.nrt` | 21 | 699,511 | 2,805,688 | `445b53caa40c6cd02a1b324458bf5ae549b1ab304043ac0eeb3d4871e6461168` |
| `neuronte-split-v9.nrt` | 35 | 898,437 | 3,607,088 | `0a92f223d47f1680929b2c5d7512d1a1728d4871e6653b33cbaad060e6bb90c0` |

Each new net is H64, 14,209 parameters; together 198,926. With the gate the
library reports 899,394 parameters for split-v9.

## Training

`train/split_expert.py`, repertoire groups, contiguous partition, seeds 0
and 1, Adam 0.002 cosine, the project teacher (grid 256, tau .15, pen .075),
120,000 steps, from the drawings in `font/symbols.txt`, `font/letters.txt`
and `font/marks.txt` (tiers tsymbol, tgreek, tcyrillic in `train/glyphs.py`;
see [PROVENANCE.md](../PROVENANCE.md)). Trained on rented RTX 3090 GPUs;
the Cyrillic and symbol runs moved to a second machine part way, resuming
from a checkpoint.

## Checks

`make test-split-v9` packs each group JSON and runs `tests/check_reference.py`
on it (C against float64 numpy), then `tests/check_split_v9.py` and
`test_api --full --accent --pixel`. The check verifies:

- split-v8 is `445b53ca…`; split-v9 is rebuilt byte for byte from it and the
  group JSON, and its provenance is the rebuild's.
- The first 21 members are split-v8's; members 21–34 are the group JSON,
  packed, in order; split-v8's table rows are all kept, the added rows are
  exactly the groups' scalars, and the gate is split-v8's with fourteen zero
  rows and suppressed biases appended.
- Every scalar 0..0x10FFFF and 0xFFFFFFFF routes as in split-v8, except the
  165 added characters, each of which was outside split-v8's table and now
  goes to the net trained on it.
- The 1,176 characters of split-v8's table draw split-v8's pixels at the 19
  ASCII qualification sizes (3×6 to 64×128) and with one sample per pixel at
  8×16, 16×32 and 48×96; about 300 unknown and invalid scalars draw as in
  split-v8 at 9×17 and 25×49, automatic and S1; each added character draws
  exactly as its group net alone at the same sizes.
- The validation record names this bundle and seed 0 of each group, binds
  every group file by hash, and records that every group failed its gates.

These are integration checks. They do not assert the quality gates.

## Speed

Measured with kilix-bench `e21e5cd` on the 165 added characters, split-v9
against split-v8 and split-v5 in the same runs, on an Intel i7-6820HQ (on
mains power) and an Intel i7-10700F, each on one pinned core with the
benchmark lock held for the whole run. One warmup and ten measured rounds, a
fresh process per job, rounds shuffled, cells 8x16, 16x32 and 48x96. ARM was
not measured. kilix-bench's float64 reader checks only table routes, and in
split-v5 and split-v8 these characters go through the gate, so a separate
file outside kilix-bench gave the reader a float64 gate for that check; it
agreed with the library's route for all 165 characters in all three bundles,
and the reference check passed (worst difference 8.6e-06).

Uncached `neuronte_coverage()`, median µs per glyph:

| CPU | Bundle | 8x16 | 16x32 | 48x96 |
|---|---|---:|---:|---:|
| i7-6820HQ | split-v5 | 858.0 | 3,421.5 | 7,645.1 |
| i7-6820HQ | split-v8 | 873.5 | 3,406.7 | 7,620.2 |
| i7-6820HQ | split-v9 | 194.7 | 748.2 | 1,666.6 |
| i7-10700F | split-v5 | 917.3 | 3,603.9 | 8,075.7 |
| i7-10700F | split-v8 | 909.2 | 3,566.2 | 8,127.6 |
| i7-10700F | split-v9 | 194.9 | 750.1 | 1,702.5 |

Over the three cells, split-v9 draws these characters 4.5 (i7-6820HQ) to
4.7 (i7-10700F) times as fast as split-v8, and as much faster than split-v5.
The i7-10700F had a load average of about 26 from other work during its run
(recorded, not stopped), so its absolute times are high; each host's
comparison is within one run. A first draw tracks coverage. A primed
(cached) draw is 1.0–1.1 µs at 8x16 against 2.4–3.1 µs for the older bundles.
Pixels are identical on both hosts.

Routing these characters is a table lookup in split-v9, 13–14 ns, instead
of split-v8's gate, about 1,000 ns. **Opening costs more:** one model open,
including the first 8x16 buffer, is 4.77 ms on the i7-6820HQ and 4.39 ms on
the i7-10700F, against 4.32 and 3.48 ms for split-v8 and 2.61 and 2.11 ms for
split-v5, paid once per process.

## Status

Not a default. split-v5 remains the terminal default, split-v8 keeps its
name and bytes, and no release pins this file.
