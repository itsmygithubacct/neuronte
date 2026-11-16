"""The opt-in untrained mark: neuronte_untrained() and neuronte_set_untrained().

usage: python3 tests/check_untrained.py build/libneuronte.so

On split-v8: a trained scalar draws identically in both modes through every
plain call; an untrained one and U+FFFD report 1, draw the mark in mode 1 and
the net in mode 0; the half calls and neuronte_route() ignore the mode; a
single-net file reports 0 everywhere; bad arguments are rejected.
"""
import ctypes as C
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
lib = C.CDLL(str(Path(sys.argv[1]).resolve()))
P, F, U8, U32 = C.c_void_p, C.POINTER(C.c_float), C.POINTER(C.c_uint8), C.POINTER(C.c_uint32)
lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(P)]
lib.neuronte_close.argtypes = [P]
lib.neuronte_untrained.argtypes = [P, C.c_uint32]
lib.neuronte_set_untrained.argtypes = [P, C.c_int]
lib.neuronte_route.argtypes = [P, C.c_uint32]
lib.neuronte_coverage.argtypes = [P, C.c_uint32, C.c_int, C.c_int, C.c_int, F]
lib.neuronte_coverage_styled.argtypes = [P, C.c_uint32, C.c_int, C.c_int, C.c_int, C.c_uint, F]
lib.neuronte_coverage_layers.argtypes = [P, C.c_uint32, C.c_int, C.c_int, C.c_int, F, U8]
lib.neuronte_coverage_half.argtypes = [P, C.c_uint32, C.c_int, C.c_int, C.c_int, C.c_int, F]
lib.neuronte_layers.argtypes = [P]
lib.neuronte_draw_scalar.argtypes = [P, U32, C.c_int, C.c_int, C.c_int, C.c_int, C.c_int, C.c_int, C.c_int, C.c_uint32, C.c_uint32]
lib.neuronte_draw_utf8.argtypes = [P, U32, C.c_int, C.c_int, C.c_int, C.c_int, C.c_int, C.c_int, C.c_int, C.c_char_p, C.c_size_t, C.c_uint32]
SIZES = ((1, 2), (3, 6), (5, 10), (8, 16), (9, 17), (12, 24), (16, 32), (25, 49), (48, 96))


def opened(path):
    h = P()
    assert lib.neuronte_open_file(str(path).encode(), C.byref(h)) == 0, path
    return h


def cover(h, s, w, hh, style=None):
    buf = (C.c_float * (w * hh))()
    rc = (lib.neuronte_coverage(h, s, w, hh, 0, buf) if style is None else
          lib.neuronte_coverage_styled(h, s, w, hh, 0, style, buf))
    assert rc == 0
    return np.frombuffer(buf, np.float32).reshape(hh, w).copy()


def layers(h, s, w, hh):
    k = lib.neuronte_layers(h)
    m, e = (C.c_float * (k * w * hh))(), (C.c_uint8 * k)()
    assert lib.neuronte_coverage_layers(h, s, w, hh, 0, m, e) == 0
    return bytes(m) + bytes(e)


def half(h, s, w, hh):
    buf = (C.c_float * (w * hh))()
    assert lib.neuronte_coverage_half(h, s, 0, w, hh, 0, buf) == 0
    return bytes(buf)


def drawn(h, s, w, hh):
    px = (C.c_uint32 * (w * hh * 3))(*([0xFF101010] * (w * hh * 3)))
    assert lib.neuronte_draw_scalar(h, px, 3 * w, 3 * w, hh, w, 0, w, hh, s, 0xFFE0E0E0) == 0
    text = 'x' + chr(s) + 'x' if s <= 0x10FFFF and not 0xD800 <= s <= 0xDFFF else None
    t = (C.c_uint32 * (w * hh * 3))(*([0xFF101010] * (w * hh * 3)))
    if text:
        b = text.encode()
        assert lib.neuronte_draw_utf8(h, t, 3 * w, 3 * w, hh, 0, 0, w, hh, b, len(b), 0xFFE0E0E0) == 3
    return bytes(px) + bytes(t)


def valid(s):
    return s if s <= 0x10FFFF and not 0xD800 <= s <= 0xDFFF else 0xFFFD


def mark(w, hh):
    """The mark, written independently from the header's description."""
    m = np.zeros((hh, w), np.float32)
    t = max(1, (w + 6) // 12)
    left, top = (w * 12 + 50) // 100, (hh * 16 + 50) // 100
    right, bottom = w - left, hh - top
    m[top:bottom, left:right] = 1
    m[top + t:bottom - t, left + t:right - t] = 0
    side = max(1, (w + 2) // 5)
    sx, sy = (w - side) // 2, (hh - side) // 2
    if sx >= left + t + 1 and sx + side <= right - t - 1 and sy >= top + t + 1 and sy + side <= bottom - t - 1:
        m[sy:sy + side, sx:sx + side] = 1
    return m


bundle = opened(ROOT / 'weights/neuronte-split-v8.nrt')
single = opened(ROOT / 'weights/neuronte-ascii-v0.nrt' if (ROOT / 'weights/neuronte-ascii-v0.nrt').exists()
                else ROOT / 'weights/neuronte-braille-v1.nrt')
try:
    trained = [ord('A'), ord('~'), 0x2800 + 0x5A, 0x2714, 0x00E9, 0x03B1, 0x0436]
    untrained = [0x2713, 0x4E00, 0x1F600, 0xFFFD]
    replaced = [0xD800, 0x110000, 0xFFFFFFFF]       # drawn as U+FFFD
    for s in trained:
        assert lib.neuronte_untrained(bundle, s) == 0, hex(s)
    for s in untrained + replaced:
        assert lib.neuronte_untrained(bundle, s) == 1, hex(s)
    for s in trained + untrained + [0x41, 0x10FFFF]:
        assert lib.neuronte_untrained(single, s) == 0
    routes = {s: lib.neuronte_route(bundle, s) for s in trained + untrained}
    before = {}
    for s in trained + untrained + replaced:
        for w, hh in SIZES:
            before[s, w, hh] = (cover(bundle, s, w, hh).tobytes(), cover(bundle, s, w, hh, 3).tobytes(),
                                layers(bundle, s, w, hh), half(bundle, valid(s), w, hh),
                                drawn(bundle, s, w, hh))
    assert lib.neuronte_set_untrained(bundle, 1) == 0
    marked = 0
    for s in trained + untrained + replaced:
        for w, hh in SIZES:
            c, st, la, ha, dr = before[s, w, hh]
            hs = valid(s)
            assert half(bundle, hs, w, hh) == ha, 'half calls ignore the mode'
            if s in trained:
                assert cover(bundle, s, w, hh).tobytes() == c and cover(bundle, s, w, hh, 3).tobytes() == st
                assert layers(bundle, s, w, hh) == la and drawn(bundle, s, w, hh) == dr, hex(s)
            else:
                m = mark(w, hh)
                assert np.array_equal(cover(bundle, s, w, hh), m), (hex(s), w, hh)
                assert layers(bundle, s, w, hh)[:m.nbytes] == m.tobytes()
                assert cover(bundle, s, w, hh).tobytes() != c or not m.any()
                marked += 1
    for s, r in routes.items():
        assert lib.neuronte_route(bundle, s) == r
    m = mark(16, 32)
    assert m.sum() > 60 and m[16, 8] == 1 and m[0].sum() == 0 and m[:, 0].sum() == 0
    # Back to mode 0: the cache gives the net's cells again.
    assert lib.neuronte_set_untrained(bundle, 0) == 0
    for s in untrained:
        for w, hh in SIZES:
            assert cover(bundle, s, w, hh).tobytes() == before[s, w, hh][0]
            assert drawn(bundle, s, w, hh) == before[s, w, hh][4]
    # Mode 1 on a single net changes nothing.
    assert lib.neuronte_set_untrained(single, 1) == 0
    assert cover(single, 0x2713, 8, 16).tobytes() == (lib.neuronte_set_untrained(single, 0), cover(single, 0x2713, 8, 16).tobytes())[1]
    for bad in (-1, 2, 99):
        assert lib.neuronte_set_untrained(bundle, bad) == -1
    assert lib.neuronte_set_untrained(None, 0) == -1 and lib.neuronte_untrained(None, 65) == -1
finally:
    lib.neuronte_close(bundle)
    lib.neuronte_close(single)
print(f'check_untrained: {len(trained)} trained scalars unchanged in both modes; {marked} untrained and replaced '
      f'cells drew the mark; half calls and routes ignore the mode; single net reports none; bad arguments rejected')
