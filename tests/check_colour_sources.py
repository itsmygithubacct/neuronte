"""Exercise colour drawing provenance across trainer and drawing changes."""
import copy
import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "train"))
import glyphs
import pack
from colour_sources import drawing_hashes


def reject(doc):
    try:
        pack.check_sources(doc, "provenance test")
    except SystemExit:
        return
    raise AssertionError("changed drawing provenance was accepted")


with open(os.path.join(pack.ROOT, "weights", "neuronte-icon-v0.json")) as fh:
    old = {"training": json.load(fh)["training"]}
# A historical trainer digest is not the identity of the drawings.
old["training"]["sources_sha256"]["train/colour.py"] = "0" * 64
pack.check_sources(old, "legacy icon")
bad = copy.deepcopy(old)
bad["training"]["sources_sha256"]["font/icons.txt"] = "0" * 64
reject(bad)

icons = glyphs.colour_icons()
scalars = pack.labelled_scalars(old, "legacy icon")
new = copy.deepcopy(old)
new["training"]["drawings_sha256"] = {"version": 1, "glyphs": drawing_hashes(icons, scalars)}
# An unrelated rule or parser edit is allowed only if all expanded labelled
# drawings are identical. The original source digest remains in the record.
new["training"]["sources_sha256"]["train/glyphs.py"] = "0" * 64
pack.check_sources(new, "semantic icon")
extra = copy.deepcopy(icons)
extra[chr(0x10FFFE)] = [("fg", [("poly", [(0, 0), (1, 0), (1, 1)])])]
with patch.object(glyphs, "colour_icons", return_value=extra):
    pack.check_sources(new, "additional unrelated drawing")
changed = copy.deepcopy(icons)
changed[chr(scalars[0])][0][1].append(("seg", 0.1, 0.2, 0.3, 0.4, 0.01))
with patch.object(glyphs, "colour_icons", return_value=changed):
    reject(new)
changed = copy.deepcopy(icons)
del changed[chr(scalars[0])]
with patch.object(glyphs, "colour_icons", return_value=changed):
    reject(new)
bad = copy.deepcopy(new)
bad["training"]["drawings_sha256"]["glyphs"].pop(f"U+{scalars[0]:04X}")
reject(bad)
bad = copy.deepcopy(new)
bad["training"]["drawings_sha256"]["version"] = 2
reject(bad)
print("colour provenance: historical trainer, unrelated addition, changed/missing drawings checked")
