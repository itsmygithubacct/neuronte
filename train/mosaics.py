"""Make font/octants.txt from Unicode's UnicodeData.txt, and check the
other mosaic characters glyphs.py draws against the same file.

usage: python3 train/mosaics.py UnicodeData.txt VERSION [--out font/octants.txt]

A code point in U+1CD00..U+1CDE5 is not its pattern. It is the pattern's
rank among the 230 octant patterns that had no character before Unicode
16, which names each by its filled cells: BLOCK OCTANT-1345, cells
numbered 1 2 / 3 4 / 5 6 / 7 8 by row of a 2 x 4 lattice. Python's
unicodedata here may be older than 16, so the names are read from the
file. The table written records the version and the file's sha256.

Checks, each against the file:

- every octant name parses, and in code point order the patterns rise;
- the 26 patterns with no octant are exactly the ones drawn from other
  characters: space, 17 block elements and the 8 in glyphs.SUBSTITUTES,
  each of which has the name expected here;
- the sextants U+1FB00..U+1FB3B are named by the cells glyphs.sextant()
  gives them.
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphs  # noqa: E402

# The octant patterns Unicode encodes outside the octant range, with the
# names they have there. Bit n - 1 is cell n.
ELSEWHERE = {
    0: (0x0020, "SPACE"),
    255: (0x2588, "FULL BLOCK"),
    15: (0x2580, "UPPER HALF BLOCK"),
    240: (0x2584, "LOWER HALF BLOCK"),
    85: (0x258C, "LEFT HALF BLOCK"),
    170: (0x2590, "RIGHT HALF BLOCK"),
    192: (0x2582, "LOWER ONE QUARTER BLOCK"),
    252: (0x2586, "LOWER THREE QUARTERS BLOCK"),
    80: (0x2596, "QUADRANT LOWER LEFT"),
    160: (0x2597, "QUADRANT LOWER RIGHT"),
    5: (0x2598, "QUADRANT UPPER LEFT"),
    245: (0x2599, "QUADRANT UPPER LEFT AND LOWER LEFT AND LOWER RIGHT"),
    165: (0x259A, "QUADRANT UPPER LEFT AND LOWER RIGHT"),
    95: (0x259B, "QUADRANT UPPER LEFT AND UPPER RIGHT AND LOWER LEFT"),
    175: (0x259C, "QUADRANT UPPER LEFT AND UPPER RIGHT AND LOWER RIGHT"),
    10: (0x259D, "QUADRANT UPPER RIGHT"),
    90: (0x259E, "QUADRANT UPPER RIGHT AND LOWER LEFT"),
    250: (0x259F, "QUADRANT UPPER RIGHT AND LOWER LEFT AND LOWER RIGHT"),
}
SUBSTITUTE_NAMES = {
    0x1FB82: "UPPER ONE QUARTER BLOCK",
    0x1FB85: "UPPER THREE QUARTERS BLOCK",
    0x1FBE6: "MIDDLE LEFT ONE QUARTER BLOCK",
    0x1FBE7: "MIDDLE RIGHT ONE QUARTER BLOCK",
    0x1CEA0: "RIGHT HALF LOWER ONE QUARTER BLOCK",
    0x1CEA3: "LEFT HALF LOWER ONE QUARTER BLOCK",
    0x1CEA8: "LEFT HALF UPPER ONE QUARTER BLOCK",
    0x1CEAB: "RIGHT HALF UPPER ONE QUARTER BLOCK",
}


def cells(bits):
    return "".join(str(n + 1) for n in range(8) if bits >> n & 1)


def bits_of(digits):
    out = 0
    for d in digits:
        if d not in "12345678" or out >> (int(d) - 1) & 1:
            raise ValueError(f"bad cells {digits!r}")
        out |= 1 << (int(d) - 1)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("data", help="UnicodeData.txt")
    p.add_argument("version", help="its Unicode version, e.g. 16.0.0")
    p.add_argument("--out", default=glyphs.OCTANTS)
    a = p.parse_args()
    with open(a.data, "rb") as fh:
        raw = fh.read()
    names = {}
    for line in raw.decode("utf-8").splitlines():
        f = line.split(";")
        if len(f) > 1:
            names[int(f[0], 16)] = f[1]

    octants = []
    for cp in range(0x1CD00, 0x1CDE6):
        name = names.get(cp, "")
        if not name.startswith("BLOCK OCTANT-"):
            raise SystemExit(f"U+{cp:04X} is {name!r}, not an octant")
        octants.append((cp, bits_of(name[len("BLOCK OCTANT-"):])))
    if names.get(0x1CDE6, "").startswith("BLOCK OCTANT-"):
        raise SystemExit("more than 230 octants")
    pats = [b for _, b in octants]
    if any(x >= y for x, y in zip(pats, pats[1:])):
        raise SystemExit("octant patterns do not rise with the code point")

    elsewhere = dict(ELSEWHERE)
    for cp, bits in glyphs.SUBSTITUTES.items():
        if bits in elsewhere:
            raise SystemExit(f"U+{cp:04X} repeats pattern {bits}")
        elsewhere[bits] = (cp, SUBSTITUTE_NAMES[cp])
    if set(SUBSTITUTE_NAMES) != set(glyphs.SUBSTITUTES):
        raise SystemExit("glyphs.SUBSTITUTES and this file name different characters")
    for bits, (cp, want) in sorted(elsewhere.items()):
        got = names.get(cp, "SPACE" if cp == 0x20 else "")
        if got != want:
            raise SystemExit(f"U+{cp:04X} is {got!r} in the file, not {want!r}")
    missing = set(range(256)) - set(pats)
    if missing != set(elsewhere):
        raise SystemExit(f"patterns with no octant {sorted(missing)} are not the ones drawn elsewhere")

    for cp in range(0x1FB00, 0x1FB3C):
        bits, rows = glyphs.sextant(cp)
        want = "BLOCK SEXTANT-" + cells(bits)
        if rows != 3 or names.get(cp) != want:
            raise SystemExit(f"U+{cp:04X} is {names.get(cp)!r}, glyphs.sextant gives {want!r}")

    sha = hashlib.sha256(raw).hexdigest()
    with open(a.out, "w") as fh:
        fh.write("# Neuronte: the octants U+1CD00..U+1CDE5 and the cells each fills,\n"
                 "# numbered 1 2 / 3 4 / 5 6 / 7 8 by row of a 2 x 4 lattice.\n"
                 "# Made by train/mosaics.py from the Unicode Character Database,\n"
                 f"# UnicodeData.txt version {a.version}, sha256\n"
                 f"# {sha}.\n"
                 "# Do not edit: run train/mosaics.py again.\n")
        for cp, bits in octants:
            fh.write(f"U+{cp:04X} {cells(bits)}\n")
    print(f"{a.out}: {len(octants)} octants from Unicode {a.version}; "
          f"{len(elsewhere)} patterns drawn elsewhere and 60 sextants agree")


if __name__ == "__main__":
    main()
