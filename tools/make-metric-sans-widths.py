#!/usr/bin/env python3
"""Write font/metric-sans-widths.txt, the advances and ink boxes of Neuronte
Sans Metric, from Adobe's Core 14 AFM metric files for Helvetica.

    python3 tools/make-metric-sans-widths.py AFM_DIR [--check]

AFM_DIR holds Helvetica.afm, Helvetica-Bold.afm, Helvetica-Oblique.afm and
Helvetica-BoldOblique.afm (text metric files, not fonts; Debian installs them
with python-matplotlib-data in /usr/share/matplotlib/mpl-data/fonts/pdfcorefonts).
The AFM files are not part of this repository; their notice is in
LICENSES/Adobe-Core14-AFM.txt. Only the numbers below are copied: for each
of the 192 characters of the desktop faces, its glyph name, its width in
Helvetica and in Helvetica-Bold, and its bounding box in Helvetica, all in
thousandths of an em; and the font's cap height, x-height, ascender, descender
and vertical stem width. The script checks that the oblique widths equal the
upright ones. With --check it compares the file in the tree with what it
would write and changes nothing.
"""
import os
import sys

ASCII = ("space exclam quotedbl numbersign dollar percent ampersand quotesingle parenleft parenright "
         "asterisk plus comma hyphen period slash zero one two three four five six seven eight nine colon "
         "semicolon less equal greater question at").split() + [chr(c) for c in range(65, 91)] + \
        "bracketleft backslash bracketright asciicircum underscore grave".split() + \
        [chr(c) for c in range(97, 123)] + "braceleft bar braceright asciitilde".split()
LATIN1 = ("space exclamdown cent sterling currency yen brokenbar section dieresis copyright ordfeminine "
          "guillemotleft logicalnot hyphen registered macron degree plusminus twosuperior threesuperior acute "
          "mu paragraph periodcentered cedilla onesuperior ordmasculine guillemotright onequarter onehalf "
          "threequarters questiondown Agrave Aacute Acircumflex Atilde Adieresis Aring AE Ccedilla Egrave "
          "Eacute Ecircumflex Edieresis Igrave Iacute Icircumflex Idieresis Eth Ntilde Ograve Oacute "
          "Ocircumflex Otilde Odieresis multiply Oslash Ugrave Uacute Ucircumflex Udieresis Yacute Thorn "
          "germandbls agrave aacute acircumflex atilde adieresis aring ae ccedilla egrave eacute ecircumflex "
          "edieresis igrave iacute icircumflex idieresis eth ntilde ograve oacute ocircumflex otilde odieresis "
          "divide oslash ugrave uacute ucircumflex udieresis yacute thorn ydieresis").split()
assert len(ASCII) == 95 and len(LATIN1) == 96
NAMES = {0x20 + i: n for i, n in enumerate(ASCII)}
NAMES.update({0xA0 + i: n for i, n in enumerate(LATIN1)})
NAMES[0x2026] = "ellipsis"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "font", "metric-sans-widths.txt")


def afm(path):
    glyphs, head = {}, {}
    for line in open(path, encoding="latin-1"):
        key = line.split(" ", 1)[0]
        if key in ("CapHeight", "XHeight", "Ascender", "Descender", "StdVW", "Version", "FontName"):
            head[key] = line.split(None, 1)[1].strip()
        if line.startswith("Notice"):
            head["Notice"] = line[7:].strip()
        if line.startswith("C "):
            f = dict(p.strip().split(" ", 1) for p in line.split(";") if p.strip())
            glyphs[f["N"]] = (int(f["WX"]), tuple(int(v) for v in f["B"].split()))
    return glyphs, head


def text(d):
    reg, h = afm(os.path.join(d, "Helvetica.afm"))
    bold, hb = afm(os.path.join(d, "Helvetica-Bold.afm"))
    obl, _ = afm(os.path.join(d, "Helvetica-Oblique.afm"))
    bobl, _ = afm(os.path.join(d, "Helvetica-BoldOblique.afm"))
    if {k: v[0] for k, v in obl.items()} != {k: v[0] for k, v in reg.items()}:
        raise SystemExit("Helvetica-Oblique's widths differ from Helvetica's")
    if {k: v[0] for k, v in bobl.items()} != {k: v[0] for k, v in bold.items()}:
        raise SystemExit("Helvetica-BoldOblique's widths differ from Helvetica-Bold's")
    lines = [
        "# Neuronte Sans Metric: the advance of each character, in thousandths of an em,",
        "# regular then bold, and its ink box in the regular weight (left, bottom, right,",
        "# top; y up from the baseline), with its AFM glyph name.",
        "# THESE NUMBERS ARE COPIED from Adobe's Core 14 AFM metric files Helvetica.afm",
        f"# ({h.get('Version')}) and Helvetica-Bold.afm ({hb.get('Version')}) by",
        "# tools/make-metric-sans-widths.py. Helvetica-Oblique and Helvetica-BoldOblique",
        "# have the same widths, which the script checks. The AFM files' notices:",
        f"#   {h.get('Notice')}",
        f"#   {hb.get('Notice')}",
        "# and Adobe's terms are in LICENSES/Adobe-Core14-AFM.txt. No font file was opened.",
        "# U+00A0 takes the metrics of `space`, U+00AD those of `hyphen`.",
        "# Lines starting M are the font's own: cap height, x-height, ascender, descender",
        "# and the vertical stem width of the regular and the bold weight.",
        f"M CapHeight {h['CapHeight']} {hb['CapHeight']}",
        f"M XHeight {h['XHeight']} {hb['XHeight']}",
        f"M Ascender {h['Ascender']} {hb['Ascender']}",
        f"M Descender {h['Descender']} {hb['Descender']}",
        f"M StdVW {h['StdVW']} {hb['StdVW']}",
    ]
    for cp in sorted(NAMES):
        n = NAMES[cp]
        w, box = reg[n]
        lines.append(f"U+{cp:04X} {w} {bold[n][0]} {' '.join(map(str, box))} {n}")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    t = text(sys.argv[1])
    if "--check" in sys.argv:
        same = os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == t
        print("metric-sans-widths.txt:", "current" if same else "DIFFERS")
        raise SystemExit(0 if same else 1)
    tmp = OUT + ".tmp"
    open(tmp, "w", encoding="utf-8").write(t)
    os.replace(tmp, OUT)
    print(f"wrote {OUT}: {t.count(chr(10) + 'U+')} characters")


def read(path=OUT):
    """{scalar: (width, bold width, (llx, lly, urx, ury), name)}, {metric: (regular, bold)}."""
    chars, metrics = {}, {}
    for line in open(path, encoding="utf-8"):
        t = line.split()
        if line.startswith("M "):
            metrics[t[1]] = (int(t[2]), int(t[3]))
        elif line.startswith("U+"):
            chars[int(t[0][2:], 16)] = (int(t[1]), int(t[2]), tuple(int(v) for v in t[3:7]), t[7])
    return chars, metrics


if __name__ == "__main__":
    main()
