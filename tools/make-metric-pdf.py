#!/usr/bin/env python3
r"""Make tests/fixtures/metric-helvetica.pdf: a page of justified text set in
Helvetica and Helvetica-Bold by GNU groff, for tests/check_metric_pdf.py.

    python3 tools/make-metric-pdf.py [--check]

groff (1.23, `groff -k -Tps -Z`, kerning and ligatures off, both margins
justified) lays the text out from its own description of Helvetica's metrics
(devps/HR and HB, metric files; no font file is opened). Its output lists each
line's words and the exact moves between them in 1/1000 point. This script
writes them as a PDF page:
- each line is one text object, the line's start by `Td` and its text by one
  `TJ` array of the words, each word space as a number;
- the fonts are the standard-14 /Helvetica and /Helvetica-Bold, not embedded,
  WinAnsiEncoding;
- the page dictionary has /NeuronteLineLength, groff's line length in points,
  and /NeuronteJustified, the indices of the lines groff justified.

A character groff draws by itself (its `C` command, used here for the Latin-1
letters) is followed in groff's output by a move of exactly its width, which is
dropped and the character written into the word's string. At the end of a word
groff would fold that width into the word space, so every such character in the
text is inside a word (or followed by one that is); the script stops otherwise.
A line counts as justified unless it ends its paragraph. groff reads a plain `'`
and `` ` `` as typographic quotes, so the text writes the ASCII ones as \(aq and \(ga. The file holds no clock, so the same groff
gives the same bytes; --check compares with the file in the tree.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tests", "fixtures", "metric-helvetica.pdf")
SOURCE = r""".fam H
.kern 0
.lg 0
.ad b
.ps 11
.vs 14
.ll 4i
.ft R
The quick brown fox jumps over the lazy dog, while Mr. Jock, TV quiz Ph.D., bags few lynx and waltzes. Sphinx of black quartz, judge my vow! How vexingly quick daft zebras jump; 0123456789 times (a+b) = [c] {d} <e> @ # $ % & * ? / \e | ~ ^ _ x\(gay x\(aqy " and the end.
.sp
.ps 9
Small print at nine points: pack my box with five dozen liquor jugs, then grab the jinxed wizards who plucked ivy from the big quilt, and keep going until the line is long enough.
.sp
.ps 11
.ft B
Bold text: Müller paid £12.50 for a½b cafés au lait x«chez»y Sørensen\(aqs x«grüße»y while the jovial quartermaster weighed extra boxes of fizzy grapefruit juice; Ægir, Ølstad, Ñandús and Øresund\(aqs naïve façades.
"""
# groff glyph names (groff_char(7)) of the characters above
NAMES = {"12": "½", "'e": "é", "Fc": "»", "Fo": "«", "/o": "ø", "Po": "£",
         ":u": "ü", "rs": "\\", "ti": "~", "ha": "^", "ga": "`", "aq": "'", "dq": '"', "lB": "[",
         "rB": "]", "lC": "{", "rC": "}", "ba": "|", "at": "@", "sh": "#", "Do": "$", "sl": "/", "ul": "_",
         "<": "<", ">": ">", "pl": "+", "eq": "=", "hy": "-", "ss": "\u00df", "AE": "\u00c6", "/O": "\u00d8", "~N": "\u00d1", "'u": "\u00fa",
         ":i": "\u00ef", ",c": "\u00e7", "'a": "\u00e1", ":a": "\u00e4", ":o": "\u00f6"}
FONTS = {"HR": "Helvetica", "HB": "Helvetica-Bold"}


def groff():
    r = subprocess.run(["groff", "-k", "-Tps", "-Z"], input=SOURCE.encode(), capture_output=True, check=True)
    return r.stdout.decode("latin-1").splitlines()


def lines():
    """[(font, size_pt, x_pt, y_pt, [str | float space_in_1/1000pt])], line length (pt)."""
    out, fonts, cur = [], {}, None
    font = size = None
    x = y = 0
    pending = None  # a C glyph waiting for its width move
    for raw in groff():
        if raw.startswith("x font "):
            _, _, n, name = raw.split()
            fonts[n] = name
            continue
        if raw.startswith(("x ", "D", "m", "p")):
            continue
        cmd, arg = raw[:1], raw[1:]
        if cmd == "f":
            font = fonts[arg]
        elif cmd == "s":
            size = int(arg)
        elif cmd == "V":
            y = int(arg)
        elif cmd == "H":
            x = int(arg)
            cur = (FONTS[font], size / 1000, x / 1000, y / 1000, [])
            out.append(cur)
        elif cmd == "t":
            if cur[4] and isinstance(cur[4][-1], str) and pending is None:
                cur[4][-1] += arg
            else:
                cur[4].append(arg)
            pending = None
        elif cmd == "C":
            ch = NAMES.get(arg) or (chr(int(arg[1:], 16)) if re.fullmatch(r"u[0-9A-F]{4}", arg) else None)
            if ch is None:
                raise SystemExit(f"unknown groff glyph {arg!r}")
            if cur[4] and isinstance(cur[4][-1], str):
                cur[4][-1] += ch
            else:
                cur[4].append(ch)
            pending = ch
        elif cmd == "h" and pending is not None:
            pending = None  # the width of the glyph just drawn
            continue
        elif pending is not None:
            raise SystemExit(f"groff glyph {pending!r} is not followed by its own width; keep it inside a word")
        elif cmd == "w":
            if arg.startswith("h"):
                cur[4].append(int(arg[1:]))
        elif cmd == "h":
            cur[4].append(int(arg))
        elif cmd == "n":
            pass
    ll = int(re.search(r"\.ll (\d+)i", SOURCE)[1]) * 72
    return out, ll


def pdf_string(s):
    b = s.encode("cp1252")
    return "(" + b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)").decode("latin-1") + ")"


def build():
    ls, ll = lines()
    justified = []
    ops = []
    page_h = 792
    vs = int(re.search(r"\.vs (\d+)", SOURCE)[1])
    for i, (font, size, x, y, items) in enumerate(ls):
        if i + 1 < len(ls) and abs(ls[i + 1][3] - y - vs) < 1e-9:  # the next line is the same paragraph's
            justified.append(i)
        arr = []
        for v in items:
            if isinstance(v, str):
                arr.append(pdf_string(v))
            else:  # a move of v/1000 pt, in TJ's thousandths of the font size (minus is right)
                arr.append(f"{-v / size:.6f}".rstrip("0").rstrip("."))
        f = "F1" if font == "Helvetica" else "F2"
        ops.append(f"BT /{f} {size:g} Tf {x:g} {page_h - y:g} Td [{' '.join(arr)}] TJ ET")
    content = "\n".join(ops).encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
         f"/Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> /NeuronteLineLength {ll} "
         f"/NeuronteJustified [{' '.join(map(str, justified))}] >>").encode(),
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    out = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offs = []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return out, len(ls), len(justified)


def main():
    data, n, j = build()
    if "--check" in sys.argv:
        same = os.path.exists(OUT) and open(OUT, "rb").read() == data
        print("metric-helvetica.pdf:", "current" if same else "DIFFERS")
        raise SystemExit(0 if same else 1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT + ".tmp", "wb").write(data)
    os.replace(OUT + ".tmp", OUT)
    print(f"wrote {OUT}: {n} lines, {j} justified")


if __name__ == "__main__":
    main()
