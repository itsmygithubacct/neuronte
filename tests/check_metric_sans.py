#!/usr/bin/env python3
"""A Neuronte Sans Metric pixel face, as shipped, draws its drawings exactly
at Helvetica's advances.

    python3 tests/check_metric_sans.py LIB.so FACE.nrt FACE.txt ADVANCES.txt

FACE.nrt is a drawing file of the face's nets and its fine advance table
(train/pack.py --drawing-bundle FACE.nrt ADVANCES.txt NET.json...). FACE.txt
is the pixel face (font/metric-sans-EM.txt or -italic.txt) and ADVANCES.txt
its fine advances file (font/metric-sans-EM.advances.txt).

For every character, regular and bold, drawn alone by neuronte_draw_text()
at the face's em with neuronte_set_binary() on:
- the pixels are exactly the drawing's (bold: struck twice, one pixel apart),
  moved by the table's shift in pixels;
- the pen moves by the table's advance in pixels, (m * em + 500) // 1000;
- neuronte_advance_milli() and neuronte_advance_shift() give the file's
  thousandths.
Then one line of all the characters is drawn and must be the characters'
drawings side by side at those advances. The nets themselves are checked
against numpy by tests/check_reference.py.
"""
import ctypes
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "train"))
import glyphs  # noqa: E402
import pack  # noqa: E402


def main():
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    lib_path, nrt, face_path, adv_path = sys.argv[1:]
    face_em = pack.read_face(face_path)
    if face_em is None:
        raise SystemExit(f"FAIL {face_path} is not a pixel face")
    em = face_em[1]
    art = glyphs.pixel_face(em, face_path)
    table = pack.read_fine(adv_path)
    if table is None or sorted(table) != sorted(map(ord, art)):
        raise SystemExit(f"FAIL {adv_path} is not a fine advances file of the face's characters")
    lib = ctypes.CDLL(lib_path)
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.neuronte_close.argtypes = [ctypes.c_void_p]
    lib.neuronte_set_binary.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.neuronte_draw_text.argtypes = ([ctypes.c_void_p, ctypes.c_void_p] + [ctypes.c_int] * 7
                                       + [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32])
    lib.neuronte_advance_milli.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int]
    lib.neuronte_advance_shift.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int,
                                           ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    h = ctypes.c_void_p()
    if lib.neuronte_open_file(nrt.encode(), ctypes.byref(h)) != 0 or not h:
        raise SystemExit(f"FAIL cannot open {nrt}")
    lib.neuronte_set_binary(h, 1)
    top = glyphs.UI_TOP[em]
    fails = []

    def px(m):
        return (m * em + 500) // 1000

    def shift_px(s):
        q = abs(s) * em
        r = (q + 500) // 1000
        return r if s >= 0 else -r

    def ink(ch, bold):
        rows = art[ch][1]
        a = np.array([[c == "#" for c in r] for r in rows], bool).reshape(em, -1)
        if bold:
            b = np.zeros((em, a.shape[1] + 1), bool)
            b[:, :-1] |= a
            b[:, 1:] |= a
            a = b
        return a

    pad = 2 * em + 4
    for ch in sorted(art, key=ord):
        cp = ord(ch)
        for bold in (0, 1):
            m, s = table[cp][bold], table[cp][2 + bold]
            got_m = lib.neuronte_advance_milli(h, cp, bold)
            sm, sp = ctypes.c_int(), ctypes.c_int()
            lib.neuronte_advance_shift(h, cp, bold, em, ctypes.byref(sm), ctypes.byref(sp))
            if got_m != m or sm.value != s or sp.value != shift_px(s):
                fails.append(f"U+{cp:04X} weight {bold}: the library gives {got_m}/{sm.value}/{sp.value}, "
                             f"the file {m}/{s}/{shift_px(s)}")
            W, H, X, Y = 3 * pad, 2 * em + 4, pad, 2
            buf = np.zeros((H, W), np.uint32)
            t = ch.encode()
            rc = lib.neuronte_draw_text(h, buf.ctypes.data, W, W, H, X, Y, em, bold, t, len(t), 0xFFFFFFFF)
            want = np.zeros((H, W), bool)
            a = ink(ch, bold)
            x0 = X + shift_px(s)
            want[Y + top:Y + top + em, x0:x0 + a.shape[1]] |= a
            if rc != px(m):
                fails.append(f"U+{cp:04X} weight {bold}: the pen moved {rc}, want {px(m)}")
            if ((buf != 0) != want).any() or ((buf != 0) & (buf != 0xFFFFFFFF)).any():
                fails.append(f"U+{cp:04X} weight {bold}: {int(((buf != 0) != want).sum())} pixels are not the face's")
    # one line of every character
    chars = sorted(art, key=ord)
    for bold in (0, 1):
        total = sum(px(table[ord(c)][bold]) for c in chars)
        W, H, X, Y = total + 2 * pad, 2 * em + 4, pad, 2
        buf = np.zeros((H, W), np.uint32)
        t = "".join(chars).encode()
        rc = lib.neuronte_draw_text(h, buf.ctypes.data, W, W, H, X, Y, em, bold, t, len(t), 0xFFFFFFFF)
        want = np.zeros((H, W), bool)
        pen = X
        for c in chars:
            a = ink(c, bold)
            x0 = pen + shift_px(table[ord(c)][2 + bold])
            want[Y + top:Y + top + em, x0:x0 + a.shape[1]] |= a
            pen += px(table[ord(c)][bold])
        if rc != total:
            fails.append(f"line weight {bold}: the pen moved {rc}, want {total}")
        if ((buf != 0) != want).any():
            fails.append(f"line weight {bold}: {int(((buf != 0) != want).sum())} pixels differ")
    lib.neuronte_close(h)
    name = os.path.basename(nrt)
    if fails:
        for f in fails[:20]:
            print("FAIL", name, f)
        raise SystemExit(f"check_metric_sans: {name}: {len(fails)} failures")
    print(f"check_metric_sans: {name}: {len(art)} characters at {em} px, regular and bold, each exactly its "
          f"drawing at Helvetica's advance, and a line of all of them")


if __name__ == "__main__":
    main()
