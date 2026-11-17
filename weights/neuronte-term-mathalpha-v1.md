# term-mathalpha-v1: the sans-serif, monospace and double-struck alphabets, on their own

`neuronte-term-mathalpha-v1.nrt` is a terminal bundle for 179 characters no earlier bundle was trained on: letters and digits of Mathematical Alphanumeric Symbols: sans-serif (U+1D5A0..U+1D5D3, digits U+1D7E2..U+1D7EB), monospace (U+1D670..U+1D6A3, digits U+1D7F6..U+1D7FF) and double-struck (U+1D538..U+1D56B less the seven capitals that live in Letterlike Symbols, digits U+1D7D8..U+1D7E1). In `neuronte-split-v9` each of them goes to the router's gate and is drawn by a net that never saw it, so it comes out as some other shape.

It is a **standalone** bundle: 18 known-only group nets and one blank net, 1,028,112 bytes, with no copy of split-v9 in it. A program opens it beside split-v9 and asks it first (see "What a consumer changes"). It is not a default and replaces nothing.

| Characters | Training set | Group nets | Common gates |
|---|---|---|---|
| 120: sans-serif and monospace letters and the digits 2 to 9, each pair in one net | `tscrmp` | 10×H64 | all 10 passed |
| 14: sans-serif and monospace 0 and 1, double-struck digits | `tscrmn` | 2×H64 | all 2 passed |
| 19: double-struck capitals | `tscrmdu` | 2×H64 | 1 of 2 passed |
| 26: double-struck smalls | `tscrmdl` | 3×H64 | all 3 passed |

## The gates

The common gates of phases 3 to 6. `gates-v2.json`, sha256 `5bf1a3f8312c45df2a20b2e69d51ee3c690c58891ec5390cf0e41cbdf9f9b51b`, was declared before any of these nets was trained and recorded in this lane's report before training. Its limits are the worst group net the owner had already accepted on a sheet, times 1.10, counted at 6×12, 8×16, 10×20, 12×24, 16×32, 24×48 and 48×96 (mean error, 99th percentile, firm-wrong fraction, the worst character, mean and worst overlap), and with one sample a pixel at 8×16, 16×32 and 48×96; at every counted size each character must be nearer its own drawing than any other drawing of the bundle (or an exact twin of it) and none may vanish. These are scored as letters, against the teacher of all 179 characters drawn for the bundle. Both seeds must pass.

**The gates were amended twice while these nets trained, by the owner, for every lane, and not by this lane.** Another lane showed that some rules are failed by a perfect net: the drawing itself, sampled as the library samples, misses them on thin strokes. `gates-v2.1.json`, sha256 `214942e398f88110cd7c6044c194f0f274274aeedb07abcbe8e1a18dc2b323c0`, dropped the overlap of the worst character for letters. `gates-v2.2.json`, sha256 `dd3cc2ea30ccb49d001c28a905bcc6e2a2d11edfcd6a741464fda91162b10e70`, **gave the verdicts here**: it is 2.1, and for each group and size a rule that the perfect drawing of that group fails is not applied there; every other rule applies with its limit, and nearest-to-itself and none-vanished are never skipped. No limit was changed.

Of the 17 groups first trained, 8 passed with both seeds under gates-v2, 10 under 2.1 and 16 under 2.2. **Rules skipped under 2.2 because a perfect net fails them: 16** in the groups of the bundle:

- `tscrmn` group 0: s1 8x16 p99 skipped: perfect net fails (0.254444, limit 0.235413)
- `tscrmn` group 1: s1 8x16 p99 skipped: perfect net fails (0.259375, limit 0.235413)
- `tscrmdu` group 0: 10x20 mae skipped: perfect net fails (0.0104377, limit 0.00866061)
- `tscrmdu` group 0: 10x20 iou_mean skipped: perfect net fails (0.777891, limit 0.791706)
- `tscrxmdu1` group 0: 8x16 iou_mean skipped: perfect net fails (0.686537, limit 0.703503)
- `tscrxmdu1` group 0: 10x20 mae skipped: perfect net fails (0.0100236, limit 0.00866061)
- `tscrxmdu1` group 0: 10x20 iou_mean skipped: perfect net fails (0.780417, limit 0.791706)
- `tscrxmdu1` group 0: 24x48 mae skipped: perfect net fails (0.00584012, limit 0.00571244)
- `tscrxmdu1` group 0: s1 8x16 p99 skipped: perfect net fails (0.263287, limit 0.235413)
- `tscrmdl` group 0: 24x48 firm skipped: perfect net fails (0.000976562, limit 0.000635634)
- `tscrmdl` group 0: s1 8x16 p99 skipped: perfect net fails (0.2475, limit 0.235413)
- `tscrmdl` group 0: s1 8x16 firm skipped: perfect net fails (0.0126953, limit 0.0107422)
- `tscrmdl` group 1: 10x20 mae skipped: perfect net fails (0.00913628, limit 0.00866061)
- `tscrmdl` group 1: 24x48 firm skipped: perfect net fails (0.000675154, limit 0.000635634)
- `tscrmdl` group 1: 24x48 iou_mean skipped: perfect net fails (0.935441, limit 0.944932)
- `tscrmdl` group 2: 10x20 iou_mean skipped: perfect net fails (0.744334, limit 0.791706)

The rule is automatic and nobody chose a net. A group whose two seeds pass ships the seed with the lower mean error over 8×16, 16×32 and 48×96. A group that fails is trained once more as two groups of half its characters; a half that still fails is left out.

- **17 groups trained, 16 passed with both seeds.**
- **1 failed** and was trained again as 2 halves: 2 halves passed and are in the bundle, 0 failed again.
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

`neuronte_untrained(more, c)` is 0 for exactly the 179 characters in `neuronte-term-mathalpha-v1.list.txt` and 1 for every other scalar. A scalar outside the list, drawn through this file anyway, comes out blank, or as the code-made hollow box after `neuronte_set_untrained(more, 1)`. The file needs the current runtime (version 2 bundles, 128-member limit). It has 19 members. Cells are the terminal's 1:2 cell; the nets were trained and measured from 6×12 to 48×96.

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
| `tscrmdu` | 1 | 𝕃 𝕄 𝕆 𝕊 𝕋 𝕌 𝕍 𝕎 𝕏 𝕐 | **failed**; trained again as `tscrxmdu1` | 1 / 0 | 0.0096 0.0041 0.0023 | 0.934, 0.781 |
| `tscrxmdu1` | 0 | 𝕃 𝕄 𝕆 𝕊 𝕋 | passed; H64, seed 1 (a half) | 0 / 0 | 0.0119 0.0047 0.0022 | 0.899, 0.687 |
| `tscrxmdu1` | 1 | 𝕌 𝕍 𝕎 𝕏 𝕐 | passed; H64, seed 1 (a half) | 0 / 0 | 0.0077 0.0035 0.0019 | 0.990, 0.883 |
| `tscrmdl` | 0 | 𝕒 𝕓 𝕔 𝕕 𝕖 𝕗 𝕘 𝕙 | passed; H64, seed 1 | 0 / 0 | 0.0078 0.0046 0.0023 | 0.905, 0.977 |
| `tscrmdl` | 1 | 𝕚 𝕛 𝕜 𝕝 𝕞 𝕟 𝕠 𝕡 𝕢 | passed; H64, seed 1 | 0 / 0 | 0.0072 0.0048 0.0021 | 0.878, 0.820 |
| `tscrmdl` | 2 | 𝕣 𝕤 𝕥 𝕦 𝕧 𝕨 𝕩 𝕪 𝕫 | passed; H64, seed 1 | 0 / 0 | 0.0072 0.0031 0.0017 | 0.804, 0.983 |

## Speed

Not measured yet.

## Files

`neuronte-term-mathalpha-v1.nrt` (1,028,112 bytes, sha256 `87e7a32017884af98d9cb9c506b619079b058ae8dc915c93787d77b0ebd13c52`), `neuronte-term-mathalpha-v1.list.txt`, `neuronte-term-mathalpha-v1.provenance.json`, `neuronte-term-mathalpha-v1.validation.json`, and 18 group nets `neuronte-term-mathalpha-v1-SET-gN.json`. All are in `weights/SHA256SUMS`.
