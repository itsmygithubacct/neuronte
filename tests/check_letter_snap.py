"""Letter edge tables (version 7): snapped letters, and nothing else changed.

usage: python3 tests/check_letter_snap.py LIB.so [FACE.nrt ADVANCES SET SNAP_BELOW on|off MEMBER.json...]

With no face: the shipped 8 px face net (one version 1 net) is packed as a
drawing file with its advances, once alone and once with a letter edge
table of its own drawings (train/pack.py letter_edges). Below the
threshold every letter with a record must be the float64 reference: the
cell's samples warped by train/snap.py's knots for that em, the net read
at the warped places, each sample clamp(0.5 + f tau W S), each pixel the
mean of its S x S. At and above the threshold, with snapping turned off
(neuronte_set_snap 0), and for a letter with no record, every coverage and
every binary draw must be byte for byte the file without the table. The
reader must refuse a damaged table, a second table, and a table alone.

With a face (a drawing bundle with a letter table, packed from MEMBER.json,
tiled or plain nets in bundle order): the face must be byte for byte what
pack.py makes (on|off: --edge-extremes), every letter must match the reference at every em from 8 to
SNAP_BELOW - 1 within 1e-3 (2 x 2 samples below 24 px, 1 from 24) and
draw as the packed file without the table from SNAP_BELOW to SNAP_BELOW + 1.
"""
import ctypes
import json
import math
import os
import struct
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "train"))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import glyphs  # noqa: E402
import pack  # noqa: E402
import snap  # noqa: E402
import tiled_reference as tr  # noqa: E402

failed = False


def fail(msg):
    global failed
    print("FAIL", msg)
    failed = True


lib = ctypes.CDLL(os.path.abspath(sys.argv[1]))
lib.neuronte_open.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_void_p)]
lib.neuronte_close.argtypes = [ctypes.c_void_p]
lib.neuronte_coverage.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                  ctypes.POINTER(ctypes.c_float)]
lib.neuronte_set_snap.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.neuronte_set_binary.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.neuronte_draw_text.argtypes = ([ctypes.c_void_p, ctypes.c_void_p] + [ctypes.c_int] * 7
                                   + [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint32])


def open_bytes(data):
    h = ctypes.c_void_p()
    rc = lib.neuronte_open(data, len(data), ctypes.byref(h))
    return rc, h


def cov(h, s, em):
    buf = (ctypes.c_float * (2 * em * em))()
    rc = lib.neuronte_coverage(h, s, em, 2 * em, 0, buf)
    if rc:
        raise SystemExit(f"coverage rc {rc}")
    return np.frombuffer(buf, np.float32).reshape(2 * em, em).copy()


def draw(h, s, em):
    lib.neuronte_set_binary(h, 1)
    W, H = 2 * em + 2, 2 * em
    buf = np.zeros((H, W), np.uint32)
    t = chr(s).encode()
    lib.neuronte_draw_text(h, buf.ctypes.data, W, W, H, 0, 0, em, 1, t, len(t), 0xFFFFFFFF)
    return buf


class Plain:
    """A version 1 net as a one-tile tiled net."""

    def __init__(self, doc):
        self.net = tr.Distance(doc)

    def at(self, s, gx, gy, cw, ss):
        yy, xx = np.meshgrid(gy, gx, indexing="ij")
        f = self.net.field(tr.normal(s), xx.ravel(), yy.ravel()).reshape(len(gy), len(gx))
        return np.clip(0.5 + f * self.net.tau * cw * ss, 0, 1)


class Tiled(tr.Tiled):
    def at(self, s, gx, gy, cw, ss):
        s = tr.normal(s)
        cols, rows = len(self.xe) - 1, len(self.ye) - 1
        xe, ye = np.asarray(self.xe), np.asarray(self.ye)
        col = np.minimum(np.searchsorted(xe, gx, side="right") - 1, cols - 1)
        row = np.minimum(np.searchsorted(ye, gy, side="right") - 1, rows - 1)
        lx = (gx - xe[col]) / (xe[col + 1] - xe[col])
        ly = (gy - ye[row]) / (ye[row + 1] - ye[row]) * 2
        out = np.full((len(gy), len(gx)), np.nan)
        for k, tile in enumerate(self.tiles):
            r, c = divmod(k, cols)
            jx, jy = np.nonzero(col == c)[0], np.nonzero(row == r)[0]
            if not len(jx) or not len(jy):
                continue
            net = self.nets[tile[0]]
            yy, xx = np.meshgrid(ly[jy], lx[jx], indexing="ij")
            f = net.field(self.code(s, tile), xx.ravel(), yy.ravel()).reshape(len(jy), len(jx))
            out[np.ix_(jy, jx)] = np.clip(0.5 + f * net.tau * (xe[c + 1] - xe[c]) * cw * ss, 0, 1)
        assert not np.isnan(out).any()
        return out


def reference(model, rec, s, em):
    """Float64 coverage of a snapped letter at em: snap.py's knots, warped samples."""
    ss = 2 if em < 24 else 1
    xs, ys = rec
    kx = snap.knots([xs], em, em)
    ky = snap.knots([ys], em, 2 * em)
    gx = snap.sample_positions(em, ss, kx, em)
    gy = snap.sample_positions(2 * em, ss, ky, em)
    return model.at(s, gx, gy, em, ss).reshape(2 * em, ss, em, ss).mean((1, 3))


def records(table):
    """{scalar: (xs, ys)} from a version 7 image."""
    count = struct.unpack_from("<I", table, 16)[0]
    out, at = {}, 20
    for _ in range(count):
        s, nx, ny = struct.unpack_from("<IHH", table, at)
        at += 8
        e = [struct.unpack_from("<fI", table, at + 8 * i) for i in range(nx + ny)]
        at += 8 * (nx + ny)
        out[s] = ([(float(p), bool(r)) for p, r in e[:nx]], [(float(p), bool(r)) for p, r in e[nx:]])
    assert at == len(table)
    return out


def check(name, with_edges, without, model, recs, chars, snap_below, ems_snapped, ems_same):
    rc1, hs = open_bytes(with_edges)
    rc2, hp = open_bytes(without)
    if rc1 or rc2:
        fail(f"{name}: open {rc1} {rc2}")
        return
    worst, snapped, same = 0.0, 0, 0
    for em in ems_snapped:
        for s in chars:
            got = cov(hs, s, em)
            if s in recs:
                want = reference(model, recs[s], s, em)
                worst = max(worst, float(np.abs(got - want).max()))
                snapped += 1
            elif got.tobytes() != cov(hp, s, em).tobytes():
                fail(f"{name}: U+{s:04X} has no record and changed at {em} px")
    if worst > 1e-3:
        fail(f"{name}: snapped coverage differs from the float64 reference by {worst:.2e}")
    for em in ems_same:
        for s in chars:
            same += 1
            if cov(hs, s, em).tobytes() != cov(hp, s, em).tobytes() or draw(hs, s, em).tobytes() != draw(hp, s, em).tobytes():
                fail(f"{name}: U+{s:04X} changed at {em} px, at or above the threshold {snap_below}")
    lib.neuronte_set_snap(hs, 0)
    for em in ems_snapped[:2]:
        for s in chars:
            same += 1
            if cov(hs, s, em).tobytes() != cov(hp, s, em).tobytes() or draw(hs, s, em).tobytes() != draw(hp, s, em).tobytes():
                fail(f"{name}: U+{s:04X} changed at {em} px with snapping off")
    lib.neuronte_set_snap(hs, -1)
    changed = sum(cov(hs, s, ems_snapped[0]).tobytes() != cov(hp, s, ems_snapped[0]).tobytes() for s in chars if s in recs)
    if not changed:
        fail(f"{name}: no letter changed at {ems_snapped[0]} px: nothing was snapped")
    lib.neuronte_close(hs)
    lib.neuronte_close(hp)
    print(f"{name}: {snapped} snapped letters within {worst:.1e} of the float64 reference; "
          f"{same} unsnapped cases byte for byte the file without edges; {changed} changed at {ems_snapped[0]} px")


def refusals(edges, bundle_members):
    """Damaged or misplaced tables must be refused, not misdrawn."""
    def drawing(extra):
        """A version 5 image built here, so the packer's own checks do not stop it."""
        members = bundle_members + extra
        out = bytearray(b"NEURONTE") + struct.pack("<2I", 5, len(members))
        off = 16 + 8 * len(members)
        for _, im in members:
            out += struct.pack("<2I", off, len(im))
            off += len(im)
        for _, im in members:
            out += im
        return bytes(out)
    good = drawing([(7, edges)])
    if open_bytes(good)[0] != 0:
        fail("the good table is refused")
    bad = {
        "a second table": None,
        "version word 8": edges[:8] + struct.pack("<I", 8) + edges[12:],
        "threshold 0": edges[:12] + struct.pack("<I", 0) + edges[16:],
        "no records": edges[:16] + struct.pack("<I", 0) + edges[20:],
        "a trailing byte": edges + b"\0",
        "cut short": edges[:-4],
        "a side of 2": edges[:20 + 8 + 4] + struct.pack("<I", 2) + edges[20 + 8 + 8:],
        "a position past the cell": edges[:20 + 8] + struct.pack("<f", 3.0) + edges[20 + 12:],
    }
    for name, img in bad.items():
        data = drawing([(7, edges), (7, edges)]) if img is None else drawing([(7, img)])
        rc, h = open_bytes(data)
        if rc == 0:
            lib.neuronte_close(h)
            fail(f"a letter table with {name} was opened")
    rc, h = open_bytes(edges)
    if rc == 0:
        fail("a letter table alone was opened")
    print(f"letter tables: {len(bad) + 1} damaged or misplaced tables refused")


chars = [ord(c) for c, _, _ in glyphs.charset("ui8")]
doc = json.load(open(os.path.join(ROOT, "weights", "neuronte-ui8-v0.json")))
net = pack.pack(os.path.join(ROOT, "weights", "neuronte-ui8-v0.json"))
table = pack.advances(pack.read_table(os.path.join(ROOT, "font", "ui-8.txt"), None), 0x3F)
edges, recs = pack.letter_edges("ui8", 12)
plain = pack.drawing_images([(1, net), (4, table)])[0]
withe = pack.drawing_images([(1, net), (4, table), (7, edges)])[0]
check("ui8 net with ui8 edges", withe, plain, Plain(doc), records(edges), chars, 12, [8, 9, 11], [12, 16])
refusals(edges, [(1, net), (4, table)])

if len(sys.argv) > 2:
    face, adv, set_name, snap_below = sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
    extremes, members = sys.argv[6] == "on", sys.argv[7:]
    edges, _ = pack.letter_edges(set_name, snap_below, None, extremes)
    made, _ = pack.face_bundle(adv, members, edges=edges)
    plain, _ = pack.face_bundle(adv, members)
    with open(face, "rb") as fh:
        data = fh.read()
    if data != made:
        fail(f"{face} is not what pack.py makes")
    docs = [json.load(open(m)) for m in members]
    parts = {}
    for m, d in zip(members, docs):
        model = Tiled(d) if d.get("format") == "neuronte-tiled-weights" else Plain(d)
        for s in pack.scalars(m)[1]:
            parts[s] = model
    fchars = [ord(c) for c, _, _ in glyphs.charset(set_name)]
    recs = records(edges)

    class Routed:
        def at(self, s, gx, gy, cw, ss):
            return parts[s].at(s, gx, gy, cw, ss)
    check(os.path.basename(face), data, plain, Routed(), recs, fchars, snap_below,
          list(range(8, snap_below)), [snap_below, snap_below + 1])

if failed:
    raise SystemExit("check_letter_snap: FAILED")
print("check_letter_snap: passed")
