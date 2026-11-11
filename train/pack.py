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
weights JSON, packed as a version 1 net; an advances file or a pixel
face, packed as a table; or a file already packed, version 1, 3 or 4, copied whole. A
version 3 colour net is copied without being read: this packer does not
make or check one.

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

One net, version 1, all little-endian:

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
        the K nets, each a whole version 1 file

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
import json
import struct
import sys

import numpy as np

SHAPE = {"position_octaves": 6, "code_bits": 64, "hidden_layers": 3}


def layers(h):
    return [("l1", h, 90), ("l2", h, h), ("l3", h, h), ("out", 1, h)]


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


def pack(path):
    """The version 1 image of one net."""
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
        lines = [(n, l.rstrip("\n")) for n, l in enumerate(fh, 1)]
    lines = [(n, l) for n, l in lines if l and l != "#" and not l.startswith("# ")]
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
        return 1, pack(path)
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
