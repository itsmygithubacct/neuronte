#!/usr/bin/env python3
"""G-MW's line test: Neuronte Sans Metric's advances set a line of text exactly
as long as Helvetica's.

    python3 tests/check_metric_pdf.py [LIBRARY FACE.nrt ...]

tests/fixtures/metric-helvetica.pdf (tools/make-metric-pdf.py) is a page that
GNU groff justified in Helvetica and Helvetica-Bold. Each line is one `TJ`
array of words and the word spaces groff chose. For every justified line, the
words' advances plus the spaces must reach the line length that the page
records, within 0.5/1000 em times the type size.

The advances are the thousandths in font/metric-sans-widths.txt. Given the
library and one or more trained faces, the test takes them instead from each
face's table through neuronte_advance_milli() and also checks that the table
equals the widths file. No font file is opened. The test fails if the PDF
holds a font program (/FontFile, /FontFile2, /FontFile3), a font descriptor
or an embedded file, or names other fonts than the two standard ones.
"""
import ctypes
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "tests", "fixtures", "metric-helvetica.pdf")
WIDTHS = os.path.join(ROOT, "font", "metric-sans-widths.txt")


def widths():
    out = {}
    for line in open(WIDTHS, encoding="utf-8"):
        if line.startswith("U+"):
            t = line.split()
            out[int(t[0][2:], 16)] = (int(t[1]), int(t[2]))
    return out


def pdf_lines():
    """[(bold, size, x, [str | number])], line length, justified indices."""
    data = open(PDF, "rb").read().decode("latin-1")
    ll = float(re.search(r"/NeuronteLineLength (\S+)", data)[1])
    just = [int(v) for v in re.search(r"/NeuronteJustified \[([^\]]*)\]", data)[1].split()]
    out = []
    for m in re.finditer(r"BT /F(\d) (\S+) Tf (\S+) (\S+) Td \[(.*?)\] TJ ET", data):
        f, size, x, _, body = m.groups()
        items, i = [], 0
        while i < len(body):
            c = body[i]
            if c == "(":
                j, s = i + 1, []
                while body[j] != ")":
                    if body[j] == "\\":
                        j += 1
                    s.append(body[j])
                    j += 1
                items.append("".join(s).encode("latin-1").decode("cp1252"))
                i = j + 1
            elif c in "-0123456789.":
                j = i
                while j < len(body) and body[j] in "-0123456789.":
                    j += 1
                items.append(float(body[i:j]))
                i = j
            else:
                i += 1
        out.append((f == "2", float(size), float(x), items))
    return out, ll, just


def no_font_program():
    """The fixture names the standard fonts and must never carry a font: no
    font program key and no embedded stream of one."""
    data = open(PDF, "rb").read()
    for key in (b"/FontFile", b"/FontFile2", b"/FontFile3", b"/FontDescriptor", b"/EmbeddedFile"):
        if key in data:
            raise SystemExit(f"FAIL: {PDF} holds {key.decode()}; no font may be embedded or committed")
    fonts = re.findall(rb"/BaseFont /([A-Za-z-]+)", data)
    if sorted(fonts) != [b"Helvetica", b"Helvetica-Bold"]:
        raise SystemExit(f"FAIL: {PDF} names fonts {fonts}, not the two standard ones")
    print("metric-helvetica.pdf: names Helvetica and Helvetica-Bold, embeds no font program")


def check(name, adv):
    lines, ll, just = pdf_lines()
    if len(just) < 5:
        raise SystemExit(f"FAIL: only {len(just)} justified lines in the fixture")
    worst = 0.0
    for i in just:
        bold, size, x, items = lines[i]
        total = 0.0  # thousandths of the type size
        for v in items:
            if isinstance(v, str):
                for ch in v:
                    a = adv(ord(ch), bold)
                    if a is None:
                        raise SystemExit(f"FAIL {name}: U+{ord(ch):04X} has no advance")
                    total += a
            else:
                total -= v
        end = x + total * size / 1000
        err = abs(end - (72 + ll))  # every line starts at the 1 inch margin
        tol = 0.5 / 1000 * size
        worst = max(worst, err / size * 1000)
        if err > tol:
            raise SystemExit(f"FAIL {name}: line {i} ends at {end:.4f} pt, the line ends at {72 + ll} "
                             f"(off by {err * 1000 / size:.3f}/1000 em, limit 0.5)")
    print(f"{name}: {len(just)} justified lines exact, worst {worst:.4f}/1000 em")


def main():
    no_font_program()
    w = widths()
    check("metric-sans-widths.txt", lambda cp, bold: w[cp][bold] if cp in w else None)
    args = sys.argv[1:]
    if not args:
        return
    lib = ctypes.CDLL(args[0])
    lib.neuronte_open_file.restype = ctypes.c_int
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.neuronte_advance_milli.restype = ctypes.c_int
    lib.neuronte_advance_milli.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int]
    lib.neuronte_close.argtypes = [ctypes.c_void_p]
    for path in args[1:]:
        h = ctypes.c_void_p()
        if lib.neuronte_open_file(path.encode(), ctypes.byref(h)) != 0 or not h:
            raise SystemExit(f"FAIL: cannot open {path}")
        try:
            for cp, (r, b) in w.items():
                got = (lib.neuronte_advance_milli(h, cp, 0), lib.neuronte_advance_milli(h, cp, 1))
                if got != (r, b):
                    raise SystemExit(f"FAIL {path}: U+{cp:04X} advances {got}, the widths file {(r, b)}")
            check(os.path.basename(path), lambda cp, bold: lib.neuronte_advance_milli(h, cp, int(bold)))
        finally:
            lib.neuronte_close(h)


if __name__ == "__main__":
    main()
