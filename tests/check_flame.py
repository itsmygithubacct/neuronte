"""The Kilix flame's acceptance through the C library, as Kilix 95 draws it.

usage: check_flame.py LIB JSON NRT [--out REPORT] [--report-only]
                      [--max-xor 16:A,B,C --max-xor 32:A,B,C]

Kilix 95 draws the mark with neuronte_draw_scalar into an s by s
transparent buffer, from an s by 2s cell placed s/2 rows up, at s = 16
and 32, so the cell's middle square is the image. Automatic sampling:
2 x 2 at 16, 1 at 32. The file's snap threshold of 14 leaves both sizes
unsnapped. At each size this checks, against the drawing sampled
analytically at 8 x 8 points a pixel (font/flame.txt):

- every palette entry is the drawing's (red, yellow, white);
- the composite on the dark and on the light theme: no channel of any
  pixel of the square more than 32 of 255 from the drawing's composite,
  and the mean at most 2 of 255;
- the image the consumer receives, premultiplied: no channel, alpha
  included, more than 32 of 255 from the drawing's;
- the printable ASCII and U+FFFD, the blanks the net was trained with,
  write no pixel at either size;
- with --max-xor, each layer's > .5 mask over the whole cell differs from
  the drawing's in at most that many pixels (the accepted net's counts).

It reports, without gating, each layer's mask differences, the mean
errors, and the largest blank coverage.
"""
import argparse
import ctypes
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "train"), os.path.join(ROOT, "tests")]
import glyphs  # noqa: E402
import pack  # noqa: E402
import strokes  # noqa: E402
from check_icon_quality import composite, sample_points  # noqa: E402

SCALAR = 0x100000
BLANKS = list(range(0x20, 0x7F)) + [0xFFFD]
SIZES = (16, 32)


def straight(cov, entries, pal):
    """Premultiplied composite on nothing, returned as straight RGBA in 0..1."""
    table = {n: np.asarray(d, np.float32) / 255 for n, d, _ in pal.values() if n >= 2}
    rgb = np.zeros((*cov.shape[1:], 3), np.float32)
    alpha = np.zeros((*cov.shape[1:], 1), np.float32)
    for c, e in zip(cov, entries):
        c = c[..., None]
        if e == 1:
            rgb *= 1 - c
            alpha *= 1 - c
        else:
            ink = table.get(e, np.ones(3, np.float32))
            rgb = ink * c + rgb * (1 - c)
            alpha = c + alpha * (1 - c)
    out = np.where(alpha > 0, rgb / np.maximum(alpha, 1e-12), 0)
    return np.concatenate([out, alpha], -1)


def parse_xor(values):
    out = {}
    for v in values or []:
        size, _, counts = v.partition(":")
        out[int(size)] = [int(x) for x in counts.split(",")]
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("lib")
    p.add_argument("json")
    p.add_argument("nrt")
    p.add_argument("--out")
    p.add_argument("--report-only", action="store_true")
    p.add_argument("--max-xor", action="append", help="SIZE:L0,L1,L2 most mask pixels per layer off the drawing")
    a = p.parse_args()
    with open(a.json) as fh:
        doc = json.load(fh)
    pack.check_sources(doc, a.json)
    if pack.colour_sources(doc) != ("font/flame.txt", "font/flame-palette.txt"):
        raise SystemExit("not a flame net")
    with open(a.nrt, "rb") as fh:
        if fh.read() != pack.pack(a.json):
            raise SystemExit("the packed file is not the packer's output for the JSON")
    max_xor = parse_xor(a.max_xor)
    pal = strokes.palette(os.path.join(ROOT, "font/flame-palette.txt"))
    layers = strokes.parse_layers(os.path.join(ROOT, "font/flame.txt"), pal)[chr(SCALAR)]
    want = [pal[name][0] for name, _ in layers]
    lib = ctypes.CDLL(os.path.abspath(a.lib))
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.neuronte_close.argtypes = [ctypes.c_void_p]
    lib.neuronte_layers.argtypes = [ctypes.c_void_p]
    lib.neuronte_coverage_layers.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int,
                                             ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
    lib.neuronte_draw_scalar.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32), ctypes.c_int,
                                         ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32]
    handle = ctypes.c_void_p()
    if lib.neuronte_open_file(a.nrt.encode(), ctypes.byref(handle)) != 0:
        raise SystemExit("C library refused the packed net")
    k = lib.neuronte_layers(handle)
    report = {"json": os.path.relpath(a.json, ROOT), "sizes": {}, "passed": True}
    for s in SIZES:
        ss = 2 if s < 24 else 1
        points = sample_points(s)
        target = np.stack([(glyphs.signed_distance(sh, points, glyphs.PEN) > 0)
                           .reshape(2 * s, 8, s, 8).mean((1, 3)) for _, sh in layers]).astype(np.float32)
        cov = np.zeros((k, 2 * s, s), np.float32)
        ent = (ctypes.c_uint8 * k)()
        if lib.neuronte_coverage_layers(handle, SCALAR, s, 2 * s, 0, cov.ctypes.data, ent) != 0:
            raise SystemExit("C coverage failed")
        entries = list(ent)
        rows = slice(s // 2, s // 2 + s)
        r = {"samples": ss, "entries": entries, "entries_ok": entries[:len(layers)] == want
             and all(c.max() == 0 for c in cov[len(layers):])}
        r["layer_xor"] = [int(((t > .5) != (c > .5)).sum()) for t, c in zip(target, cov)]
        for theme in ("dark", "light"):
            err = np.abs(composite(cov[:len(layers)], entries, pal, theme)
                         - composite(target, want, pal, theme))[rows] * 255
            r[theme] = {"max": float(err.max()), "mean": float(err.mean())}
        buf = (ctypes.c_uint32 * (s * s))()
        if lib.neuronte_draw_scalar(handle, buf, s, s, s, 0, -s // 2, s, 2 * s, SCALAR, 0xFFFFFFFF) != 0:
            raise SystemExit("C draw failed")
        px = np.frombuffer(buf, np.uint32).reshape(s, s)
        got = np.stack([(px >> 16) & 255, (px >> 8) & 255, px & 255, px >> 24], -1).astype(np.float64)
        ref = straight(target, want, pal)[rows] * 255
        # Compare premultiplied: a colour with almost no alpha carries no weight.
        pm = lambda im: np.concatenate([im[..., :3] * im[..., 3:] / 255, im[..., 3:]], -1)
        diff = np.abs(pm(got) - pm(ref))
        r["consumer"] = {"max": float(diff.max()), "mean": float(diff.mean()),
                         "visible_pixels": int((px >> 24 > 0).sum())}
        blank_px, blank_cov = 0, 0.0
        for b in BLANKS:
            bb = (ctypes.c_uint32 * (s * s))()
            if lib.neuronte_draw_scalar(handle, bb, s, s, s, 0, -s // 2, s, 2 * s, b, 0xFFFFFFFF) != 0:
                raise SystemExit("C draw failed")
            blank_px += int((np.frombuffer(bb, np.uint32) != 0).sum())
            bc = np.zeros((k, 2 * s, s), np.float32)
            be = (ctypes.c_uint8 * k)()
            lib.neuronte_coverage_layers(handle, b, s, 2 * s, 0, bc.ctypes.data, be)
            blank_cov = max(blank_cov, float(bc.max()))
        r["blank_pixels_written"] = blank_px
        r["blank_max_coverage"] = blank_cov
        ok = (r["entries_ok"] and max(r["dark"]["max"], r["light"]["max"]) <= 32
              and max(r["dark"]["mean"], r["light"]["mean"]) <= 2 and r["consumer"]["max"] <= 32
              and blank_px == 0)
        if s in max_xor:
            r["max_xor"] = max_xor[s]
            ok = ok and all(x <= m for x, m in zip(r["layer_xor"], max_xor[s]))
        r["passed"] = bool(ok)
        report["passed"] &= r["passed"]
        report["sizes"][str(s)] = r
        print(f"{s}px: entries {entries}, layer xor {r['layer_xor']}, composite max/mean dark "
              f"{r['dark']['max']:.2f}/{r['dark']['mean']:.3f} light {r['light']['max']:.2f}/{r['light']['mean']:.3f}, "
              f"consumer max/mean {r['consumer']['max']:.2f}/{r['consumer']['mean']:.3f}, "
              f"blank px {blank_px} (max cov {blank_cov:.4f}): {'pass' if ok else 'FAIL'}", flush=True)
    lib.neuronte_close(handle)
    if a.out:
        tmp = a.out + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(report, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, a.out)
    print("flame gate: " + ("PASS" if report["passed"] else "FAIL"))
    return 0 if report["passed"] or a.report_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
