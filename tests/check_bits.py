"""The packed text mask calls (src/bits.c) against the same work done a
pixel at a time: neuronte_bits_pack, neuronte_alpha_pack and
neuronte_bits_compose, and their refusal of a buffer or line too small.

usage: python3 tests/check_bits.py build/libneuronte.so
"""
import ctypes
import os
import sys

import numpy as np


class Cell(ctypes.Structure):
    _fields_ = [("offset", ctypes.c_uint32), ("width", ctypes.c_uint16), ("advance", ctypes.c_uint16),
                ("bold_advance", ctypes.c_uint16), ("reserved", ctypes.c_uint16)]


def text_masks(lib):
    """The packed-mask calls against the same work done a pixel at a time."""
    u8 = ctypes.POINTER(ctypes.c_uint8)
    lib.neuronte_bits_pack.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, u8, ctypes.c_size_t]
    lib.neuronte_alpha_pack.argtypes = lib.neuronte_bits_pack.argtypes
    lib.neuronte_bits_compose.argtypes = [u8, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, u8, ctypes.c_size_t,
                                          ctypes.POINTER(Cell), ctypes.c_size_t,
                                          ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t, ctypes.c_int]
    rng = np.random.default_rng(95)
    bad = 0

    def ptr(a):
        return a.ctypes.data_as(u8)

    for _ in range(200):
        w, h, pad = int(rng.integers(1, 70)), int(rng.integers(1, 20)), int(rng.integers(0, 5))
        px = (rng.integers(0, 2, (h, w + pad)) * rng.integers(1, 2 ** 32, (h, w + pad))).astype(np.uint32)
        bits = np.full((h, (w + 7) // 8), 0xAA, np.uint8)
        alpha = np.full((h, w), 0xAA, np.uint8)
        ok = (lib.neuronte_bits_pack(px.ctypes.data, w + pad, w, h, ptr(bits), bits.size) == 0
              and lib.neuronte_alpha_pack(px.ctypes.data, w + pad, w, h, ptr(alpha), alpha.size) == 0)
        ok = ok and (bits == np.packbits(px[:, :w] != 0, axis=1)).all() and (alpha == (px[:, :w] >> 24)).all()
        ok = ok and lib.neuronte_bits_pack(px.ctypes.data, w + pad, w, h, ptr(bits), bits.size - 1) == -1
        ok = ok and lib.neuronte_alpha_pack(px.ctypes.data, w - 1, w, h, ptr(alpha), alpha.size) == -1
        bad += not ok
    for trial in range(300):
        rows, count = int(rng.integers(1, 40)), int(rng.integers(1, 30))
        cells, atlas, inks = (Cell * count)(), bytearray(), []
        for i in range(count):
            width = int(rng.integers(0, 45)) if i else 0
            ink = rng.integers(0, 2, (rows, width)).astype(bool)
            raw = np.packbits(ink, axis=1) if width else np.zeros((rows, 0), np.uint8)
            if width % 8:
                raw[:, -1] |= int(rng.integers(0, 256)) & (0xFF >> (width % 8))   # junk past the width is not ink
            adv = int(rng.integers(0, 50))
            cells[i] = Cell(len(atlas), width, adv, adv + 1, 0)
            atlas += raw.tobytes()
            inks.append(ink)
        text = rng.integers(0, count, int(rng.integers(0, 40))).astype(np.uint32)
        store = (ctypes.c_uint8 * max(len(atlas), 1)).from_buffer_copy(bytes(atlas) or b"\0")
        for bold in (0, 1):
            want_w = max([1] + [sum(int(cells[j].bold_advance if bold else cells[j].advance) for j in text[:k])
                                + int(cells[text[k]].width) + bold for k in range(len(text)) if cells[text[k]].width])
            pen_end = sum(int(cells[j].bold_advance if bold else cells[j].advance) for j in text)
            out_w = max(want_w, pen_end, 1) + int(rng.integers(0, 9))
            want = np.zeros((rows, out_w), bool)
            pen = 0
            for j in text:
                c = cells[j]
                for dx in range(bold + 1):
                    want[:, pen + dx:pen + dx + c.width] |= inks[j]
                pen += c.bold_advance if bold else c.advance
            got = np.full((rows, (out_w + 7) // 8), 0xAA, np.uint8)
            tp = text.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32))
            rc = lib.neuronte_bits_compose(ptr(got), got.size, out_w, rows, store, len(atlas), cells, count,
                                           tp, len(text), bold)
            ok = rc == pen and (got == np.packbits(want, axis=1)).all()
            # Too narrow a line, or an index past the cells, writes nothing.
            if len(text) and max(want_w, pen_end) > 1:
                keep = got.copy()
                narrow = max(want_w, pen_end) - 1
                ok = ok and lib.neuronte_bits_compose(ptr(got), got.size, narrow, rows, store, len(atlas), cells,
                                                      count, tp, len(text), bold) == -1 and (got == keep).all()
                ok = ok and lib.neuronte_bits_compose(ptr(got), got.size, out_w, rows, store, len(atlas), cells,
                                                      int(text.max()), tp, len(text), bold) == -1 and (got == keep).all()
            bad += not ok
    print(f"check_bits: packed text masks, 200 packings and 600 lines against a pixel loop, {bad} differ")
    return bad


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(1 if text_masks(ctypes.CDLL(os.path.abspath(sys.argv[1]))) else 0)
