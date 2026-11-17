"""Assemble a tiled member from tile nets trained by train/tile_expert.py.

usage: python3 train/tile_member.py OUT.json COLUMNSxROWS NET.json...
                                    [--note TEXT]

NET.json are the tile nets of one set and one seed, in row-major tile
order (split_expert.py's part order). Writes a neuronte-tiled-weights
JSON, which train/pack.py packs as one version 6 net and
train/standalone_bundle.py takes as a member. The nets are copied whole,
with their training records; this trains nothing and changes no weight.

Every tile is given the character's own scalar, the code its net was
trained on: code "extract", base the set's first scalar, mask the low
bits that span the set. The member's range is the set's first to last
scalar; the characters it was trained on are listed in training.labelled,
which is what a bundle's table is made from.
MIT licence; see LICENSE.
"""
import argparse
import hashlib
import json
import os

import numpy as np


def ranges(scalars):
    out = []
    for v in sorted(scalars):
        if out and out[-1][1] == v - 1:
            out[-1][1] = v
        else:
            out.append([v, v])
    return " ".join(f"U+{a:04X}" if a == b else f"U+{a:04X}..U+{b:04X}" for a, b in out)


def build(columns, rows, nets, note=None):
    if len(nets) != columns * rows:
        raise SystemExit(f"a {columns} x {rows} grid takes {columns * rows} nets, got {len(nets)}")
    docs, sources, scalars, name, seed = [], [], None, None, None
    for i, path in enumerate(nets):
        with open(path, "rb") as fh:
            raw = fh.read()
        doc = json.loads(raw)
        if doc.get("format") != "neuronte-weights" or doc.get("version") != 1:
            raise SystemExit(f"{path}: not a version 1 distance weights file")
        tr = doc["training"]
        ex = tr["experiment"]
        want = [i % columns / columns, (i % columns + 1) / columns, 2 * (i // columns) / rows, 2 * (i // columns + 1) / rows]
        if ex["index"] != i or any(abs(a - b) > 1e-12 for a, b in zip(ex["region"], want)):
            raise SystemExit(f"{path}: not the net of tile {i} of a {columns} x {rows} grid")
        mine = [int(t[2:], 16) for t in tr["labelled"].split()]
        if scalars is None:
            scalars, name, seed = mine, tr["set"], tr["seed"]
        elif (mine, tr["set"], tr["seed"]) != (scalars, name, seed):
            raise SystemExit(f"{path}: another set, seed or list of characters than the first net's")
        docs.append(doc)
        sources.append({"file": os.path.basename(path), "sha256": hashlib.sha256(raw).hexdigest()})
    first, last = min(scalars), max(scalars)
    mask = (1 << (last - first).bit_length()) - 1
    training = {"set": name, "labelled": ranges(scalars), "layout": f"{columns}x{rows}", "seed": seed,
                "tile_sources": sources}
    if note:
        training["note"] = note
    return {"format": "neuronte-tiled-weights", "version": 1, "training": training,
            "first": f"U+{first:04X}", "last": f"U+{last:04X}",
            "columns": [float(np.float32(c / columns)) for c in range(columns)] + [1.0],
            "rows": [float(np.float32(2 * r / rows)) for r in range(rows)] + [2.0],
            "nets": docs,
            "tiles": [{"net": i, "mask": f"0x{mask:X}", "base": f"U+{first:04X}", "code": "extract"}
                      for i in range(columns * rows)]}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out")
    p.add_argument("grid")
    p.add_argument("nets", nargs="+")
    p.add_argument("--note")
    a = p.parse_args()
    columns, rows = (int(v) for v in a.grid.split("x"))
    doc = build(columns, rows, a.nets, a.note)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(json.dumps(doc) + "\n")
    os.replace(tmp, a.out)
    print(f"{a.out}: {columns} x {rows} tiles, {len(a.nets)} nets, {doc['first']}..{doc['last']}, "
          f"trained on {doc['training']['labelled']}")


if __name__ == "__main__":
    main()
