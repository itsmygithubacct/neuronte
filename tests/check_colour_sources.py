"""Exercise colour drawing provenance across trainer and drawing changes."""
import copy
import os
from pathlib import Path
import shutil
import sys
import tempfile
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


# Build a legacy-format fixture from this tree. A shipped historical net may
# correctly fail this check after unrelated generated-glyph code has changed;
# that must not turn this format regression test into an asset migration.
icons = glyphs.colour_icons()
old = {"training": {
    "labelled": " ".join(f"U+{ord(c):04X}" for c in icons),
    "sources_sha256": {rel: pack.sha256_file(os.path.join(pack.ROOT, rel))
                       for rel in ("font/icons.txt", "font/palette.txt", "train/glyphs.py")},
}}
# A historical trainer digest is not the identity of the drawings.
old["training"]["sources_sha256"]["train/colour.py"] = "0" * 64
pack.check_sources(old, "legacy icon")
bad = copy.deepcopy(old)
bad["training"]["sources_sha256"]["font/icons.txt"] = "0" * 64
reject(bad)
bad = copy.deepcopy(old)
bad["training"]["sources_sha256"]["train/strokes.py"] = "0" * 64
reject(bad)
# Missing historical parser metadata is not permission to change the parser.
original_sha256_file = pack.sha256_file
def changed_parser_digest(path):
    return "0" * 64 if str(path).endswith("/train/strokes.py") else original_sha256_file(path)
with patch.object(pack, "sha256_file", side_effect=changed_parser_digest):
    reject(old)

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

# Custom drawings (the flame) use their own geometry and palette, not icons.
flame = {"training": {
    "drawing": "font/flame.txt", "palette": "font/flame-palette.txt",
    "labelled": "U+100000", "sources_sha256": {
        rel: pack.sha256_file(os.path.join(pack.ROOT, rel))
        for rel in ("font/flame.txt", "font/flame-palette.txt")},
}}
pack.check_sources(flame, "legacy custom drawing")
# The trainer permits named drawing/palette paths outside font/. Both must be
# bound by their own hashes, irrespective of directory name.
with tempfile.TemporaryDirectory(prefix="neuronte-custom-provenance-") as directory:
    root = Path(directory)
    (root / "assets").mkdir()
    (root / "train").mkdir()
    for source, destination in (("font/flame.txt", "assets/mark.txt"),
                                ("font/flame-palette.txt", "assets/colours.txt"),
                                ("train/strokes.py", "train/strokes.py")):
        shutil.copyfile(Path(pack.ROOT) / source, root / destination)
    custom = copy.deepcopy(flame)
    custom["training"].update(drawing="assets/mark.txt", palette="assets/colours.txt")
    custom["training"]["sources_sha256"] = {
        rel: pack.sha256_file(root / rel) for rel in ("assets/mark.txt", "assets/colours.txt")}
    with patch.object(pack, "ROOT", str(root)):
        pack.check_sources(custom, "legacy external-directory drawing")
        for rel in ("assets/mark.txt", "assets/colours.txt"):
            bad = copy.deepcopy(custom)
            bad["training"]["sources_sha256"][rel] = "0" * 64
            reject(bad)
        with (root / "assets/mark.txt").open("a") as handle:
            handle.write("\n# changed drawing source\n")
        reject(custom)
flame["training"]["drawings_sha256"] = {
    "version": 1, "glyphs": drawing_hashes(pack.colour_drawings(flame), [0x100000])}
pack.check_sources(flame, "semantic custom drawing")
changed = copy.deepcopy(pack.colour_drawings(flame))
changed[chr(0x100000)][0][1].append(("seg", 0.1, 0.2, 0.3, 0.4, 0.01))
with patch.object(pack, "colour_drawings", return_value=changed):
    reject(flame)
print("colour provenance: custom drawing and palette paths checked")
