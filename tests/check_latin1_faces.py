"""Check that a Latin-1 face draws its kept characters exactly as the face it extends.

usage: python3 tests/check_latin1_faces.py LIB.so OLD.nrt NEW.nrt CHARS EM... [--blended] [--snap]

CHARS is 'ascii' (printable ASCII and U+2026) or 'ascii+58' (those and the
Latin-1 characters the older Latin-1 files hold: U+00A0, the letters with a
mark and the four spacing marks, train/glyphs.py large_latin1). Each character,
regular and bold, is drawn alone through neuronte_draw_text() into a fresh
canvas at each em: binary by default (neuronte_set_binary 1, as the desktop
draws the pixel faces), blended with --blended. Both files must give the same
pixels and move the pen by the same advance. For the ems listed the old file
must already be the one a consumer uses there, so equality means the new
file changes nothing that was drawn before.
"""
import ctypes
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train"))
import glyphs  # noqa: E402

args = sys.argv[1:]
blended = "--blended" in args
args = [a for a in args if a != "--blended"]
lib_path, old_path, new_path, which = args[:4]
ems = [int(e) for e in args[4:]]
chars = [chr(c) for c in range(32, 127)] + ["…"]
if which == "ascii+58":
    chars += sorted(glyphs.large_latin1())
elif which != "ascii":
    raise SystemExit(__doc__)

lib = ctypes.CDLL(lib_path)
lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
lib.neuronte_close.argtypes = [ctypes.c_void_p]
lib.neuronte_set_binary.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.neuronte_draw_text.argtypes = ([ctypes.c_void_p, ctypes.c_void_p] + [ctypes.c_int] * 7
                                   + [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32])


def opened(path):
    h = ctypes.c_void_p()
    rc = lib.neuronte_open_file(path.encode(), ctypes.byref(h))
    if rc != 0:
        raise SystemExit(f"FAIL {path}: neuronte_open_file returned {rc}")
    lib.neuronte_set_binary(h, 0 if blended else 1)
    return h


def drawn(h, ch, em, bold):
    W, H = 3 * em + 4, 2 * em + 4
    buf = np.zeros((H, W), np.uint32)
    text = ch.encode()
    rc = lib.neuronte_draw_text(h, buf.ctypes.data, W, W, H, 2, 2, em, bold, text, len(text), 0xFFFFFFFF)
    return rc, buf.tobytes()


old, new = opened(old_path), opened(new_path)
failed = 0
for em in ems:
    for ch in chars:
        for bold in (0, 1):
            if drawn(old, ch, em, bold) != drawn(new, ch, em, bold):
                print(f"FAIL U+{ord(ch):04X} at {em} px weight {bold}: {new_path} differs from {old_path}")
                failed += 1
lib.neuronte_close(old)
lib.neuronte_close(new)
if failed:
    raise SystemExit(1)
print(f"{len(chars)} characters at {', '.join(map(str, ems))} px, regular and bold, "
      f"{'blended' if blended else 'binary'}: {os.path.basename(new_path)} draws them exactly as {os.path.basename(old_path)}")
