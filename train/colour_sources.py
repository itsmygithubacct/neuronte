"""Identity of the expanded drawings used by a colour net.

Source-file hashes record the training implementation. These hashes bind the
labelled shapes instead, so adding an unrelated glyph or changing the trainer
does not invalidate the edge table of an existing net.
"""
import hashlib
import json


def drawing_hashes(icons, scalars):
    """Hash each glyph's ordered palette names and expanded shape primitives."""
    return {f"U+{s:04X}": hashlib.sha256(json.dumps(
        icons[chr(s)], ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")).hexdigest() for s in sorted(scalars)}
