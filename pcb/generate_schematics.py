#!/usr/bin/env python3
"""Geometry sanity-check diagrams for the generated .kicad_pcb files.

THESE ARE NOT KICAD RENDERS. They do not use KiCad in any way -- they are
plotted directly with matplotlib from the same coordinate data
generate_pcb.py used, as a way to visually sanity-check hole/pad/MLCC
geometry without a working KiCad installation. They show no real copper
color, solder mask, or silkscreen rendering; layers are just color-coded
shapes. See pcb/FABRICATION_REVIEW.md for what this is and is not a
substitute for.

Usage:
    python3 generate_schematics.py
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

PCB_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PCB_DIR)
from generate_pcb import (
    VARIANTS, PACKAGES, HOLES, HOLE_DIA, EDGE_PADS, EDGE_PAD_X, EDGE_PAD_DIA,
    BOARD_L, BOARD_W, mlcc_pad_positions, route_traces, VARIANT_LABEL_POS,
)


def draw_board(ax, variant):
    spec = VARIANTS[variant]
    pkg = spec["footprint"]
    mlcc_x, mlcc_y, orientation = spec["mlcc_x"], spec["mlcc_y"], spec["orientation"]
    pspec = PACKAGES[pkg]

    ax.add_patch(Rectangle((0, 0), BOARD_L, BOARD_W, fill=False, edgecolor="black", linewidth=1.2))

    for hx, hy in HOLES:
        ax.add_patch(Circle((hx, hy), HOLE_DIA / 2, fill=False, edgecolor="dimgray", linewidth=1))

    for name, y in EDGE_PADS:
        ax.add_patch(Circle((EDGE_PAD_X, y), EDGE_PAD_DIA / 2, facecolor="goldenrod", edgecolor="black", linewidth=0.5))
        ax.text(EDGE_PAD_X + 3, y, name, fontsize=6, va="center")

    pad1, pad2 = mlcc_pad_positions(pkg, mlcc_x, mlcc_y, orientation)
    pad_w, pad_h = pspec["pad_w"], pspec["pad_h"]
    if orientation == 90:
        w, h = pad_w, pad_h
    else:
        w, h = pad_h, pad_w
    for px, py, lbl in [(pad1[0], pad1[1], "+"), (pad2[0], pad2[1], "-")]:
        ax.add_patch(Rectangle((px - w / 2, py - h / 2), w, h, facecolor="goldenrod", edgecolor="black", linewidth=0.4))
        ax.text(px, py + h / 2 + 1.2, lbl, fontsize=6, ha="center", color="darkred")

    for seg_line in route_traces(pkg, mlcc_x, mlcc_y, orientation).splitlines():
        # parse "(segment (start x y) (end x y) (width w) ..."
        import re
        m = re.search(
            r"\(start ([\-0-9.]+) ([\-0-9.]+)\) \(end ([\-0-9.]+) ([\-0-9.]+)\) \(width ([\-0-9.]+)\) .*\(net (\d+)\)",
            seg_line,
        )
        if not m:
            continue
        sx, sy, ex, ey, w = (float(m.group(i)) for i in range(1, 6))
        net = int(m.group(6))
        color = "crimson" if net == 1 else "steelblue"
        ax.plot([sx, ex], [sy, ey], color=color, linewidth=max(w * 3, 0.5))

    lx, ly = VARIANT_LABEL_POS
    ax.text(lx, ly, variant, fontsize=6, color="darkgreen")

    ax.set_xlim(-3, BOARD_L + 3)
    ax.set_ylim(-3, BOARD_W + 3)
    ax.set_aspect("equal")
    ax.set_title(variant, fontsize=10)
    ax.set_xlabel("x (mm)", fontsize=7)
    ax.set_ylabel("y (mm)", fontsize=7)
    ax.tick_params(labelsize=6)


def main():
    for variant in VARIANTS:
        fig, ax = plt.subplots(figsize=(6, 3))
        draw_board(ax, variant)
        fig.suptitle(f"{variant} -- geometry sanity-check schematic (NOT a KiCad render)", fontsize=8)
        fig.tight_layout()
        out_dir = os.path.join(PCB_DIR, variant, "renders")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{variant}_layout_schematic_NOT_A_KICAD_RENDER.png")
        fig.savefig(out_path, dpi=200)
        plt.close(fig)
        print(f"wrote {out_path}")

    fig, axes = plt.subplots(5, 1, figsize=(7, 13))
    for ax, variant in zip(axes, VARIANTS):
        draw_board(ax, variant)
    fig.suptitle(
        "All 5 variants, same scale -- geometry sanity-check schematic\n"
        "NOT a KiCad render (KiCad is not installed in this environment)",
        fontsize=10,
    )
    fig.tight_layout()
    out_path = os.path.join(PCB_DIR, "PCB_5_VARIANT_LAYOUT_SCHEMATIC_NOT_A_KICAD_RENDER.png")
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
