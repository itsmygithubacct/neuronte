"""Render the Kilix flame drawing at 16 and 32 pixels and make its review sheet.

Usage: python3 tools/flame-preview.py [--output previews]

Needs numpy and Pillow. Evaluates the drawings with glyphs.signed_distance;
there are no trained weights. All labels use the project's own ui-10 face.
MIT licence. See LICENSE.
"""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "train"))
import glyphs  # noqa: E402
import strokes  # noqa: E402

SAMPLES = 8
BACKGROUNDS = {"dark": (17, 21, 28), "light": (250, 250, 247)}


def drawing():
    path = ROOT / "font" / "flame.json"
    doc = json.loads(path.read_text())
    if doc["form"] != "A" or doc["design_cell"] != [10, 20]:
        raise ValueError("the flame must be form A on the 10 by 20 design cell")
    if doc["square_crop"] != [0, 5, 10, 15]:
        raise ValueError("the flame occupies the middle square of the cell")
    pal = strokes.palette(path.parent / doc["palette"])
    layers = []
    for layer in doc["layers"]:
        name = layer["entry"]
        points = np.asarray(layer["polygon"], dtype=np.float64)
        if points.ndim != 2 or points.shape[1] != 2 or len(points) < 3 or not np.isfinite(points).all():
            raise ValueError(f"{name}: a polygon needs at least three finite points")
        if (points < [0, 5]).any() or (points > [10, 15]).any():
            raise ValueError(f"{name}: polygon is outside the square crop")
        layers.append((name, [("poly", (points / 10).tolist())]))
    if [name for name, _ in layers] != ["red", "yellow", "white"]:
        raise ValueError("the flame has three layers: red, yellow, white, back to front")
    if any(pal[name][0] < 2 or pal[name][1] != pal[name][2] for name, _ in layers):
        raise ValueError("the flame's colours must be fixed in both themes")
    seams = glyphs.layer_seams(layers)
    if seams:
        raise ValueError(f"layers meet without an overlap: {seams}")
    return layers, pal


def coverage(layers, size):
    # This is the square crop of a size by 2*size cell. The y offset is
    # half a cell width, so a square icon keeps the teacher's proportions.
    xs = (np.arange(size * SAMPLES) + 0.5) / (size * SAMPLES)
    yy, xx = np.meshgrid(xs + 0.5, xs, indexing="ij")
    points = np.stack([xx.ravel(), yy.ravel()], axis=1)
    masks = []
    for _, shapes in layers:
        inside = glyphs.signed_distance(shapes, points, glyphs.PEN) > 0
        masks.append(inside.reshape(size, SAMPLES, size, SAMPLES).mean((1, 3)))
    return np.stack(masks)


def composite(masks, layers, pal, theme=0):
    """Form A back-to-front coverage, saved as straight RGBA for the PNG."""
    size = masks.shape[1]
    rgb = np.zeros((size, size, 3))
    alpha = np.zeros((size, size))
    for mask, (name, _) in zip(masks, layers):
        rgb = np.asarray(pal[name][1 + theme]) * mask[..., None] + rgb * (1 - mask[..., None])
        alpha = mask + alpha * (1 - mask)
    straight = np.divide(rgb, alpha[..., None], out=np.zeros_like(rgb), where=alpha[..., None] > 0)
    rgba = np.concatenate([straight, alpha[..., None] * 255], axis=2)
    return Image.fromarray(np.rint(rgba).clip(0, 255).astype(np.uint8))


def label(image, face, xy, text, scale=1, ink=(30, 35, 44)):
    """Use our pixel face directly; do not load a system font for the sheet."""
    x, y = xy
    for ch in text:
        advance, rows = face[ch]
        mask = np.asarray([[p == "#" for p in row] for row in rows], dtype=np.uint8) * 255
        glyph = Image.new("RGBA", (len(rows[0]), len(rows)), (*ink, 0))
        glyph.putalpha(Image.fromarray(mask))
        if scale != 1:
            glyph = glyph.resize((glyph.width * scale, glyph.height * scale), Image.Resampling.NEAREST)
        image.alpha_composite(glyph, (x, y))
        x += advance * scale


def sheet(images, masks, layers, pal):
    out = Image.new("RGBA", (1000, 790), (234, 237, 241, 255))
    draw = ImageDraw.Draw(out)
    face = glyphs.pixel_face(10)
    label(out, face, (32, 26), "Kilix flame mark", 3)
    label(out, face, (32, 72), "Drawing targets / three flat layers / 16 and 32 pixels", 2)
    for x, size, name in ((32, 16, "16 px - Start button"), (516, 32, "32 px - Desktop icon")):
        draw.rectangle((x, 114, x + 451, 536), fill=(255, 255, 255, 255))
        label(out, face, (x + 20, 130), name, 2)
        for dx, theme in ((20, "dark"), (232, "light")):
            bg = (*BACKGROUNDS[theme], 255)
            draw.rectangle((x + dx, 174, x + dx + 191, 249), fill=bg)
            out.alpha_composite(images[size], (x + dx + (192 - size) // 2, 174 + (76 - size) // 2))
            label(out, face, (x + dx, 260), f"Native size / {theme}")
            draw.rectangle((x + dx, 294, x + dx + 191, 485), fill=bg)
            enlarged = images[size].resize((192, 192), Image.Resampling.NEAREST)
            out.alpha_composite(enlarged, (x + dx, 294))
            label(out, face, (x + dx, 502), f"{192 // size}x pixel enlargement")
    label(out, face, (32, 561), "Layers, back to front", 2)
    for i, (name, shapes) in enumerate(layers):
        x = 32 + 322 * i
        draw.rectangle((x, 600, x + 291, 743), fill=(*BACKGROUNDS["dark"], 255))
        one = composite(masks[32][i:i + 1], [(name, shapes)], pal)
        out.alpha_composite(one.resize((128, 128), Image.Resampling.NEAREST), (x + 8, 608))
        label(out, face, (x + 150, 624), f"{i + 1} {name}", 2, (240, 242, 245))
        colour = "#" + "".join(f"{v:02X}" for v in pal[name][1])
        label(out, face, (x + 150, 666), colour, 1, (190, 198, 211))
    label(out, face, (32, 765), "Same polygons at both sizes. Labels use Neuronte's own pixel face. No trained weights.")
    return out.convert("RGB")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("previews"))
    args = parser.parse_args()
    layers, pal = drawing()
    masks = {size: coverage(layers, size) for size in (16, 32)}
    images = {}
    for size in (16, 32):
        images[size] = composite(masks[size], layers, pal)
        alpha = np.zeros((size, size))
        for mask in masks[size]:
            alpha = mask + alpha * (1 - mask)
        if not np.allclose(alpha, masks[size][0]):
            raise ValueError(f"{size} px: inner layers change the outer silhouette")
        if images[size].tobytes() != composite(masks[size], layers, pal, theme=1).tobytes():
            raise ValueError(f"{size} px: the mark changes colour between themes")
        rgba = np.asarray(images[size])
        for name, _ in layers:
            if not np.any(np.all(rgba == (*pal[name][1], 255), axis=2)):
                raise ValueError(f"{size} px: {name} has no fully covered pixel")
        if rgba[0, 0, 3] or rgba[-1, -1, 3]:
            raise ValueError(f"{size} px: the exterior is not transparent")
        print(f"flame {size} px: three colours visible, silhouette unchanged, themes identical")
    args.output.mkdir(parents=True, exist_ok=True)
    for size, img in images.items():
        img.save(args.output / f"flame-{size}.png")
    sheet(images, masks, layers, pal).save(args.output / "flame-sheet.png")
    print("flame: no seams between layers; wrote flame-16.png, flame-32.png and flame-sheet.png")


if __name__ == "__main__":
    main()
