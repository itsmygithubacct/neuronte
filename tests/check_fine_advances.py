"""Fine advance tables: a version 4 table in thousandths of an em (100 units
per em) and a version 8 table, thousandths plus a shift of each letter's
drawing, regular and bold.

    python3 tests/check_fine_advances.py build/libneuronte.so [DRAWING.nrt ...]

Checks, with tables made here byte by byte:
- the calls on a standalone table: records, milli, steps, pixels, shifts,
  text width, the fallback;
- every damaged or out-of-bounds table is refused, and a table in
  hundredths still reads as before;
- for each drawing file given (a shipped face with a version 4 table in
  hundredths), the same file with its table rewritten in thousandths, as
  version 4 and as version 8 with no shift, draws byte for byte as the
  original, regular and bold, at several ems, from memory and from a file;
- the same file with shifts draws each letter where the original draws it
  moved by the shift's pixels, and moves the pen as before.
"""
import ctypes
import os
import struct
import sys
import tempfile

lib = ctypes.CDLL(os.path.abspath(sys.argv[1]))
V, U32, I = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int
lib.neuronte_open.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(V)]
lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(V)]
lib.neuronte_close.argtypes = [V]
lib.neuronte_advances.argtypes = [V]
lib.neuronte_advance_steps.argtypes = [V, U32, I]
lib.neuronte_advance_milli.argtypes = [V, U32, I]
lib.neuronte_advance.argtypes = [V, U32, I, I]
lib.neuronte_advance_scalar.argtypes = [V, U32]
lib.neuronte_advance_scalar.restype = U32
lib.neuronte_advance_shift.argtypes = [V, U32, I, I, ctypes.POINTER(I), ctypes.POINTER(I)]
lib.neuronte_text_width.argtypes = [V, ctypes.c_char_p, ctypes.c_size_t, I, I]
lib.neuronte_set_binary.argtypes = [V, I]
lib.neuronte_draw_text.argtypes = [V, ctypes.POINTER(U32), I, I, I, I, I, I, I, ctypes.c_char_p, ctypes.c_size_t, U32]
lib.neuronte_draw_text_stroke.argtypes = [V, ctypes.POINTER(U32), I, I, I, I, I, I, I, ctypes.c_char_p, ctypes.c_size_t, U32]
OK, ERR_ARG, ERR_FORMAT = 0, -1, -2

failures = 0


def check(cond, what):
    global failures
    if not cond:
        failures += 1
        print("FAIL", what)


def table(records, version=4, units=100, steps=10, weights=2, fallback=0x3F, count=None, extra=b""):
    """records: (scalar, regular, bold[, shift_regular, shift_bold])."""
    out = b"NEURONTE" + struct.pack("<6I", version, units, steps, weights,
                                    len(records) if count is None else count, fallback)
    for r in records:
        out += struct.pack("<IHH", r[0], r[1], r[2])
        if version == 8:
            out += struct.pack("<hh", *(r[3:5] if len(r) > 3 else (0, 0)))
    return out + extra


def opened(data):
    h = V()
    rc = lib.neuronte_open(data, len(data), ctypes.byref(h))
    return rc, h


def shift(h, s, bold, em):
    m, p = I(), I()
    rc = lib.neuronte_advance_shift(h, s, bold, em, ctypes.byref(m), ctypes.byref(p))
    return rc, m.value, p.value


# ---- standalone tables
fine = [(0x20, 278, 278), (0x3F, 556, 611), (0x2026, 1000, 1000)]
rc, h = opened(table(fine))
check(rc == OK, f"fine version 4 opens ({rc})")
check(lib.neuronte_advances(h) == 3, "three records")
for s, r, b in fine:
    for w, v in ((0, r), (1, b)):
        check(lib.neuronte_advance_milli(h, s, w) == v, f"milli U+{s:04X} w{w}")
        check(lib.neuronte_advance_steps(h, s, w) == (v + 5) // 10, f"steps U+{s:04X} w{w}")
        for em in list(range(1, 130)) + [1000, 4095, 4096]:
            check(lib.neuronte_advance(h, s, w, em) == (v * em + 500) // 1000, f"px U+{s:04X} w{w} em {em}")
        check(shift(h, s, w, 16) == (OK, 0, 0), "no shift in version 4")
check(lib.neuronte_advance_milli(h, ord("A"), 0) == 556 and lib.neuronte_advance_scalar(h, ord("A")) == 0x3F, "fallback")
text = "? …A".encode()
for em in (9, 11, 16, 33, 100):
    want = sum((v * em + 500) // 1000 for v in (556, 278, 1000, 556))
    check(lib.neuronte_text_width(h, text, len(text), 0, em) == want, f"text width at {em}")
check(lib.neuronte_advance_milli(h, 0x3F, 2) == ERR_ARG and lib.neuronte_advance_milli(None, 0x3F, 0) == ERR_ARG,
      "milli argument checks")
check(lib.neuronte_advance_shift(h, 0x3F, 0, 0, None, None) == ERR_ARG and
      lib.neuronte_advance_shift(h, 0x3F, 0, 4097, None, None) == ERR_ARG and
      lib.neuronte_advance_shift(h, 0x3F, 0, 12, None, None) == OK, "shift argument checks")
lib.neuronte_close(h)

# shifts, rounding to the nearest pixel, a tie away from zero
v8 = [(0x20, 278, 278, 0, 0), (0x3F, 556, 611, 50, -50), (0x2026, 1000, 1000, -500, 500)]
rc, h = opened(table(v8, version=8))
check(rc == OK, f"version 8 opens ({rc})")
check(shift(h, 0x3F, 0, 10) == (OK, 50, 1) and shift(h, 0x3F, 1, 10) == (OK, -50, -1), "ties go away from zero")
check(shift(h, 0x3F, 0, 9) == (OK, 50, 0) and shift(h, 0x3F, 1, 9) == (OK, -50, 0), "0.45 px rounds to 0")
check(shift(h, 0x2026, 0, 33) == (OK, -500, -17) and shift(h, 0x2026, 1, 33) == (OK, 500, 17), "half an em")
check(lib.neuronte_advance(h, 0x3F, 1, 16) == (611 * 16 + 500) // 1000, "version 8 pixels")
lib.neuronte_close(h)

# a table in hundredths reads as before
rc, h = opened(table([(0x20, 30, 30), (0x3F, 55, 62)], units=10))
check(rc == OK and lib.neuronte_advance(h, 0x3F, 0, 10) == 6 and lib.neuronte_advance(h, 0x3F, 1, 11) == 7 and
      lib.neuronte_advance_milli(h, 0x3F, 1) == 620 and shift(h, 0x3F, 1, 11) == (OK, 0, 0), "hundredths unchanged")
lib.neuronte_close(h)

# refusals
bad = {
    "version 8 in hundredths": table(v8, version=8, units=10),
    "units 20": table(fine, units=20),
    "steps 100": table(fine, steps=100),
    "one weight": table(fine, weights=1),
    "milli 99": table([(0x3F, 99, 611)]),
    "milli 2001": table([(0x3F, 556, 2001)]),
    "shift 501": table([(0x3F, 556, 611, 501, 0)], version=8),
    "shift -501": table([(0x3F, 556, 611, 0, -501)], version=8),
    "version 8 cut short": table(v8, version=8)[:-1],
    "version 8 a byte long": table(v8, version=8, extra=b"\0"),
    "version 8 with version 4 records": table(fine, version=4)[:8] + struct.pack("<I", 8) + table(fine)[12:],
    "fallback absent": table(fine, fallback=0x41),
    "scalars not rising": table([(0x3F, 556, 611), (0x20, 278, 278)]),
    "a surrogate": table([(0x3F, 556, 611), (0xD800, 500, 500)]),
    "no records": table([], count=0),
    "version 9": table(fine, version=9),
}
for what, data in bad.items():
    rc, h = opened(data)
    check(rc == ERR_FORMAT, f"refused: {what} ({rc})")
    if rc == OK:
        lib.neuronte_close(h)


# ---- drawing files: rewrite the table and draw
def members(data):
    assert data[:8] == b"NEURONTE" and struct.unpack_from("<I", data, 8)[0] == 5
    m = struct.unpack_from("<I", data, 12)[0]
    return [data[o:o + n] for o, n in (struct.unpack_from("<II", data, 16 + 8 * i) for i in range(m))]


def drawing(mems):
    head = 16 + 8 * len(mems)
    out, off = b"NEURONTE" + struct.pack("<II", 5, len(mems)), head
    for m in mems:
        out += struct.pack("<II", off, len(m))
        off += len(m)
    return out + b"".join(mems)


def old_records(t):
    n, fb = struct.unpack_from("<II", t, 24)
    return [struct.unpack_from("<IHH", t, 32 + 8 * i) for i in range(n)], fb


def draw(h, text, em, bold, stroke=None, x=7):
    W, H = 64 * em + 32, 2 * em + 8
    buf = (U32 * (W * H))()
    if stroke is None:
        rc = lib.neuronte_draw_text(h, buf, W, W, H, x, 3, em, bold, text, len(text), 0xFF000000)
    else:
        rc = lib.neuronte_draw_text_stroke(h, buf, W, W, H, x, 3, em, stroke, text, len(text), 0xFF000000)
    return rc, bytes(buf)


def from_file(data):
    with tempfile.NamedTemporaryFile(suffix=".nrt", delete=False) as f:
        f.write(data)
    h = V()
    rc = lib.neuronte_open_file(f.name.encode(), ctypes.byref(h))
    os.unlink(f.name)
    return rc, h


for path in sys.argv[2:]:
    data = open(path, "rb").read()
    mems = members(data)
    ti = [i for i, m in enumerate(mems) if struct.unpack_from("<I", m, 8)[0] == 4]
    assert len(ti) == 1, path
    recs, fb = old_records(mems[ti[0]])
    scalars = [r[0] for r in recs]
    text = "".join(chr(s) for s in scalars if s >= 0x21)[:40].encode() + b" A\xc3\xa9?"
    rc, orig = opened(data)
    assert rc == OK, (path, rc)
    variants = {
        "v4 thousandths": table([(s, a * 10, b * 10) for s, a, b in recs], fallback=fb),
        "v8 no shift": table([(s, a * 10, b * 10, 0, 0) for s, a, b in recs], version=8, fallback=fb),
    }
    for what, t in variants.items():
        new = drawing(mems[:ti[0]] + [t] + mems[ti[0] + 1:])
        for opener in (opened, from_file):
            rc, h = opener(new)
            check(rc == OK, f"{path} {what} opens ({rc})")
            if rc != OK:
                continue
            for binary in (0, 1):
                lib.neuronte_set_binary(orig, binary)
                lib.neuronte_set_binary(h, binary)
                for em in (11, 17, 24, 33, 48):
                    for bold in (0, 1):
                        check(draw(h, text, em, bold) == draw(orig, text, em, bold),
                              f"{path} {what} draws as before at {em} bold {bold} binary {binary}")
                    check(draw(h, text, em, 0, stroke=2) == draw(orig, text, em, 0, stroke=2),
                          f"{path} {what} stroke draw as before at {em}")
            lib.neuronte_close(h)
    # shifts: each letter where the original draws it, moved
    sh = {s: ((i * 37) % 161 - 80, (i * 53) % 201 - 100) for i, s in enumerate(scalars)}
    new = drawing(mems[:ti[0]] + [table([(s, a * 10, b * 10, *sh[s]) for s, a, b in recs], version=8,
                                        fallback=fb)] + mems[ti[0] + 1:])
    rc, h = opened(new)
    check(rc == OK, f"{path} shifted opens")
    lib.neuronte_set_binary(orig, 0)
    lib.neuronte_set_binary(h, 0)
    chars = text.decode()
    for em in (11, 24, 48):
        for bold in (0, 1):
            for stroke in (None, 2):
                W, Hh = 64 * em + 32, 2 * em + 8
                want = (U32 * (W * Hh))()
                pen = 40
                for c in chars:
                    s = lib.neuronte_advance_scalar(orig, ord(c))
                    w = bold if stroke is None else 0
                    v = sh[s][w] * em
                    dx = (v + 500) // 1000 if v >= 0 else -((-v + 500) // 1000)
                    one = c.encode()
                    if stroke is None:
                        lib.neuronte_draw_text(orig, want, W, W, Hh, pen + dx, 3, em, bold, one, len(one), 0xFF000000)
                        pen += lib.neuronte_advance(orig, ord(c), bold, em)
                    else:
                        lib.neuronte_draw_text_stroke(orig, want, W, W, Hh, pen + dx, 3, em, stroke, one, len(one),
                                                      0xFF000000)
                        pen += lib.neuronte_advance(orig, ord(c), 0, em) + stroke
                rc2, got = draw(h, text, em, bold, stroke=stroke, x=40)
                check(got == bytes(want) and rc2 == pen - 40,
                      f"{path} shifted draw at {em} bold {bold} stroke {stroke}")
    lib.neuronte_close(h)
    lib.neuronte_close(orig)
    print(f"{path}: {len(recs)} records, rewritten tables draw as the original")

if failures:
    print(f"{failures} failures")
    sys.exit(1)
print("fine advance tables: all checks passed")
