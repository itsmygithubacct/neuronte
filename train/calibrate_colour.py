"""Apply a recorded uniform offset to a colour net's learned distances.

usage: calibrate_colour.py INPUT.json OUTPUT.json --offset -0.008

The offset is in normalized field units (cell widths divided by tau), not
pixels. It changes only the final distance biases. The original artifact,
palette head, drawing identity and training source hashes remain intact.
Always score both seeds and the packed result after calibration.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--offset", type=float, required=True)
    a = p.parse_args()
    offset = np.float32(a.offset)
    if not np.isfinite(offset):
        p.error("offset must be finite in float32")
    raw = Path(a.input).read_bytes()
    doc = json.loads(raw)
    if (doc.get("format") != "neuronte-colour-weights" or doc.get("version") != 1
            or doc.get("shape", {}).get("form") != "A"):
        p.error("input must be a version 1 form A colour net")
    biases = np.asarray(doc["layers"]["out"]["bias"], np.float32) + offset
    if biases.shape != (doc["shape"]["glyph_layers"],) or not np.isfinite(biases).all():
        p.error("invalid calibrated distance biases")
    doc["layers"]["out"]["bias"] = biases.tolist()
    doc["training"].setdefault("postprocessing", []).append({
        "kind": "uniform-distance-offset", "offset": float(offset),
        "source_weights_sha256": hashlib.sha256(raw).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    # Exclusive creation also protects INPUT when the paths name the same file.
    with open(a.output, "x") as fh:
        json.dump(doc, fh)
    print(a.output, "distance offset", float(offset))


if __name__ == "__main__":
    main()
