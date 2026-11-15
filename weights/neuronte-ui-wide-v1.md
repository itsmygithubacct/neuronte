# Faster v1 desktop faces: ui32, ui27-italic, ui31, ui31-italic, ui32-italic

Five desktop faces with some of the widest v0 nets (768 for ui32, 512 for
the other four) now also come as v1 drawing files. Each one is a single bundle
of 8 small nets with the same advance table as v0. Each net draws one
contiguous group of 12 of the face's 96 characters (U+0020..U+007E and
U+2026), and the bundle routes every character to the net for its group.
Both training seeds reproduce every letter exactly, regular and bold, at
the native em. Drawing the whole face, which is what a desktop does when it
builds its letter cells, is 6 to 18 times faster than v0.

The -v0 files are unchanged and are still what the installer and Kilix 95
load. The v1 files have new names, so nothing that binds a v0 file by name
or hash sees a change.

| File | Face | Nets | Width | Parameters | Bytes | v0 width, bytes |
|---|---|---:|---:|---:|---:|---|
| `neuronte-ui32-v1` | 32 px | 8 | 96 | 219,656 | 881,256 | 768, 5,008,400 |
| `neuronte-ui27-italic-v1` | 27 px italic | 8 | 96 | 219,656 | 881,256 | 512, 2,290,704 |
| `neuronte-ui31-v1` | 31 px | 8 | 96 | 219,656 | 881,256 | 512, 2,290,704 |
| `neuronte-ui31-italic-v1` | 31 px italic | 8 | 128 | 358,408 | 1,436,264 | 512, 2,290,704 |
| `neuronte-ui32-italic-v1` | 32 px italic | 8 | 128 | 358,408 | 1,436,264 | 512, 2,290,704 |

Every net is the usual distance MLP, 90 → H → H → H → 1, with 2H² + 94H + 1
parameters. The files:

- `neuronte-<face>-v1.nrt`: the packed drawing file, seed 0.
- `neuronte-<face>-v1-p0.json` … `-p7.json`: the seed-0 nets, one per group.
- `neuronte-<face>-v1-p<i>.seed1.json`: the seed-1 nets.
- `.scores.json` files beside each net.

Pack a face again with `make pack-faces-wide-v1`, which uses
`train/pack.py --drawing-bundle`. The runtime needs the drawing-file
routing added with these faces: a drawing file may hold one bundle as its
only member with nets.

## Training

The recipe is the unchanged v0 recipe from `train/train.py`, so pen, grid,
tau, optimiser and schedule are as v0, with `--unlabelled 0`. Two things
differ:

- `--labelled` restricts each net to its group, for example
  `U+0020..U+002B`.
- Every net trains for 40,000 steps.

Groups are the face's 96 characters in code-point order, cut into 8 runs of
12. Seeds 0 and 1 use the identical recipe. Neither seed was edited after
training: no calibration and no member swapping.

## Gates, declared before training

- **G1 (exact):** for each seed, `tests/check_reference.py --drawing-bundle`
  must report 192 binary letters, each exactly its drawing at the native
  em. Advances must be exact, C and NumPy coverage within 1e-3, routes as
  the table says, and the packed bytes equal to the packer's output.
- **G2:** a recipe counts only if both seeds pass G1.
- **G3:** among recipes that pass G2, a replacement must beat v0 for both
  seeds on both x86 hosts, by median uncached whole-face draw. The fastest
  by geometric mean is chosen; otherwise v0 is kept.

`make test` runs `test-faces-wide-v1`, which checks both seeds of every face.

Recipes trained and checked: 1 net (H512 at 60,000 steps for ui32, H384 at
80,000 for the others), 2 × H384, 4 × H256, 4 × H192, 8 × H128 and 8 × H96,
plus 16 × H64 for ui32. Failures at G1, with weight 0 regular and weight 1
bold:

- **ui32, 16 × H64:** seed 1 has 1 wrong pixel in `8`, regular.
- **ui31-italic, 4 × H192:** seed 1 has 1 wrong pixel in `W`.
- **ui31-italic, 8 × H96:** both seeds have 1 or 2 wrong pixels in `8`,
  `@`, `w`, `M` or `\`.
- **ui32-italic, 8 × H96:** seed 1 has 1 wrong pixel each in `@` and `b`.

Every other recipe passed for both seeds. Each face's chosen recipe is its
fastest one that passes G2.

## Speed

Measured with kilix-bench 0.2.3, using its face experiment
(`--face-experiment`). One warmup and 10 rounds, median, pinned to one CPU,
powersave governor, shuffled order, and a fresh process and handle for
every job. The library was built with `-O3` from the commit that adds these
faces' runtime.

Each case calls the face as Kilix 95 does. For every character it calls
`neuronte_text_width` for regular and bold, then `neuronte_draw_text` of
the regular letter at the native em, with binary drawing on.

- **Cold draw:** a fresh handle draws all 96 characters once. This is the
  cost a desktop pays at start-up for each face it has not cached.
- **Warm draw:** the same characters with the runtime cache primed.
- **Open:** opening the file.

The benchmark also checked every case against a float64 reference and the
face's own pixels; all were exact.

Cold whole-face draw, ms per face (v1 shows seed 0 / seed 1):

| Face | CPU | v0 | v1 | Faster by | Open v0 → v1, ms | Warm draw v0 → v1, µs |
|---|---|---:|---:|---:|---|---|
| ui32 | Intel i7-10700F | 2814 | 156 / 165 | 17–18× | 5.5 → 0.8 | 527 → 521 / 537 |
| ui32 | Intel i7-6820HQ | 3529 | 211 / 223 | 16–17× | 7.7 → 1.3 | 763 → 764 / 764 |
| ui27-italic | Intel i7-10700F | 1093 | 117 / 126 | 8.7–9.4× | 3.3 → 0.8 | 403 → 400 / 402 |
| ui27-italic | Intel i7-6820HQ | 1384 | 158 / 172 | 8.1–8.7× | 4.8 → 1.3 | 581 → 585 / 586 |
| ui31 | Intel i7-10700F | 1702 | 146 / 150 | 11.3–11.6× | 3.2 → 0.8 | 498 → 497 / 497 |
| ui31 | Intel i7-6820HQ | 2140 | 197 / 204 | 10.5–10.8× | 4.7 → 1.3 | 721 → 756 / 724 |
| ui31-italic | Intel i7-10700F | 1417 | 213 / 208 | 6.7–6.8× | 3.2 → 1.7 / 1.6 | 505 → 508 / 506 |
| ui31-italic | Intel i7-6820HQ | 1802 | 289 / 284 | 6.2–6.3× | 4.7 → 2.4 | 730 → 733 / 733 |
| ui32-italic | Intel i7-10700F | 1450 | 221 / 219 | 6.6× | 3.3 → 1.6 / 1.7 | 531 → 534 / 529 |
| ui32-italic | Intel i7-6820HQ | 1845 | 301 / 297 | 6.1–6.2× | 4.1 → 2.4 | 771 → 774 / 774 |

Once the cache is primed, drawing is the same speed as v0, because it no
longer runs a net. All the gain is at the cold draw, which happens when the
OS is provisioned, after a Neuronte library change, and for any face or
size not yet cached.

## Limits

- Exact at each face's native em, with binary drawing, for its 96
  characters only.
- Like v0, the nets were trained with `--unlabelled 0`. What they draw for
  other scalars is not trained; the consumer draws only the scalars in the
  advance table, and the rest fall back to `?`.
- Drawn blended or at another size, a v1 face is not held to any gate and
  may differ from v0.
