# Third-party notices

Neuronte's core library has no third-party code in it. It needs a C11 compiler
and the C maths library. The separate, optional media library includes
adaptations from FFmpeg, as described below. This file lists the third-party data and tools
the project uses and whether each one is redistributed here.

## Redistributed in this repository

### FFmpeg 7.1 command-line video handling

`src/media.c` adapts the timestamp, seeking, filtering and constant-frame-rate
handling in FFmpeg 7.1's `fftools/ffmpeg_demux.c`, `ffmpeg_dec.c`,
`ffmpeg_filter.c`, `ffmpeg_mux_init.c` and `ffmpeg_opt.c`. Each adapted step
names its upstream function. Neuronte exposes these steps through a decoding
API with one video stream and a bounded frame queue, and declines unsupported
input behaviours. This file is under LGPL-2.1-or-later, separately from the
MIT core renderer and weights.

Upstream source: <https://ffmpeg.org/releases/ffmpeg-7.1.tar.xz>.
The upstream files carry this notice:

> FFmpeg is free software; you can redistribute it and/or
> modify it under the terms of the GNU Lesser General Public
> License as published by the Free Software Foundation; either
> version 2.1 of the License, or (at your option) any later version.
>
> FFmpeg is distributed in the hope that it will be useful,
> but WITHOUT ANY WARRANTY; without even the implied warranty of
> MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
> Lesser General Public License for more details.
>
> You should have received a copy of the GNU Lesser General Public
> License along with FFmpeg; if not, write to the Free Software
> Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

The full licence is in [LICENSES/FFmpeg-LGPL-2.1-or-later.txt](LICENSES/FFmpeg-LGPL-2.1-or-later.txt).
`libneuronte-media.so` dynamically links the separately installed FFmpeg
libraries. Those libraries and the `ffmpeg` command are not vendored here;
their applicable licence depends on the installed FFmpeg build and its
enabled components. The core `libneuronte.so` does not link them.

### Unicode Character Database 16.0.0 (derived data)

`font/octants.txt` is made by `train/mosaics.py` from `UnicodeData.txt`,
version 16.0.0, SHA-256
`ff58e5823bd095166564a006e47d111130813dcf8bf234ef79fa51a870edb48f`. It
holds the code points U+1CD00..U+1CDE5 and the cells each one fills,
which `train/mosaics.py` reads from the character names.

`train/gate.py` reads `Blocks.txt`, version 16.0.0, SHA-256
`f3907b395d410f1b97342292ca6bc83dd12eb4b205f2a0c48efdef99e517d7b0`, to
choose training samples for the router's gate. `Blocks.txt` itself is
not in this repository. The range table the router uses is written by
this project.

The Unicode data files are used under the Unicode License V3:

```
UNICODE LICENSE V3

COPYRIGHT AND PERMISSION NOTICE

Copyright © 1991-2024 Unicode, Inc.

NOTICE TO USER: Carefully read the following legal agreement. BY
DOWNLOADING, INSTALLING, COPYING OR OTHERWISE USING DATA FILES, AND/OR
SOFTWARE, YOU UNEQUIVOCALLY ACCEPT, AND AGREE TO BE BOUND BY, ALL OF THE
TERMS AND CONDITIONS OF THIS AGREEMENT. IF YOU DO NOT AGREE, DO NOT
DOWNLOAD, INSTALL, COPY, DISTRIBUTE OR USE THE DATA FILES OR SOFTWARE.

Permission is hereby granted, free of charge, to any person obtaining a
copy of data files and any associated documentation (the "Data Files") or
software and any associated documentation (the "Software") to deal in the
Data Files or Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, and/or sell
copies of the Data Files or Software, and to permit persons to whom the
Data Files or Software are furnished to do so, provided that either (a)
this copyright and permission notice appear with all copies of the Data
Files or Software, or (b) this copyright and permission notice appear in
associated Documentation.

THE DATA FILES AND SOFTWARE ARE PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF
THIRD PARTY RIGHTS.

IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS INCLUDED IN THIS NOTICE
BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT OR CONSEQUENTIAL DAMAGES,
OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THE DATA
FILES OR SOFTWARE.

Except as contained in this notice, the name of a copyright holder shall
not be used in advertising or otherwise to promote the sale, use or other
dealings in these Data Files or Software without prior written
authorization of the copyright holder.
```

Unicode is a registered trademark of Unicode, Inc. This project is not
affiliated with or endorsed by Unicode, Inc.

## Used but not redistributed

Nothing below is copied into this repository or into a weight file. Each
is installed separately by whoever builds, trains or tests.

| Component | Used by | Its licence |
|---|---|---|
| Python and its `unicodedata` module | Training, tools, tests. `unicodedata` supplies character names and decompositions | PSF License; the module's data is under the Unicode licence |
| PyTorch | `train/train.py`, `train/colour.py`, `train/gate.py` and the calibration scripts | BSD-3-Clause |
| NumPy | Training, and the reference evaluation in `make test` | BSD-3-Clause |
| SciPy | The video trainer, its helpers and its test | BSD-3-Clause |
| Pillow | Preview and video tools, to read and write images | MIT-CMU |
| zlib | The terminal demos only | zlib licence |
| kitty-framebuffer | The terminal demos only; compiled from its own source tree at build time | MIT |

The licences in this table are as the projects state them. Check each
project's own licence file for the version you install.

## Not used

No font, icon font, emoji font or image set is an input to any drawing or
weight file here. See [PROVENANCE.md](PROVENANCE.md).
