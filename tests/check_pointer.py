"""The NW pointer's acceptance through the C library, for any pointer net.

usage: check_pointer.py LIB JSON NRT [--out REPORT] [--report-only]
                        [--max-xor 16:A,B --max-xor 32:A,B]

The checks of tools/pointer-preview.py (weights/neuronte-pointer-v0.md),
unchanged, at the two accepted cells, 16 x 32 with 2 x 2 samples and
32 x 64 with 1: palette entries 2 and 3, C within 1e-3 of an independent
float64 NumPy evaluation of the JSON, each layer's > .5 mask IoU >= .97
against the drawing's 8 x 8 analytic samples, zero alpha on the cell's
border, first visible tip within one pixel of the drawing's, one
eight-connected visible component, at least 15 contrasting pixels on
each theme, and mean composite error below 4/255. Added here:

- the first visible pixel (coverage > .1 on the silhouette) is exactly
  the consumer's hotspot, (1, 1) at 16 and (3, 3) at 32, so the manifest's
  hotspots stay true;
- with --max-xor, each layer's mask differs from the drawing's in at most
  that many pixels (the accepted net's counts).
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
from check_icon_quality import composite, counts, sample_points  # noqa: E402

SCALAR = 0x100001
CELLS = {16: (2, (1, 1)), 32: (1, (3, 3))}


def numpy_masks(doc, w, ss):
    """Independent float64 inference from JSON; no packed data or C calls."""
    def linear(x, layer):
        weight = np.asarray(layer["weight"], dtype=np.float32).astype(float)
        bias = np.asarray(layer["bias"], dtype=np.float32).astype(float)
        return x @ weight.reshape(layer["rows"], layer["cols"]).T + bias
    masks = [int(m, 16) for m in doc["shape"]["parity_masks"]]
    bits = [(SCALAR >> i) & 1 for i in range(21)]
    bits += [(SCALAR & m).bit_count() & 1 for m in masks]
    code = 2 * np.array(bits) - 1
    yy, xx = np.meshgrid((np.arange(2 * w * ss) + .5) / (w * ss),
                         (np.arange(w * ss) + .5) / (w * ss), indexing="ij")
    x, y = xx.ravel(), yy.ravel()
    features = [2 * x - 1, y - 1]
    for octave in range(6):
        f = 2 * np.pi * 2 ** octave
        features += [np.sin(f * x), np.sin(f * y), np.cos(f * x), np.cos(f * y)]
    inp = np.concatenate([np.stack(features, 1), np.broadcast_to(code, (x.size, 64))], 1)
    for key in ("l1", "l2", "l3"):
        inp = np.maximum(linear(inp, doc["layers"][key]), 0)
    field = linear(inp, doc["layers"]["out"])
    tau = float(np.float32(doc["shape"]["tau"]))
    cov = np.clip(.5 + field * tau * w * ss, 0, 1).reshape(2 * w, ss, w, ss, 2).mean((1, 3))
    logits = linear(np.maximum(linear(code, doc["head"]["h1"]), 0), doc["head"]["out"])
    entries = [sum(int(logits[k * 5 + b] > 0) << b for b in range(5)) for k in range(2)]
    return np.moveaxis(cov, -1, 0), entries


def components(mask):
    """Count eight-connected visible components, detecting detached specks."""
    remaining = set(map(tuple, np.argwhere(mask)))
    total = 0
    while remaining:
        total += 1
        stack = [remaining.pop()]
        while stack:
            y, x = stack.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    point = (y + dy, x + dx)
                    if point in remaining:
                        remaining.remove(point)
                        stack.append(point)
    return total


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("lib")
    p.add_argument("json")
    p.add_argument("nrt")
    p.add_argument("--out")
    p.add_argument("--report-only", action="store_true")
    p.add_argument("--max-xor", action="append", help="SIZE:L0,L1 most mask pixels per layer off the drawing")
    a = p.parse_args()
    max_xor = {}
    for v in a.max_xor or []:
        size, _, cs = v.partition(":")
        max_xor[int(size)] = [int(x) for x in cs.split(",")]
    with open(a.json) as fh:
        doc = json.load(fh)
    pack.check_sources(doc, a.json)
    if pack.colour_sources(doc) != ("font/pointer.txt", "font/pointer-palette.txt"):
        raise SystemExit("not a pointer net")
    with open(a.nrt, "rb") as fh:
        if fh.read() != pack.pack(a.json):
            raise SystemExit("the packed file is not the packer's output for the JSON")
    pal = strokes.palette(os.path.join(ROOT, "font/pointer-palette.txt"))
    layers = strokes.parse_layers(os.path.join(ROOT, "font/pointer.txt"), pal)[chr(SCALAR)]
    lib = ctypes.CDLL(os.path.abspath(a.lib))
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.neuronte_close.argtypes = [ctypes.c_void_p]
    lib.neuronte_coverage_layers.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_int,
                                             ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
    handle = ctypes.c_void_p()
    if lib.neuronte_open_file(a.nrt.encode(), ctypes.byref(handle)) != 0:
        raise SystemExit("C library refused the packed net")
    report = {"json": os.path.relpath(os.path.abspath(a.json), ROOT), "sizes": {}, "passed": True}
    for w, (ss, hotspot) in CELLS.items():
        points = sample_points(w)
        target = np.stack([(glyphs.signed_distance(sh, points, glyphs.PEN) > 0)
                           .reshape(2 * w, 8, w, 8).mean((1, 3)) for _, sh in layers])
        cov = np.zeros((2, 2 * w, w), np.float32)
        entries = (ctypes.c_uint8 * 2)()
        assert lib.neuronte_coverage_layers(handle, SCALAR, w, 2 * w, ss, cov.ctypes.data, entries) == 0
        ref, ent = numpy_masks(doc, w, ss)
        delta = float(np.max(np.abs(ref - cov)))
        layer_scores = [counts(t > .5, c > .5) for t, c in zip(target, cov)]
        xor = [int(((t > .5) != (c > .5)).sum()) for t, c in zip(target, cov)]
        alpha = 1 - (1 - cov[0]) * (1 - cov[1])
        edge = float(max(alpha[0].max(), alpha[-1].max(), alpha[:, 0].max(), alpha[:, -1].max()))
        ty, tx = np.argwhere(target[0] > .1)[0]
        py, px = np.argwhere(cov[0] > .1)[0]
        tip_error = int(max(abs(int(tx) - int(px)), abs(int(ty) - int(py))))
        connected = components(alpha > .1)
        contrast = {theme: int((np.abs(composite(cov, entries, pal, theme) -
                    np.array((17, 21, 28) if theme == "dark" else (250, 250, 247)) / 255)
                    .max(-1) > .5).sum()) for theme in ("dark", "light")}
        errors = {theme: float(np.abs(composite(cov, entries, pal, theme) -
                  composite(target, [2, 3], pal, theme)).mean() * 255) for theme in ("dark", "light")}
        card = (list(entries) == ent == [2, 3] and delta < 1e-3
                and min(x["iou"] for x in layer_scores) >= .97
                and edge == 0 and tip_error <= 1 and connected == 1 and min(contrast.values()) >= 15
                and max(errors.values()) < 4)
        hot = [int(px), int(py)] == list(hotspot)
        ok = card and hot and (w not in max_xor or all(x <= m for x, m in zip(xor, max_xor[w])))
        report["passed"] &= bool(ok)
        report["sizes"][str(w)] = dict(layers=layer_scores, layer_xor=xor, numpy_max_error=delta,
                                       border_alpha_max=edge, tip_error_pixels=tip_error,
                                       first_visible_xy=[int(px), int(py)], hotspot=list(hotspot),
                                       visible_components=connected, contrast_pixels=contrast,
                                       composite_mean_error_255=errors, card_passed=bool(card),
                                       max_xor=max_xor.get(w), passed=bool(ok))
        print(f"{w}x{2 * w}: IoU {[round(x['iou'], 6) for x in layer_scores]}, xor {xor}, numpy {delta:.2e}, "
              f"tip {[int(px), int(py)]}, components {connected}, contrast {contrast}, "
              f"error {errors['dark']:.3f}/{errors['light']:.3f}: {'pass' if ok else 'FAIL'}", flush=True)
    lib.neuronte_close(handle)
    if a.out:
        tmp = a.out + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(report, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, a.out)
    print("pointer gate: " + ("PASS" if report["passed"] else "FAIL"))
    return 0 if report["passed"] or a.report_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
