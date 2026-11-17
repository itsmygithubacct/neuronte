#!/usr/bin/env python3
"""Group a term-* tier's characters for training: by shape family, then balanced.

usage: tools/term-partition.py TIER [--check]        TIER: math, sym or ding

A group net draws about the same amount of ink edge whatever its family. A
drawing's edge is counted on a 48-wide grid with the training pen (the cells
where ink meets no ink), and a family's class is set by its mean edge: 12
characters to a net up to 265, 10 up to 330, 8 above. Each class is one
training set (tmath12, tmath10 and tmath8 for math): its families in a
fixed order, cut into consecutive groups whose sizes differ by at most one, as
train/split_expert.py's contiguous partition cuts a set, so the trainer
needs no change. Inside a family the characters are dealt, largest edge
first, to the group with the least edge per place so far, so the groups a
family spans are balanced. Writes font/term-TIER-partition.json; --check
compares instead.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "train"))
import glyphs  # noqa: E402
import term_glyphs  # noqa: E402

# The words each file carries about how it was made. The math file was written
# with the usage line here and its bytes are what its nets recorded, so it
# keeps that line.
METHOD = {"math": "usage: tools/term-partition.py TIER [--check] TIER: math"}
CLASSES = ((12, 265.0), (10, 330.0), (8, float("inf")))
NODES = glyphs.nodes(48)


def edge(shapes):
    ink = glyphs.signed_distance(shapes, NODES, glyphs.PEN).reshape(97, 49) > 0
    return int((ink[1:] != ink[:-1]).sum() + (ink[:, 1:] != ink[:, :-1]).sum())


def partition(tier):
    made = getattr(term_glyphs, tier)()
    edges = {ord(c): edge(g) for c, g in made.items()}
    families = {}
    for cp in sorted(edges):
        families.setdefault(term_glyphs.FAMILY[cp], []).append(cp)
    mean = {f: sum(edges[c] for c in v) / len(v) for f, v in families.items()}
    sets = {}
    for size, limit in CLASSES:
        low = max([lim for _, lim in CLASSES if lim < limit], default=0.0)
        names = sorted(f for f in families if low < mean[f] <= limit or (low == 0.0 and mean[f] <= limit))
        if not names:
            continue
        seq = [(f, c) for f in names for c in families[f]]
        n = len(seq)
        parts = max(1, round(n / size))
        bounds = [n * i // parts for i in range(parts + 1)]
        group_of = [next(i for i in range(parts) if bounds[i] <= p < bounds[i + 1]) for p in range(n)]
        groups = [[] for _ in range(parts)]
        pos = 0
        for f in names:
            cps = families[f]
            room = {}
            for p in range(pos, pos + len(cps)):
                room[group_of[p]] = room.get(group_of[p], 0) + 1
            pos += len(cps)
            load = {g: 0.0 for g in room}
            put = {g: [] for g in room}
            for c in sorted(cps, key=lambda c: (-edges[c], c)):
                g = min((g for g in room if len(put[g]) < room[g]), key=lambda g: (load[g] / room[g], g))
                put[g].append(c)
                load[g] += edges[c]
            for g in room:
                groups[g] += sorted(put[g])
        sets[f"t{tier}{size}"] = {
            "parts": parts, "families": {f: round(mean[f], 1) for f in names},
            "groups": [[f"U+{c:04X}" for c in g] for g in groups],
            "group_edge": [sum(edges[c] for c in g) for g in groups]}
    return {"format": "neuronte-term-partition", "version": 1, "tier": f"t{tier}",
            "method": METHOD.get(tier, " ".join(__doc__.split("\n\n")[2].split())), "edge": {f"U+{c:04X}": e for c, e in sorted(edges.items())},
            "sets": sets}


if __name__ == "__main__":
    tier = sys.argv[1]
    path = ROOT / "font" / f"term-{tier}-partition.json"
    text = json.dumps(partition(tier), indent=1, ensure_ascii=True) + "\n"
    if "--check" in sys.argv:
        if path.read_text() != text:
            raise SystemExit(f"{path.name} is not what tools/term-partition.py makes")
        print(path.name, "matches")
    else:
        path.write_text(text)
        doc = json.loads(text)
        for name, s in doc["sets"].items():
            print(name, s["parts"], "groups", sorted(set(len(g) for g in s["groups"])), "a net; edge",
                  min(s["group_edge"]), "to", max(s["group_edge"]), list(s["families"]))
