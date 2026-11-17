#!/usr/bin/env python3
"""Pack group nets as a bundle that stands alone.

usage: python3 train/standalone_bundle.py OUT.nrt --list LIST.txt
           [--apart-from OTHER.nrt]... [--record OUT.json] NET.json...

known_bundle.add_known() adds group nets to a copy of a bundle that
already draws everything else. This packs the group nets alone, for a
program that opens several bundles and asks each which characters it was
trained on.

- The table sends every trained scalar to its group net, as in any
  bundle. There is no gate.
- A scalar outside the table goes to one more member this tool adds, the
  blank net: one hidden unit, every weight 0, output bias BLANK. It draws
  an empty cell at every size, so an untrained scalar is never drawn as
  some other character's shape.
- neuronte_untrained() is then right with no change to the library: 0
  for a scalar in the table, 1 for any other. With
  neuronte_set_untrained(font, 1) the other scalars draw the library's
  mark for an untrained character instead of the empty cell.

--list names the bundle's list: U+XXXX or U+XXXX..U+YYYY tokens, # to the
end of a line a comment. The nets' trained scalars must be exactly the
list. --apart-from names a bundle no listed scalar may be in the table
of; give it once for every bundle the new one is used beside.
"""
import argparse
import hashlib
import json
import os
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack  # noqa: E402
import strokes  # noqa: E402

# The blank net's output everywhere. Times tau it is a distance of 1.2 cell
# widths outside any stroke, which is no ink even in a cell one pixel wide.
BLANK = -8.0
BLANK_TAU = 0.15


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_list(path):
    """The scalars of a list file, in file order, each once."""
    out, seen = [], set()
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            for tok in line.split("#")[0].split():
                lo, _, hi = tok.partition("..")
                a = pack._scalar(lo, f"{path}:{n}")
                b = pack._scalar(hi, f"{path}:{n}") if hi else a
                if b < a:
                    raise SystemExit(f"{path}:{n}: {tok} runs backwards")
                for v in range(a, b + 1):
                    if v in seen:
                        raise SystemExit(f"{path}:{n}: U+{v:04X} is listed twice")
                    seen.add(v)
                    out.append(v)
    if not out:
        raise SystemExit(f"{path}: an empty list")
    return out


def read_table(data):
    """{scalar: member} from a bundle's table; None for a file with no table."""
    if len(data) < 28 or data[:8] != b"NEURONTE":
        raise SystemExit("not a Neuronte file")
    version, nets, ranges = struct.unpack_from("<3I", data, 8)
    if version != 2:
        return None
    if not 1 <= nets <= 128 or 28 + 4 * nets + 12 * ranges > len(data):
        raise SystemExit("a damaged bundle header")
    out, at = {}, 28 + 4 * nets
    for i in range(ranges):
        first, last, net = struct.unpack_from("<3I", data, at + 12 * i)
        if first > last or last > 0x10FFFF or net >= nets:
            raise SystemExit("a damaged bundle table")
        for v in range(first, last + 1):
            out[v] = net
    return out


def blank():
    """The version 1 image of the blank net."""
    weights = {name: (np.zeros((rows, cols), np.float32), np.zeros(rows, np.float32))
               for name, rows, cols in pack.layers(1)}
    weights["out"][1][0] = BLANK
    return pack.image_v1(1, BLANK_TAU, strokes.masks(), weights)


def standalone(nets, listed, apart=()):
    """(bundle bytes, record) for group net JSON paths and the list's scalars."""
    if not 1 <= len(nets) <= 127:
        raise SystemExit("a standalone bundle holds 1 to 127 group nets")
    images = [pack.pack_v1(p) for p in nets]
    ranges = pack.table(nets)        # refuses a scalar two nets were trained on
    trained = {v for first, last, _ in ranges for v in range(first, last + 1)}
    want = set(listed)
    if trained != want:
        missing, extra = sorted(want - trained), sorted(trained - want)
        raise SystemExit("the nets' trained scalars are not the list: "
                         f"{len(missing)} listed and not trained {[f'U+{v:04X}' for v in missing[:8]]}, "
                         f"{len(extra)} trained and not listed {[f'U+{v:04X}' for v in extra[:8]]}")
    others = []
    for path in apart:
        with open(path, "rb") as fh:
            data = fh.read()
        table = read_table(data)
        if table is None:
            raise SystemExit(f"{path}: has no table to be apart from")
        shared = sorted(want & set(table))
        if shared:
            raise SystemExit(f"{path} already has {len(shared)} of the listed scalars: "
                             f"{[f'U+{v:04X}' for v in shared[:8]]}")
        others.append({"file": os.path.basename(path), "sha256": digest(data), "table_scalars": len(table)})
    images.append(blank())
    fallback = len(nets)
    out = bytearray(b"NEURONTE")
    out += struct.pack("<5I", 2, len(images), len(ranges), fallback, 0)
    out += struct.pack(f"<{len(images)}I", *map(len, images))
    for r in ranges:
        out += struct.pack("<3I", *r)
    for im in images:
        out += im
    out = bytes(out)
    members = []
    for i, (path, im) in enumerate(zip(nets, images)):
        with open(path, "rb") as fh:
            raw = fh.read()
        members.append({"member": i, "json": os.path.basename(path), "json_sha256": digest(raw),
                        "image_sha256": digest(im), "bytes": len(im), "set": pack.scalars(path)[0],
                        "scalars": [f"U+{v:04X}" for v in sorted(pack.scalars(path)[1])]})
    record = {"schema": "neuronte.standalone-bundle/v1", "sha256": digest(out), "bytes": len(out),
              "members": len(images), "group_nets": len(nets), "ranges": len(ranges), "gate": None,
              "trained_scalars": len(trained),
              "fallback": {"member": fallback, "kind": "blank", "hidden_width": 1, "distance": BLANK,
                           "image_sha256": digest(images[-1]), "bytes": len(images[-1])},
              "apart_from": others, "nets": members}
    return out, record


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("out")
    p.add_argument("nets", nargs="+")
    p.add_argument("--list", required=True, dest="listed")
    p.add_argument("--apart-from", action="append", default=[])
    p.add_argument("--record")
    a = p.parse_args()
    with open(a.listed, "rb") as fh:
        list_sha = digest(fh.read())
    image, record = standalone(a.nets, read_list(a.listed), a.apart_from)
    record["list"] = {"file": os.path.basename(a.listed), "sha256": list_sha}
    for path, data in ((a.out, image),) + (((a.record, (json.dumps(record, indent=1) + "\n").encode()),) if a.record else ()):
        tmp = path + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.replace(tmp, path)
    print(f"{a.out}: {record['group_nets']} group nets and the blank net, {record['trained_scalars']} scalars in "
          f"{record['ranges']} ranges, {len(image)} bytes, sha256 {record['sha256'][:16]}")


if __name__ == "__main__":
    main()
