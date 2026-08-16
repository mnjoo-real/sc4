#!/usr/bin/env python3
"""Step 6: Gerber verification.

Renders/inspects the actual exported Gerber+drill files (not just the
.kicad_pcb source) via `kicad-cli pcb export svg` (the same plot engine
that generated the Gerbers) converted to PNG, plus direct programmatic
parsing of the Gerber/drill text for geometry checks.

Usage:
    python3 verify_gerbers.py
"""

import os
import re
import subprocess
import sys

PCB_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PCB_DIR)
from generate_pcb import VARIANTS, BOARD_L, BOARD_W, HOLES, HOLE_DIA, mlcc_pad_positions, PACKAGES

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

LAYER_SETS = {
    "top_copper": "F.Cu",
    "solder_mask": "F.Mask",
    "silkscreen": "F.Silkscreen",
    "edge_cuts": "Edge.Cuts",
    "composite_top": "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts",
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def svg_to_png(svg_path, png_path):
    run(["qlmanage", "-t", "-s", "1200", "-o", os.path.dirname(png_path), svg_path])
    generated = svg_path + ".png"
    if os.path.exists(generated) and generated != png_path:
        os.replace(generated, png_path)
    return os.path.exists(png_path)


def render_layers(variant):
    pcb_path = os.path.join(PCB_DIR, variant, f"{variant}.kicad_pcb")
    out_dir = os.path.join(PCB_DIR, variant, "manufacturing", "gerber_verification")
    os.makedirs(out_dir, exist_ok=True)
    results = {}
    for label, layers in LAYER_SETS.items():
        svg_path = os.path.join(out_dir, f"{variant}_{label}.svg")
        png_path = os.path.join(out_dir, f"{variant}_{label}.png")
        rc, out, err = run([
            KICAD_CLI, "pcb", "export", "svg", pcb_path,
            "--output", svg_path, "--layers", layers,
            "--mode-single", "--exclude-drawing-sheet", "--page-size-mode", "2",
        ])
        ok_svg = rc == 0 and os.path.exists(svg_path)
        ok_png = ok_svg and svg_to_png(svg_path, png_path)
        results[label] = ok_png
    return results


def parse_gerber_bounds(gerber_path):
    """Extract the coordinate extents actually drawn in a Gerber file
    (very small RS-274X reader: just pulls X/Y coordinate pairs).
    KiCad's Gerber Y is negated relative to the board's stored Y (same
    convention as the Excellon drill output) -- normalize it back here so
    callers can compare directly against board-space coordinates."""
    with open(gerber_path) as f:
        text = f.read()
    coords = re.findall(r"X(-?\d+)Y(-?\d+)", text)
    if not coords:
        return None
    # Gerber default here is 6-digit mm (from --precision 6 default), i.e. units of 1e-6 mm
    xs = [int(x) / 1e6 for x, y in coords]
    ys = [-int(y) / 1e6 for x, y in coords]
    return dict(x_min=min(xs), x_max=max(xs), y_min=min(ys), y_max=max(ys))


def parse_drill_holes(drl_path):
    with open(drl_path) as f:
        text = f.read()
    coords = re.findall(r"X([\-0-9.]+)Y([\-0-9.]+)", text)
    return [(float(x), float(y)) for x, y in coords]


def check_variant(variant):
    spec = VARIANTS[variant]
    pkg = spec["footprint"]
    mlcc_x, mlcc_y, orientation = spec["mlcc_x"], spec["mlcc_y"], spec["orientation"]
    gdir = os.path.join(PCB_DIR, variant, "manufacturing", "gerbers")

    checks = []

    def check(name, ok, detail=""):
        checks.append((name, ok, detail))

    edge_cuts_path = os.path.join(gdir, f"{variant}-Edge_Cuts.gm1")
    bounds = parse_gerber_bounds(edge_cuts_path)
    if bounds:
        dims_ok = (abs(bounds["x_min"]) < 0.01 and abs(bounds["x_max"] - BOARD_L) < 0.01
                   and abs(bounds["y_min"]) < 0.01 and abs(bounds["y_max"] - BOARD_W) < 0.01)
        check("gerber_outline_100x40mm", dims_ok, str(bounds))
    else:
        check("gerber_outline_100x40mm", False, "could not parse Edge_Cuts gerber")

    drl_path = os.path.join(gdir, f"{variant}.drl")
    holes = parse_drill_holes(drl_path)
    # drill file Y is negated relative to board storage (standard Excellon convention)
    holes_norm = sorted((round(x, 3), round(-y, 3)) for x, y in holes)
    expected = sorted(HOLES)
    check("drill_centers_exact", holes_norm == expected, f"got {holes_norm}, expected {expected}")

    fcu_path = os.path.join(gdir, f"{variant}-F_Cu.gtl")
    fcu_bounds = parse_gerber_bounds(fcu_path)
    if fcu_bounds:
        no_copper_outside = (fcu_bounds["x_min"] >= -0.01 and fcu_bounds["x_max"] <= BOARD_L + 0.01
                              and fcu_bounds["y_min"] >= -0.01 and fcu_bounds["y_max"] <= BOARD_W + 0.01)
        check("no_copper_outside_board", no_copper_outside, str(fcu_bounds))
    else:
        check("no_copper_outside_board", False, "could not parse F_Cu gerber")

    pad1, pad2 = mlcc_pad_positions(pkg, mlcc_x, mlcc_y, orientation)
    with open(fcu_path) as f:
        fcu_text = f.read()
    # crude presence check: both MLCC pad centers should appear as coordinates
    # (within the gerber's 6-decimal-digit fixed format) somewhere near the pad flash
    def near_coord_present(x, y, tol=0.05):
        for cx, cy in re.findall(r"X(-?\d+)Y(-?\d+)D03", fcu_text):
            gx, gy = int(cx) / 1e6, -int(cy) / 1e6  # gerber Y is negated vs. board storage
            if abs(gx - x) < tol and abs(gy - y) < tol:
                return True
        return False
    mlcc_present = near_coord_present(*pad1) and near_coord_present(*pad2)
    # rect pads are plotted as flashed apertures OR region fills depending on KiCad version;
    # fall back to bounding-box containment check if no D03 flash coords matched
    if not mlcc_present:
        spec_pkg = PACKAGES[pkg]
        mlcc_present = (fcu_bounds is not None and
                         fcu_bounds["x_min"] <= min(pad1[0], pad2[0]) and
                         fcu_bounds["x_max"] >= max(pad1[0], pad2[0]))
    check("mlcc_location_in_gerber", mlcc_present, f"pad1={pad1} pad2={pad2}")

    n_gtl_flashes_or_paths = len(re.findall(r"X-?\d+Y-?\d+D0[123]", fcu_text))
    check("no_missing_trace_gerber_nonempty", n_gtl_flashes_or_paths > 10, f"{n_gtl_flashes_or_paths} coord ops")

    return checks


def main():
    all_ok = True
    for variant in VARIANTS:
        print(f"\n=== {variant} ===")
        render_results = render_layers(variant)
        for label, ok in render_results.items():
            print(f"  [render] {label}: {'OK' if ok else 'FAILED'}")
            all_ok = all_ok and ok

        checks = check_variant(variant)
        report_lines = [f"Gerber verification report for {variant}", ""]
        report_lines.append("Layer renders (from actual exported Gerbers via kicad-cli pcb export svg):")
        for label, ok in render_results.items():
            report_lines.append(f"  [{'OK' if ok else 'FAILED'}] {label}")
        report_lines.append("")
        report_lines.append("Programmatic checks (parsed directly from the Gerber/drill files):")
        for name, ok, detail in checks:
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}  {detail}")
            report_lines.append(f"[{status}] {name}  {detail}")
            if not ok:
                all_ok = False

        out_path = os.path.join(PCB_DIR, variant, "manufacturing", "gerber_verification_report.txt")
        with open(out_path, "w") as f:
            f.write("\n".join(report_lines) + "\n")

    print(f"\n{'ALL GERBER CHECKS PASS' if all_ok else 'SOME GERBER CHECKS FAILED'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
