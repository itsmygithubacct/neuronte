"""usage: fit_advances.py LO HI OUT.txt OUT.json [--italic]
       fit_advances.py --extend IN.txt OUT.txt

The second form writes IN's lines and then one line for each Latin-1
character that uilarge composes (glyphs.large_latin1): the base letter's
regular and bold advance, the space's for U+00A0 and the grave accent's
for a spacing mark.

Fit an advance table (steps of 1/100 em; the library draws (steps * em + 50) // 100 pixels) to the
hand faces' whole-pixel advances over a range of ems: per character and weight, the steps (10..200)
with the least summed |pixels - hand| over the range, then the fewest mismatches, then nearest the
ui-large table. Writes an advances file in pack.py's syntax (design units, one decimal) and a JSON
of every mismatch per em."""
import json, os, sys
from decimal import Decimal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphs, pack
if sys.argv[1:2] == ["--extend"]:
    src, dst = sys.argv[2], sys.argv[3]
    table = pack.read_table(src)
    lines = open(src, encoding="utf-8").read().rstrip("\n").split("\n")
    lines.insert(next(i for i, l in enumerate(lines) if not l.startswith("#")),
                 "# Then the Latin-1 letters uilarge composes, each at its base letter's advance (train/fit_advances.py --extend).")
    for c, (_, base) in sorted(glyphs.large_latin1().items()):
        r, b = table[ord(base)]
        name = c if c.isprintable() and not c.isspace() else f"U+{ord(c):04X}"
        lines.append(f"{name} {Decimal(r) / 10} {Decimal(b) / 10}")
    open(dst, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(dst, len(table), "+", len(glyphs.large_latin1()))
    sys.exit(0)
lo, hi, out_txt, out_json = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
ems = range(lo, hi + 1)
ITALIC = "--italic" in sys.argv
hand = {em: glyphs.pixel_face(em, glyphs.UI_ITALIC[em] if ITALIC else None) for em in ems}
large = pack.read_table(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "font", "ui-large-advances.txt"))
def px(st, em): return (st * em + 50) // 100
rows, miss = [], {}
chars = sorted(hand[lo], key=ord)
for c in chars:
    best = []
    for w in (0, 1):
        want = {em: hand[em][c][0] + w for em in ems}
        ref = int(large[ord(c)][w]) if ord(c) in large else 0
        cand = min(range(10, 201), key=lambda st: (sum(abs(px(st, e) - want[e]) for e in ems),
                                                  sum(px(st, e) != want[e] for e in ems), abs(st - ref)))
        best.append(cand)
        for e in ems:
            if px(cand, e) != want[e]:
                miss.setdefault(str(e), []).append({"char": f"U+{ord(c):04X}", "bold": w, "drawn": px(cand, e), "hand": want[e]})
    rows.append((c, best))
with open(out_txt, "w") as fh:
    fh.write(f"# Advances fitted to font/ui-EM{'-italic' if ITALIC else ''}.txt for ems {lo} to {hi} (train/fit_advances.py):\n")
    fh.write("# per character and weight, the step with the least summed pixel error over the range.\n")
    for c, (r, b) in rows:
        name = c if c.isprintable() and c not in " #" else f"U+{ord(c):04X}"
        fh.write(f"{name} {Decimal(r) / 10} {Decimal(b) / 10}\n")
tot = sum(len(v) for v in miss.values())
json.dump({"ems": [lo, hi], "mismatches_total": tot, "cases": 2 * len(chars) * len(ems),
           "per_em": {e: len(miss.get(str(e), [])) for e in ems}, "mismatches": miss}, open(out_json, "w"), indent=0)
print(lo, hi, "mismatches", tot, "of", 2 * len(chars) * len(ems), {e: len(miss.get(str(e), [])) for e in ems})
