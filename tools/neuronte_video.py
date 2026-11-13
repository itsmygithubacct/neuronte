"""Neuronte video cells. RGB input/output is uint8, row-major, without padding.

TwoInk fits bounded RGB colours by exact least squares for every candidate.
MultiInk uses three cached neural masks, with eight Gray-labelled colours.
No coverage thresholding is performed. See tools/neuronte-video.md.
"""
from pathlib import Path
import ctypes as C
import json
import os
import sys
import struct
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'train'))
import glyphs


class NeuralMasks:
    def __init__(self, weights=None, library=None):
        self.lib = C.CDLL(str(library or ROOT / 'build/libneuronte.so'))
        self.lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(C.c_void_p)]
        self.lib.neuronte_close.argtypes = [C.c_void_p]
        self.lib.neuronte_coverage.argtypes = [C.c_void_p, C.c_uint32, C.c_int, C.c_int, C.c_int, C.POINTER(C.c_float)]
        self.handle = C.c_void_p()
        path = Path(weights or ROOT / 'weights/neuronte-split-v5.nrt')
        if self.lib.neuronte_open_file(str(path).encode(), C.byref(self.handle)):
            raise ValueError(f'cannot load {path}')

    def mask(self, cp, width, height, samples=1):
        a = np.empty((height, width), np.float32)
        rc = self.lib.neuronte_coverage(self.handle, cp, width, height, samples, a.ctypes.data_as(C.POINTER(C.c_float)))
        if rc:
            raise ValueError(f'coverage failed: {rc}')
        return a

    def close(self):
        if self.handle:
            self.lib.neuronte_close(self.handle)
            self.handle = C.c_void_p()

    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def octant_characters():
    """All 256 patterns, using Unicode's explicit lattice definitions."""
    out = {bits: cp for cp, bits in glyphs.octants().items()}
    out.update({bits: cp for cp, bits in glyphs.SUBSTITUTES.items()})
    # Remaining patterns encoded by space, halves, quarters and quadrants.
    out.update({0: 0x20, 255: 0x2588, 15: 0x2580, 240: 0x2584,
                85: 0x258c, 170: 0x2590, 192: 0x2582,
                252: 0x2586, 80: 0x2596, 160: 0x2597,
                5: 0x2598, 245: 0x2599, 165: 0x259a,
                95: 0x259b, 175: 0x259c, 10: 0x259d,
                90: 0x259e, 250: 0x259f})
    assert set(out) == set(range(256)), sorted(set(range(256)) - out.keys())
    return out


def exactness(weights=None, library=None):
    weights = weights or ROOT / 'weights/neuronte-video-masks-v0.nrt'
    rows = []
    with NeuralMasks(weights, library) as net:
        for bits, cp in sorted(octant_characters().items()):
            expected = np.array([bits >> k & 1 for k in range(8)]).reshape(4, 2)
            actual = net.mask(cp, 2, 4)
            rows.append(dict(scalar=f'U+{cp:04X}', bits=bits,
                             max_error=float(np.max(np.abs(expected - actual))),
                             exact=bool(np.array_equal(expected, actual))))
    return dict(patterns=256, points=2048, exact=all(x['exact'] for x in rows),
                max_error=max(x['max_error'] for x in rows), results=rows)


def patches(frame, width, height):
    frame = np.asarray(frame)
    if frame.dtype != np.uint8 or frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError('frame must be HxWx3 uint8 RGB')
    h, w = frame.shape[:2]
    if w % width or h % height:
        raise ValueError('frame dimensions must be multiples of cell dimensions')
    return frame.reshape(h // height, height, w // width, width, 3).transpose(0, 2, 1, 3, 4)


def unpatch(p):
    rows, cols, h, w, _ = p.shape
    return p.transpose(0, 2, 1, 3, 4).reshape(rows * h, cols * w, 3)


class MultiInk:
    planes = (0x2590, 0x1cd33, 0x2584)
    row_labels = (0, 1, 3, 2)

    def __init__(self, weights=None, library=None, cell_w=2, cell_h=4):
        if cell_w < 2 or cell_h < 4 or cell_w % 2 or cell_h % 4:
            raise ValueError('multi-ink cells require width divisible by 2, height by 4')
        self.width, self.height = cell_w, cell_h
        weights = weights or ROOT / 'weights/neuronte-video-masks-v0.nrt'
        with NeuralMasks(weights, library) as net:
            masks = np.stack([net.mask(cp, cell_w, cell_h) for cp in self.planes])
            self.library = net.lib
        self.native_rgb24 = getattr(self.library, 'neuronte_video_rgb24', None)
        if self.native_rgb24 is not None:
            self.native_rgb24.argtypes = [C.c_void_p, C.c_size_t, C.c_size_t,
                                         C.c_void_p, C.c_size_t, C.c_size_t,
                                         C.c_int, C.c_int, C.c_void_p]
            self.native_rgb24.restype = C.c_int
        self.native_planes = getattr(self.library, 'neuronte_video_planes_rgb24', None)
        if self.native_planes is not None:
            self.native_planes.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, C.c_size_t, C.c_size_t,
                                          C.c_void_p, C.c_size_t, C.c_size_t,
                                          C.c_int, C.c_int, C.c_void_p]
            self.native_planes.restype = C.c_int
        # Integer selection is valid only AFTER the actual neural masks are
        # exactly binary. No coverage is rounded and no geometric mask is
        # substituted. Fractional models retain the continuous blend below.
        self.ink_indices = None
        if np.all((masks == 0) | (masks == 1)):
            self.ink_indices = (masks[0] + 2*masks[1] + 4*masks[2]).astype(np.uint8)
        self.mix = np.stack([np.prod(np.stack([masks[b] if k >> b & 1 else 1 - masks[b] for b in range(3)]), axis=0) for k in range(8)])

    def encode(self, rgb):
        p = patches(rgb, self.width, self.height)
        rows, cols = p.shape[:2]
        out = np.empty((rows, cols, 8, 3), np.uint8)
        if (self.width, self.height) == (2, 4):
            # A subcell already is one RGB8 pixel: avoid a floating-point
            # mean of a single value and its unnecessary large temporaries.
            for y, label in enumerate(self.row_labels):
                out[:, :, label * 2:label * 2 + 2] = p[:, :, y]
        else:
            means = p.reshape(rows, cols, 4, self.height // 4, 2, self.width // 2, 3).mean(axis=(3, 5))
            for y, label in enumerate(self.row_labels):
                out[:, :, label * 2:label * 2 + 2] = np.rint(means[:, :, y]).astype(np.uint8)
        return out

    def render_rgb24(self, rgb, out=None):
        """Render 2x4 cells at source size, reusing an optional RGB buffer.

        The C path uses the actual binary neural ink map. Older libraries
        and fractional models retain the independent palette/blend path.
        Odd edges replicate exactly as pad -> encode -> decode -> crop.
        """
        rgb = np.asarray(rgb)
        if ((self.width, self.height) != (2, 4) or rgb.dtype != np.uint8 or
                rgb.ndim != 3 or rgb.shape[2] != 3 or min(rgb.shape[:2]) < 1):
            raise ValueError('natural RGB rendering requires 2x4 cells and nonempty HxWx3 uint8')
        if out is None:
            out = np.empty(rgb.shape, np.uint8)
        if (not isinstance(out, np.ndarray) or out.shape != rgb.shape or
                out.dtype != np.uint8 or not out.flags.c_contiguous or not out.flags.writeable):
            raise ValueError('output must be a writable contiguous RGB array of the same shape')
        if np.shares_memory(rgb, out):
            raise ValueError('source and output must not overlap')
        rgb = np.ascontiguousarray(rgb)
        height, width = rgb.shape[:2]
        if self.native_rgb24 is not None and self.ink_indices is not None:
            indices = np.ascontiguousarray(self.ink_indices, dtype=np.uint8)
            if indices.shape != (4, 2):
                raise ValueError('binary ink map must be 4x2')
            result = self.native_rgb24(rgb.ctypes.data, rgb.nbytes, rgb.strides[0],
                                       out.ctypes.data, out.nbytes, out.strides[0],
                                       width, height, indices.ctypes.data)
            if result:
                raise ValueError(f'native RGB composition failed: {result}')
        else:
            padded = np.pad(rgb, ((0, -height % 4), (0, -width % 2), (0, 0)), mode='edge')
            np.copyto(out, self.decode(self.encode(padded))[:height, :width])
        return out

    def natural_input_format(self):
        """The decoded layout render_natural takes at the lowest cost.

        FFmpeg's planar gbrp output is the same scaled and converted image
        as packed rgb24 (tests/check_video.py compares them on the installed
        FFmpeg) but its conversion runs faster. Planes only pay off when the
        native compositor packs them while applying the learned selection.
        """
        return ('gbrp' if self.native_planes is not None and self.ink_indices is not None
                and (self.width, self.height) == (2, 4) else 'rgb24')

    def render_gbrp(self, planes, out=None):
        """render_rgb24 for G, B and R planes (FFmpeg gbrp order), shape 3xHxW.

        The native path packs the planes and applies the actual learned
        selection in one pass. Otherwise the planes are packed first and the
        packed path runs unchanged, including fractional models.
        """
        planes = np.asarray(planes)
        if ((self.width, self.height) != (2, 4) or planes.dtype != np.uint8 or
                planes.ndim != 3 or planes.shape[0] != 3 or min(planes.shape[1:]) < 1):
            raise ValueError('natural planar rendering requires 2x4 cells and nonempty 3xHxW uint8')
        height, width = planes.shape[1:]
        if out is None:
            out = np.empty((height, width, 3), np.uint8)
        if (not isinstance(out, np.ndarray) or out.shape != (height, width, 3) or
                out.dtype != np.uint8 or not out.flags.c_contiguous or not out.flags.writeable):
            raise ValueError('output must be a writable contiguous RGB array of the planes\' size')
        if np.shares_memory(planes, out):
            raise ValueError('source and output must not overlap')
        if self.native_planes is None or self.ink_indices is None:
            return self.render_rgb24(np.stack((planes[2], planes[0], planes[1]), axis=-1), out)
        planes = np.ascontiguousarray(planes)
        indices = np.ascontiguousarray(self.ink_indices, dtype=np.uint8)
        if indices.shape != (4, 2):
            raise ValueError('binary ink map must be 4x2')
        base, plane = planes.ctypes.data, planes.strides[0]
        result = self.native_planes(base + 2 * plane, base, base + plane, plane, planes.strides[1],
                                    out.ctypes.data, out.nbytes, out.strides[0],
                                    width, height, indices.ctypes.data)
        if result:
            raise ValueError(f'native planar composition failed: {result}')
        return out

    def render_planes(self, red, green, blue, stride, width, height, out):
        """render_gbrp for three plane addresses that share one row stride,
        such as a MediaStream frame; no plane is copied first. Requires the
        native compositor and a binary learned ink map."""
        if self.native_planes is None or self.ink_indices is None or (self.width, self.height) != (2, 4):
            raise ValueError('planes by address need the native compositor and a binary 2x4 ink map')
        if width < 1 or height < 1 or stride < width:
            raise ValueError('invalid plane geometry')
        if (not isinstance(out, np.ndarray) or out.shape != (height, width, 3) or
                out.dtype != np.uint8 or not out.flags.c_contiguous or not out.flags.writeable):
            raise ValueError('output must be a writable contiguous RGB array of the planes\' size')
        indices = np.ascontiguousarray(self.ink_indices, dtype=np.uint8)
        result = self.native_planes(red, green, blue, (height - 1) * stride + width, stride,
                                    out.ctypes.data, out.nbytes, out.strides[0],
                                    width, height, indices.ctypes.data)
        if result:
            raise ValueError(f'native planar composition failed: {result}')
        return out

    def decode(self, colours):
        colours = np.asarray(colours)
        if colours.dtype != np.uint8 or colours.ndim != 4 or colours.shape[2:] != (8, 3):
            raise ValueError('colours must be rows x columns x 8 x 3 uint8')
        if self.ink_indices is not None:
            if (self.width, self.height) == (2, 4):
                # Write each actual neural ink selection into image order.
                # Avoid the full patch-order take followed by an unpatch copy.
                rows, cols = colours.shape[:2]
                image = np.empty((rows * 4, cols * 2, 3), np.uint8)
                for y in range(4):
                    for x in range(2):
                        image[y::4, x::2] = colours[:, :, self.ink_indices[y, x]]
                return image
            return unpatch(np.take(colours, self.ink_indices, axis=2))
        p = np.einsum('rckd,khw->rchwd', colours.astype(np.float32), self.mix, optimize=True)
        return np.clip(np.rint(unpatch(p)), 0, 255).astype(np.uint8)


class RGBFrameReader:
    """Read complete RGB frames into one reusable array.

    Packed frames are HxWx3; planar (gbrp) frames are 3xHxW, G, B, R. A
    returned frame is valid until the next read. EOF before a frame returns
    None; EOF within a frame is an error rather than an apparently clean end.
    """
    def __init__(self, width, height, planar=False):
        if width < 1 or height < 1:
            raise ValueError('frame size must be positive')
        self.frame = np.empty((3, height, width) if planar else (height, width, 3), np.uint8)
        self.buffer = memoryview(self.frame).cast('B')

    def read(self, stream):
        offset = 0
        while offset < len(self.buffer):
            size = stream.readinto(self.buffer[offset:])
            if not size:
                if offset:
                    raise ValueError('truncated RGB frame')
                return None
            offset += size
        return self.frame


DECODED_FORMATS = ('rgb24', 'gbrp')


def decoder_command(video, width, height, fps, *, start=0., chroma=None,
                    lavfi=False, exact_pixels=True, filter_threads=1,
                    decoder_threads=0, output_threads=1, pix_fmt='rgb24'):
    """Build the shared RGB decoder command used by playback and benchmarks.

    Decoder threads precede the input; rawvideo encoder threads follow it.
    Keeping these separate makes startup buffering and CPU costs measurable.
    pix_fmt gbrp writes the same RGB samples as three planes, G, B, R.
    """
    if (width < 1 or height < 1 or not math.isfinite(fps) or fps <= 0 or
            not math.isfinite(start) or start < 0 or
            min(filter_threads, decoder_threads, output_threads) < 0):
        raise ValueError('invalid video geometry, timing or thread count')
    if pix_fmt not in DECODED_FORMATS:
        raise ValueError('decoded format must be rgb24 or gbrp')
    flags = 'lanczos+accurate_rnd+full_chroma_int+full_chroma_inp' if exact_pixels else 'area'
    scale = f'scale={width}:{height}:flags={flags}'
    if chroma is not None:
        if chroma not in ('left', 'center', 'topleft', 'top', 'bottomleft', 'bottom'):
            raise ValueError('unknown source chroma location')
        scale += ':in_chroma_loc=' + chroma
    return ['ffmpeg', '-v', 'error', '-nostdin', '-filter_threads', str(filter_threads),
            '-threads:v', str(decoder_threads),
            *(['-f', 'lavfi'] if lavfi else ['-ss', f'{start:.3f}']),
            '-i', str(video), '-an', '-sn', '-vf', f'fps={fps},{scale}',
            '-threads:v', str(output_threads), '-f', 'rawvideo', '-pix_fmt', pix_fmt, '-']


class MediaFrame(C.Structure):
    """struct neuronte_media_frame (include/neuronte_media.h)."""
    _fields_ = [('data', C.c_void_p * 4), ('linesize', C.c_int * 4), ('width', C.c_int),
                ('height', C.c_int), ('planes', C.c_int), ('number', C.c_int64)]


class MediaDecoder:
    """decoder_command's frames decoded inside this process.

    build/libneuronte-media.so repeats what FFmpeg 7.1's command does with
    the same arguments (include/neuronte_media.h), without a process start,
    a second probe or a pipe for each start and seek. open() takes what
    decoder_command takes and passes the library the command's own -ss,
    -vf, -pix_fmt and thread arguments. It returns None where the command
    must run instead: an lavfi source, other FFmpeg libraries, an input the
    library declines, or one it cannot open (the command then reports the
    error as before).
    """
    OK, END, AGAIN, ERROR, UNSUPPORTED, ARG = 0, 1, 2, -1, -2, -3

    def __init__(self, library=None):
        self.lib = C.CDLL(str(library or ROOT / 'build/libneuronte-media.so'))
        self.lib.neuronte_media_open.argtypes = [C.POINTER(C.c_void_p), C.c_char_p, C.c_char_p, C.c_char_p,
                                                 C.c_char_p, C.c_int, C.c_int, C.c_char_p, C.c_int]
        self.lib.neuronte_media_open.restype = C.c_int
        self.lib.neuronte_media_next.argtypes = [C.c_void_p, C.POINTER(MediaFrame), C.c_int]
        self.lib.neuronte_media_next.restype = C.c_int
        self.lib.neuronte_media_message.argtypes = [C.c_void_p]
        self.lib.neuronte_media_message.restype = C.c_char_p
        self.lib.neuronte_media_close.argtypes = [C.c_void_p]
        self.lib.neuronte_media_close.restype = None

    def open(self, video, width, height, fps, **options):
        command = decoder_command(video, width, height, fps, **options)
        if '-ss' not in command:
            return None

        def value(flag):
            return command[command.index(flag) + 1]
        handle, message = C.c_void_p(), C.create_string_buffer(1024)
        status = self.lib.neuronte_media_open(C.byref(handle), os.fsencode(video), value('-ss').encode(),
                                              value('-vf').encode(), value('-pix_fmt').encode(),
                                              int(value('-threads:v')), int(value('-filter_threads')),
                                              message, len(message))
        if status == self.ARG:
            raise ValueError('invalid in-process decoder arguments')
        if status != self.OK:
            return None
        return MediaStream(self.lib, handle, width, height, value('-pix_fmt') == 'gbrp')


class MediaStream:
    """One run of MediaDecoder: the frames one ffmpeg process would write."""

    def __init__(self, lib, handle, width, height, planar):
        self.lib, self.handle = lib, handle
        self.width, self.height, self.planar = width, height, planar
        self.frame = MediaFrame()
        self.failure = ''

    def read(self, wait_ms=None):
        """The next frame, valid until the next read or close; None at the
        end. failure then says why, if decoding failed. A finite wait_ms
        returns b'' when no frame is ready, so callers can handle controls."""
        if not self.handle:
            raise ValueError('the decoder is closed')
        if wait_ms is not None and (not isinstance(wait_ms, int) or wait_ms < 0):
            raise ValueError('wait_ms must be a nonnegative integer or None')
        while True:
            # A bounded wait lets Python handle signals between calls.
            status = self.lib.neuronte_media_next(self.handle, C.byref(self.frame),
                                                 100 if wait_ms is None else wait_ms)
            if status == MediaDecoder.AGAIN and wait_ms is not None:
                return b''
            if status != MediaDecoder.AGAIN:
                break
        if status == MediaDecoder.OK:
            frame = self.frame
            if (frame.width, frame.height) != (self.width, self.height) or frame.planes < (3 if self.planar else 1):
                raise ValueError('a decoded frame does not have the requested size and layout')
            return frame
        if status == MediaDecoder.ERROR:
            self.failure = (self.lib.neuronte_media_message(self.handle) or b'').decode(errors='replace').strip() \
                or 'decoding failed'
        return None

    def planes(self, frame):
        """(red, green, blue, stride) addresses of a gbrp frame whose planes
        share one stride, or None."""
        if not self.planar or len(set(frame.linesize[:3])) != 1:
            return None
        return frame.data[2], frame.data[0], frame.data[1], frame.linesize[0]

    def copy(self, frame, out):
        """Copy a frame into an array of RGBFrameReader's layout."""
        row = self.width * (1 if self.planar else 3)
        for index, target in enumerate(out if self.planar else [out.reshape(self.height, row)]):
            stride = frame.linesize[index]
            span = (self.height - 1) * stride + row
            flat = np.ctypeslib.as_array((C.c_uint8 * span).from_address(frame.data[index]))
            np.copyto(target.reshape(self.height, row),
                      np.lib.stride_tricks.as_strided(flat, (self.height, row), (stride, 1)))
        return out

    def close(self):
        if self.handle:
            self.lib.neuronte_media_close(self.handle)
            self.handle = None

    def __del__(self):
        self.close()


def candidates(mode, width, height, weights=None, library=None):
    if mode == 'portable':
        entries = [(' ', 'block', [])] + glyphs.charset('pixel')
        # Ideal binary geometry at pixel centres; no font dependency.
        yy, xx = np.mgrid[:height, :width]
        points = np.stack([(xx.ravel() + .5) / width, (yy.ravel() + .5) * 2 / height], -1)
        masks = np.stack([(glyphs.signed_distance(shape, points, .075) > 0).astype(np.float32) for _, _, shape in entries])
        return np.array([ord(ch) for ch, _, _ in entries], np.uint32), masks
    if mode != 'full': raise ValueError('mode must be portable or full')
    # Use the loaded bundle's explicit routing ranges, so newly trained
    # bundles cannot silently be searched with an obsolete scalar manifest.
    path = Path(weights or ROOT / 'weights/neuronte-split-v5.nrt')
    with NeuralMasks(path, library) as net:
        data = path.read_bytes()
        if len(data) < 28 or struct.unpack_from('<I', data, 8)[0] != 2:
            raise ValueError('full video mode requires a bundle with explicit scalar ranges')
        nets, ranges = struct.unpack_from('<II', data, 12)
        lengths = struct.unpack_from(f'<{nets}I', data, 28)
        member = len(data) - sum(lengths)
        for length in lengths:
            # Distance nets and tiled collections of distance nets are
            # monochrome and support arbitrary foreground/background fits.
            if struct.unpack_from('<I', data, member + 8)[0] not in (1, 6):
                raise ValueError('full two-ink mode requires monochrome nets; fixed-colour bundles cannot use arbitrary foreground/background fits')
            member += length
        offset = 28 + 4 * nets
        cps = []
        for i in range(ranges):
            lo, hi, _ = struct.unpack_from('<III', data, offset + 12*i)
            cps.extend(cp for cp in range(lo, min(hi, 0x10ffff)+1) if not 0xd800 <= cp <= 0xdfff)
        cps = np.array(cps, np.uint32)
        masks = np.stack([net.mask(int(cp), width, height).ravel() for cp in cps])
    return cps, masks


class TwoInk:
    def __init__(self, mode='portable', cell_w=8, cell_h=16, weights=None, library=None, margin=0):
        if cell_w < 1 or cell_h < 1 or margin < 0: raise ValueError('invalid cell size or margin')
        self.width, self.height, self.margin = cell_w, cell_h, margin
        self.scalars, self.masks = candidates(mode, cell_w, cell_h, weights, library)
        self.masks = self.masks.astype(np.float64)
        self.previous = None

    def fit(self, rgb, proposals=None):
        p = patches(rgb, self.width, self.height)
        grid = p.shape[:2]
        x = p.reshape(-1, self.width * self.height, 3).astype(np.float64)
        if proposals is not None:
            proposals = np.asarray(proposals)
            if proposals.ndim != 3 or proposals.shape[:2] != grid or proposals.shape[2] < 1:
                raise ValueError('proposals must have shape rows x columns x candidates')
            if proposals.dtype.kind not in 'iu' or np.any(proposals < 0) or np.any(proposals >= len(self.masks)):
                raise ValueError('proposal index outside mask manifest')
            proposals = proposals.reshape(-1, proposals.shape[2])
        # Design matrix [1-m, m]. Each channel's box-constrained quadratic
        # optimum is either interior or on one of the four box edges.
        moments = np.stack([((1-self.masks)**2).sum(1),
                            (self.masks*(1-self.masks)).sum(1),
                            (self.masks*self.masks).sum(1)])
        ids, colours, losses = [], [], []
        for start in range(0, len(x), 64):
            chunk = x[start:start+64]
            selected = proposals[start:start+len(chunk)] if proposals is not None else None
            if selected is None:
                a,b,d = [r[None,:,None] for r in moments]
            else:
                a,b,d = [r[selected][:,:,None] for r in moments]
            det = a*d-b*b
            if selected is None:
                v = np.einsum('kp,bpc->bkc', self.masks, chunk, optimize=True)
            else:
                v = np.matmul(self.masks[selected], chunk)
            u = chunk.sum(1)[:, None, :] - v
            energy = (chunk*chunk).sum(1)[:, None, :]
            def divide(n, den): return np.divide(n, den, out=np.zeros_like(n), where=den > 1e-12)
            bg, fg = divide(d*u-b*v, det), divide(a*v-b*u, det)
            choices = [(bg, fg, (bg>=0)&(bg<=255)&(fg>=0)&(fg<=255)&(det>1e-12))]
            for bound in (0., 255.):
                choices += [(np.full_like(u,bound), np.clip(divide(v-b*bound,d),0,255), True),
                            (np.clip(divide(u-b*bound,a),0,255), np.full_like(v,bound), True)]
            best = np.full_like(u, np.inf); cb = np.zeros_like(u); cf = np.zeros_like(v)
            for bg, fg, valid in choices:
                loss = np.where(valid, energy+a*bg*bg+2*b*bg*fg+d*fg*fg-2*u*bg-2*v*fg, np.inf)
                take = loss < best
                best = np.where(take,loss,best); cb = np.where(take,bg,cb); cf = np.where(take,fg,cf)
            total = best.sum(2)
            choice = total.argmin(1)
            ix = np.arange(len(chunk))
            if proposals is None and self.previous is not None and self.previous.shape == grid:
                old = self.previous.ravel()[start:start+len(chunk)]
                choice = np.where(total[ix,old] <= total[ix,choice] + self.margin * self.width*self.height*3, old, choice)
            ids.extend(choice if selected is None else selected[ix, choice]); colours.extend(np.stack([cb[ix,choice],cf[ix,choice]],1)); losses.extend(total[ix,choice])
        idx = np.array(ids).reshape(grid)
        self.previous = idx.copy()
        return dict(indices=idx, colours=np.clip(np.rint(colours),0,255).astype(np.uint8).reshape(*grid,2,3),
                    sse=np.maximum(losses,0).reshape(grid))

    def decode(self, cells):
        masks = self.masks[cells['indices']].reshape(*cells['indices'].shape,self.height,self.width,1)
        c = cells['colours'].astype(np.float64)
        pixels = c[:,:,0,None,None,:]*(1-masks)+c[:,:,1,None,None,:]*masks
        return np.clip(np.rint(unpatch(pixels)),0,255).astype(np.uint8)

    def ansi(self, cells, previous=None):
        out = []
        for y,x in np.ndindex(cells['indices'].shape):
            i = cells['indices'][y,x]; c = cells['colours'][y,x]
            if previous is not None and i == previous['indices'][y,x] and np.array_equal(c,previous['colours'][y,x]): continue
            bg,fg = c
            out.append(f'\x1b[{y+1};{x+1}H\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m'+chr(int(self.scalars[i])))
        return ''.join(out)+'\x1b[0m'
