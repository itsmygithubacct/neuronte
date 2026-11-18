#!/usr/bin/env python3
"""neuronte_draw_text_exact() and neuronte_text_width_exact().

    python3 tests/check_draw_exact.py LIB.so FACE.nrt[+TABLE.txt]...

FACE.nrt+TABLE.txt is the drawing file FACE.nrt with its advance table
replaced by TABLE.txt packed by train/pack.py (a fine advances file, so a
version 8 table with shifts can be tried on nets that exist), written to a
temporary file under build/ for the test.

For each face (hundredths or thousandths tables alike), at several ems,
regular and bold, binary and blended:
- neuronte_text_width_exact() of a line is round(S * em / 1000), S the sum
  of its characters' neuronte_advance_milli(), and within half a pixel of
  S * em / 1000;
- neuronte_draw_text_exact() returns that width and draws exactly what
  neuronte_draw_text() draws when each character is drawn alone, in order,
  into the same buffer, its pen at x + round(S_k * em / 1000), S_k the sum
  of the thousandths before it (so the shift and the blending are the old
  call's);
- at an em of 100 px, where every advance of a hundredths table is a whole
  pixel, the line is byte for byte neuronte_draw_text()'s;
- bad arguments are refused.
"""
import ctypes
import os
import random
import struct
import sys
import tempfile

import numpy as np


def with_table(spec, tmp):
    """The path to open for one argument: FACE.nrt, or FACE.nrt with TABLE.txt as its table."""
    if "+" not in spec:
        return spec
    face, table = spec.split("+", 1)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train"))
    import pack
    raw = open(face, "rb").read()
    if struct.unpack_from("<I", raw, 8)[0] != 5:
        raise SystemExit(f"FAIL {face} is not a drawing file")
    members = []
    for i in range(struct.unpack_from("<I", raw, 12)[0]):
        off, ln = struct.unpack_from("<2I", raw, 16 + 8 * i)
        im = raw[off:off + ln]
        v = struct.unpack_from("<I", im, 8)[0]
        if v not in (4, 8):
            members.append((v, im))
    members.append(pack.table_image(table))
    out = os.path.join(tmp, f"{len(os.listdir(tmp))}.nrt")
    open(out, "wb").write(pack.drawing_images(members)[0])
    return out


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    lib = ctypes.CDLL(sys.argv[1])
    P = ctypes.c_void_p
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(P)]
    lib.neuronte_close.argtypes = [P]
    lib.neuronte_set_binary.argtypes = [P, ctypes.c_int]
    draw = [P, P] + [ctypes.c_int] * 7 + [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32]
    lib.neuronte_draw_text.argtypes = draw
    lib.neuronte_draw_text_exact.argtypes = draw
    lib.neuronte_text_width_exact.argtypes = [P, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
    lib.neuronte_text_width.argtypes = [P, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int]
    lib.neuronte_advance_milli.argtypes = [P, ctypes.c_uint32, ctypes.c_int]
    lib.neuronte_advances.argtypes = [P]
    rng = random.Random(7)
    pool = [chr(c) for c in range(0x20, 0x7F)] + [chr(c) for c in range(0xA0, 0x100)] + ["…", "�", "一"]
    lines = 0
    build = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build")
    os.makedirs(build, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="check-draw-exact-", dir=build)
    for spec in sys.argv[2:]:
        path = with_table(spec, tmp)
        h = P()
        if lib.neuronte_open_file(path.encode(), ctypes.byref(h)) != 0 or not h:
            raise SystemExit(f"FAIL cannot open {path}")
        try:
            texts = ["Hamburgefonstiv 0123456789", "The quick brown fox jumps over the lazy dog.",
                     "".join(rng.choice(pool) for _ in range(60)), "", "i" * 40, "W" * 7]
            for em in (1, 3, 7, 9, 12, 16, 23, 33, 48):
                for bold in (0, 1):
                    for binary in (1, 0):
                        lib.neuronte_set_binary(h, binary)
                        for text in texts:
                            b = text.encode("utf-8")
                            ms = [lib.neuronte_advance_milli(h, ord(c), bold) for c in text]
                            S = sum(ms)
                            want_w = (S * em + 500) // 1000
                            got_w = lib.neuronte_text_width_exact(h, b, len(b), bold, em)
                            if got_w != want_w or abs(got_w - S * em / 1000) > 0.5:
                                raise SystemExit(f"FAIL {path} em {em} bold {bold}: width {got_w}, want {want_w}")
                            W, H, X, Y = want_w + 4 * em + 8, 2 * em + 4, 2 * em + 2, 2
                            got = np.full((H, W), 0x10203040, np.uint32)
                            rc = lib.neuronte_draw_text_exact(h, got.ctypes.data, W, W, H, X, Y, em, bold, b, len(b), 0xC0FF8000)
                            if rc != want_w:
                                raise SystemExit(f"FAIL {path} em {em} bold {bold}: draw returned {rc}, want {want_w}")
                            ref = np.full((H, W), 0x10203040, np.uint32)
                            acc = 0
                            for c, m in zip(text, ms):
                                cb = c.encode("utf-8")
                                pen = X + (acc * em + 500) // 1000
                                lib.neuronte_draw_text(h, ref.ctypes.data, W, W, H, pen, Y, em, bold, cb, len(cb), 0xC0FF8000)
                                acc += m
                            if em >= 7 and text in texts[:2] and not (got != 0x10203040).any():
                                raise SystemExit(f"FAIL {path} em {em} bold {bold} binary {binary}: nothing was drawn for {text!r}")
                            if (got != ref).any():
                                raise SystemExit(f"FAIL {path} em {em} bold {bold} binary {binary}: "
                                                 f"{int((got != ref).sum())} pixels differ from the characters drawn alone")
                            lines += 1
            # hundredths tables at 100 px: every advance is whole, so both calls agree
            lib.neuronte_set_binary(h, 0)
            b = texts[0].encode()
            fine = any(lib.neuronte_advance_milli(h, ord(c), 0) % 10 for c in texts[0])
            if not fine:
                W, H = lib.neuronte_text_width(h, b, len(b), 0, 100) + 220, 204
                a1 = np.zeros((H, W), np.uint32)
                a2 = np.zeros((H, W), np.uint32)
                r1 = lib.neuronte_draw_text(h, a1.ctypes.data, W, W, H, 2, 2, 100, 0, b, len(b), 0xFFFFFFFF)
                r2 = lib.neuronte_draw_text_exact(h, a2.ctypes.data, W, W, H, 2, 2, 100, 0, b, len(b), 0xFFFFFFFF)
                if r1 != r2 or (a1 != a2).any():
                    raise SystemExit(f"FAIL {path}: at 100 px the exact line differs from neuronte_draw_text()'s")
            # refusals
            buf = np.zeros((4, 4), np.uint32)
            bad = [lib.neuronte_text_width_exact(h, b, len(b), 2, 12), lib.neuronte_text_width_exact(h, None, 3, 0, 12),
                   lib.neuronte_text_width_exact(h, b, len(b), 0, 0), lib.neuronte_text_width_exact(None, b, len(b), 0, 12),
                   lib.neuronte_draw_text_exact(h, buf.ctypes.data, 4, 4, 4, 0, 0, 12, 2, b, len(b), 0xFFFFFFFF),
                   lib.neuronte_draw_text_exact(h, None, 4, 4, 4, 0, 0, 12, 0, b, len(b), 0xFFFFFFFF),
                   lib.neuronte_draw_text_exact(h, buf.ctypes.data, 3, 4, 4, 0, 0, 12, 0, b, len(b), 0xFFFFFFFF),
                   lib.neuronte_draw_text_exact(h, buf.ctypes.data, 4, 4, 4, 0, 0, -1, 0, b, len(b), 0xFFFFFFFF)]
            if any(v >= 0 for v in bad):
                raise SystemExit(f"FAIL {path}: a bad argument was accepted: {bad}")
            # far off the buffer: nothing drawn, no overflow
            far = np.zeros((4, 4), np.uint32)
            lib.neuronte_draw_text_exact(h, far.ctypes.data, 4, 4, 4, 2**31 - 5, 0, 48, 1, b, len(b), 0xFFFFFFFF)
            lib.neuronte_draw_text_exact(h, far.ctypes.data, 4, 4, 4, -2**31, 0, 48, 1, b, len(b), 0xFFFFFFFF)
            if far.any():
                raise SystemExit(f"FAIL {path}: a line far outside the buffer drew into it")
        finally:
            lib.neuronte_close(h)
    import shutil
    shutil.rmtree(tmp)
    print(f"check_draw_exact: {lines} lines in {len(sys.argv) - 2} faces, each exactly its characters at their "
          "true positions, widths within half a pixel")


if __name__ == "__main__":
    main()
