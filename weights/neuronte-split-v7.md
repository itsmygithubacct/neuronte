# split-v7: tiled Braille and ASCII character groups

`neuronte-split-v7.nrt` combines two qualified experts in one font:

- Braille, U+2800..U+28FF, is drawn by `neuronte-braille-v1`, the tiled expert
  of `neuronte-split-v6` ([recipe and validation](neuronte-braille-v1.md)).
- Printable ASCII, U+0020..U+007E, is drawn by the four H64 character-group
  nets of `neuronte-ascii-groups-v1`
  ([recipe and validation](neuronte-ascii-next.md)).

It is `train/known_bundle.py` applied to split-v6, with the group nets as
known-only replacements for expert 0:

```sh
python3 train/known_bundle.py weights/neuronte-split-v6.nrt weights/neuronte-split-v7.nrt \
  weights/neuronte-ascii-groups-v1-p0.json weights/neuronte-ascii-groups-v1-p1.json \
  weights/neuronte-ascii-groups-v1-p2.json weights/neuronte-ascii-groups-v1-p3.json --expert 0
```

`neuronte-split-v7.provenance.json` is that command's record. split-v6's six
members are kept byte for byte, including the original ASCII expert. The gate
still chooses that expert for characters outside the range table, so unknown
characters draw exactly as in split-v6. The four group members and their
constant, suppressed gate outputs are appended, and only the printable ASCII
table entries are reassigned to them. The result is also exactly
`neuronte-split-ascii-groups-v1` with its Braille member replaced by
`neuronte-braille-v1`: the composition commutes.

| File | Members | Net parameters | Bytes | SHA256 |
|---|---:|---:|---:|---|
| `neuronte-split-v6.nrt` | 6 | 384,232 | 1,539,388 | `bbfa988a91f2214addbc89c291847da83387363327a6405a63d72873534b648a` |
| `neuronte-split-v7.nrt` | 10 | 441,068 | 1,768,128 | `b6e8ad1ac6fbc2370fbacc14727180954b4fc6d23cf7c0506a93116853f92f1f` |

Net parameters are counted as for split-v6: its 384,232 plus four nets of
14,209 (90→64→64→64→1). The appended gate outputs add 132 constant floats.
Ten members fit the 16-member limit of the earlier runtime as well as the
current 128.

## Checks

`make test-split-v7` runs:

- `tests/check_split_v7.py` checks bytes, routes and pixels against both
  parents.
  - The file is rebuilt byte for byte from split-v6 and the group JSON.
  - The first six members are split-v6's.
  - The counts, ranges, gate and members match the ASCII package except
    member 5.
  - Every scalar 0..0x10FFFF and 0xFFFFFFFF routes as in split-v6, except
    printable ASCII, which goes to its group.
  - Every other range scalar draws split-v6's pixels at 5x10, 8x16 and
    16x32, and so do the ASCII release check's representative scalars.
  - ASCII draws the qualified direct file's pixels at all 19 qualification
    sizes, so the teacher gates of `tests/check_ascii_next.py` carry over.
  - Planted defects at each stage fail it.
- `tests/check_braille_v1.py` on split-v7 against the ASCII package checks
  the Braille member. All 256 patterns must be binary-exact at three sizes,
  within the selection's error budget.
- `test_api` with `--full --accent --pixel`.

## Speed

Measured as a whole bundle with kilix-bench `e21e5cd`, against split-v5,
split-v6 and the ASCII package (`neuronte-split-ascii-groups-v1`) in the same
runs. Two x86 hosts, an Intel i7-10700F and an i7-6820HQ, each on one pinned
core with the benchmark lock held for the whole run. One warmup and ten
measured rounds, a fresh process per job, rounds shuffled. ARM was not
measured for this bundle, and no figure here is carried over from the ASCII or
Braille campaigns.

Uncached `neuronte_coverage()`, geometric mean over cells of (other bundle /
split-v7); above 1 means split-v7 is faster. Figures are i7-10700F /
i7-6820HQ.

| Corpus | Cells | split-v5 | split-v6 | ASCII package |
|---|---|---:|---:|---:|
| Printable ASCII (95) | 8x16, 16x32, 48x96 | 2.25 / 2.22 | 2.26 / 2.23 | 1.00 / 1.00 |
| Braille (256) | 8x16, 16x32, 25x49, 48x96 | 11.47 / 11.49 | 1.00 / 1.00 | 11.61 / 11.60 |

Median µs per glyph at 16x32, uncached coverage:

| CPU | ASCII, split-v6 | ASCII, split-v7 | Braille, split-v6 | Braille, split-v7 |
|---|---:|---:|---:|---:|
| i7-10700F | 2,040.5 | 899.8 | 32.5 | 32.8 |
| i7-6820HQ | 2,740.8 | 1,222.8 | 44.1 | 44.1 |

Pixels are identical on both hosts. ASCII draws exactly as the ASCII package,
and Braille exactly as split-v6, so combining the experts costs neither any
drawing speed. A primed (cached) draw costs the same for all four bundles.

Opening (one model open, including the first 8x16 buffer) and table routing
are the only added costs:

| CPU | Open ms, split-v6 | Open ms, split-v7 | Route ns, split-v6 | Route ns, split-v7 |
|---|---:|---:|---:|---:|
| i7-10700F | 1.69–1.71 | 1.78–1.89 | 6.59–6.73 | 7.01–7.14 |
| i7-6820HQ | 2.57–2.58 | 2.84–2.86 | 11.39–12.04 | 11.90–12.59 |

Each range spans the two corpus runs. The extra opening time, paid once per
process, matches the ASCII package; the four appended members are the likely
cause.

## Status

Not a default. The video player still draws full mode with split-v6, and no
release pins this file.
