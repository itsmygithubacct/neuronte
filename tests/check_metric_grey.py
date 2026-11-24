#!/usr/bin/env python3
"""Gate a greyscale Neuronte Sans Metric face (sets uiEMmsg, uiEMmsgi) against its drawing.

usage: check_metric_grey.py LIBNEURONTE FACE.nrt SET ADVANCES.txt [--left-out U+XXXX,...] [--json OUT]

G-GC (coverage): every one of the set's 192 characters is drawn by the library at the face's em
(neuronte_coverage, automatic samples) and compared with the teacher: the set's own strokes
(train/metric_sans_grey.py), their exact signed distance taken through the library's formula, a ramp
one sample wide at the library's sample positions. ink-MAE is the mean |error| over the pixels where
either side has any coverage. Pass: every character ink-MAE <= 0.010 and worst pixel <= 0.15; the face's
mean ink-MAE <= 0.004.

--left-out lists the characters of a group the Method left out (it failed G-GC, was halved once, and a half
still failed): each must be untrained in the file (neuronte_untrained() = 1), so that a consumer can tell
and draw it from the binary face of that em. They are not measured, and the face mean is over the rest.

G-GW (widths): every advance, regular and bold, in thousandths, equals ADVANCES.txt's (the binary face's
fine advances file of that em).

No font file is opened. Exit 0 when both pass, 1 otherwise.
MIT licence; see LICENSE.
"""
import argparse
import ctypes
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "train"))
import glyphs  # noqa: E402
import face_parts  # noqa: E402

CHAR_MAE, CHAR_MAX, FACE_MAE = 0.010, 0.15, 0.004


def teacher(shapes, em, pen, ss):
    if not shapes:
        return np.zeros((2 * em, em))
    n = em * ss
    xs = (np.arange(n) + 0.5) / n
    ys = (np.arange(2 * n) + 0.5) / n
    yy, xx = np.meshgrid(ys, xs, indexing="ij")
    sd = glyphs.signed_distance(shapes, np.stack([xx.ravel(), yy.ravel()], 1), pen).reshape(2 * n, n)
    return np.clip(0.5 + sd * n, 0, 1).reshape(2 * em, ss, em, ss).mean((1, 3))


def fine_advances(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.startswith("U+"):
            t = line.split()
            out[int(t[0][2:], 16)] = (int(t[1]), int(t[2]))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("lib")
    p.add_argument("face")
    p.add_argument("set")
    p.add_argument("advances")
    p.add_argument("--left-out", default="")
    p.add_argument("--json")
    a = p.parse_args()
    em = face_parts.face_em(a.set)
    if em is None or not a.set.removesuffix("i").endswith("msg"):
        raise SystemExit(f"{a.set} is not a greyscale Metric Sans set")
    lib = ctypes.CDLL(a.lib)
    P = ctypes.c_void_p
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(P)]
    lib.neuronte_close.argtypes = [P]
    lib.neuronte_coverage.argtypes = [P, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                      ctypes.POINTER(ctypes.c_float)]
    lib.neuronte_advance_milli.argtypes = [P, ctypes.c_uint32, ctypes.c_int]
    lib.neuronte_untrained.argtypes = [P, ctypes.c_uint32]
    left_out = {int(c.removeprefix("U+"), 16) for c in a.left_out.split(",") if c}
    h = P()
    if lib.neuronte_open_file(a.face.encode(), ctypes.byref(h)) != 0 or not h:
        raise SystemExit(f"cannot open {a.face}")
    ss = 2 if em < 24 else 1
    pen = glyphs.PENS[a.set]
    buf = (ctypes.c_float * (2 * em * em))()
    rows, fails = [], []
    for ch, _, shapes in glyphs.charset(a.set):
        if ord(ch) in left_out:
            if lib.neuronte_untrained(h, ord(ch)) != 1:
                fails.append(f"U+{ord(ch):04X} is listed as left out but is trained in the file")
            continue
        if lib.neuronte_coverage(h, ord(ch), em, 2 * em, 0, buf) != 0:
            raise SystemExit(f"coverage failed for U+{ord(ch):04X}")
        net = np.frombuffer(buf, np.float32).reshape(2 * em, em).astype(np.float64)
        want = teacher(shapes, em, pen, ss)
        d = np.abs(net - want)
        inked = (net > 0) | (want > 0)
        mae = float(d[inked].mean()) if inked.any() else 0.0
        worst = float(d.max())
        rows.append({"cp": f"U+{ord(ch):04X}", "ink_mae": round(mae, 6), "worst": round(worst, 6)})
        if mae > CHAR_MAE or worst > CHAR_MAX:
            fails.append(f"U+{ord(ch):04X} ink-MAE {mae:.4f} worst {worst:.3f}")
    face_mae = float(np.mean([r["ink_mae"] for r in rows]))
    adv = fine_advances(a.advances)
    width_fails = []
    for ch, _, _ in glyphs.charset(a.set):
        cp = ord(ch)
        got = (lib.neuronte_advance_milli(h, cp, 0), lib.neuronte_advance_milli(h, cp, 1))
        if got != adv[cp]:
            width_fails.append(f"U+{cp:04X} {got} != {adv[cp]}")
    lib.neuronte_close(h)
    gc = not fails and face_mae <= FACE_MAE
    gw = not width_fails
    summary = {"set": a.set, "face": os.path.basename(a.face), "em": em, "characters": len(rows), "left_out": [f"U+{c:04X}" for c in sorted(left_out)],
               "face_ink_mae": round(face_mae, 6), "worst_char_ink_mae": max(r["ink_mae"] for r in rows),
               "worst_pixel": max(r["worst"] for r in rows), "G-GC": "PASS" if gc else "FAIL",
               "G-GW": "PASS" if gw else "FAIL", "char_fails": fails, "width_fails": width_fails}
    if a.json:
        with open(a.json + ".tmp", "w") as out:
            json.dump({"summary": summary, "characters": rows}, out, indent=1)
        os.replace(a.json + ".tmp", a.json)
    print(f"{a.set} {os.path.basename(a.face)}: face ink-MAE {face_mae:.4f}, worst character "
          f"{summary['worst_char_ink_mae']:.4f}, worst pixel {summary['worst_pixel']:.3f}; "
          f"G-GC {summary['G-GC']} ({len(fails)} characters fail), G-GW {summary['G-GW']}")
    for f in fails[:20] + width_fails[:20]:
        print("  ", f)
    return 0 if gc and gw else 1


if __name__ == "__main__":
    raise SystemExit(main())
