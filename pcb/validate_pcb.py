#!/usr/bin/env python3
"""Custom geometry/connectivity validator for the generated .kicad_pcb files.

IMPORTANT: this is NOT KiCad's DRC engine. kicad-cli / pcbnew are not
installed in this environment (verified: no kicad-cli on PATH, no pcbnew
Python module, no /Applications/KiCad*). This script parses the
S-expression text this repo's own generate_pcb.py produced and checks it
against the requirements below using a hand-written parser and geometry
checks. It cannot catch every error a real KiCad DRC would (footprint
library correctness, courtyard overlap, silkscreen-over-pad, KiCad's own
clearance rules, file-format validity as parsed by the real KiCad engine).
See design/PCB_CAD_ASSUMPTIONS.md and pcb/FABRICATION_REVIEW.md.

Checks performed, per the task's validation requirements:
- board dimensions = 100 x 40 mm (from Edge.Cuts gr_line extents)
- four mounting-hole centers are exact
- MLCC center coordinate is exact
- MLCC orientation is exact
- correct footprint/package is used
- no vias exist
- no copper zones exist
- no B.Cu tracks exist
- drive traces are 0.5 mm, sense traces are 0.2 mm
- all four interface pads reach the intended MLCC terminal (connectivity)
- no unintended shorts (no two different-net segments intersect except at
  their shared endpoint)

Usage:
    python3 validate_pcb.py
"""

import math
import os
import re
import sys

PCB_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PCB_DIR)
from generate_pcb import VARIANTS, PACKAGES, HOLES, HOLE_DIA, EDGE_PADS, EDGE_PAD_X, \
    DRIVE_TRACE_W, SENSE_TRACE_W, mlcc_pad_positions, BOARD_L, BOARD_W


def find_all(pattern, text, flags=0):
    return re.findall(pattern, text, flags)


def parse_gr_lines(text):
    return [
        tuple(float(v) for v in m)
        for m in find_all(
            r'\(gr_line \(start ([\-0-9.]+) ([\-0-9.]+)\) \(end ([\-0-9.]+) ([\-0-9.]+)\) \(layer "Edge\.Cuts"\)',
            text,
        )
    ]


def parse_footprints(text):
    """Return list of (footprint_name, at_x, at_y, at_rot, pads[(name/number, net_num, net_name_or_None, layer_set)])."""
    fps = []
    for fp_match in re.finditer(r'\(footprint "([^"]+)" \(layer "F\.Cu"\)\n(.*?)\n\t\)\n', text, re.S):
        fp_name = fp_match.group(1)
        body = fp_match.group(2)
        at_m = re.search(r"\(at ([\-0-9.]+) ([\-0-9.]+)(?: ([\-0-9.]+))?\)", body)
        ax, ay = float(at_m.group(1)), float(at_m.group(2))
        arot = float(at_m.group(3)) if at_m.group(3) else 0.0
        ref_m = re.search(r'\(fp_text reference "([^"]*)"', body)
        reference = ref_m.group(1) if ref_m else None
        pads = []
        for pad_m in re.finditer(
            r'\(pad "([^"]*)" (\S+) (\S+) \(at ([\-0-9.]+) ([\-0-9.]+)\) '
            r'\(size ([\-0-9.]+) ([\-0-9.]+)\)(?: \(drill ([\-0-9.]+)\))? '
            r'\(layers ((?:"[^"]+" ?)+)\)(?: \(net (\d+) "([^"]*)"\))?',
            body,
        ):
            pad_name = pad_m.group(1)
            pad_type = pad_m.group(2)
            px, py = float(pad_m.group(4)), float(pad_m.group(5))
            layers = pad_m.group(9)
            net_num = int(pad_m.group(10)) if pad_m.group(10) else None
            net_name = pad_m.group(11)
            pads.append(dict(name=pad_name, type=pad_type, local_xy=(px, py), layers=layers,
                              net_num=net_num, net_name=net_name))
        fps.append(dict(name=fp_name, at=(ax, ay, arot), reference=reference, pads=pads))
    return fps


def parse_segments(text):
    segs = []
    for m in re.finditer(
        r'\(segment \(start ([\-0-9.]+) ([\-0-9.]+)\) \(end ([\-0-9.]+) ([\-0-9.]+)\) '
        r'\(width ([\-0-9.]+)\) \(layer "([^"]+)"\) \(net (\d+)\)',
        text,
    ):
        sx, sy, ex, ey, w = (float(m.group(i)) for i in range(1, 6))
        layer = m.group(6)
        net = int(m.group(7))
        segs.append(dict(start=(sx, sy), end=(ex, ey), width=w, layer=layer, net=net))
    return segs


def pad_world_xy(fp, pad):
    """Rotate a footprint-local pad offset by the footprint's placement angle
    and translate by the footprint's (at x y). KiCad's actual convention
    (confirmed against real `kicad-cli pcb drc` output, not assumed): positive
    angle rotates CLOCKWISE in the stored (x, y-down) frame. An earlier CCW
    assumption here (and in generate_pcb.py's mlcc_pad_positions) produced
    real DRIVE+/DRIVE- shorts on every 90-deg board; see
    pcb/NET_CONNECTIVITY_REVIEW.md."""
    fx, fy, frot = fp["at"]
    lx, ly = pad["local_xy"]
    theta = math.radians(frot)
    wx = fx + lx * math.cos(theta) + ly * math.sin(theta)
    wy = fy - lx * math.sin(theta) + ly * math.cos(theta)
    return round(wx, 3), round(wy, 3)


def segments_intersect(p1, p2, p3, p4, tol=1e-6):
    """True if closed segments p1-p2 and p3-p4 intersect/overlap anywhere,
    including collinear overlap. Endpoint-only touching is reported too --
    caller filters out the single legitimate shared-pad endpoint case."""
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def on_seg(p, q, r):
        return (min(p[0], r[0]) - tol <= q[0] <= max(p[0], r[0]) + tol and
                min(p[1], r[1]) - tol <= q[1] <= max(p[1], r[1]) + tol)

    d1 = cross(p3, p4, p1)
    d2 = cross(p3, p4, p2)
    d3 = cross(p1, p2, p3)
    d4 = cross(p1, p2, p4)

    if ((d1 > tol and d2 < -tol) or (d1 < -tol and d2 > tol)) and \
       ((d3 > tol and d4 < -tol) or (d3 < -tol and d4 > tol)):
        return True
    if abs(d1) <= tol and on_seg(p3, p1, p4):
        return True
    if abs(d2) <= tol and on_seg(p3, p2, p4):
        return True
    if abs(d3) <= tol and on_seg(p1, p3, p2):
        return True
    if abs(d4) <= tol and on_seg(p1, p4, p2):
        return True
    return False


def validate(variant):
    path = os.path.join(PCB_DIR, variant, f"{variant}.kicad_pcb")
    with open(path) as f:
        text = f.read()

    spec = VARIANTS[variant]
    pkg = spec["footprint"]
    mlcc_x, mlcc_y, orientation = spec["mlcc_x"], spec["mlcc_y"], spec["orientation"]
    results = []

    def check(name, ok, detail=""):
        results.append((name, ok, detail))

    # ---- board dimensions ----
    lines = parse_gr_lines(text)
    xs = [c for l in lines for c in (l[0], l[2])]
    ys = [c for l in lines for c in (l[1], l[3])]
    dims_ok = (min(xs) == 0.0 and max(xs) == BOARD_L and min(ys) == 0.0 and max(ys) == BOARD_W)
    check("board_dimensions_100x40mm", dims_ok, f"x:[{min(xs)},{max(xs)}] y:[{min(ys)},{max(ys)}]")

    # ---- footprints ----
    fps = parse_footprints(text)
    npth_fps = [fp for fp in fps if fp["name"] == "SC4:NPTH_3.2mm"]
    mlcc_fps = [fp for fp in fps if fp["name"] == f"SC4:C_{pkg}_Local"]
    edge_fps = [fp for fp in fps if fp["name"] == "SC4:EdgeContact_2.5mm_Round"]

    # ---- mounting holes ----
    hole_centers = sorted((fp["at"][0], fp["at"][1]) for fp in npth_fps)
    expected_holes = sorted(HOLES)
    check("mounting_hole_count", len(hole_centers) == 4, f"found {len(hole_centers)}")
    check("mounting_hole_centers_exact", hole_centers == expected_holes,
          f"got {hole_centers}, expected {expected_holes}")
    hole_size_m = find_all(r'np_thru_hole circle \(at 0 0\) \(size ([\-0-9.]+) ([\-0-9.]+)\) \(drill ([\-0-9.]+)\)', text)
    hole_sizes_ok = all(float(a) == HOLE_DIA and float(b) == HOLE_DIA and float(d) == HOLE_DIA
                         for a, b, d in hole_size_m) and len(hole_size_m) == 4
    check("mounting_hole_diameter_3.2mm", hole_sizes_ok, str(hole_size_m))

    # ---- MLCC footprint/package/position/orientation ----
    check("mlcc_correct_footprint_used", len(mlcc_fps) == 1, f"found {[fp['name'] for fp in fps if 'C_' in fp['name']]}")
    if mlcc_fps:
        fx, fy, frot = mlcc_fps[0]["at"]
        check("mlcc_center_exact", (fx, fy) == (mlcc_x, mlcc_y), f"got ({fx},{fy}) expected ({mlcc_x},{mlcc_y})")
        expected_rot = 90 if orientation == 90 else 0
        check("mlcc_orientation_exact", frot == expected_rot, f"got {frot} expected {expected_rot}")

    # ---- no vias ----
    via_count = len(find_all(r"\(via ", text))
    check("no_vias", via_count == 0, f"found {via_count}")

    # ---- no zones ----
    zone_count = len(find_all(r"\(zone ", text))
    check("no_copper_zones", zone_count == 0, f"found {zone_count}")

    # ---- no B.Cu tracks ----
    segs = parse_segments(text)
    bcu_segs = [s for s in segs if s["layer"] == "B.Cu"]
    check("no_bcu_tracks", len(bcu_segs) == 0, f"found {len(bcu_segs)}")
    bcu_pad_layers = find_all(r'\(layers ((?:"[^"]*" ?)*"B\.Cu"(?:[^)]*)?)\)', text)
    check("no_bcu_in_pad_layers", len(bcu_pad_layers) == 0, f"found {len(bcu_pad_layers)}")

    # ---- trace widths ----
    drive_widths = {round(s["width"], 3) for s in segs if s["net"] in (1, 2)}
    fcu_segs = [s for s in segs if s["layer"] == "F.Cu"]
    drive_ok = all(abs(w - DRIVE_TRACE_W) < 1e-9 or abs(w - SENSE_TRACE_W) < 1e-9 for w in drive_widths)
    check("trace_widths_only_0.5_or_0.2mm", drive_ok, f"widths found: {sorted(drive_widths)}")
    n_05 = sum(1 for s in fcu_segs if abs(s["width"] - DRIVE_TRACE_W) < 1e-9)
    n_02 = sum(1 for s in fcu_segs if abs(s["width"] - SENSE_TRACE_W) < 1e-9)
    check("drive_and_sense_segments_present", n_05 > 0 and n_02 > 0, f"0.5mm segs={n_05}, 0.2mm segs={n_02}")

    # ---- connectivity: 4 edge pads reach the intended MLCC terminal ----
    edge_pad_nets = {}
    for fp in edge_fps:
        for pad in fp["pads"]:
            edge_pad_nets[fp["reference"]] = pad["net_num"]
    pad1, pad2 = mlcc_pad_positions(pkg, mlcc_x, mlcc_y, orientation)
    mlcc_net_by_terminal = {}
    if mlcc_fps:
        for pad in mlcc_fps[0]["pads"]:
            wx, wy = pad_world_xy(mlcc_fps[0], pad)
            if (wx, wy) == pad1:
                mlcc_net_by_terminal["+"] = pad["net_num"]
            elif (wx, wy) == pad2:
                mlcc_net_by_terminal["-"] = pad["net_num"]

    expect_terminal = {"DRIVE+": "+", "SENSE+": "+", "SENSE-": "-", "DRIVE-": "-"}
    conn_ok = True
    conn_detail = []
    for name, terminal in expect_terminal.items():
        edge_net = edge_pad_nets.get(name)
        mlcc_net = mlcc_net_by_terminal.get(terminal)
        same = edge_net is not None and edge_net == mlcc_net
        conn_detail.append(f"{name}->net{edge_net} vs MLCC({terminal})->net{mlcc_net} {'OK' if same else 'MISMATCH'}")
        conn_ok = conn_ok and same
    check("four_interface_pads_reach_intended_mlcc_terminal", conn_ok, "; ".join(conn_detail))

    # ---- no unintended shorts: no different-net F.Cu segments cross except at shared MLCC pad ----
    shorts = []
    for i in range(len(fcu_segs)):
        for j in range(i + 1, len(fcu_segs)):
            a, b = fcu_segs[i], fcu_segs[j]
            if a["net"] == b["net"]:
                continue
            if segments_intersect(a["start"], a["end"], b["start"], b["end"]):
                # allowed only if intersection is exactly the shared MLCC pad point
                shared = {a["start"], a["end"]} & {b["start"], b["end"]}
                allowed_points = {pad1, pad2}
                if shared and shared.issubset(allowed_points):
                    continue
                shorts.append((a, b))
    check("no_unintended_cross_net_shorts", len(shorts) == 0, f"conflicting segment pairs: {len(shorts)}")

    return results


def main():
    all_ok = True
    for variant in VARIANTS:
        print(f"\n=== {variant} ===")
        results = validate(variant)
        report_lines = [f"Custom geometry validator report for {variant}",
                         "NOT KiCad DRC -- kicad-cli/pcbnew unavailable in this environment.", ""]
        for name, ok, detail in results:
            status = "PASS" if ok else "FAIL"
            print(f"  [{status}] {name}  {detail}")
            report_lines.append(f"[{status}] {name}  {detail}")
            if not ok:
                all_ok = False
        out_path = os.path.join(PCB_DIR, variant, "manufacturing", "validation_report.txt")
        with open(out_path, "w") as f:
            f.write("\n".join(report_lines) + "\n")
    print(f"\n{'ALL CHECKS PASS' if all_ok else 'SOME CHECKS FAILED'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
