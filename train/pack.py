"""Pack weights JSON into the binary file the C library loads.

usage: python3 train/pack.py WEIGHTS.json OUT.nrt
       python3 train/pack.py --bundle OUT.nrt NET.json... [--gate GATE.json]
                             [--fallback I]

The first form packs one net. The second packs a bundle of nets with a
router: each scalar a net was trained on is drawn by that net, so no two
nets may share one. Other scalars go to the gate (from train/gate.py, made
for the same nets in the same order) or, with no gate, to net I (0).

One distance net, version 1, all little-endian:

    0   8 bytes   "NEURONTE"
    8   u32       format version, 1
    12  u32       position octaves, 6
    16  u32       code bits, 64
    20  u32       hidden width H, a multiple of 8 from 8 to 1024
    24  u32       hidden layers, 3
    28  f32       tau
    32  43 x u32  parity masks
    204 f32 ...   l1 weight (H x 90, row-major), l1 bias, l2 weight (H x H),
                  l2 bias, l3 weight (H x H), l3 bias, out weight (1 x H),
                  out bias

204 + 4 (2 H^2 + 94 H + 1) bytes in all: 179,408 for H = 128 and
620,752 for H = 256.

A bundle, version 2:

    0   8 bytes   "NEURONTE"
    8   u32       format version, 2
    12  u32       nets K, 1 to 16
    16  u32       table ranges R
    20  u32       fallback net, below K
    24  u32       gate hidden width G, 0 for no gate, at most 256
    28  K x u32   the length of each net
        R x 3 u32 first scalar, last scalar, net; sorted, not overlapping
        when G > 0: 43 x u32 parity masks, then f32 gate l1 weight
                  (G x 64, row-major), l1 bias, out weight (K x G), out bias
        the K nets, each a whole version 1 file or a whole version 3 file

A colour net, version 3, is form A only (neuronte-colour-weights version 1).
Form B is rejected. The trunk has K distance outputs. A palette head and
the straight edges of the drawings follow it. Inside a bundle the bundle
stays version 2; every colour member must carry the same palette and the
same snap threshold.

    0   8 bytes   "NEURONTE"
    8   u32       format version, 3
    12  u32       position octaves, 6
    16  u32       code bits, 64
    20  u32       hidden width H, a multiple of 8 from 8 to 1024
    24  u32       hidden layers, 3
    28  f32       tau, finite and positive
    32  u32       K, layers a glyph may have, 1 to 16
    36  u32       palette entries, 32
    40  u32       entry bits, 5
    44  u32       palette-head width R, a multiple of 8 from 8 to 256
    48  u32       edge records E
    52  u32       snap when the cell is narrower than this many pixels, 14
    56  43 x u32  parity masks
    228 32 x 3    dark palette, R, G, B, entry 0 first
    324 32 x 3    light palette, same order
    420 f32       trunk, then palette head, then the edge table

The trunk is l1 (H x 90), l1 bias, l2 (H x H), l2 bias, l3 (H x H), l3 bias,
out (K x H), out bias. The head is h1 (R x 64), h1 bias, out (K*5 x R),
out bias. Float count is 2 H^2 + (93 + K) H + K for the trunk and
R (65 + 5 K) + 5 K for the head.

One edge record per labelled glyph, sorted by scalar. A record is the
scalar as u32, then K layer blocks. A block is an x-edge count and a
y-edge count as u16, then that many x edges and that many y edges. An
edge is an f32 position in design-cell widths and a u32 side, 1 for
rising and 0 for falling. The edges come from font/icons.txt, and the
packer refuses the file when that drawing's sha256 is not the one in
training.sources_sha256.
"""
import hashlib
import json
import os
import struct
import sys

import numpy as np

import snap
import strokes

SHAPE = {"position_octaves": 6, "code_bits": 64, "hidden_layers": 3}
COLOUR_FIXED = 420
SNAP_PX = 14
PALETTE_N = 32
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def layers(h):
    return [("l1", h, 90), ("l2", h, h), ("l3", h, h), ("out", 1, h)]


def colour_layers(h, k):
    return [("l1", h, 90), ("l2", h, h), ("l3", h, h), ("out", k, h)]


def head_layers(r, k):
    return [("h1", r, 64), ("out", k * 5, r)]


def trunk_floats(h, k):
    return 2 * h * h + (93 + k) * h + k


def head_floats(r, k):
    return r * (65 + 5 * k) + 5 * k


def length(h):
    return 204 + 4 * (2 * h * h + 94 * h + 1)


def load(path):
    with open(path) as fh:
        doc = json.load(fh)
    if doc.get("format") != "neuronte-weights" or doc.get("version") != 1:
        raise SystemExit(f"{path}: not a version 1 Neuronte weights file")
    shape = doc["shape"]
    for k, v in SHAPE.items():
        if shape.get(k) != v:
            raise SystemExit(f"{path}: {k} is {shape.get(k)}, this packer is for {v}")
    h = shape.get("hidden_width")
    if not (isinstance(h, int) and 8 <= h <= 1024 and h % 8 == 0):
        raise SystemExit(f"{path}: hidden width {h} is not a multiple of 8 from 8 to 1024")
    masks = [int(m, 16) for m in shape["parity_masks"]]
    if len(masks) != 43 or any(not 0 < m < 1 << 21 for m in masks):
        raise SystemExit(f"{path}: parity masks must be 43 values over 21 bits")
    out = {}
    for name, rows, cols in layers(h):
        layer = doc["layers"][name]
        w = np.asarray(layer["weight"], np.float32)
        b = np.asarray(layer["bias"], np.float32)
        if (layer["rows"], layer["cols"]) != (rows, cols) or w.size != rows * cols or b.size != rows:
            raise SystemExit(f"{path}: layer {name} is not {rows} x {cols}")
        if not (np.isfinite(w).all() and np.isfinite(b).all()):
            raise SystemExit(f"{path}: layer {name} holds a value that is not finite")
        out[name] = (w.reshape(rows, cols), b)
    return h, float(np.float32(shape["tau"])), masks, out


def pack_v1(path):
    """The version 1 image of one distance net."""
    h, tau, masks, weights = load(path)
    out = bytearray(b"NEURONTE")
    out += struct.pack("<5I", 1, 6, 64, h, 3)
    out += struct.pack("<f", tau)
    out += struct.pack("<43I", *masks)
    for name, _, _ in layers(h):
        w, b = weights[name]
        out += w.astype("<f4").tobytes() + b.astype("<f4").tobytes()
    assert len(out) == length(h), len(out)
    return bytes(out)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        digest.update(fh.read())
    return digest.hexdigest()


def check_sources(doc, path):
    """The drawings named in the weights are the files in this tree."""
    src = doc.get("training", {}).get("sources_sha256")
    if not isinstance(src, dict) or "font/icons.txt" not in src:
        raise SystemExit(f"{path}: training.sources_sha256 has no font/icons.txt")
    for rel, digest in src.items():
        if not isinstance(rel, str) or os.path.isabs(rel) or ".." in rel.split("/"):
            raise SystemExit(f"{path}: sources_sha256 path {rel!r} is not inside the tree")
        fp = os.path.join(ROOT, rel)
        if not os.path.isfile(fp):
            raise SystemExit(f"{path}: {rel} is not in the tree")
        if sha256_file(fp) != digest:
            raise SystemExit(f"{path}: {rel} sha256 does not match training.sources_sha256")


def labelled_scalars(doc, path):
    """The labelled scalars, in the order written. None may be repeated."""
    out = []
    seen = set()
    for tok in doc["training"]["labelled"].split():
        lo, _, hi = tok.partition("..")
        try:
            a = int(lo[2:], 16)
            b = int((hi or lo)[2:], 16)
        except ValueError:
            raise SystemExit(f"{path}: labelled token {tok!r} is not U+XXXX") from None
        if b < a:
            raise SystemExit(f"{path}: labelled range {tok} is backwards")
        for v in range(a, b + 1):
            if v in seen:
                raise SystemExit(f"{path}: U+{v:04X} is listed twice")
            seen.add(v)
            out.append(v)
    if not out:
        raise SystemExit(f"{path}: a colour net names no labelled glyphs")
    return out


def palette_bytes(doc, path):
    """192 bytes: dark RGB, then light RGB. Entries 0 and 1 are zeros."""
    got = doc.get("palette")
    file_pal = strokes.palette()
    if not isinstance(got, dict) or set(got) != set(file_pal):
        raise SystemExit(f"{path}: palette names do not match font/palette.txt")
    dark, light = bytearray(PALETTE_N * 3), bytearray(PALETTE_N * 3)
    for name, (n, fd, fl) in file_pal.items():
        ent = got[name]
        if ent.get("entry") != n:
            raise SystemExit(f"{path}: palette entry {name} is not {n}")
        for side, buf, want in (("dark", dark, fd), ("light", light, fl)):
            col = ent.get(side)
            if n < 2:
                if col is not None:
                    raise SystemExit(f"{path}: palette entry {n} stores a colour")
                continue
            if not (isinstance(col, str) and len(col) == 7 and col.startswith("#")):
                raise SystemExit(f"{path}: palette entry {n} {side} is not #RRGGBB")
            rgb = bytes.fromhex(col[1:])
            if rgb != bytes(want):
                raise SystemExit(f"{path}: palette entry {n} {side} does not match font/palette.txt")
            buf[n * 3:n * 3 + 3] = rgb
    return bytes(dark), bytes(light)


def _layer_arrays(doc, group, name, rows, cols, path):
    layer = doc[group][name]
    w = np.asarray(layer["weight"], np.float32)
    b = np.asarray(layer["bias"], np.float32)
    if (layer["rows"], layer["cols"]) != (rows, cols) or w.size != rows * cols or b.size != rows:
        raise SystemExit(f"{path}: {group} {name} is not {rows} x {cols}")
    if not (np.isfinite(w).all() and np.isfinite(b).all()):
        raise SystemExit(f"{path}: {group} {name} holds a value that is not finite")
    return w.reshape(rows, cols), b


def edge_records(doc, path, k):
    """One record per labelled glyph, sorted by scalar, padded out to K layers."""
    icons = strokes.parse_layers()
    recs = []
    for s in sorted(labelled_scalars(doc, path)):
        ch = chr(s)
        if ch not in icons:
            raise SystemExit(f"{path}: U+{s:04X} is labelled and is not in font/icons.txt")
        drawn = icons[ch]
        if len(drawn) > k:
            raise SystemExit(f"{path}: U+{s:04X} has {len(drawn)} layers and K is {k}")
        probed = list(snap.probe(drawn))
        while len(probed) < k:
            probed.append(([], []))
        recs.append((s, probed[:k]))
    return recs


def pack_edges(recs):
    out = bytearray()
    for scalar, layers in recs:
        out += struct.pack("<I", scalar)
        for xs, ys in layers:
            xs = sorted((float(p), bool(r)) for p, r in xs)
            ys = sorted((float(p), bool(r)) for p, r in ys)
            out += struct.pack("<HH", len(xs), len(ys))
            for pos, rising in xs + ys:
                out += struct.pack("<fI", np.float32(pos), 1 if rising else 0)
    return bytes(out)


def pack_colour(path, doc):
    """The version 3 image of one form A colour net."""
    if doc.get("version") != 1:
        raise SystemExit(f"{path}: colour weights are version {doc.get('version')}, this packer is for 1")
    if doc.get("shape", {}).get("form") != "A":
        raise SystemExit(f"{path}: form {doc.get('shape', {}).get('form')} is not packed")
    shape = doc["shape"]
    for key, val in SHAPE.items():
        if shape.get(key) != val:
            raise SystemExit(f"{path}: {key} is {shape.get(key)}, this packer is for {val}")
    if shape.get("entry_bits") != 5 or shape.get("glyph_layers") is None:
        raise SystemExit(f"{path}: a colour net needs 5 entry bits and glyph_layers")
    h, k, r = shape.get("hidden_width"), shape.get("glyph_layers"), shape.get("head_width")
    if not (isinstance(h, int) and 8 <= h <= 1024 and h % 8 == 0):
        raise SystemExit(f"{path}: hidden width {h} is not a multiple of 8 from 8 to 1024")
    if not (isinstance(k, int) and 1 <= k <= 16):
        raise SystemExit(f"{path}: K {k} is not 1 to 16")
    if not (isinstance(r, int) and 8 <= r <= 256 and r % 8 == 0):
        raise SystemExit(f"{path}: palette-head width {r} is not a multiple of 8 from 8 to 256")
    tau = float(np.float32(shape["tau"]))
    if not np.isfinite(tau) or tau <= 0:
        raise SystemExit(f"{path}: tau must be finite and positive")
    masks = [int(m, 16) for m in shape["parity_masks"]]
    if len(masks) != 43 or any(not 0 < m < 1 << 21 for m in masks):
        raise SystemExit(f"{path}: parity masks must be 43 values over 21 bits")
    check_sources(doc, path)
    dark, light = palette_bytes(doc, path)
    weights = {name: _layer_arrays(doc, "layers", name, rows, cols, path)
               for name, rows, cols in colour_layers(h, k)}
    head = {name: _layer_arrays(doc, "head", name, rows, cols, path)
            for name, rows, cols in head_layers(r, k)}
    recs = edge_records(doc, path, k)
    out = bytearray(b"NEURONTE")
    out += struct.pack("<5I", 3, 6, 64, h, 3)
    out += struct.pack("<f", tau)
    out += struct.pack("<5I", k, PALETTE_N, 5, r, len(recs))
    out += struct.pack("<I", SNAP_PX)
    out += struct.pack("<43I", *masks)
    out += dark + light
    assert len(out) == COLOUR_FIXED, len(out)
    for name, _, _ in colour_layers(h, k):
        w, b = weights[name]
        out += w.astype("<f4").tobytes() + b.astype("<f4").tobytes()
    for name, _, _ in head_layers(r, k):
        w, b = head[name]
        out += w.astype("<f4").tobytes() + b.astype("<f4").tobytes()
    out += pack_edges(recs)
    return bytes(out)


def pack(path):
    """The version 1 image of a distance net, or the version 3 image of form A."""
    with open(path) as fh:
        doc = json.load(fh)
    fmt = doc.get("format")
    if fmt == "neuronte-weights":
        return pack_v1(path)
    if fmt == "neuronte-colour-weights":
        return pack_colour(path, doc)
    if fmt == "neuronte-colour-weights-experimental" or doc.get("shape", {}).get("form") == "B":
        raise SystemExit(f"{path}: form B and the experimental colour file are not packed")
    raise SystemExit(f"{path}: not a Neuronte weights file")


def colour_signature(image):
    """(snap threshold, 192 palette bytes) for a version 3 image, else None."""
    if len(image) < COLOUR_FIXED or image[:8] != b"NEURONTE":
        return None
    if struct.unpack_from("<I", image, 8)[0] != 3:
        return None
    return image[52:56], image[228:COLOUR_FIXED]


def read_colour(data):
    """The fields of a version 3 image, for the tests."""
    if len(data) < COLOUR_FIXED or data[:8] != b"NEURONTE" or struct.unpack_from("<I", data, 8)[0] != 3:
        raise ValueError("not a version 3 Neuronte file")
    h = struct.unpack_from("<I", data, 20)[0]
    k, p, bits, r, e = struct.unpack_from("<5I", data, 32)
    tau = struct.unpack_from("<f", data, 28)[0]
    snap = struct.unpack_from("<I", data, 52)[0]
    masks = list(struct.unpack_from("<43I", data, 56))
    dark, light = data[228:324], data[324:420]
    off = COLOUR_FIXED
    trunk = trunk_floats(h, k)
    head_n = head_floats(r, k)
    floats = np.frombuffer(data[off:off + 4 * (trunk + head_n)], dtype="<f4").astype(np.float32).copy()
    off += 4 * (trunk + head_n)
    recs = []
    for _ in range(e):
        scalar = struct.unpack_from("<I", data, off)[0]
        off += 4
        layers = []
        for _k in range(k):
            nx, ny = struct.unpack_from("<HH", data, off)
            off += 4
            edges = []
            for _e in range(nx + ny):
                pos, rising = struct.unpack_from("<fI", data, off)
                off += 8
                edges.append((float(pos), int(rising)))
            layers.append((edges[:nx], edges[nx:]))
        recs.append((scalar, layers))
    if off != len(data):
        raise ValueError(f"version 3 image has {len(data) - off} trailing bytes")
    return {"hidden_width": h, "layers": k, "palette_entries": p, "entry_bits": bits,
            "head_width": r, "edge_records": e, "tau": tau, "snap": snap, "masks": masks,
            "dark": dark, "light": light, "floats": floats, "records": recs}


def scalars(path):
    """The scalars a net was trained on, from its JSON."""
    with open(path) as fh:
        doc = json.load(fh)
    out = set()
    for tok in doc["training"]["labelled"].split():
        lo, _, hi = tok.partition("..")
        out.update(range(int(lo[2:], 16), int((hi or lo)[2:], 16) + 1))
    # The first ASCII weights were made before sets had names.
    return doc["training"].get("set", "ascii"), out


def table(nets):
    """Sorted (first, last, net) ranges over the scalars each net knows."""
    owner = {}
    for i, path in enumerate(nets):
        for v in scalars(path)[1]:
            if v in owner:
                raise SystemExit(f"U+{v:04X} is in both {nets[owner[v]]} and {path}")
            owner[v] = i
    out = []
    for v in sorted(owner):
        if out and out[-1][1] == v - 1 and out[-1][2] == owner[v]:
            out[-1][1] = v
        else:
            out.append([v, v, owner[v]])
    return out


def load_gate(path, names):
    with open(path) as fh:
        doc = json.load(fh)
    if doc.get("format") != "neuronte-gate" or doc.get("version") != 1:
        raise SystemExit(f"{path}: not a version 1 Neuronte gate")
    if doc["nets"] != names:
        raise SystemExit(f"{path}: made for nets {doc['nets']}, the bundle has {names}")
    g, k = doc["hidden_width"], len(names)
    if not (isinstance(g, int) and 1 <= g <= 256):
        raise SystemExit(f"{path}: gate width {g} is not 1 to 256")
    masks = [int(m, 16) for m in doc["parity_masks"]]
    if len(masks) != 43 or any(not 0 < m < 1 << 21 for m in masks):
        raise SystemExit(f"{path}: parity masks must be 43 values over 21 bits")
    out = bytearray(struct.pack("<43I", *masks))
    for name, rows, cols in (("l1", g, 64), ("out", k, g)):
        layer = doc["layers"][name]
        w = np.asarray(layer["weight"], np.float32)
        b = np.asarray(layer["bias"], np.float32)
        if (layer["rows"], layer["cols"]) != (rows, cols) or w.size != rows * cols or b.size != rows:
            raise SystemExit(f"{path}: gate layer {name} is not {rows} x {cols}")
        if not (np.isfinite(w).all() and np.isfinite(b).all()):
            raise SystemExit(f"{path}: gate layer {name} holds a value that is not finite")
        out += w.astype("<f4").tobytes() + b.astype("<f4").tobytes()
    return g, bytes(out)


def bundle(nets, gate=None, fallback=0):
    if not 1 <= len(nets) <= 16:
        raise SystemExit("a bundle holds 1 to 16 nets")
    if not 0 <= fallback < len(nets):
        raise SystemExit(f"fallback {fallback} is not one of the {len(nets)} nets")
    images = [pack(p) for p in nets]
    sigs = [s for s in (colour_signature(im) for im in images) if s is not None]
    if any(s != sigs[0] for s in sigs):
        raise SystemExit("colour nets in one bundle must carry the same palette and snap threshold")
    ranges = table(nets)
    g, gate_bytes = load_gate(gate, [scalars(p)[0] for p in nets]) if gate else (0, b"")
    out = bytearray(b"NEURONTE")
    out += struct.pack("<5I", 2, len(nets), len(ranges), fallback, g)
    out += struct.pack(f"<{len(nets)}I", *map(len, images))
    for r in ranges:
        out += struct.pack("<3I", *r)
    out += gate_bytes
    for im in images:
        out += im
    return bytes(out), ranges


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--bundle"] and len(args) >= 3:
        gate, fallback, nets = None, 0, []
        it = iter(args[2:])
        for a in it:
            if a == "--gate":
                gate = next(it)
            elif a == "--fallback":
                fallback = int(next(it))
            else:
                nets.append(a)
        data, ranges = bundle(nets, gate, fallback)
        out = args[1]
        print(out, len(data), "bytes,", len(nets), "nets,", len(ranges), "ranges,",
              "a gate" if gate else f"fallback net {fallback}")
    elif len(args) == 2 and not args[0].startswith("--"):
        data, out = pack(args[0]), args[1]
        print(out, len(data), "bytes")
    else:
        raise SystemExit(__doc__)
    with open(out, "wb") as fh:
        fh.write(data)
