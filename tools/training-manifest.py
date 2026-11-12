#!/usr/bin/env python3
"""Write TRAINING_MANIFEST.md from the training records in weights/*.json.

usage: python3 tools/training-manifest.py [--check]

Every number in the manifest is read from a weight file, a validation
record or weights/SHA256SUMS; nothing is typed by hand. --check exits 1
if TRAINING_MANIFEST.md differs from what this script would write.
"""
import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "TRAINING_MANIFEST.md")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def cell(v):
    return "-" if v is None or v == "" else str(v)


def sources(t):
    names = []
    for key in ("sources_sha256",):
        if isinstance(t.get(key), dict):
            names += sorted(t[key])
    if "strokes_sha256" in t:
        names.append("font/strokes.txt")
    if "blocks" in t:
        names.append(str(t["blocks"]))
    return ", ".join("`%s`" % n for n in names) or "-"


def after(t):
    steps = [k for k in ("output_bias_calibration", "coverage_calibration",
                         "postprocessing", "continuation") if k in t]
    return ", ".join(steps) or "-"


def build():
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "weights", "*.json"))):
        with open(path) as f:
            d = json.load(f)
        t = d.get("training") if isinstance(d, dict) else None
        if not isinstance(t, dict):
            continue
        name = os.path.basename(path)
        packed = path[:-5] + ".nrt"
        rows.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | `%s` | %s |" % (
            name, cell(t.get("set") or t.get("drawing")), cell(t.get("steps")),
            cell(t.get("seed")), cell(t.get("unlabelled_weight")),
            cell(t.get("pen_radius")), sources(t), after(t), sha(path)[:16],
            "`%s`" % sha(packed)[:16] if os.path.exists(packed) else "-"))
    commits = []
    for path in sorted(glob.glob(os.path.join(ROOT, "weights", "*.validation.json"))):
        with open(path) as f:
            d = json.load(f)
        if isinstance(d, dict) and d.get("training_commit"):
            commits.append("| `%s` | `%s` | %s |" % (
                os.path.basename(path), d["training_commit"], cell(d.get("selected_seed"))))
    with open(os.path.join(ROOT, "weights", "SHA256SUMS")) as f:
        listed = sum(1 for line in f if line.strip())
    lines = [
        "# Training manifest",
        "",
        "Written by `tools/training-manifest.py` from the `training` record inside",
        "each `weights/*.json`. Do not edit by hand: run the script again.",
        "`make test` does not run it; `python3 tools/training-manifest.py --check`",
        "fails if this file is out of date.",
        "",
        "## What each record holds",
        "",
        "- **Set or drawing**: the character set in `train/glyphs.py`, or the",
        "  drawing file a colour net was trained on.",
        "- **Steps, seed, unlabelled weight, pen radius**: the arguments the",
        "  trainer ran with.",
        "- **Sources hashed**: the files whose SHA-256 the trainer stored in the",
        "  weight file when it ran. The hashes themselves are in the weight file.",
        "- **After training**: recorded post-training steps, each with the hash",
        "  of its input and of the tool that made it.",
        "- **JSON, packed**: the first 16 hex digits of the SHA-256 of the weight",
        "  file and of its packed `.nrt`, if one is shipped. The full hashes of",
        "  the %d files it lists are in `weights/SHA256SUMS`. The pointer net's" % listed,
        "  files are not in that list; theirs are in",
        "  `weights/neuronte-pointer-v0.sha256`.",
        "",
        "## What is not recorded",
        "",
        "- The weight files do not record the Python, PyTorch, CUDA or GPU",
        "  used. Where a model card under `weights/*.md` states them, the card",
        "  is the only record.",
        "- A training commit is recorded only for the models listed under",
        "  *Recorded training commits*. For the others, the stored source",
        "  hashes identify the inputs, not the commit.",
        "- No training run has been repeated by a third party. Two seeds were",
        "  trained by the project for the models whose `seed1` files are here.",
        "",
        "## Weight files (%d)" % len(rows),
        "",
        "| Weight file | Set or drawing | Steps | Seed | Unlabelled weight | Pen radius | Sources hashed | After training | JSON | Packed |",
        "|---|---|---:|---:|---:|---:|---|---|---|---|",
    ] + rows + [
        "",
        "## Recorded training commits",
        "",
        "| Validation record | Training commit | Selected seed |",
        "|---|---|---:|",
    ] + commits + [""]
    return "\n".join(lines)


if __name__ == "__main__":
    text = build()
    if "--check" in sys.argv[1:]:
        with open(OUT) as f:
            sys.exit(0 if f.read() == text else 1)
    with open(OUT, "w") as f:
        f.write(text)
