"""Assemble a tiled Braille expert from separately trained tile nets.

usage: python3 tools/braille-tiled.py OUT.json --layout LAYOUT NET.json...
                                      [--note TEXT]

Writes a neuronte-tiled-weights JSON, which train/pack.py packs as one
version 6 net covering U+2800..U+28FF. The nets are copied whole, with
their own training records; this tool trains nothing and changes no
weight.

Layouts cut the 1 x 2 design cell along Braille's own lattice. Dots sit at
x = 0.25 + 0.5 c and y = 0.25 + 0.5 r (train/glyphs.py), so these edges
never cut a dot unevenly. NET.json files are given in row-major tile
order, except for the shared layouts, which take one net.

  whole        1 x 1, one net, every bit                  (the original)
  columns      2 x 1, left 0x47, right 0xb8
  rows         1 x 2, top 0x1b, bottom 0xe4
  quadrants    2 x 2, 0x03 0x18 / 0x44 0xa0
  dots         2 x 4, one dot per tile
  grid12       3 x 4, edges 0, 1/4, 3/4, 1: the middle column holds the
               inner halves of both dots of its row
  dots-shared  the dots grid drawn by ONE net for every tile. The net is
               given the dot's own bit as U+2800 (absent) or U+2801
               (present), so it must have been trained on tile (0, 0),
               whose target is the same dot at the same place in every
               tile.

A tile net's code is U+2800 | (bits & mask) ("place"), the input the
separately trained tile nets were trained on; the shared layout uses
"extract".
"""
import argparse
import hashlib
import json
from pathlib import Path

DOT_BITS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))  # (left, right) per row


def _grid(columns, rows):
    """Masks of a grid whose rows are the four dot rows (or pairs of them)."""
    masks = []
    per = 4 // (len(rows) - 1)
    for r in range(len(rows) - 1):
        for x0, x1 in zip(columns, columns[1:]):
            m = 0
            for dr in range(per):
                left, right = DOT_BITS[r * per + dr]
                m |= (left if x0 < .5 else 0) | (right if x1 > .5 else 0)
            masks.append(m)
    return masks


LAYOUTS = {
    "whole": ([0, 1], [0, 2], [0xFF]),
    "columns": ([0, .5, 1], [0, 2], [0x47, 0xB8]),
    "rows": ([0, 1], [0, 1, 2], [0x1B, 0xE4]),
    "quadrants": ([0, .5, 1], [0, 1, 2], [0x03, 0x18, 0x44, 0xA0]),
    "dots": ([0, .5, 1], [0, .5, 1, 1.5, 2], _grid([0, .5, 1], [0, .5, 1, 1.5, 2])),
    "grid12": ([0, .25, .75, 1], [0, .5, 1, 1.5, 2], _grid([0, .25, .75, 1], [0, .5, 1, 1.5, 2])),
}
LAYOUTS["dots-shared"] = LAYOUTS["dots"]
SHARED = {"dots-shared"}
assert _grid([0, .5, 1], [0, 1, 2]) == LAYOUTS["quadrants"][2]
assert _grid([0, .5, 1], [0, 2]) == LAYOUTS["columns"][2]


def build(layout, nets, note=None):
    columns, rows, masks = LAYOUTS[layout]
    want = 1 if layout in SHARED else len(masks)
    if len(nets) != want:
        raise SystemExit(f"{layout} takes {want} net(s), got {len(nets)}")
    docs, sources = [], []
    for path in nets:
        raw = Path(path).read_bytes()
        doc = json.loads(raw)
        if doc.get("format") != "neuronte-weights" or doc.get("version") != 1:
            raise SystemExit(f"{path}: not a version 1 distance weights file")
        docs.append(doc)
        sources.append({"file": Path(path).name, "sha256": hashlib.sha256(raw).hexdigest()})
    if layout in SHARED:
        tiles = [{"net": 0, "mask": f"0x{m:02X}", "base": "U+2800", "code": "extract"} for m in masks]
    else:
        tiles = [{"net": i, "mask": f"0x{m:02X}", "base": "U+2800", "code": "place"}
                 for i, m in enumerate(masks)]
    training = {"set": "braille", "labelled": "U+2800..U+28FF", "layout": layout,
                "tile_sources": sources}
    if note:
        training["note"] = note
    return {"format": "neuronte-tiled-weights", "version": 1, "training": training,
            "first": "U+2800", "last": "U+28FF", "columns": columns, "rows": rows,
            "tiles": tiles, "nets": docs}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out", type=Path)
    p.add_argument("--layout", required=True, choices=sorted(LAYOUTS))
    p.add_argument("--note")
    p.add_argument("nets", nargs="+")
    a = p.parse_args()
    if a.out.resolve() in {Path(n).resolve() for n in a.nets}:
        p.error("the output must not be one of the nets")
    a.out.write_text(json.dumps(build(a.layout, a.nets, a.note)) + "\n")
    print(a.out, a.layout, len(a.nets), "net(s)")


if __name__ == "__main__":
    main()
