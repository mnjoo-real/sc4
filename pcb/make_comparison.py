#!/usr/bin/env python3
"""Step 7: PCB_5_VARIANT_COMPARISON.png -- all 5 boards, same scale.

Stacks the 5 top-view renders (all captured with identical `kicad-cli pcb
render` camera/zoom settings in render_3d.py, so they are already at
directly comparable scale) into one labeled composite image.

Usage:
    python3 make_comparison.py
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

PCB_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PCB_DIR)
from generate_pcb import VARIANTS


def main():
    imgs = []
    for variant in VARIANTS:
        path = os.path.join(PCB_DIR, variant, "renders", f"{variant}_top.png")
        im = Image.open(path).convert("RGBA")
        flat = Image.new("RGBA", im.size, "white")
        flat.alpha_composite(im)
        imgs.append((variant, flat.convert("RGB")))

    w = max(im.width for _, im in imgs)
    label_h = 40
    row_h = max(im.height for _, im in imgs) + label_h
    total_h = row_h * len(imgs)

    canvas = Image.new("RGB", (w, total_h), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except Exception:
        font = ImageFont.load_default()

    y = 0
    for variant, im in imgs:
        draw.text((10, y + 5), variant, fill="black", font=font)
        canvas.paste(im, ((w - im.width) // 2, y + label_h))
        y += row_h

    out_path = os.path.join(PCB_DIR, "PCB_5_VARIANT_COMPARISON.png")
    canvas.save(out_path)
    print(f"wrote {out_path} ({canvas.width}x{canvas.height})")


if __name__ == "__main__":
    main()
