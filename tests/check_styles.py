"""Real-net acceptance for synthetic styles and consistent scalable weight.

Compare against ordinary unstyled coverage, using independent NumPy mask
operations. Check geometry, compositing once, clipping, immutable legacy
metrics and error paths. Usage: python3 tests/check_styles.py LIB.so
"""
import ctypes as C
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
P, I, U, F = C.c_void_p, C.c_int, C.c_uint32, C.POINTER(C.c_float)
lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(P)]
lib.neuronte_close.argtypes = [P]
lib.neuronte_set_samples.argtypes = lib.neuronte_set_binary.argtypes = [P, I]
lib.neuronte_coverage.argtypes = [P, U, I, I, I, F]
lib.neuronte_coverage_styled.argtypes = [P, U, I, I, I, U, F]
lib.neuronte_draw_scalar.argtypes = [P, P, I, I, I, I, I, I, I, U, U]
lib.neuronte_draw_scalar_styled.argtypes = lib.neuronte_draw_scalar.argtypes + [U]
lib.neuronte_draw_text.argtypes = [P, P, I, I, I, I, I, I, I, C.c_char_p, C.c_size_t, U]
lib.neuronte_draw_text_stroke.argtypes = lib.neuronte_draw_text.argtypes
lib.neuronte_text_width.argtypes = [P, C.c_char_p, C.c_size_t, I, I]
lib.neuronte_text_width_stroke.argtypes = lib.neuronte_text_width.argtypes
lib.neuronte_advance.argtypes = [P, U, I, I]


def open_net(name):
    ptr = P()
    assert lib.neuronte_open_file(str(ROOT / 'weights' / name).encode(), C.byref(ptr)) == 0
    return ptr


def cov(ptr, cp, w, h, samples=1, style=None):
    out = np.full((h, w), -1, np.float32)
    args = [ptr, cp, w, h, samples]
    if style is not None:
        args.append(style)
    fn = lib.neuronte_coverage if style is None else lib.neuronte_coverage_styled
    assert fn(*args, out.ctypes.data_as(F)) == 0
    return out


def dilate_right(mask, amount):
    h, w = mask.shape
    full = np.pad(mask, ((0, 0), (0, amount)))
    return np.maximum.reduce([np.roll(full, offset, axis=1) for offset in range(amount + 1)])


def styled(mask, flags):
    h, w = mask.shape
    # Work on an oversized transparent canvas before cropping back to the
    # terminal cell; this also keeps negative shifts away from array wrap.
    canvas = np.pad(mask, ((0, 0), (w, w)))
    if flags & 2:
        shifts = (0.675 - (np.arange(h) + 0.5) / h) * w / 2
        shifts = (np.sign(shifts) * np.floor(np.abs(shifts) + 0.5)).astype(int)
        canvas = np.stack([np.roll(row, shift) for row, shift in zip(canvas, shifts)])
    if flags & 1:
        canvas = dilate_right(canvas, max(1, (w + 16) // 32))
    return canvas[:, w:2*w]


ptr = open_net('neuronte-split-v4.nrt')
try:
    for w, h, samples in ((12,24,2),(32,64,1),(48,64,1),(7,19,0)):
        for cp in (ord('H'), ord('g'), 0xE9):
            plain = cov(ptr, cp, w, h, samples)
            assert lib.neuronte_set_samples(ptr, samples) == 0
            for flags in range(4):
                expected = styled(plain, flags)
                got = cov(ptr, cp, w, h, samples, flags)
                np.testing.assert_array_equal(got, expected)
                if flags:
                    assert not np.array_equal(got, plain), (w,h,cp,flags)
                for binary in (0, 1):
                    assert lib.neuronte_set_binary(ptr, binary) == 0
                    # Transparent padding and a non-opaque caller colour check
                    # that overlaps are composited only once.
                    pixels = np.zeros((h+4,w+6), np.uint32)
                    assert lib.neuronte_draw_scalar_styled(ptr, pixels.ctypes.data, w+6, w+6, h+4,
                                                           3, 2, w, h, cp, 0x80402010, flags) == 0
                    alpha = np.floor(((expected > .5) if binary else expected) * 128 + .5).astype(np.uint32)
                    np.testing.assert_array_equal(pixels[2:h+2,3:w+3] >> 24, alpha)
                    assert not pixels[:2].any() and not pixels[h+2:].any()
                    assert not pixels[:,:3].any() and not pixels[:,w+3:].any()
                    clipped = np.zeros((h-4,w+1), np.uint32)
                    assert lib.neuronte_draw_scalar_styled(ptr, clipped.ctypes.data, w+1,w-3,h-4,
                                                           -3,-4,w,h,cp,0x80402010,flags) == 0
                    np.testing.assert_array_equal(clipped[:,:w-3], pixels[6:h+2,6:w+3])
                    assert not clipped[:,w-3:].any()
            # Zero style preserves the scalar API even after style cache use.
            old = np.zeros((h,w), np.uint32); new = old.copy()
            assert lib.neuronte_draw_scalar(ptr, old.ctypes.data,w,w,h,0,0,w,h,cp,0xFFFFFFFF) == 0
            assert lib.neuronte_draw_scalar_styled(ptr,new.ctypes.data,w,w,h,0,0,w,h,cp,0xFFFFFFFF,0) == 0
            np.testing.assert_array_equal(new,old)
    out = np.full((8,4),-1,np.float32)
    for flags in (4, 0xFFFFFFFF):
        assert lib.neuronte_coverage_styled(ptr,65,4,8,1,flags,out.ctypes.data_as(F)) == -1
        assert (out == -1).all()
    for w,h,s in ((0,8,1),(4,0,1),(4097,8,1),(4,8,9)):
        assert lib.neuronte_coverage_styled(ptr,65,w,h,s,1,out.ctypes.data_as(F)) == -1
    pixels = np.full((8,4),0xAABBCCDD,np.uint32)
    for x,y in ((2**31-1,0),(-2**31,0),(0,2**31-1),(0,-2**31)):
        assert lib.neuronte_draw_scalar_styled(ptr,pixels.ctypes.data,4,4,8,x,y,4,8,65,0xFFFFFFFF,3) == 0
        assert (pixels == 0xAABBCCDD).all()
    assert lib.neuronte_draw_scalar_styled(ptr,pixels.ctypes.data,4,4,8,0,0,4,8,65,0xFFFFFFFF,4) == -1
    assert (pixels == 0xAABBCCDD).all()
finally:
    lib.neuronte_close(ptr)

# Fixed-colour artwork is preserved for every style, not sheared or recoloured.
ptr = open_net('neuronte-flame-v0.nrt')
try:
    base = cov(ptr,0x100000,8,16)
    original = np.zeros((16,8),np.uint32)
    assert lib.neuronte_set_samples(ptr,1) == 0
    assert lib.neuronte_draw_scalar(ptr,original.ctypes.data,8,8,16,0,0,8,16,0x100000,0xFFFFFFFF) == 0
    for style in range(4):
        np.testing.assert_array_equal(cov(ptr,0x100000,8,16,style=style),base)
        pixels = np.zeros_like(original)
        assert lib.neuronte_draw_scalar_styled(ptr,pixels.ctypes.data,8,8,16,0,0,8,16,0x100000,0xFFFFFFFF,style) == 0
        np.testing.assert_array_equal(pixels,original)
finally:
    lib.neuronte_close(ptr)

ptr = open_net('neuronte-ui-large-v0.nrt')
try:
    assert lib.neuronte_set_samples(ptr,1) == 0
    for em in (33,48,64,96,128):
        stroke = max(1,(em+16)//32)
        legacy_width = lib.neuronte_text_width(ptr,b'H g?',4,1,em)
        for text in (b'H g?', 'H\u0301g'.encode(), b'H\xffg', b''):
            count = len(text.decode('utf8','replace'))
            regular_width = lib.neuronte_text_width(ptr,text,len(text),0,em)
            width = lib.neuronte_text_width_stroke(ptr,text,len(text),stroke,em)
            assert width == regular_width + count*stroke
            pixels = np.zeros((2*em,width+em+stroke),np.uint32)
            assert lib.neuronte_draw_text_stroke(ptr,pixels.ctypes.data,pixels.shape[1],pixels.shape[1],2*em,
                                                 0,0,em,stroke,text,len(text),0x80FFFFFF) == width
        for cp in (ord('H'),ord('g')):
            regular = cov(ptr,cp,em,2*em)
            expected = dilate_right(regular,stroke)
            pixels = np.zeros(expected.shape,np.uint32)
            text = bytes([cp])
            assert lib.neuronte_draw_text_stroke(ptr,pixels.ctypes.data,em+stroke,em+stroke,2*em,
                                                 0,0,em,stroke,text,1,0x80FFFFFF) == lib.neuronte_advance(ptr,cp,0,em)+stroke
            np.testing.assert_array_equal(pixels>>24,np.floor(expected*128+.5).astype(np.uint32))
            assert expected.sum() > regular.sum()
        assert lib.neuronte_text_width(ptr,b'H g?',4,1,em) == legacy_width
        # Explicit zero stroke is pixel/metric identical to regular text.
        a = np.zeros((2*em,4*em),np.uint32); b = a.copy()
        old = lib.neuronte_draw_text(ptr,a.ctypes.data,4*em,4*em,2*em,0,0,em,0,b'Hg',2,0xFFFFFFFF)
        new = lib.neuronte_draw_text_stroke(ptr,b.ctypes.data,4*em,4*em,2*em,0,0,em,0,b'Hg',2,0xFFFFFFFF)
        assert old == new
        np.testing.assert_array_equal(a,b)
    for stroke in (-1,129):
        assert lib.neuronte_text_width_stroke(ptr,b'',0,stroke,128) == -1
    assert lib.neuronte_text_width_stroke(ptr,None,1,1,128) == -1
    assert lib.neuronte_text_width_stroke(ptr,b'',0,0,0) == -1
finally:
    lib.neuronte_close(ptr)
print('check_styles: terminal bold/italic, clipping, colour preservation and scalable weight passed')
