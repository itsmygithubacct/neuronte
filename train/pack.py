"""Pack weights JSON into the binary file the C library loads.

usage: python3 train/pack.py WEIGHTS.json OUT.nrt
       python3 train/pack.py --bundle OUT.nrt NET.json... [--gate GATE.json]
                             [--fallback I]
       python3 train/pack.py --advances ADVANCES.txt OUT.nrt
                             [--fallback-char U+003F] [--bold-add UNITS]
       python3 train/pack.py --drawing OUT.nrt MEMBER...
                             [--fallback-char U+003F] [--bold-add UNITS]

The first form packs one net. The second packs a bundle of nets with a
router: each scalar a net was trained on is drawn by that net, so no two
nets may share one. Other scalars go to the gate (from train/gate.py, made
for the same nets in the same order) or, with no gate, to net I (0).

The third packs an advance table for a proportional face, and the fourth
a drawing file, whose members are kept in the order given. A member is
weights JSON, packed as a version 1 net; a colour JSON, packed as a
version 3 net; an advances file or a pixel face, packed as a table; or
a file already packed, version 1, 3 or 4, copied whole.

An advances file has one character per line, as the stroke files do: the
character (or U+XXXX), a space, then its regular and its bold advance in
design units, 10 to the em, to one decimal:

    U+0020 3.0 3.0
    A 6.4 7.1

A line with one number takes the bold advance as that number plus
--bold-add. An advance is the pen's step, side bearings included, from
1.0 to 20.0. Lines starting "# " are comments. The fallback character,
which a character with no line is measured and drawn as, must have a
line.

ADVANCES.txt may instead be a pixel face, such as font/ui-10.txt: a
face drawn as rows of pixels for one em, each character's line giving
its advance in pixels. The table then holds, for each character, steps
that come to that many pixels at that em, and to one pixel more for
bold. --bold-add is not used.

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
rising and 0 for falling. The edges come from training.drawing (default
font/icons.txt), including generated icon rules, and training.palette
(default font/palette.txt). New weights bind each expanded labelled drawing
with training.drawings_sha256. Legacy weights require matching drawing-file
and rule-module hashes in training.sources_sha256. Historical trainer hashes
remain provenance records rather than blocking unrelated code changes.

An advance table, version 4. An advance is stored in steps of a tenth of
a design unit:

    0   8 bytes   "NEURONTE"
    8   u32       format version, 4
    12  u32       design units per em, 10
    16  u32       steps per design unit, 10
    20  u32       weights, 2: regular, then bold
    24  u32       records N, 1 to 4096
    28  u32       fallback scalar, the scalar of one of the records
    32  N x 8     u32 scalar, u16 regular, u16 bold, each 10 to 200 steps;
                  sorted by scalar, none repeated

32 + 8 N bytes in all. An advance of a steps is (a * e + 50) // 100
pixels at an em of e pixels: the nearest pixel, a tie going up.

A drawing file, version 5:

    0   8 bytes   "NEURONTE"
    8   u32       format version, 5
    12  u32       members M, 1 to 16
    16  M x 2 u32 each member's offset from the start of the file, and
                  its length
        the M members, in that order with nothing between them, each a
                  whole version 1, 3 or 4 file; at most one is version 4
"""
import decimal
import hashlib
import json
import os
import struct
import sys

import numpy as np

import glyphs
import snap
import strokes
from colour_sources import drawing_hashes, drawing_at, wide_halves

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


def colour_sources(doc):
    """The drawing and the palette a colour net was trained on, relative to the tree."""
    training = doc.get("training", {})
    return training.get("drawing", "font/icons.txt"), training.get("palette", "font/palette.txt")


def colour_drawings(doc):
    """Expand the named drawing, including rules only for the icon collection."""
    drawing, palette = colour_sources(doc)
    pal = strokes.palette(os.path.join(ROOT, palette))
    if drawing == "font/icons.txt":
        return glyphs.colour_icons(pal=pal)
    drawings = strokes.parse_layers(os.path.join(ROOT, drawing), pal)
    return wide_halves(drawings) if doc.get("training", {}).get("cell_columns", 1) == 2 else drawings


# The original colour artifacts predate explicit parser/expanded-drawing hashes.
# Their archived sources used this parser. Do not silently repack them with a
# changed parser: a later parser needs recorded provenance or semantic hashes.
LEGACY_STROKES_SHA256 = "31382edcb36b1286b2f56de05dfd2e22b998778abb1a93d68d07a277b47833a2"


def check_sources(doc, path):
    """Bind packing to the labelled drawings, not an unrelated trainer edit.

    New nets record expanded per-glyph drawings as well as historical source
    hashes. Legacy files retain their named drawing/palette, parser and rule
    checks. A legacy file without a parser digest requires the original parser.
    Trainer hashes are evidence of how weights were made, not a requirement
    that future packers run from that same trainer revision.
    """
    src = doc.get("training", {}).get("sources_sha256")
    for rel in colour_sources(doc):
        if not isinstance(src, dict) or rel not in src:
            raise SystemExit(f"{path}: training.sources_sha256 has no {rel}")
    for rel, digest in src.items():
        if not isinstance(rel, str) or os.path.isabs(rel) or ".." in rel.split("/"):
            raise SystemExit(f"{path}: sources_sha256 path {rel!r} is not inside the tree")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise SystemExit(f"{path}: sources_sha256 digest for {rel} is not SHA256")
    drawings = doc["training"].get("drawings_sha256")
    if drawings is not None:
        if not isinstance(drawings, dict) or drawings.get("version") != 1:
            raise SystemExit(f"{path}: unsupported drawings_sha256 version")
        try:
            want = drawing_hashes(colour_drawings(doc), labelled_scalars(doc, path))
        except KeyError as error:
            raise SystemExit(f"{path}: a labelled drawing is missing: {error}") from None
        if drawings.get("glyphs") != want:
            raise SystemExit(f"{path}: labelled drawings do not match training.drawings_sha256")
        return
    required = set(colour_sources(doc)) | {"train/glyphs.py", "train/strokes.py"}
    for rel, digest in src.items():
        if not rel.startswith("font/") and rel not in required:
            continue
        fp = os.path.join(ROOT, rel)
        if not os.path.isfile(fp):
            raise SystemExit(f"{path}: {rel} is not in the tree")
        if sha256_file(fp) != digest:
            raise SystemExit(f"{path}: {rel} sha256 does not match training.sources_sha256")
    if "train/strokes.py" not in src:
        parser_path = os.path.join(ROOT, "train/strokes.py")
        if not os.path.isfile(parser_path) or sha256_file(parser_path) != LEGACY_STROKES_SHA256:
            raise SystemExit(f"{path}: legacy drawing has no parser digest and requires the original train/strokes.py")


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
    rel = colour_sources(doc)[1]
    file_pal = strokes.palette(os.path.join(ROOT, rel))
    if not isinstance(got, dict) or set(got) != set(file_pal):
        raise SystemExit(f"{path}: palette names do not match {rel}")
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
                raise SystemExit(f"{path}: palette entry {n} {side} does not match {rel}")
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
    icons = colour_drawings(doc)
    ruled = set(glyphs.ruled_codepoints()) if colour_sources(doc)[0] == "font/icons.txt" else set()
    recs = []
    for s in sorted(labelled_scalars(doc, path)):
        try:
            drawn = drawing_at(icons, s)
        except (KeyError, ValueError):
            raise SystemExit(f"{path}: U+{s:04X} is labelled and is not in {colour_sources(doc)[0]}")
        if s in ruled and "train/glyphs.py" not in doc["training"]["sources_sha256"]:
            raise SystemExit(f"{path}: U+{s:04X} is made by rule and training.sources_sha256 has no train/glyphs.py")
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
    return _bundle_images(nets, [pack(p) for p in nets], gate, fallback)


def _bundle_images(nets, images, gate=None, fallback=0):
    """Assemble already packed members; callers must bind them to their sources."""
    if len(images) != len(nets):
        raise SystemExit("packed member inventory differs from source inventory")
    if not 1 <= len(nets) <= 16:
        raise SystemExit("a bundle holds 1 to 16 nets")
    if not 0 <= fallback < len(nets):
        raise SystemExit(f"fallback {fallback} is not one of the {len(nets)} nets")
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


ADV_STEPS = (10, 200)  # the least and the greatest advance, in steps
ADV_RECORDS = 4096
MEMBERS = 16


def pixels(steps, em):
    """An advance of that many steps, in pixels, at an em of em pixels."""
    return (steps * em + 50) // 100


def _steps(tok, where):
    try:
        steps = decimal.Decimal(tok) * 10
    except decimal.InvalidOperation:
        raise SystemExit(f"{where}: {tok!r} is not a number") from None
    if not steps.is_finite() or steps != steps.to_integral_value():
        raise SystemExit(f"{where}: {tok} has more than one decimal")
    if not ADV_STEPS[0] <= steps <= ADV_STEPS[1]:
        raise SystemExit(f"{where}: an advance of {tok} is not 1.0 to 20.0")
    return int(steps)


def _scalar(tok, where):
    try:
        v = int(tok[2:], 16) if tok.startswith("U+") else -1
    except ValueError:
        v = -1
    if not (0 <= v <= 0x10FFFF) or 0xD800 <= v <= 0xDFFF:
        raise SystemExit(f"{where}: {tok!r} is not U+ and a Unicode scalar")
    return v


def read_advances(path, bold_add=None):
    """{scalar: (regular, bold)} in steps, from an advances file."""
    add = None if bold_add is None else decimal.Decimal(bold_add)
    out = {}
    with open(path, encoding="utf-8") as fh:
        for num, raw in enumerate(fh, 1):
            line, where = raw.rstrip("\n"), f"{path}:{num}"
            if line.startswith("# ") or line == "#" or not line.strip():
                continue
            if line.startswith("U+"):
                head, _, rest = line.partition(" ")
                v = _scalar(head, where)
            elif line[1:2] == " ":
                v, rest = ord(line[0]), line[2:]
            else:
                raise SystemExit(f"{where}: a line is a character or U+XXXX, a space, and its advances")
            tok = rest.split()
            if len(tok) == 1 and add is not None:
                try:
                    tok.append(str(decimal.Decimal(tok[0]) + add))
                except decimal.InvalidOperation:
                    raise SystemExit(f"{where}: {tok[0]!r} is not a number") from None
            if len(tok) != 2:
                raise SystemExit(f"{where}: U+{v:04X} needs a regular and a bold advance"
                                 + ("" if add is not None or len(tok) != 1 else ", or --bold-add"))
            if v in out:
                raise SystemExit(f"{where}: U+{v:04X} has a line already")
            out[v] = (_steps(tok[0], where), _steps(tok[1], where))
    return out


def read_face(path):
    """({scalar: (regular, bold)} in steps, em) from a pixel face, or None
    if the file is not one. A pixel face has a character line, a
    character or U+XXXX and its advance in pixels, then em rows of . and
    #. The steps come to that advance at that em, and bold to one more."""
    with open(path, encoding="utf-8") as fh:
        raw = [(n, l.rstrip("\n")) for n, l in enumerate(fh, 1)]
    lines, seen = [], False
    for n, l in raw:
        if not l or l.startswith("# "):
            continue
        # A bare "#" before the first character is a comment. After it,
        # "#" is a row of one inked pixel.
        if l == "#" and not seen:
            continue
        if " " in l:
            seen = True
        lines.append((n, l))
    if len(lines) < 2 or " " in lines[1][1] or set(lines[1][1]) - set(".#"):
        return None
    blocks = []
    for n, l in lines:
        if " " in l:
            blocks.append((n, l, []))
        elif not blocks or set(l) - set(".#"):
            raise SystemExit(f"{path}:{n}: a row is . and #, after a character line")
        else:
            blocks[-1][2].append(l)
    em, out = len(blocks[0][2]), {}
    for n, l, rows in blocks:
        where = f"{path}:{n}"
        head, _, px = l.partition(" ")
        v = _scalar(head, where) if head.startswith("U+") else ord(head) if len(head) == 1 else None
        if v is None or not px.isdigit():
            raise SystemExit(f"{where}: a character line is a character or U+XXXX, a space, and its advance in pixels")
        if v in out:
            raise SystemExit(f"{where}: U+{v:04X} has a block already")
        if len(rows) != em or len({len(r) for r in rows}) != 1:
            raise SystemExit(f"{where}: U+{v:04X} is not {em} rows of one length")
        steps = tuple((100 * p + em // 2) // em for p in (int(px), int(px) + 1))
        if not 1 <= int(px) < 2 * em or len(rows[0]) > em or [pixels(s, em) for s in steps] != [int(px), int(px) + 1]:
            raise SystemExit(f"{where}: an advance is 1 to {2 * em - 1} pixels and a row at most {em}")
        out[v] = steps
    return out, em


def read_table(path, bold_add=None):
    """{scalar: (regular, bold)} in steps, from an advances file or a
    pixel face."""
    face = read_face(path)
    return face[0] if face else read_advances(path, bold_add)


def advances(table, fallback=0x3F):
    """The version 4 image of {scalar: (regular, bold)}, in steps."""
    if not 1 <= len(table) <= ADV_RECORDS:
        raise SystemExit(f"an advance table holds 1 to {ADV_RECORDS} characters, not {len(table)}")
    if fallback not in table:
        raise SystemExit(f"the fallback U+{fallback:04X} has no advance")
    out = bytearray(b"NEURONTE")
    out += struct.pack("<6I", 4, 10, 10, 2, len(table), fallback)
    for v in sorted(table):
        if not (0 <= v <= 0x10FFFF) or 0xD800 <= v <= 0xDFFF:
            raise SystemExit(f"{v:#x} is not a Unicode scalar")
        if any(not ADV_STEPS[0] <= s <= ADV_STEPS[1] for s in table[v]) or len(table[v]) != 2:
            raise SystemExit(f"U+{v:04X}: advances {table[v]} are not two of 10 to 200 steps")
        out += struct.pack("<I2H", v, *table[v])
    assert len(out) == 32 + 8 * len(table), len(out)
    return bytes(out)


def member(path, fallback=0x3F, bold_add=None):
    """One member of a drawing file, as (version, image)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw[:8] == b"NEURONTE":
        if len(raw) < 12:
            raise SystemExit(f"{path}: too short to be a packed file")
        version = struct.unpack_from("<I", raw, 8)[0]
        if version == 1:
            h = struct.unpack_from("<I", raw, 20)[0] if len(raw) >= 24 else 0
            if not (8 <= h <= 1024 and h % 8 == 0) or len(raw) != length(h):
                raise SystemExit(f"{path}: not a whole version 1 net")
        elif version == 4:
            n = struct.unpack_from("<I", raw, 24)[0] if len(raw) >= 32 else 0
            if not 1 <= n <= ADV_RECORDS or len(raw) != 32 + 8 * n:
                raise SystemExit(f"{path}: not a whole version 4 advance table")
        elif version != 3:
            raise SystemExit(f"{path}: a version {version} file cannot be a member of a drawing file")
        return version, raw
    if raw.lstrip()[:1] == b"{":
        image = pack(path)
        if len(image) < 12 or image[:8] != b"NEURONTE":
            raise SystemExit(f"{path}: pack did not make a Neuronte file")
        return struct.unpack_from("<I", image, 8)[0], image
    return 4, advances(read_table(path, bold_add), fallback)


def drawing(paths, fallback=0x3F, bold_add=None):
    """The version 5 image of the members, in the order given."""
    if not 1 <= len(paths) <= MEMBERS:
        raise SystemExit(f"a drawing file holds 1 to {MEMBERS} members")
    members = [member(p, fallback, bold_add) for p in paths]
    if sum(v == 4 for v, _ in members) > 1:
        raise SystemExit("a drawing file holds at most one advance table")
    for p, (_, im) in zip(paths, members):
        if len(im) > length(1024):
            raise SystemExit(f"{p}: {len(im)} bytes is more than a member may be, {length(1024)}")
    out = bytearray(b"NEURONTE")
    out += struct.pack("<2I", 5, len(members))
    off = 16 + 8 * len(members)
    for _, im in members:
        out += struct.pack("<2I", off, len(im))
        off += len(im)
    for _, im in members:
        out += im
    assert len(out) == off, len(out)
    return bytes(out), [v for v, _ in members]


def _options(args):
    """(positional, fallback scalar, bold add) from the table forms' arguments."""
    rest, fallback, bold_add, it = [], 0x3F, None, iter(args)
    for a in it:
        if a in ("--fallback-char", "--bold-add"):
            value = next(it, None)
            if value is None:
                raise SystemExit(f"{a} needs a value")
            if a == "--fallback-char":
                fallback = _scalar(value, a)
            else:
                try:
                    bold_add = decimal.Decimal(value)
                except decimal.InvalidOperation:
                    raise SystemExit(f"--bold-add {value!r} is not a number") from None
        elif a.startswith("--"):
            raise SystemExit(__doc__)
        else:
            rest.append(a)
    return rest, fallback, bold_add


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--advances"]:
        rest, fallback, bold_add = _options(args[1:])
        if len(rest) != 2:
            raise SystemExit(__doc__)
        table = read_table(rest[0], bold_add)
        data, out = advances(table, fallback), rest[1]
        print(out, len(data), "bytes,", len(table), f"advances, fallback U+{fallback:04X}")
    elif args[:1] == ["--drawing"]:
        rest, fallback, bold_add = _options(args[1:])
        if len(rest) < 2:
            raise SystemExit(__doc__)
        out = rest[0]
        data, versions = drawing(rest[1:], fallback, bold_add)
        kind = {1: "net", 3: "colour net", 4: "advance table"}
        print(out, len(data), "bytes, members:", ", ".join(kind[v] for v in versions))
    elif args[:1] == ["--bundle"] and len(args) >= 3:
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
