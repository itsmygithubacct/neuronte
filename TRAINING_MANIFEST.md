# Training manifest

Written by `tools/training-manifest.py` from the `training` record inside
each `weights/*.json`. Do not edit by hand: run the script again.
`make test` does not run it; `python3 tools/training-manifest.py --check`
fails if this file is out of date.

## What each record holds

- **Set or drawing**: the character set in `train/glyphs.py`, or the
  drawing file a colour net was trained on.
- **Steps, seed, unlabelled weight, pen radius**: the arguments the
  trainer ran with.
- **Sources hashed**: the files whose SHA-256 the trainer stored in the
  weight file when it ran. The hashes themselves are in the weight file.
- **After training**: recorded post-training steps, each with the hash
  of its input and of the tool that made it.
- **JSON, packed**: the first 16 hex digits of the SHA-256 of the weight
  file and of its packed `.nrt`, if one is shipped. The full hashes of
  the 297 files it lists are in `weights/SHA256SUMS`. The pointer net's
  files are not in that list; theirs are in
  `weights/neuronte-pointer-v0.sha256`.

## What is not recorded

- The weight files do not record the Python, PyTorch, CUDA or GPU
  used. Where a model card under `weights/*.md` states them, the card
  is the only record.
- A training commit is recorded only for the models listed under
  *Recorded training commits*. For the others, the stored source
  hashes identify the inputs, not the commit.
- No training run has been repeated by a third party. Two seeds were
  trained by the project for the models whose `seed1` files are here.

## Weight files (93)

| Weight file | Set or drawing | Steps | Seed | Unlabelled weight | Pen radius | Sources hashed | After training | JSON | Packed |
|---|---|---:|---:|---:|---:|---|---|---|---|
| `neuronte-accent-v1.json` | accent | 20000 | 0 | 1.0 | 0.075 | `font/letters.txt`, `font/marks.txt`, `font/strokes.txt`, `train/glyphs.py`, `train/strokes.py` | - | `5b19063025433ece` | - |
| `neuronte-accent-v2.json` | accent | 40000 | 0 | 1.0 | 0.075 | `font/code-masks.txt`, `font/letters.txt`, `font/marks.txt`, `font/strokes.txt`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `b1e194cd27d436ae` | `d4e29e75333c39c8` |
| `neuronte-ascii-v0.json` | - | 20000 | 0 | 1.0 | 0.075 | `font/strokes.txt` | - | `900ebaafc6a5ba2c` | `e1d3b97811dba461` |
| `neuronte-braille-v0.json` | braille | 20000 | 0 | 1.0 | 0.075 | `train/glyphs.py`, `train/strokes.py` | - | `733bdf975abff08d` | - |
| `neuronte-draw-v2.json` | boxshade | 20000 | 1 | 1.0 | 0.075 | `train/glyphs.py`, `train/strokes.py` | - | `9d463ec642826349` | - |
| `neuronte-emoji-e0-v0.json` | emoji-0of3 | 60000 | 0 | - | 0.075 | `font/code-masks.txt`, `font/emoji-manifest.json`, `font/emoji-palette.txt`, `font/emoji.txt`, `font/icons.txt`, `train/checkpoint.py`, `train/colour.py`, `train/colour_sources.py`, `train/emoji.py`, `train/glyphs.py`, `train/strokes.py` | output_bias_calibration | `93725d293e2d8437` | `b61c16931bf31376` |
| `neuronte-emoji-e1-v0.json` | emoji-1of3 | 60000 | 0 | - | 0.075 | `font/code-masks.txt`, `font/emoji-manifest.json`, `font/emoji-palette.txt`, `font/emoji.txt`, `font/icons.txt`, `train/checkpoint.py`, `train/colour.py`, `train/colour_sources.py`, `train/emoji.py`, `train/glyphs.py`, `train/strokes.py` | output_bias_calibration | `99c45378334dcbbc` | `fc9d0124285dd0de` |
| `neuronte-emoji-e2-v0.json` | emoji-2of3 | 60000 | 0 | - | 0.075 | `font/code-masks.txt`, `font/emoji-manifest.json`, `font/emoji-palette.txt`, `font/emoji.txt`, `font/icons.txt`, `train/checkpoint.py`, `train/colour.py`, `train/colour_sources.py`, `train/emoji.py`, `train/glyphs.py`, `train/strokes.py` | coverage_calibration | `ef0516991a822458` | `ddfee63f01e6feea` |
| `neuronte-flame-v0.json` | flame | 20000 | 0 | - | 0.075 | `font/flame-palette.txt`, `font/flame.txt`, `train/colour.py` | - | `edd99af5f3d8b995` | `55a306ee5b9165ca` |
| `neuronte-full-v2.json` | full | 20000 | 0 | 1.0 | 0.075 | `font/letters.txt`, `font/marks.txt`, `font/strokes.txt`, `font/symbols.txt`, `train/glyphs.py`, `train/strokes.py` | - | `85765c219b1b6185` | `4a74401d9ad9c6f9` |
| `neuronte-full-v3.json` | full | 40000 | 1 | 1.0 | 0.075 | `font/code-masks.txt`, `font/letters.txt`, `font/marks.txt`, `font/strokes.txt`, `font/symbols.txt`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `87ae8ff669348d00` | `b127e91ebf6891ea` |
| `neuronte-gate-v3.json` | - | 3000 | 0 | - | - | `Blocks-16.0.0.txt` | - | `9568acb86ef860d7` | - |
| `neuronte-gate-v4.json` | - | 6000 | 0 | - | - | `Blocks-16.0.0.txt` | - | `177bb8eb77ce412b` | - |
| `neuronte-icon-v1.json` | icons | 40000 | 0 | - | 0.075 | `font/code-masks.txt`, `font/icons.txt`, `font/palette.txt`, `train/colour.py`, `train/colour_sources.py`, `train/glyphs.py`, `train/strokes.py` | postprocessing | `82d7d526f5160b2c` | `1c2023a5f7af300b` |
| `neuronte-pixel-v1.json` | pixel | 20000 | 0 | 1.0 | 0.075 | `font/octants.txt`, `train/glyphs.py`, `train/strokes.py` | - | `4c061fdba3c24364` | - |
| `neuronte-pointer-v0.json` | pointer | 20000 | 0 | - | 0.075 | `font/code-masks.txt`, `font/pointer-palette.txt`, `font/pointer.txt`, `train/checkpoint.py`, `train/colour.py`, `train/colour_sources.py`, `train/glyphs.py`, `train/strokes.py` | coverage_calibration | `8d7b16cd52b9f280` | `bc2bd5ed584ed1aa` |
| `neuronte-pointer-v0.raw.json` | pointer | 20000 | 0 | - | 0.075 | `font/code-masks.txt`, `font/pointer-palette.txt`, `font/pointer.txt`, `train/checkpoint.py`, `train/colour.py`, `train/colour_sources.py`, `train/glyphs.py`, `train/strokes.py` | - | `a71d34fe8da4ee52` | `ccf62db1f0a9b196` |
| `neuronte-pointer-v0.seed1.json` | pointer | 20000 | 1 | - | 0.075 | `font/code-masks.txt`, `font/pointer-palette.txt`, `font/pointer.txt`, `train/checkpoint.py`, `train/colour.py`, `train/colour_sources.py`, `train/glyphs.py`, `train/strokes.py` | coverage_calibration | `4bbddebee4793d88` | `744cceced55c62db` |
| `neuronte-pointer-v0.seed1.raw.json` | pointer | 20000 | 1 | - | 0.075 | `font/code-masks.txt`, `font/pointer-palette.txt`, `font/pointer.txt`, `train/checkpoint.py`, `train/colour.py`, `train/colour_sources.py`, `train/glyphs.py`, `train/strokes.py` | - | `97727aa8480904a0` | `51c9d08a96ab09cf` |
| `neuronte-symbol-v0.json` | symbol | 20000 | 0 | 1.0 | 0.075 | `font/symbols.txt`, `train/glyphs.py`, `train/strokes.py` | - | `981629fc7e61c49c` | - |
| `neuronte-ui-large-v0.json` | uilarge | 20000 | 0 | 0.0 | 0.046875 | `font/ui-large.txt`, `train/glyphs.py`, `train/strokes.py` | - | `2b914704f7c4b81f` | `00736e339edc6eda` |
| `neuronte-ui1-v0.json` | ui1 | 20000 | 0 | 0.0 | 0.55 | `font/ui-1.txt`, `train/glyphs.py`, `train/strokes.py` | - | `589a33bbdac6d0b6` | `74792e9cf615c7d1` |
| `neuronte-ui10-italic-v0.json` | ui10i | 20000 | 0 | 0.0 | 0.05500000000000001 | `font/ui-10-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `df1ae419c09ceb7c` | `f734c7bc51cd18fe` |
| `neuronte-ui10-v0.json` | ui10 | 20000 | 0 | 0.0 | 0.05500000000000001 | `font/ui-10.txt`, `train/glyphs.py`, `train/strokes.py` | - | `879c999b3cbe9193` | `936d0a0ad2f2f37f` |
| `neuronte-ui11-italic-v0.json` | ui11i | 20000 | 0 | 0.0 | 0.05 | `font/ui-11-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `83a23f119307552c` | `77e3885eb8a19958` |
| `neuronte-ui11-v0.json` | ui11 | 20000 | 0 | 0.0 | 0.05 | `font/ui-11.txt`, `train/glyphs.py`, `train/strokes.py` | - | `d43dbaefc905537a` | `6a3996276b0258a2` |
| `neuronte-ui12-italic-v0.json` | ui12i | 20000 | 0 | 0.0 | 0.04583333333333334 | `font/ui-12-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `af00449224a7cba3` | `30f66e973afa2bb1` |
| `neuronte-ui12-v0.json` | ui12 | 20000 | 0 | 0.0 | 0.04583333333333334 | `font/ui-12.txt`, `train/glyphs.py`, `train/strokes.py` | - | `b60514c422497486` | `b2669c2c0ebb8973` |
| `neuronte-ui13-italic-v0.json` | ui13i | 40000 | 0 | 0.0 | 0.04230769230769231 | `font/code-masks.txt`, `font/ui-13-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `155716fd3caa35c4` | `869955a3b68402a1` |
| `neuronte-ui13-v0.json` | ui13 | 20000 | 0 | 0.0 | 0.04230769230769231 | `font/ui-13.txt`, `train/glyphs.py`, `train/strokes.py` | - | `f55243f32fd3ffbe` | `175fe343eaa422f3` |
| `neuronte-ui14-italic-v0.json` | ui14i | 20000 | 0 | 0.0 | 0.03928571428571429 | `font/ui-14-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `26d6b05442ab8667` | `bf79b824658ccf9e` |
| `neuronte-ui14-v0.json` | ui14 | 20000 | 0 | 0.0 | 0.03928571428571429 | `font/ui-14.txt`, `train/glyphs.py`, `train/strokes.py` | - | `8d834a0ccf39b0f4` | `14620f0dabedcab3` |
| `neuronte-ui15-italic-v0.json` | ui15i | 30000 | 0 | 0.0 | 0.03666666666666667 | `font/code-masks.txt`, `font/ui-15-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `351821081aef3920` | `4e391b199dd53850` |
| `neuronte-ui15-v0.json` | ui15 | 20000 | 0 | 0.0 | 0.03666666666666667 | `font/ui-15.txt`, `train/glyphs.py`, `train/strokes.py` | - | `60063a24d7208211` | `953d86b9e6665d33` |
| `neuronte-ui16-italic-v0.json` | ui16i | 20000 | 0 | 0.0 | 0.034375 | `font/ui-16-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `d36c3cbb2216a115` | `cfc333bccbdba27e` |
| `neuronte-ui16-v0.json` | ui16 | 20000 | 0 | 0.0 | 0.034375 | `font/ui-16.txt`, `train/glyphs.py`, `train/strokes.py` | - | `6012fe7229d087b0` | `ceaafc0faa879510` |
| `neuronte-ui17-italic-v0.json` | ui17i | 40000 | 0 | 0.0 | 0.03235294117647059 | `font/code-masks.txt`, `font/ui-17-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `f42317e6da947d64` | `162c17bfbe1da6eb` |
| `neuronte-ui17-v0.json` | ui17 | 20000 | 0 | 0.0 | 0.03235294117647059 | `font/ui-17.txt`, `train/glyphs.py`, `train/strokes.py` | - | `91d937cd6e67ffb4` | `9f86aa85b5fc2a4f` |
| `neuronte-ui18-italic-v0.json` | ui18i | 20000 | 0 | 0.0 | 0.030555555555555558 | `font/ui-18-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `e7289f5e47e2535f` | `92d6b2503dc15450` |
| `neuronte-ui18-v0.json` | ui18 | 20000 | 0 | 0.0 | 0.030555555555555558 | `font/ui-18.txt`, `train/glyphs.py`, `train/strokes.py` | - | `10365cf1fceeb801` | `17f3dbe77185b255` |
| `neuronte-ui19-italic-v0.json` | ui19i | 40000 | 0 | 0.0 | 0.028947368421052635 | `font/code-masks.txt`, `font/ui-19-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `409be4d17f226f1b` | `d331ceb98af99a2d` |
| `neuronte-ui19-v0.json` | ui19 | 20000 | 0 | 0.0 | 0.028947368421052635 | `font/ui-19.txt`, `train/glyphs.py`, `train/strokes.py` | - | `086e7c56a008c161` | `9f3d572ceddadd97` |
| `neuronte-ui2-v0.json` | ui2 | 20000 | 0 | 0.0 | 0.275 | `font/ui-2.txt`, `train/glyphs.py`, `train/strokes.py` | - | `0364aa3d10681e5d` | `ad58c75c80a98398` |
| `neuronte-ui20-italic-v0.json` | ui20i | 20000 | 0 | 0.0 | 0.027500000000000004 | `font/ui-20-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `62e81ce68421c18a` | `4bbbcbaf32e9cce8` |
| `neuronte-ui20-v0.json` | ui20 | 20000 | 0 | 0.0 | 0.027500000000000004 | `font/ui-20.txt`, `train/glyphs.py`, `train/strokes.py` | - | `3034a6f30fafb1be` | `67cefc574064342c` |
| `neuronte-ui21-italic-v0.json` | ui21i | 40000 | 0 | 0.0 | 0.02619047619047619 | `font/code-masks.txt`, `font/ui-21-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `5c2530b02af00007` | `c59298cbf1f746a1` |
| `neuronte-ui21-v0.json` | ui21 | 20000 | 0 | 0.0 | 0.02619047619047619 | `font/ui-21.txt`, `train/glyphs.py`, `train/strokes.py` | - | `a8c64ae84c785723` | `4a1a76f3864964c8` |
| `neuronte-ui22-italic-v0.json` | ui22i | 20000 | 0 | 0.0 | 0.025 | `font/ui-22-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `d10ea2c99741f800` | `9e2a0e23b65ecc87` |
| `neuronte-ui22-v0.json` | ui22 | 20000 | 0 | 0.0 | 0.025 | `font/ui-22.txt`, `train/glyphs.py`, `train/strokes.py` | - | `e4db5bed13c9165e` | `873f0640a1f21344` |
| `neuronte-ui23-italic-v0.json` | ui23i | 40000 | 0 | 0.0 | 0.02391304347826087 | `font/code-masks.txt`, `font/ui-23-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `d8cea77c833992a7` | `183aa15b27419388` |
| `neuronte-ui23-v0.json` | ui23 | 20000 | 0 | 0.0 | 0.02391304347826087 | `font/ui-23.txt`, `train/glyphs.py`, `train/strokes.py` | - | `d230b138fcc432bb` | `e1043934b25d2011` |
| `neuronte-ui24-italic-v0.json` | ui24i | 20000 | 0 | 0.0 | 0.02291666666666667 | `font/ui-24-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `2e44228c592e29ac` | `42e37abbf4b6ef2d` |
| `neuronte-ui24-v0.json` | ui24 | 20000 | 0 | 0.0 | 0.02291666666666667 | `font/ui-24.txt`, `train/glyphs.py`, `train/strokes.py` | - | `9b3be10293489fc6` | `ac0cb990ffe7d669` |
| `neuronte-ui25-italic-v0.json` | ui25i | 40000 | 0 | 0.0 | 0.022000000000000002 | `font/code-masks.txt`, `font/ui-25-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `c5e1099c319baef6` | `1099e5f7e154b02b` |
| `neuronte-ui25-v0.json` | ui25 | 20000 | 0 | 0.0 | 0.022000000000000002 | `font/ui-25.txt`, `train/glyphs.py`, `train/strokes.py` | - | `9ce0b5eaf9507672` | `641585e581c4c035` |
| `neuronte-ui26-italic-v0.json` | ui26i | 20000 | 0 | 0.0 | 0.021153846153846155 | `font/ui-26-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `c9c9f1eb23a41f15` | `51f4b79c302f7b2d` |
| `neuronte-ui26-v0.json` | ui26 | 20000 | 0 | 0.0 | 0.021153846153846155 | `font/ui-26.txt`, `train/glyphs.py`, `train/strokes.py` | - | `05e383f7b810713f` | `62efca43654c0715` |
| `neuronte-ui27-italic-v0.json` | ui27i | 80000 | 0 | 0.0 | 0.020370370370370372 | `font/code-masks.txt`, `font/ui-27-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | output_bias_calibration, continuation | `3b136f6c44428faa` | `c9937e96e103e3ab` |
| `neuronte-ui27-v0.json` | ui27 | 20000 | 0 | 0.0 | 0.020370370370370372 | `font/ui-27.txt`, `train/glyphs.py`, `train/strokes.py` | - | `5848c85f6a3eebf9` | `914a7cf82c797b9c` |
| `neuronte-ui28-italic-v0.json` | ui28i | 40000 | 0 | 0.0 | 0.019642857142857146 | `font/ui-28-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `ee2edb9d5f221433` | `34d9b193df479842` |
| `neuronte-ui28-v0.json` | ui28 | 20000 | 0 | 0.0 | 0.019642857142857146 | `font/ui-28.txt`, `train/glyphs.py`, `train/strokes.py` | - | `42d426e5d6e36dba` | `1a70a4006691b84c` |
| `neuronte-ui29-italic-v0.json` | ui29i | 40000 | 0 | 0.0 | 0.018965517241379314 | `font/code-masks.txt`, `font/ui-29-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `3fe4ebaea6d34ada` | `f03d6f2fc2a7d614` |
| `neuronte-ui29-v0.json` | ui29 | 20000 | 0 | 0.0 | 0.018965517241379314 | `font/ui-29.txt`, `train/glyphs.py`, `train/strokes.py` | - | `af35ed3e8aa13ba0` | `584de27ec67a2b8c` |
| `neuronte-ui3-italic-v0.json` | ui3i | 20000 | 0 | 0.0 | 0.18333333333333335 | `font/code-masks.txt`, `font/ui-3-italic.txt`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `450fbbbed42fa74e` | `804da54d358f8408` |
| `neuronte-ui3-v0.json` | ui3 | 20000 | 0 | 0.0 | 0.18333333333333335 | `font/ui-3.txt`, `train/glyphs.py`, `train/strokes.py` | - | `4194d9640c1cbd29` | `2bce8160323baf9e` |
| `neuronte-ui30-italic-v0.json` | ui30i | 20000 | 0 | 0.0 | 0.018333333333333333 | `font/ui-30-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `e9ec9cbb3be7acb3` | `abf6fda6b534268b` |
| `neuronte-ui30-v0.json` | ui30 | 20000 | 0 | 0.0 | 0.018333333333333333 | `font/ui-30.txt`, `train/glyphs.py`, `train/strokes.py` | - | `58192a67e1981f24` | `feac177645610a99` |
| `neuronte-ui31-italic-v0.json` | ui31i | 40000 | 0 | 0.0 | 0.017741935483870968 | `font/code-masks.txt`, `font/ui-31-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `c6e5c64661b01020` | `6a3b8df4aadc39e8` |
| `neuronte-ui31-v0.json` | ui31 | 20000 | 0 | 0.0 | 0.017741935483870968 | `font/ui-31.txt`, `train/glyphs.py`, `train/strokes.py` | - | `d68a9e86329f8b85` | `54396b1ea8f35b33` |
| `neuronte-ui32-italic-v0.json` | ui32i | 40000 | 0 | 0.0 | 0.0171875 | `font/ui-32-italic.txt`, `train/glyphs.py`, `train/strokes.py` | - | `ce194e9fb2c50c2f` | `e733416d94900b74` |
| `neuronte-ui32-v0.json` | ui32 | 20000 | 0 | 0.0 | 0.0171875 | `font/ui-32.txt`, `train/glyphs.py`, `train/strokes.py` | - | `3cda6726c6ff896f` | `9b20e873cb412343` |
| `neuronte-ui33-v0.json` | ui33 | 20000 | 0 | 0.0 | 0.016666666666666666 | `font/ui-33.txt`, `train/glyphs.py`, `train/strokes.py` | - | `1619a9b74e8c3a10` | `dc34f775de8e77ed` |
| `neuronte-ui34-v0.json` | ui34 | 20000 | 0 | 0.0 | 0.016176470588235296 | `font/ui-34.txt`, `train/glyphs.py`, `train/strokes.py` | - | `f33a2bde6b45f75d` | `c6c83c575eb62e9a` |
| `neuronte-ui35-v0.json` | ui35 | 20000 | 0 | 0.0 | 0.015714285714285715 | `font/ui-35.txt`, `train/glyphs.py`, `train/strokes.py` | - | `bf861cbf6a1b8711` | `bc4014c9fa05b4ea` |
| `neuronte-ui36-v0.json` | ui36 | 20000 | 0 | 0.0 | 0.015277777777777779 | `font/ui-36.txt`, `train/glyphs.py`, `train/strokes.py` | - | `d2a3f55b130f66a3` | `82d2980f1716e670` |
| `neuronte-ui37-v0.json` | ui37 | 20000 | 0 | 0.0 | 0.014864864864864866 | `font/ui-37.txt`, `train/glyphs.py`, `train/strokes.py` | - | `36025b20b21e51aa` | `bf74f315a689e0b0` |
| `neuronte-ui38-v0.json` | ui38 | 20000 | 0 | 0.0 | 0.014473684210526317 | `font/ui-38.txt`, `train/glyphs.py`, `train/strokes.py` | - | `6833cb8432c77932` | `1298c7a955bd95f7` |
| `neuronte-ui39-v0.json` | ui39 | 20000 | 0 | 0.0 | 0.014102564102564105 | `font/ui-39.txt`, `train/glyphs.py`, `train/strokes.py` | - | `f52ac45604546d59` | `e01ba7df70c50c94` |
| `neuronte-ui4-italic-v0.json` | ui4i | 20000 | 0 | 0.0 | 0.1375 | `font/code-masks.txt`, `font/ui-4-italic.txt`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `4abf17748c7c03b2` | `9881badd3945777c` |
| `neuronte-ui4-v0.json` | ui4 | 20000 | 0 | 0.0 | 0.1375 | `font/ui-4.txt`, `train/glyphs.py`, `train/strokes.py` | - | `0bbf7162ede883ee` | `40965625cb1262f7` |
| `neuronte-ui43-v0.json` | ui43 | 20000 | 0 | 0.0 | 0.012790697674418606 | `font/ui-43.txt`, `train/glyphs.py`, `train/strokes.py` | - | `0407c2c3f9a60504` | `aaa608d9d6e413cb` |
| `neuronte-ui5-italic-v0.json` | ui5i | 20000 | 0 | 0.0 | 0.11000000000000001 | `font/code-masks.txt`, `font/ui-5-italic.txt`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `785e2d3008a7bdbb` | `5abdd42373166c9b` |
| `neuronte-ui5-v0.json` | ui5 | 20000 | 0 | 0.0 | 0.11000000000000001 | `font/ui-5.txt`, `train/glyphs.py`, `train/strokes.py` | - | `583738c2405a7681` | `bbb196a8190c9292` |
| `neuronte-ui6-italic-v0.json` | ui6i | 20000 | 0 | 0.0 | 0.09166666666666667 | `font/code-masks.txt`, `font/ui-6-italic.txt`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `f82e13ad4edb9f76` | `741ce998a565adbf` |
| `neuronte-ui6-v0.json` | ui6 | 20000 | 0 | 0.0 | 0.09166666666666667 | `font/ui-6.txt`, `train/glyphs.py`, `train/strokes.py` | - | `72a44ab04a02e227` | `dfeba6386a77ec55` |
| `neuronte-ui7-italic-v0.json` | ui7i | 20000 | 0 | 0.0 | 0.07857142857142858 | `font/code-masks.txt`, `font/ui-7-italic.txt`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `981a6ace9244f55c` | `4e2bf301b7d2cccc` |
| `neuronte-ui7-v0.json` | ui7 | 20000 | 0 | 0.0 | 0.07857142857142858 | `font/ui-7.txt`, `train/glyphs.py`, `train/strokes.py` | - | `a78748a6914f7d28` | `43cfeefab132712a` |
| `neuronte-ui8-italic-v0.json` | ui8i | 40000 | 0 | 0.0 | 0.06875 | `font/code-masks.txt`, `font/ui-8-italic.txt`, `train/checkpoint.py`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `980498d0708a888c` | `10acbd6c6292716c` |
| `neuronte-ui8-v0.json` | ui8 | 20000 | 0 | 0.0 | 0.06875 | `font/ui-8.txt`, `train/glyphs.py`, `train/strokes.py` | - | `4ae8d7e4481609ff` | `c0e6b08e7d19ece7` |
| `neuronte-ui9-italic-v0.json` | ui9i | 20000 | 0 | 0.0 | 0.061111111111111116 | `font/code-masks.txt`, `font/ui-9-italic.txt`, `train/glyphs.py`, `train/strokes.py`, `train/train.py` | - | `7e94a510fbebf07e` | `9b09fcbfc2e8ca19` |
| `neuronte-ui9-v0.json` | ui9 | 20000 | 0 | 0.0 | 0.061111111111111116 | `font/ui-9.txt`, `train/glyphs.py`, `train/strokes.py` | - | `eb558596d250d630` | `a5adfabd05c69aaa` |
| `neuronte-video-ascii-v0.json` | - | 20000 | 0 | 1.0 | 0.075 | `font/strokes.txt` | - | `8a388678b2c57dcd` | - |
| `neuronte-video-pixel-v1.json` | pixel | 20000 | 0 | 1.0 | 0.075 | `font/octants.txt`, `train/glyphs.py`, `train/strokes.py` | - | `ccafc4a0207bfbb8` | - |

## Recorded training commits

| Validation record | Training commit | Selected seed |
|---|---|---:|
| `neuronte-full-v3.validation.json` | `d05f14f6c0d0e6ed2077d6007b4a5f588e4ca802` | 1 |
| `neuronte-split-v5.validation.json` | `d05f14f6c0d0e6ed2077d6007b4a5f588e4ca802` | 0 |

## Accent decomposition experiments

`train/decompose.py --expert accent` uses the original 318-label teacher:
203 Latin and spacing marks, 49 Greek letters, and 66 Russian letters.
Sparse scalars are mapped explicitly into teacher rows. The original accent
model has H256 and 155,137 parameters.

| Design | Hidden widths | New parameters | Label partition |
|---|---|---:|---|
| Four repertoire groups | 4 x 64 | 56,836 | Latin 101, Latin 102, Greek 49, Russian 66 |
| Four spatial tiles | 4 x 64 | 56,836 | All 318 in each tile of a 2x2 grid |
| Eight repertoire groups | 8 x 32 | 40,456 | Four Latin groups, two Greek, two Russian |
| Eight spatial tiles | 8 x 32 | 40,456 | All 318 in each tile of a 2x4 grid |
| Three scripts | 128,64,64 | 73,219 | Latin 203, Greek 49, Russian 66 |

These are experimental recipes, not replacements for `neuronte-split-v5.nrt`.
The packager retains the original six experts and original gate rows, clears
only the original accent table labels, and appends the new accent members.
New constant gate logits cannot win against the original gate, so unknown
scalars retain their original routing and coverage. Consequently the new
parameters are **added** to the full bundle. Smaller per-glyph inference does
not imply a smaller bundle. Spatial members use the shared version 6 format.

Prepare and train the uniform-width comparisons with seeds 0 and 1, the original
40,000-step Adam/cosine schedule, and unknown regularization 1:

```sh
python3 train/decompose.py prepare experiment --expert accent
python3 train/decompose.py train experiment --expert accent \
    --mode repertoire --parts 4 --seeds 0,1 --steps 40000 \
    --batch-models 8 --compile --checkpoint-every 1000
```

Use `--mode spatial` for spatial tiles. For eight parts use
`--parts 8 --batch-models 16`. Compiled CUDA training needs a C compiler.
Checkpoints bind teacher and trainer hashes, full training schedule, model
inventory, optimizer and RNG state; `--resume` refuses different identities.
The two-seed uniform comparisons were trained from source `70b8d87`.

The three-script follow-up uses source `90ebb36`. Train it in separate
experiment directories for `--unlabelled 1` and `--unlabelled 0`, reusing the
identical teacher. Each directory needs four homogeneous-width batches:

```sh
python3 train/decompose.py train experiment --expert accent \
    --mode repertoire --parts 3 --seeds 0,1 --steps 40000 \
    --start 0 --batch-models 1 --unlabelled 0 --compile
```

Repeat with `(start,batch-models)` of `(1,2)`, `(3,1)`, and `(4,2)`.
Members are ordered by seed, then Latin/Greek/Russian. Mixed-width batches
are rejected. The regularization 0 follow-up is valid only with preserved
original fallback; it does not train replacement unknown-glyph behavior.

Package each seed under a distinct directory and score through the native API:

```sh
python3 tools/pack-accent-experiment.py experiment package \
    --mode repertoire --parts 3 --seed 0
python3 tools/accent-quality.py --library build/libneuronte.so \
    --model weights/neuronte-split-v5.nrt --teacher experiment --out baseline
python3 tools/accent-quality.py --library build/libneuronte.so \
    --model package/neuronte-accent-next-repertoire3-s0.nrt \
    --teacher experiment --baseline baseline/quality.json --out candidate
```

Run native quality and performance under a host-wide benchmark lock. The
quality output records model/library/teacher/reference hashes, raw coverage,
per-glyph metrics and per-script gates. Its `complete` field must be true.
A failed quality gate remains a valid experimental result and does not cause
a nonzero process exit; inspect `passed`. Incomplete evaluations must not be
used as final evidence. The following gates were fixed before candidate scoring:

- Each script: MAE no more than baseline+.0015, pixel-error p99 no more than
  baseline+.02, firm-error fraction no more than baseline+.0005, and mean
  binary IoU no less than baseline-.005.
- Each glyph: MAE no more than baseline+.01, IoU no less than baseline-.05,
  no newly lost glyph and no loss of a baseline-compatible nearest identity.
- Exactly tied teacher identities count as compatible; ambiguity is reported.
  Binary exactness is descriptive because the antialiased baseline is not
  binary-perfect.

Production qualification requires **both seeds**, all three standard sizes
8x16/16x32/48x96, and small/odd/boundary cells:
1x1,1x2,2x3,3x5,5x9,7x13,9x17,17x35,23x46,23x47,24x48,25x49,25x50,
16x16,12x40,33x61. Automatic sampling changes from 2 to 1 at width 24.
The video consumer uses 1 sample per axis; compare `--samples 1` against a
separately calibrated S1 baseline. The evaluator rejects mismatched sampling.
The tiny-cell baseline itself loses identities, so gates are relative to its
measured limits. Whole-glyph cache, unaffected expert/unknown fallback and
consumer API checks are additional requirements.
