#!/usr/bin/env python3
"""Count the letters that touch in a face, so that a regression shows.

usage: python3 tests/check_touching.py LIB.so FACE.nrt EM BOLD MAX8 MAX4
       python3 tests/check_touching.py --table TABLE.txt LIB.so [ROOT]

The 189 printed characters of the desktop faces (printable ASCII without the
space, U+2026 and U+00A1..U+00FF without U+00AD), in code order, make 188
adjacent pairs. Each character is drawn alone by neuronte_draw_text(), in
binary mode, at EM with weight BOLD (0 or 1); the next one is drawn alone at
the pen the first one returned. A pair touches when a pixel of one is next to
a pixel of the other: of its 8 neighbours (MAX8), or of its 4 edge neighbours
(MAX4, strokes meeting edge to edge). The test fails when either count is
above its maximum, and prints both counts. A maximum of -1 only prints.

--table reads one line per face and weight, FACE EM BOLD MAX8 MAX4 (FACE a path
under ROOT, default the working directory; blank lines and # lines are
skipped), and runs every one. tests/metric-sans-touching.txt holds the counts
of the shipped Neuronte Sans Metric faces as the limits: a drawing that makes
more letters touch than shipped fails.
"""
import ctypes
import sys

import numpy as np

CHARS = ([chr(c) for c in range(0x21, 0x7F)] + ["…"]
         + [chr(c) for c in range(0xA1, 0x100) if c != 0xAD])
EIGHT = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
FOUR = [(0, 1), (0, -1), (1, 0), (-1, 0)]


def main():
    if len(sys.argv) in (4, 5) and sys.argv[1] == "--table":
        import os
        root = sys.argv[4] if len(sys.argv) == 5 else "."
        n = 0
        for line in open(sys.argv[2]):
            t = line.split()
            if not t or t[0].startswith("#"):
                continue
            face, em, bold, max8, max4 = t
            one(sys.argv[3], os.path.join(root, face), int(em), int(bold), int(max8), int(max4), quiet=True)
            n += 1
        print(f"check_touching: {n} faces and weights within their recorded limits")
        return
    if len(sys.argv) != 7:
        raise SystemExit(__doc__)
    lib_path, nrt, em, bold, max8, max4 = sys.argv[1:]
    one(lib_path, nrt, int(em), int(bold), int(max8), int(max4))


def one(lib_path, nrt, em, bold, max8, max4, quiet=False):
    lib = ctypes.CDLL(lib_path)
    P = ctypes.c_void_p
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(P)]
    lib.neuronte_close.argtypes = [P]
    lib.neuronte_set_binary.argtypes = [P, ctypes.c_int]
    lib.neuronte_draw_text.argtypes = [P, P] + [ctypes.c_int] * 7 + [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32]
    h = P()
    if lib.neuronte_open_file(nrt.encode(), ctypes.byref(h)) != 0 or not h:
        raise SystemExit(f"FAIL cannot open {nrt}")
    lib.neuronte_set_binary(h, 1)
    W, H = 6 * em + 8, 2 * em
    x0 = 2 * em

    def ink(ch, x):
        buf = np.zeros((H, W), np.uint32)
        b = ch.encode()
        adv = lib.neuronte_draw_text(h, buf.ctypes.data, W, W, H, x, 0, em, bold, b, len(b), 0xFFFFFFFF)
        if adv < 0:
            raise SystemExit(f"FAIL U+{ord(ch):04X} does not draw (rc {adv})")
        return (buf & 0xFF) > 127, adv

    def grown(a, nb):
        g = np.zeros_like(a)
        for dy, dx in nb:
            g |= np.roll(np.roll(a, dy, 0), dx, 1)
        return g

    n8 = n4 = 0
    pairs8 = []
    for a, b in zip(CHARS, CHARS[1:]):
        A, adv = ink(a, x0)
        B, _ = ink(b, x0 + adv)
        if (grown(A, EIGHT) & B).any():
            n8 += 1
            pairs8.append(a + b)
        if (grown(A, FOUR) & B).any():
            n4 += 1
    lib.neuronte_close(h)
    bad = (max8 >= 0 and n8 > max8) or (max4 >= 0 and n4 > max4)
    if not quiet or bad:
        print(f"check_touching: {nrt.rsplit('/', 1)[-1]} at {em} px weight {bold}: "
              f"{n8} of {len(CHARS) - 1} pairs touch (8-neighbour), {n4} edge to edge")
    if bad:
        print("FAIL more pairs touch than the recorded", max8, max4, ":", " ".join(pairs8))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
