# term-mathalpha-v1: the sans-serif, monospace and double-struck alphabets, on their own

`neuronte-term-mathalpha-v1.nrt` is a terminal bundle for 179 characters no earlier bundle was trained on: letters and digits of Mathematical Alphanumeric Symbols: sans-serif (U+1D5A0..U+1D5D3, digits U+1D7E2..U+1D7EB), monospace (U+1D670..U+1D6A3, digits U+1D7F6..U+1D7FF) and double-struck (U+1D538..U+1D56B less the seven capitals that live in Letterlike Symbols, digits U+1D7D8..U+1D7E1). In `neuronte-split-v9` each of them goes to the router's gate and is drawn by a net that never saw it, so it comes out as some other shape.

It is a **standalone** bundle: 17 known-only group nets and one blank net, 971,056 bytes, with no copy of split-v9 in it. A program opens it beside split-v9 and asks it first (see "What a consumer changes"). It is not a default and replaces nothing.

| Characters | Training set | Group nets | Common gates |
|---|---|---|---|
| 120: sans-serif and monospace letters and the digits 2 to 9, each pair in one net | `tscrmp` | 10×H64 | all 10 passed |
| 14: sans-serif and monospace 0 and 1, double-struck digits | `tscrmn` | 2×H64 | all 2 passed |
| 19: double-struck capitals | `tscrmdu` | 2×H64 | all 2 passed |
| 26: double-struck smalls | `tscrmdl` | 3×H64 | all 3 passed |

## The gates

The common gates of phases 3 to 6. `gates-v2.json`, sha256 `5bf1a3f8312c45df2a20b2e69d51ee3c690c58891ec5390cf0e41cbdf9f9b51b`, was declared before any of these nets was trained and recorded in this lane's report before training. Its limits are the worst group net the owner had already accepted on a sheet, times 1.10, counted at 6×12, 8×16, 10×20, 12×24, 16×32, 24×48 and 48×96 (mean error, 99th percentile, firm-wrong fraction, the worst character, mean and worst overlap), and with one sample a pixel at 8×16, 16×32 and 48×96; at every counted size each character must be nearer its own drawing than any other drawing of the bundle (or an exact twin of it) and none may vanish. These are scored as letters, against the teacher of all 179 characters drawn for the bundle. Both seeds must pass.

**The gates were amended three times while these nets trained and were scored, by the owner, for every lane, and not by this lane.** Another lane showed that some rules are failed by a perfect net: the drawing itself, sampled as the library samples, misses them on thin strokes.

- `gates-v2.1.json`, sha256 `214942e398f88110cd7c6044c194f0f274274aeedb07abcbe8e1a18dc2b323c0`: the overlap of the worst character is dropped for letters.
- `gates-v2.2.json`, sha256 `dd3cc2ea30ccb49d001c28a905bcc6e2a2d11edfcd6a741464fda91162b10e70`: 2.1, and a rule the perfect drawing of a group fails at a size is not applied there.
- `gates-v2.3.json`, sha256 `2ccff8354eeda45e05525490b9fdee6ab13d4970a2389537c44af1504fc50fc4`, **gave the verdicts here**: instead of skipping such a rule, no limit is tighter than the perfect drawing's own score for that group, size and rule eased by 10 per cent (an error ceiling at perfect × 1.10, an overlap floor at 1 − (1 − perfect) × 1.10); and a seed whose net puts every pixel on the correct side at every counted size passes whatever the error-amount rules say. Nearest-to-itself and none-vanished always apply and are never eased.

Of the 17 groups first trained, 8 passed with both seeds under gates-v2, 10 under 2.1, 16 under 2.2 and 17 under 2.3. Seeds passing as pixel-exact: 0. **Limits eased under 2.3 to the perfect drawing's score and 10 per cent: 20** in the groups of the bundle (rule: declared limit, perfect drawing, limit applied):

- `tscrmn` group 0: 10x20 iou_mean: 0.7917, 0.8051, 0.7856
- `tscrmn` group 0: s1 8x16 p99: 0.2354, 0.2544, 0.2799
- `tscrmn` group 1: 24x48 firm: 0.0006356, 0.00062, 0.000682
- `tscrmn` group 1: s1 8x16 p99: 0.2354, 0.2594, 0.2853
- `tscrmdu` group 0: 8x16 mae: 0.01428, 0.01305, 0.01435
- `tscrmdu` group 0: 10x20 mae: 0.008661, 0.01044, 0.01148
- `tscrmdu` group 0: 10x20 iou_mean: 0.7917, 0.7779, 0.7557
- `tscrmdu` group 0: s1 8x16 p99: 0.2354, 0.23, 0.253
- `tscrmdu` group 1: 10x20 mae: 0.008661, 0.008527, 0.009379
- `tscrmdu` group 1: s1 8x16 p99: 0.2354, 0.2501, 0.2751
- `tscrmdl` group 0: 10x20 mae: 0.008661, 0.008446, 0.009291
- `tscrmdl` group 0: 24x48 firm: 0.0006356, 0.0009766, 0.001074
- `tscrmdl` group 0: s1 8x16 p99: 0.2354, 0.2475, 0.2723
- `tscrmdl` group 0: s1 8x16 firm: 0.01074, 0.0127, 0.01396
- `tscrmdl` group 1: 10x20 mae: 0.008661, 0.009136, 0.01005
- `tscrmdl` group 1: 10x20 iou_mean: 0.7917, 0.8065, 0.7872
- `tscrmdl` group 1: 24x48 firm: 0.0006356, 0.0006752, 0.0007427
- `tscrmdl` group 1: 24x48 iou_mean: 0.9449, 0.9354, 0.929
- `tscrmdl` group 1: s1 8x16 p99: 0.2354, 0.23, 0.253
- `tscrmdl` group 2: 10x20 iou_mean: 0.7917, 0.7443, 0.7188

**One group changed hands between amendments.** Under gates-v2.2 the second group of double-struck
capitals (`tscrmdu` group 1: L M O S T U V W X Y) failed with seed 0 on mean error at 10×20, so it was trained once
more as two halves of five, and both halves passed. Under gates-v2.3 that limit is the perfect drawing's own score
and 10 per cent (0.00938 in place of 0.00866) and the group passes as first trained, so the net first trained is
the one in the bundle and the halves are not; their set line is gone from `font/term-scripts.txt` and their nets
are kept only with the lane's evidence.

The rule is automatic and nobody chose a net. A group whose two seeds pass ships the seed with the lower mean error over 8×16, 16×32 and 48×96. A group that fails is trained once more as two groups of half its characters; a half that still fails is left out.

- **17 groups trained, 17 passed with both seeds.**
- **Left out: none.** Every character drawn for the bundle is in it.
- Every group net in the bundle passes the C-against-float64 check.

**Small cells.** The gates are loose at 6×12 by their formula (a letter group passes with a mean overlap of 0.44). Here the lowest overlap of any one character at 6×12 is 0.38 (`tscrmp` group 6). Below 6×12 nothing is counted.

## What a consumer changes

Nothing, until it opens this file. It does not replace split-v9 and holds none of its characters; `tests/check_bundle_lists.py` checks that it shares no trained scalar with split-v9 or any other listed bundle.

```c
neuronte_open_file("neuronte-split-v9.nrt", &base);
neuronte_open_file("neuronte-term-mathalpha-v1.nrt", &more);
/* for each scalar c */
font = neuronte_untrained(more, c) ? base : more;
```

`neuronte_untrained(more, c)` is 0 for exactly the 179 characters in `neuronte-term-mathalpha-v1.list.txt` and 1 for every other scalar. A scalar outside the list, drawn through this file anyway, comes out blank, or as the code-made hollow box after `neuronte_set_untrained(more, 1)`. The file needs the current runtime (version 2 bundles, 128-member limit). It has 18 members. Cells are the terminal's 1:2 cell; the nets were trained and measured from 6×12 to 48×96.

## Recipe

- **Drawings.** Monospace letters and digits are this face's own ASCII strokes as they are (the face is
  a monospace one). Sans-serif is the same strokes but for six drawn in
  `font/term-scripts.txt`: I, i, j and 1 without slab serifs, l with a curved
  foot, 0 without its slash; so 56 sans-serif characters have exactly the
  drawing of their monospace twin. The 55 double-struck characters are drawn
  by hand with a thinner pen: one stem doubled, a chord inside the left of a
  round letter. The list has only these three styles: no bold, italic,
  script or fraktur is in it, so none is drawn.
  No font was opened or rasterised; DejaVu Sans Mono gave only its list of code points.
- **Sets and groups.** 4 training sets of `font/term-scripts.txt`, each cut in order into group nets of 7 to 12 characters (17 in all).
- **Training.** `train/split_expert.py train --mode repertoire --partition contiguous`, unchanged: hidden width 64, 120,000 steps, the project teacher (grid 256), seeds 0 and 1. No retry at another width.
- **Selection.** As under "The gates". Only the shipped seed's JSON is in `weights/`; the other seed's hash and measurements are in the validation record.
- **Packing.** `train/standalone_bundle.py`: the group nets, a table from each listed scalar to its net, no gate, and a blank net as the fallback.

```sh
make pack-term-mathalpha-v1    # rebuilds the .nrt byte for byte from the group nets
make test-term-mathalpha-v1
```

## Checks

`make test-term-mathalpha-v1` (part of `make test`): every group net against the float64 reference; the bundle rebuilt byte for byte; its table exactly `neuronte-term-mathalpha-v1.list.txt`, which is its training sets in `font/term-scripts.txt` less any group left out; every scalar from U+0000 to U+10FFFF routed as the table says; pixels through the bundle equal to each group net alone at 19 cell sizes and with one sample a pixel; `test_api --standalone`; and the validation record: every shipped group passed with both seeds and ships the seed the rule selects.

## Results by group

Mean error against the teacher at 8×16, 16×32 and 48×96 and mean overlap at 6×12 and 8×16, for the shipped seed (for a group not shipped, the lower-error seed).

| Set | Group | Characters | Result | Rules missed (seed 0 / seed 1) | Mean error | Overlap 6×12, 8×16 |
|---|---:|---|---|---|---|---|
| `tscrmp` | 0 | 𝖠 𝙰 𝖡 𝙱 𝖢 𝙲 𝖣 𝙳 𝖤 𝙴 𝖥 𝙵 | passed; H64, seed 1 | 0 / 0 | 0.0066 0.0028 0.0014 | 0.990, 0.970 |
| `tscrmp` | 1 | 𝖦 𝙶 𝖧 𝙷 𝖨 𝙸 𝖩 𝙹 𝖪 𝙺 𝖫 𝙻 | passed; H64, seed 1 | 0 / 0 | 0.0063 0.0030 0.0014 | 0.959, 0.967 |
| `tscrmp` | 2 | 𝖬 𝙼 𝖭 𝙽 𝖯 𝙿 𝖰 𝚀 𝖱 𝚁 𝖳 𝚃 | passed; H64, seed 1 | 0 / 0 | 0.0075 0.0032 0.0016 | 0.990, 0.946 |
| `tscrmp` | 3 | 𝖴 𝚄 𝖵 𝚅 𝖶 𝚆 𝖷 𝚇 𝖸 𝚈 𝖹 𝚉 | passed; H64, seed 1 | 0 / 0 | 0.0046 0.0024 0.0011 | 0.970, 0.987 |
| `tscrmp` | 4 | 𝖮 𝙾 𝖲 𝚂 𝗈 𝚘 𝗌 𝚜 𝟥 𝟹 𝟪 𝟾 | passed; H64, seed 1 | 0 / 0 | 0.0041 0.0018 0.0012 | 1.000, 0.978 |
| `tscrmp` | 5 | 𝖺 𝚊 𝖻 𝚋 𝖼 𝚌 𝖽 𝚍 𝖾 𝚎 𝖿 𝚏 | passed; H64, seed 0 | 0 / 0 | 0.0044 0.0020 0.0012 | 0.945, 0.961 |
| `tscrmp` | 6 | 𝗀 𝚐 𝗁 𝚑 𝗂 𝚒 𝗃 𝚓 𝗄 𝚔 𝗅 𝚕 | passed; H64, seed 1 | 0 / 0 | 0.0056 0.0028 0.0013 | 0.915, 0.954 |
| `tscrmp` | 7 | 𝗆 𝚖 𝗇 𝚗 𝗉 𝚙 𝗊 𝚚 𝗋 𝚛 𝗍 𝚝 | passed; H64, seed 1 | 0 / 0 | 0.0052 0.0024 0.0012 | 0.888, 0.954 |
| `tscrmp` | 8 | 𝗎 𝚞 𝗏 𝚟 𝗐 𝚠 𝗑 𝚡 𝗒 𝚢 𝗓 𝚣 | passed; H64, seed 1 | 0 / 0 | 0.0033 0.0018 0.0010 | 1.000, 0.972 |
| `tscrmp` | 9 | 𝟤 𝟸 𝟦 𝟺 𝟧 𝟻 𝟨 𝟼 𝟩 𝟽 𝟫 𝟿 | passed; H64, seed 0 | 0 / 0 | 0.0051 0.0029 0.0014 | 0.974, 0.985 |
| `tscrmn` | 0 | 𝟢 𝟶 𝟘 𝟙 𝟚 𝟛 𝟜 | passed; H64, seed 1 | 0 / 0 | 0.0083 0.0035 0.0021 | 0.913, 0.940 |
| `tscrmn` | 1 | 𝟣 𝟷 𝟝 𝟞 𝟟 𝟠 𝟡 | passed; H64, seed 1 | 0 / 0 | 0.0060 0.0036 0.0018 | 0.900, 0.973 |
| `tscrmdu` | 0 | 𝔸 𝔹 𝔻 𝔼 𝔽 𝔾 𝕀 𝕁 𝕂 | passed; H64, seed 1 | 0 / 0 | 0.0129 0.0052 0.0026 | 0.937, 0.796 |
| `tscrmdu` | 1 | 𝕃 𝕄 𝕆 𝕊 𝕋 𝕌 𝕍 𝕎 𝕏 𝕐 | passed; H64, seed 1 | 0 / 0 | 0.0096 0.0041 0.0023 | 0.934, 0.781 |
| `tscrmdl` | 0 | 𝕒 𝕓 𝕔 𝕕 𝕖 𝕗 𝕘 𝕙 | passed; H64, seed 1 | 0 / 0 | 0.0078 0.0046 0.0023 | 0.905, 0.977 |
| `tscrmdl` | 1 | 𝕚 𝕛 𝕜 𝕝 𝕞 𝕟 𝕠 𝕡 𝕢 | passed; H64, seed 1 | 0 / 0 | 0.0072 0.0048 0.0021 | 0.878, 0.820 |
| `tscrmdl` | 2 | 𝕣 𝕤 𝕥 𝕦 𝕧 𝕨 𝕩 𝕪 𝕫 | passed; H64, seed 1 | 0 / 0 | 0.0072 0.0031 0.0017 | 0.804, 0.983 |

## Speed

kilix-bench e21e5cd on two x86 hosts, Intel Core i7-6820HQ and Intel Core i7-10700F, each under the hosts' shared benchmark lock: one pinned core, a fresh process for every job, one warmup and ten measured rounds in shuffled order, medians, every model checked against the float64 reference first (worst difference 9.2e-06). The corpus is this bundle's 179 characters. split-v9 sends each through its gate to another of its nets, which never saw it; term-mathalpha-v1 looks it up in its table and runs a small group net.

| µs per character, Intel Core i7-6820HQ | split-v9 | term-mathalpha-v1 | split-v9 / term-mathalpha-v1 |
|---|---:|---:|---:|
| Coverage, uncached, 8×16 | 496.0 | 205.7 | 2.41 |
| Coverage, uncached, 16×32 | 1936.1 | 785.0 | 2.47 |
| Coverage, uncached, 48×96 | 4325.1 | 1748.7 | 2.47 |
| Draw, cold, 8×16 | 510.8 | 207.8 | 2.46 |
| Draw, cold, 16×32 | 1948.7 | 794.3 | 2.45 |
| Draw, cold, 48×96 | 4359.8 | 1787.5 | 2.44 |
| Draw, warm, 8×16 | 4.0 | 1.0 | 3.86 |
| Draw, warm, 16×32 | 6.9 | 3.1 | 2.21 |
| Draw, warm, 48×96 | 28.3 | 22.6 | 1.25 |

On the Intel Core i7-6820HQ: a lookup takes 13 ns in this bundle's table against 1228 ns for split-v9's gate; opening the file takes 1.4 ms against 4.8 ms for split-v9 (a program that opens both pays both).

| µs per character, Intel Core i7-10700F | split-v9 | term-mathalpha-v1 | split-v9 / term-mathalpha-v1 |
|---|---:|---:|---:|
| Coverage, uncached, 8×16 | 375.2 | 155.8 | 2.41 |
| Coverage, uncached, 16×32 | 1456.5 | 599.5 | 2.43 |
| Coverage, uncached, 48×96 | 3227.1 | 1332.4 | 2.42 |
| Draw, cold, 8×16 | 381.6 | 157.3 | 2.43 |
| Draw, cold, 16×32 | 1465.0 | 607.4 | 2.41 |
| Draw, cold, 48×96 | 3279.3 | 1356.4 | 2.42 |
| Draw, warm, 8×16 | 3.0 | 0.7 | 3.99 |
| Draw, warm, 16×32 | 5.0 | 2.3 | 2.21 |
| Draw, warm, 48×96 | 20.2 | 16.0 | 1.26 |

On the Intel Core i7-10700F: a lookup takes 7 ns in this bundle's table against 901 ns for split-v9's gate; opening the file takes 0.9 ms against 3.8 ms for split-v9 (a program that opens both pays both).

Uncached, term-mathalpha-v1 draws these characters 2.4 times as fast as split-v9's fallback does (geometric mean over both hosts and the three cells; per host 2.4 on the Intel Core i7-6820HQ, 2.4 on the Intel Core i7-10700F). Cold draw: 2.5, 2.4; warm draw: 2.20, 2.23. The pixels are identical on both hosts.

A handle caches 1,024 drawn cells. A screen that shows more distinct cells than that redraws some each frame, whichever bundle draws them.

## Files

`neuronte-term-mathalpha-v1.nrt` (971,056 bytes, sha256 `b6bd7d73a1c2116b4383d70c810fe780ca3e36846c32c7178c1e5a2764167c57`), `neuronte-term-mathalpha-v1.list.txt`, `neuronte-term-mathalpha-v1.provenance.json`, `neuronte-term-mathalpha-v1.validation.json`, and 17 group nets `neuronte-term-mathalpha-v1-SET-gN.json`. All are in `weights/SHA256SUMS`.
