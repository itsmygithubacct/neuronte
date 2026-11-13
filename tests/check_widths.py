"""Pack narrow models and compare the native runtime with NumPy evaluation."""
import ctypes as C
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "train"))
import pack
import strokes


def fixture(width):
    rng = np.random.default_rng(123)
    layers = {}
    for name, rows, cols in pack.layers(width):
        layers[name] = {"rows": rows, "cols": cols,
                        "weight": rng.normal(0, .08, (rows, cols)).astype(np.float32).ravel().tolist(),
                        "bias": ([.3] * rows if name != "out" else [-.1])}
    return {"format": "neuronte-weights", "version": 1,
            "shape": {"position_octaves": 6, "code_bits": 64, "hidden_layers": 3,
                      "hidden_width": width, "tau": .15,
                      "parity_masks": [hex(m) for m in strokes.masks()]},
            "layers": layers, "training": {"set": "narrow-fixture", "labelled": "U+2800..U+28FF"}}


library = Path(sys.argv[1]).resolve()
lib = C.CDLL(str(library))
lib.neuronte_open_file.argtypes = [C.c_char_p, C.POINTER(C.c_void_p)]
lib.neuronte_close.argtypes = [C.c_void_p]
with tempfile.TemporaryDirectory(prefix="neuronte-widths-") as temporary:
    directory = Path(temporary)
    for width in (8, 12, 20, 48):
        source, packed = directory / f"h{width}.json", directory / f"h{width}.nrt"
        source.write_text(json.dumps(fixture(width)))
        raw = pack.pack(str(source))
        assert len(raw) == 204 + 4 * (2*width*width + 94*width + 1)
        assert struct.unpack_from("<I", raw, 20)[0] == width
        packed.write_bytes(raw)
        assert pack.member(str(packed)) == (1, raw)
        subprocess.run([sys.executable, str(ROOT / "tests/check_reference.py"),
                        str(library), str(source), str(packed)], check=True)
        if width == 12:
            bundle, _ = pack.bundle([str(source)])
            drawing, _ = pack.drawing([str(packed)])
            for name, image in (("bundle", bundle), ("drawing", drawing)):
                wrapped = directory / (name + ".nrt")
                wrapped.write_bytes(image)
                handle = C.c_void_p()
                assert lib.neuronte_open_file(os.fsencode(wrapped), C.byref(handle)) == 0
                lib.neuronte_close(handle)
    for width in (4, 10, 1028):
        invalid = fixture(8)
        invalid["shape"]["hidden_width"] = width
        source.write_text(json.dumps(invalid))
        try:
            pack.pack(str(source))
        except SystemExit:
            pass
        else:
            raise AssertionError("invalid hidden width was packed")
print("check_widths: supported widths, independent reference, wrappers and invalid shapes passed")
