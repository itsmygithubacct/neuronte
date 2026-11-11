"""Identity of the expanded drawings used by a colour net.

Source-file hashes record the training implementation. These hashes bind the
labelled shapes instead, so adding an unrelated glyph or changing the trainer
does not invalidate the edge table of an existing net.
"""
import hashlib
import json


def scalar(key):
    """Unicode strings for old drawings, integer codes for wide halves."""
    return key if isinstance(key, int) else ord(key)


def drawing_at(drawings, code):
    return drawings[code] if code in drawings else drawings[chr(code)]


def wide_halves(drawings):
    """Split original 2x2 drawings without cutting their geometry at the seam.

    Both halves keep the same layer stack. A layer wholly in the other half
    is intentionally empty here. Keeping the overhanging shapes makes the
    distance field and antialiasing continuous at the join.
    """
    import glyphs
    out = {}
    for ch, layers in sorted(drawings.items()):
        s = scalar(ch)
        if not 0 <= s <= 0xEFFFF or 0xD800 <= s <= 0xDFFF:
            raise ValueError("wide drawing code cannot fit both halves in 21 bits")
        for half in (0, 1):
            out[s + half * 0x110000] = [(entry, glyphs.moved(shapes, lambda x, y: (x - half, y)))
                                       for entry, shapes in layers]
    return out


def drawing_hashes(icons, scalars):
    """Hash each glyph's ordered palette names and expanded shape primitives."""
    return {f"U+{s:04X}": hashlib.sha256(json.dumps(
        drawing_at(icons, s), ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")).hexdigest() for s in sorted(scalars)}
