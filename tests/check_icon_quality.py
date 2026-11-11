"""Score every packed icon layer independently through the C API.

usage: check_icon_quality.py LIB JSON NRT [--out SCORES] [--report-only]

The acceptance gate is mean 16px IoU >= .990, exact palette entries, no
positive unused coverage, and no lost nonempty or zero-coverage used
layer at any of 12/16/32px. Empty thresholded targets are counted separately. Target
coverage follows the trainer's float16 grid256, bilinear interpolation,
8x8 positive-inside samples and strict >.5 threshold. An additional score
uses the analytic drawings to expose grid-boundary differences.
"""
import argparse
import ctypes
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train"))
import glyphs
import pack
import strokes

THEMES = {"dark": ((0x11, 0x15, 0x1C), (0xE9, 0xE6, 0xDF)),
          "light": ((0xFA, 0xFA, 0xF7), (0x1E, 0x23, 0x30))}


def composite(cov, entries, palette, theme):
    bg, fg = (np.asarray(c, np.float32) / 255 for c in THEMES[theme])
    table = {n: fg if n == 0 else np.asarray(d if theme == "dark" else l, np.float32) / 255
             for n, d, l in palette.values() if n != 1}
    rgb = np.zeros((*cov.shape[1:], 3), np.float32)
    alpha = np.zeros((*cov.shape[1:], 1), np.float32)
    for c, entry in zip(cov, entries):
        c = c[..., None]
        if entry == 1:
            rgb *= 1 - c
            alpha *= 1 - c
        else:
            rgb = table[entry] * c + rgb * (1 - c)
            alpha = c + alpha * (1 - c)
    return rgb + bg * (1 - alpha)


def sample_points(cw, ss=8):
    xs = (np.arange(cw * ss, dtype=np.float32) + .5) / (cw * ss)
    ys = (np.arange(2 * cw * ss, dtype=np.float32) + .5) / (2 * cw * ss) * 2
    yy, xx = np.meshgrid(ys, xs, indexing="ij")
    return np.stack([xx.ravel(), yy.ravel()], 1)


def interpolate(field, points, grid):
    uv = points * grid
    ij = np.floor(uv).astype(int)
    ij[:, 0] = np.clip(ij[:, 0], 0, grid - 1)
    ij[:, 1] = np.clip(ij[:, 1], 0, 2 * grid - 1)
    fraction = uv - ij.astype(np.float32)
    u, v = fraction.T
    x, y = ij.T
    return ((field[y, x] * (1 - u) + field[y, x + 1] * u) * (1 - v)
            + (field[y + 1, x] * (1 - u) + field[y + 1, x + 1] * u) * v)


def mask(samples, cw):
    return (samples > 0).reshape(2 * cw, 8, cw, 8).mean((1, 3)) > .5


def counts(truth, predicted):
    intersection = int((truth & predicted).sum())
    union = int((truth | predicted).sum())
    return {"iou": intersection / union if union else 1.0,
            "intersection": intersection, "union": union,
            "target_ink": int(truth.sum()), "predicted_ink": int(predicted.sum())}


def passes_gate(results):
    return (set(results) == {"12", "16", "32"} and results["16"]["iou_mean"] >= .990
            and all(r["head_wrong"] == 0 and r["stray_unused"] == 0
                    and r["stray_positive"] == 0 and r["lost_used"] == 0
                    and r["zero_coverage_used"] == 0 for r in results.values()))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("lib")
    p.add_argument("json")
    p.add_argument("nrt")
    p.add_argument("--out")
    p.add_argument("--report-only", action="store_true")
    a = p.parse_args()
    with open(a.json) as fh:
        doc = json.load(fh)
    pack.check_sources(doc, a.json)
    labelled = pack.labelled_scalars(doc, a.json)
    icons, pal = glyphs.colour_icons(), strokes.palette()
    if len(labelled) != 167 or sum(len(icons[chr(s)]) for s in labelled) != 209:
        raise SystemExit("quality gate requires the full 167-icon, 209-layer batch")
    k = doc["shape"]["glyph_layers"]
    grid, pen = doc["training"]["grid"], doc["training"]["pen_radius"]
    tau = doc["shape"]["tau"]
    lib = ctypes.CDLL(os.path.abspath(a.lib))
    lib.neuronte_open_file.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.neuronte_set_snap.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.neuronte_close.argtypes = [ctypes.c_void_p]
    lib.neuronte_coverage_layers.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                            ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                            ctypes.c_void_p, ctypes.c_void_p]
    handle = ctypes.c_void_p()
    if lib.neuronte_open_file(a.nrt.encode(), ctypes.byref(handle)) != 0:
        raise SystemExit("C library refused the packed net")
    if lib.neuronte_set_snap(handle, 0) != 0:
        raise SystemExit("C library refused snap=0")
    widths = (12, 16, 32)
    points = {cw: sample_points(cw) for cw in widths}
    results = {str(cw): {"layers": [], "head_wrong": 0, "stray_unused": 0,
                        "stray_positive": 0,
                        **{theme: {"mean_err": 0., "off_gt32": 0.} for theme in THEMES}}
               for cw in widths}
    for scalar in labelled:
        layers = icons[chr(scalar)]
        fields = [glyphs.field(shapes, grid, pen, tau).astype(np.float16).astype(np.float32)
                  for _, shapes in layers]
        want = [pal[layers[i][0]][0] if i < len(layers) else 0 for i in range(k)]
        for cw in widths:
            r = results[str(cw)]
            cov = np.zeros((k, 2 * cw, cw), np.float32)
            ent = (ctypes.c_uint8 * k)()
            if lib.neuronte_coverage_layers(handle, scalar, cw, 2 * cw,
                                            2 if cw < 24 else 1, cov.ctypes.data, ent) != 0:
                raise SystemExit(f"C coverage failed for U+{scalar:04X}")
            r["head_wrong"] += sum(x != y for x, y in zip(ent, want))
            r["stray_unused"] += int((cov[len(layers):] > .5).any(axis=(1, 2)).sum())
            r["stray_positive"] += int((cov[len(layers):] > 0).any(axis=(1, 2)).sum())
            target_cov = np.zeros_like(cov)
            for i, (_, shapes) in enumerate(layers):
                predicted = cov[i] > .5
                values = interpolate(fields[i], points[cw], grid)
                target_cov[i] = (values > 0).reshape(2 * cw, 8, cw, 8).mean((1, 3))
                target = target_cov[i] > .5
                analytic = mask(glyphs.signed_distance(shapes, points[cw], pen), cw)
                r["layers"].append({"scalar": f"U+{scalar:04X}", "layer": i,
                                     **counts(target, predicted),
                                     "target_coverage_sum": float(target_cov[i].sum()),
                                     "predicted_coverage_sum": float(cov[i].sum()),
                                     "analytic": counts(analytic, predicted)})
            for theme in THEMES:
                err = np.abs(composite(cov, ent, pal, theme)
                             - composite(target_cov, want, pal, theme)) * 255
                r[theme]["mean_err"] += float(err.mean()) / len(labelled)
                r[theme]["off_gt32"] += float((err.max(-1) > 32).mean()) / len(labelled)
    lib.neuronte_close(handle)
    for cw in widths:
        r = results[str(cw)]
        r["iou_mean"] = float(np.mean([x["iou"] for x in r["layers"]]))
        r["iou_min"] = min(x["iou"] for x in r["layers"])
        r["lost_used"] = sum(x["target_ink"] > 0 and x["intersection"] == 0 for x in r["layers"])
        r["empty_target_used"] = sum(x["target_ink"] == 0 for x in r["layers"])
        r["zero_coverage_used"] = sum(x["predicted_coverage_sum"] == 0 for x in r["layers"])
        r["analytic_iou_mean"] = float(np.mean([x["analytic"]["iou"] for x in r["layers"]]))
        print(f"{cw}px: IoU {r['iou_mean']:.9f}, min {r['iou_min']:.6f}, "
              f"lost {r['lost_used']}, empty target {r['empty_target_used']}, "
              f"stray {r['stray_unused']}, head {r['head_wrong']}; "
              f"analytic IoU {r['analytic_iou_mean']:.9f}", flush=True)
        print(f"  composite error dark/light {r['dark']['mean_err']:.6f}/{r['light']['mean_err']:.6f}; "
              f"zero-coverage used {r['zero_coverage_used']}, positive unused {r['stray_positive']}", flush=True)
    passed = passes_gate(results)
    if a.out:
        with open(a.out, "w") as fh:
            json.dump({"passed": passed, "per_size": results}, fh, indent=2)
            fh.write("\n")
    print("icon gate: " + ("PASS" if passed else "FAIL"))
    return 0 if passed or a.report_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
