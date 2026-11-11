"""A small version 3 colour file for the tests. No icon net is trained.

usage: python3 tests/colour_fixture.py build/colour-fixture.nrt

The trunk is a hand-written position field, and the palette head is built
so each labelled glyph returns the entry written in font/icons.txt. The
edge table is the drawings' straight edges, appended by train/pack.py.
"""
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train"))
import pack  # noqa: E402
import strokes  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# One grid-aligned icon, one with a fixed colour, one that clears, and one
# whose three layers use foreground, clear and red. K is 3.
LABELLED = (0xE654, 0xF04C, 0xF007A, 0xF036D)
H, R, K = 8, 8, 3


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def code_of(scalar, masks):
    bits = [(scalar >> i) & 1 for i in range(21)] + [bin(scalar & m).count("1") & 1 for m in masks]
    return np.array([1.0 if b else -1.0 for b in bits], np.float32)


def expected_entries(icons, pal):
    out = []
    for s in LABELLED:
        layers = icons[chr(s)]
        if len(layers) > K:
            raise SystemExit(f"U+{s:04X} has more than {K} layers")
        row = [pal[layers[k][0]][0] if k < len(layers) else 0 for k in range(K)]
        out.append(row)
    return out


def head_weights(codes, targets):
    """One hidden unit per glyph. It is 1 on that glyph and off on every other."""
    w1 = np.zeros((R, 64), np.float32)
    b1 = np.full(R, -1.0, np.float32)
    wo = np.zeros((K * 5, R), np.float32)
    bo = np.zeros(K * 5, np.float32)
    for g, code in enumerate(codes):
        w1[g] = code
        b1[g] = np.float32(-63.0)
        for k, entry in enumerate(targets[g]):
            for b in range(5):
                wo[k * 5 + b, g] = np.float32(1.0 if (entry >> b) & 1 else -1.0)
    return w1, b1, wo, bo


def head_entries(code, w1, b1, wo, bo):
    hid = np.maximum(w1 @ code + b1, 0)
    logits = wo @ hid + bo
    idx = []
    for k in range(K):
        bits = [1 if logits[k * 5 + b] > 0 else 0 for b in range(5)]
        idx.append(sum(bit << b for b, bit in enumerate(bits)))
    return idx


def layer(weight, bias):
    w = np.asarray(weight, np.float32)
    b = np.asarray(bias, np.float32)
    return {"rows": int(w.shape[0]), "cols": int(w.shape[1]),
            "weight": [float(x) for x in w.reshape(-1)], "bias": [float(x) for x in b.reshape(-1)]}


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    nrt_path = sys.argv[1]
    json_path = os.path.splitext(nrt_path)[0] + ".json"
    masks = strokes.masks()
    pal = strokes.palette()
    icons = strokes.parse_layers(pal=pal)
    codes = [code_of(s, masks) for s in LABELLED]
    targets = expected_entries(icons, pal)
    w1, b1, wo, bo = head_weights(codes, targets)
    for s, code, want in zip(LABELLED, codes, targets):
        got = head_entries(code, w1, b1, wo, bo)
        if got != want:
            raise SystemExit(f"U+{s:04X} head returns {got}, drawings say {want}")
    # A different scalar must not light any of those units.
    other = head_entries(code_of(0x41, masks), w1, b1, wo, bo)
    if other != [0, 0, 0]:
        raise SystemExit(f"an unlabelled scalar returned {other}")

    l1 = np.zeros((H, 90), np.float32)
    l1[0, 0] = np.float32(0.25)
    l1[0, 1] = np.float32(0.10)
    lb1 = np.zeros(H, np.float32)
    lb1[0] = np.float32(1.0)
    # Pass hidden unit 0 through. Zero weights here would ReLU the field to
    # the output bias, and snapping would not be visible.
    zero_h = np.zeros((H, H), np.float32)
    zero_h[0, 0] = np.float32(1.0)
    zero_b = np.zeros(H, np.float32)
    out_w = np.zeros((K, H), np.float32)
    out_b = np.zeros(K, np.float32)
    out_w[0, 0] = np.float32(1.0)
    out_w[1, 0] = np.float32(-0.5)
    out_b[1] = np.float32(0.2)
    out_w[2, 0] = np.float32(0.3)
    out_b[2] = np.float32(-0.1)

    doc = {
        "format": "neuronte-colour-weights",
        "version": 1,
        "shape": {
            "form": "A",
            "glyph_layers": K,
            "position_octaves": 6,
            "code_bits": 64,
            "hidden_width": H,
            "hidden_layers": 3,
            "tau": 0.15,
            "parity_masks": [f"0x{m:06X}" for m in masks],
            "entry_bits": 5,
            "head_width": R,
        },
        "palette": {
            name: {"entry": n, "dark": None if d is None else f"#{d[0]:02X}{d[1]:02X}{d[2]:02X}",
                   "light": None if li is None else f"#{li[0]:02X}{li[1]:02X}{li[2]:02X}"}
            for name, (n, d, li) in pal.items()
        },
        "training": {
            "set": "icons",
            "labelled": " ".join(f"U+{s:04X}" for s in LABELLED),
            "sources_sha256": {
                "font/icons.txt": sha(os.path.join(ROOT, "font", "icons.txt")),
                "font/palette.txt": sha(os.path.join(ROOT, "font", "palette.txt")),
                "train/colour.py": sha(os.path.join(ROOT, "train", "colour.py")),
            },
            "pen_radius": 0.075,
            "grid": 256,
            "steps": 0,
            "seed": 0,
        },
        "layers": {
            "l1": layer(l1, lb1),
            "l2": layer(zero_h, zero_b),
            "l3": layer(zero_h, zero_b),
            "out": layer(out_w, out_b),
        },
        "head": {"h1": layer(w1, b1), "out": layer(wo, bo)},
    }
    os.makedirs(os.path.dirname(os.path.abspath(nrt_path)), exist_ok=True)
    with open(json_path, "w") as fh:
        json.dump(doc, fh)
    image = pack.pack(json_path)
    with open(nrt_path, "wb") as fh:
        fh.write(image)

    bad = dict(doc)
    bad["shape"] = dict(doc["shape"], form="B")
    bad_path = json_path + ".form-b"
    with open(bad_path, "w") as fh:
        json.dump(bad, fh)
    try:
        pack.pack(bad_path)
    except SystemExit:
        pass
    else:
        raise SystemExit("form B was packed")
    os.remove(bad_path)
    print(nrt_path, len(image), "bytes,", len(pack.read_colour(image)["records"]), "edge records")


if __name__ == "__main__":
    main()
