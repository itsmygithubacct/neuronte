# split-v7-symbol-v1: tiled Braille, ASCII character groups and symbol groups

`neuronte-split-v7-symbol-v1.nrt` combines three qualified expert replacements
in one font:

- Braille, U+2800..U+28FF: `neuronte-braille-v1`, the tiled expert of
  split-v6 ([recipe and validation](neuronte-braille-v1.md)).
- Printable ASCII, U+0020..U+007E: the four H64 character-group nets of
  `neuronte-ascii-groups-v1` ([recipe and validation](neuronte-ascii-next.md)).
- The 49 symbols of `neuronte-symbol-v0`: the four width-32 character-group
  nets of `neuronte-symbol-v1` ([recipe, gates and timing](neuronte-symbol-v1.md)).

It is `train/known_bundle.py` applied to split-v7, with the symbol groups as
known-only replacements for expert 2:

```sh
python3 train/known_bundle.py weights/neuronte-split-v7.nrt weights/neuronte-split-v7-symbol-v1.nrt \
  weights/neuronte-symbol-v1-g0.json weights/neuronte-symbol-v1-g1.json \
  weights/neuronte-symbol-v1-g2.json weights/neuronte-symbol-v1-g3.json --expert 2
```

`neuronte-split-v7-symbol-v1.provenance.json` is that command's record.
split-v7's ten members are kept byte for byte, including the original ASCII
and symbol experts. The gate still chooses those for characters outside the
range table, so unknown characters draw exactly as in split-v7 (and split-v6).
The four symbol members and their constant, suppressed gate outputs are
appended, and only the 49 symbol table entries are reassigned to them.

| File | Members | Net parameters | Bytes | SHA256 |
|---|---:|---:|---:|---|
| `neuronte-split-v7.nrt` | 10 | 441,068 | 1,768,128 | `b6e8ad1ac6fbc2370fbacc14727180954b4fc6d23cf7c0506a93116853f92f1f` |
| `neuronte-split-v7-symbol-v1.nrt` | 14 | 461,296 | 1,850,412 | `b98a5b05b597aa5198a26c511460f819540b3d38abf38b6961e6552dcb22ed6a` |

Net parameters are split-v7's plus four nets of 5,057 (90→32→32→32→1). The
appended gate outputs add 132 constant floats. Like split-v7, the file is
larger than the bundle it extends, because every original expert stays for
unknown characters; a smaller active symbol model does not reduce opening
cost.

## Checks

`make test-split-v7-symbol` runs:

- `tests/check_split_v7_symbol.py`:
  - The file is rebuilt byte for byte from split-v7 and the group JSON.
  - Every scalar 0..0x10FFFF and 0xFFFFFFFF routes as in split-v7, except
    the 49 symbols, which go to the group trained on them.
  - Each symbol's coverage equals its group net alone and
    `neuronte-split-v5-symbol-v1`, bit for bit, at 13 cells from 1×2 to
    64×128 (including 3×6, 5×9, 7×13 and widths 23, 24 and 25), so the
    symbol-v1 quality gates carry over unchanged.
  - Every other labelled scalar (Braille, ASCII, box drawing, accents,
    pixel) and about 3,000 untrained scalars cover exactly as in split-v7.
  - A first draw equals a cached redraw.
  - A planted defect (group 0's seed-1 net) is detected.
- `tests/check_split_v7.py` and `tests/check_braille_v1.py` still gate
  split-v7 itself, whose Braille and ASCII members and routes this file
  shares exactly.
- `test_api` with `--full --accent --pixel`.

## Status

Not a default; no release pins it. The video player still draws full mode
with split-v6.
