#!/usr/bin/env python3
"""A Neuronte Sans Metric pixel face, as shipped, draws its drawings exactly
at Helvetica's advances.

    python3 tests/check_metric_sans.py LIB.so FACE.nrt FACE.txt ADVANCES.txt
    python3 tests/check_metric_sans.py --large LIB.so FACE.nrt REF.nrt ADVANCES.txt
    python3 tests/check_metric_sans.py --hundredths ADVANCES.txt OUT.txt

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

--large checks the large or scaled face, FACE.nrt, whose table is the
version 8 table of ADVANCES.txt (font/metric-sans-advances.txt), against
REF.nrt, a drawing file of the same nets (and letter edges) with any table,
which tests/check_reference.py or tests/check_letter_snap.py has checked:
- at every em from 1 to 128 and at 4096, every character's advance and
  shift, regular and bold, are the file's thousandths and their pixels
  ((m * em + 500) // 1000; shifts to the nearest, a half away from zero);
- at 17, 24, 32, 33, 48 and 64 px, blended and binary, regular and bold,
  every character drawn alone is REF.nrt's drawing moved by its shift, and
  a line of all of them is those drawings at the advances.

--hundredths writes ADVANCES.txt's advances rounded to hundredths of an em
as an advances file for train/pack.py, so that REF.nrt can be packed and
checked by tests/check_reference.py and tests/check_letter_snap.py, which
read only hundredths. REF.nrt is a test file, never shipped.
"""
import ctypes
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "train"))
import glyphs  # noqa: E402
import pack  # noqa: E402


def shift_pixels(s, em):
    r = (abs(s) * em + 500) // 1000
    return r if s >= 0 else -r


def large(lib_path, nrt, ref, adv_path):
    table = pack.read_fine(adv_path)
    if table is None:
        raise SystemExit(f"FAIL {adv_path} is not a fine advances file")
    lib = ctypes.CDLL(lib_path)
    P = ctypes.c_void_p
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(P)]
    lib.neuronte_close.argtypes = [P]
    lib.neuronte_set_binary.argtypes = [P, ctypes.c_int]
    lib.neuronte_draw_text.argtypes = [P, P] + [ctypes.c_int] * 7 + [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32]
    lib.neuronte_advance.argtypes = [P, ctypes.c_uint32, ctypes.c_int, ctypes.c_int]
    lib.neuronte_advance_milli.argtypes = [P, ctypes.c_uint32, ctypes.c_int]
    lib.neuronte_advance_shift.argtypes = [P, ctypes.c_uint32, ctypes.c_int, ctypes.c_int,
                                           ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    lib.neuronte_advances.argtypes = [P]
    h, r = P(), P()
    for path, handle in ((nrt, h), (ref, r)):
        if lib.neuronte_open_file(path.encode(), ctypes.byref(handle)) != 0 or not handle:
            raise SystemExit(f"FAIL cannot open {path}")
    fails = []
    if lib.neuronte_advances(h) != len(table):
        fails.append(f"the file has {lib.neuronte_advances(h)} advances, the table {len(table)}")
    sm, sp = ctypes.c_int(), ctypes.c_int()
    for cp, rec in sorted(table.items()):
        for bold in (0, 1):
            m, s = rec[bold], rec[2 + bold]
            if lib.neuronte_advance_milli(h, cp, bold) != m:
                fails.append(f"U+{cp:04X} weight {bold}: thousandths {lib.neuronte_advance_milli(h, cp, bold)}, want {m}")
            for em in list(range(1, 129)) + [4096]:
                got = lib.neuronte_advance(h, cp, bold, em)
                lib.neuronte_advance_shift(h, cp, bold, em, ctypes.byref(sm), ctypes.byref(sp))
                if got != (m * em + 500) // 1000 or sm.value != s or sp.value != shift_pixels(s, em):
                    fails.append(f"U+{cp:04X} weight {bold} at {em} px: advance {got}, shift {sm.value}/{sp.value}")
                    break
    chars = [chr(c) for c in sorted(table)]
    drawn = 0
    for em in (17, 24, 32, 33, 48, 64):
        for binary in (0, 1):
            lib.neuronte_set_binary(h, binary)
            lib.neuronte_set_binary(r, binary)
            for bold in (0, 1):
                pad = 2 * em + 4
                H = 2 * em + 4
                total = sum((table[ord(c)][bold] * em + 500) // 1000 for c in chars)
                W = total + 2 * pad
                line_ref = np.zeros((H, W), np.uint32)
                pen = pad
                for c in chars:
                    b = c.encode()
                    dx = shift_pixels(table[ord(c)][2 + bold], em)
                    one = np.zeros((H, 3 * pad), np.uint32)
                    lib.neuronte_draw_text(h, one.ctypes.data, 3 * pad, 3 * pad, H, pad, 2, em, bold, b, len(b), 0xFFFFFFFF)
                    want = np.zeros((H, 3 * pad), np.uint32)
                    lib.neuronte_draw_text(r, want.ctypes.data, 3 * pad, 3 * pad, H, pad + dx, 2, em, bold, b, len(b), 0xFFFFFFFF)
                    if (one != want).any():
                        fails.append(f"U+{ord(c):04X} at {em} px weight {bold} binary {binary}: "
                                     f"{int((one != want).sum())} pixels differ from the reference moved {dx}")
                    lib.neuronte_draw_text(r, line_ref.ctypes.data, W, W, H, pen + dx, 2, em, bold, b, len(b), 0xFFFFFFFF)
                    pen += (table[ord(c)][bold] * em + 500) // 1000
                    drawn += 1
                line = np.zeros((H, W), np.uint32)
                t = "".join(chars).encode()
                rc = lib.neuronte_draw_text(h, line.ctypes.data, W, W, H, pad, 2, em, bold, t, len(t), 0xFFFFFFFF)
                if rc != total or (line != line_ref).any():
                    fails.append(f"the line at {em} px weight {bold} binary {binary}: pen {rc} (want {total}), "
                                 f"{int((line != line_ref).sum())} pixels differ")
    lib.neuronte_close(h)
    lib.neuronte_close(r)
    name = os.path.basename(nrt)
    if fails:
        for f in fails[:20]:
            print("FAIL", name, f)
        raise SystemExit(f"check_metric_sans: {name}: {len(fails)} failures")
    print(f"check_metric_sans: {name}: {len(table)} advances and shifts at 129 ems, regular and bold; "
          f"{drawn} letters drawn alone and in lines, each the reference's moved by its shift")


def hundredths(adv_path, out):
    table = pack.read_fine(adv_path)
    if table is None:
        raise SystemExit(f"FAIL {adv_path} is not a fine advances file")
    lines = [f"# {os.path.basename(adv_path)} rounded to hundredths, for the reference checks only"]
    for cp, (r, b, _, _) in sorted(table.items()):
        lines.append(f"U+{cp:04X} {(r + 5) // 10 / 10:.1f} {(b + 5) // 10 / 10:.1f}")
    open(out, "w").write("\n".join(lines) + "\n")


def main():
    if sys.argv[1:2] == ["--hundredths"] and len(sys.argv) == 4:
        return hundredths(*sys.argv[2:])
    if sys.argv[1:2] == ["--large"] and len(sys.argv) == 6:
        return large(*sys.argv[2:])
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
