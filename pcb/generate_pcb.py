#!/usr/bin/env python3
"""Generate KiCad PCB source files for the 5 singing-capacitor board variants.

Source of truth: design/pcb_variants.csv, design/pcb_coordinates.csv,
design/PCB_FABRICATION_SPEC.md. Genuinely unspecified fabrication parameters
(edge-pad shape/size, exact trace routing paths) are documented in
design/PCB_CAD_ASSUMPTIONS.md and implemented here.

IMPORTANT: this script builds .kicad_pcb / .kicad_mod S-expression files by
direct text generation, NOT via KiCad's own pcbnew Python API, because KiCad
is not installed in this environment (checked: no kicad-cli, no pcbnew
module, no /Applications/KiCad*). These files have therefore never been
opened or parsed by real KiCad. See pcb/FABRICATION_REVIEW.md.

Usage:
    python3 generate_pcb.py
"""

import math
import os
import uuid

PCB_DIR = os.path.dirname(os.path.abspath(__file__))

BOARD_L = 100.0
BOARD_W = 40.0
HOLES = [(5.0, 5.0), (95.0, 5.0), (5.0, 35.0), (95.0, 35.0)]
HOLE_DIA = 3.2

# nominal IPC land-pattern dims from design/PCB_FABRICATION_SPEC.md section 4
PACKAGES = {
    "0402": dict(pad_w=0.6, pad_h=0.6, pitch=1.0),
    "0603": dict(pad_w=0.9, pad_h=1.0, pitch=1.6),
    "0805": dict(pad_w=1.2, pad_h=1.45, pitch=1.9),
}

# Standard KiCad-shipped 3D models, used for visual rendering only (Step 7).
# Does NOT change footprint pads/electrical definition -- see
# design/PCB_CAD_ASSUMPTIONS.md. Path is this machine's KiCad install
# location; portable installs should use ${KICAD9_3DMODEL_DIR}-style env
# vars instead if moving to a different machine/KiCad version.
KICAD_3D_BASE = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels"
PACKAGE_3D_MODELS = {
    "0402": f"{KICAD_3D_BASE}/Capacitor_SMD.3dshapes/C_0402_1005Metric.step",
    "0603": f"{KICAD_3D_BASE}/Capacitor_SMD.3dshapes/C_0603_1608Metric.step",
    "0805": f"{KICAD_3D_BASE}/Capacitor_SMD.3dshapes/C_0805_2012Metric.step",
}

# from design/pcb_coordinates.csv (v0.3.0-C) -- do not change without
# re-checking against that file
VARIANTS = {
    "S90-0402": dict(footprint="0402", mlcc_x=50.0, mlcc_y=10.0, orientation=90),
    "S90-0603": dict(footprint="0603", mlcc_x=50.0, mlcc_y=10.0, orientation=90),
    "S90-0805": dict(footprint="0805", mlcc_x=50.0, mlcc_y=10.0, orientation=90),
    "W90-0603": dict(footprint="0603", mlcc_x=20.0, mlcc_y=20.0, orientation=90),
    "S0-0603":  dict(footprint="0603", mlcc_x=50.0, mlcc_y=10.0, orientation=0),
}

# edge interface: assumption per design/PCB_CAD_ASSUMPTIONS.md
# x/y centers reuse the v0.3.0-C "suggested reference pad row"; diameter/shape
# is new (task default: round 2.5mm)
EDGE_PAD_X = 5.0
EDGE_PADS = [
    ("DRIVE+", 12.5),
    ("SENSE+", 17.5),
    ("SENSE-", 22.5),
    ("DRIVE-", 27.5),
]
EDGE_PAD_DIA = 2.5

DRIVE_TRACE_W = 0.5
SENSE_TRACE_W = 0.2

# merged Kelvin nets -- see design/PCB_CAD_ASSUMPTIONS.md for why DRIVE+/SENSE+
# (and DRIVE-/SENSE-) are modeled as one KiCad net each
NET_PLUS = "DRIVE_SENSE_PLUS"
NET_MINUS = "DRIVE_SENSE_MINUS"

VARIANT_LABEL_POS = (5.0, 31.0)  # silkscreen variant-ID text, see assumptions doc


def new_uuid():
    return str(uuid.uuid4())


# --------------------------------------------------------------------- layers

LAYERS_BLOCK = """\t(layers
\t\t(0 "F.Cu" signal)
\t\t(31 "B.Cu" signal)
\t\t(34 "F.Paste" user)
\t\t(35 "B.Paste" user)
\t\t(36 "B.SilkS" user "B.Silkscreen")
\t\t(37 "F.SilkS" user "F.Silkscreen")
\t\t(38 "B.Mask" user)
\t\t(39 "F.Mask" user)
\t\t(44 "Edge.Cuts" user)
\t\t(48 "B.Fab" user)
\t\t(49 "F.Fab" user)
\t)
"""


def header(nets):
    net_lines = "".join(f'\t(net {i} "{name}")\n' for i, name in enumerate(nets))
    return (
        "(kicad_pcb\n"
        "\t(version 20221018)\n"
        '\t(generator "sc4-modeling-generate_pcb.py")\n'
        "\t(general\n"
        "\t\t(thickness 1.0)\n"
        "\t)\n"
        '\t(paper "A4")\n'
        + LAYERS_BLOCK
        + "\t(setup\n"
        "\t\t(pad_to_mask_clearance 0.05)\n"
        "\t)\n"
        + net_lines
    )


# --------------------------------------------------------------- board outline

def edge_cuts():
    x0, y0, x1, y1 = 0.0, 0.0, BOARD_L, BOARD_W
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    lines = []
    for (sx, sy), (ex, ey) in zip(corners, corners[1:]):
        lines.append(
            f"\t(gr_line (start {sx} {sy}) (end {ex} {ey}) (layer \"Edge.Cuts\") "
            f'(width 0.1) (uuid "{new_uuid()}"))'
        )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------- mounting holes (NPTH)

def mounting_hole(ref, x, y):
    fp_uuid = new_uuid()
    pad_uuid = new_uuid()
    return (
        f'\t(footprint "SC4:NPTH_3.2mm" (layer "F.Cu")\n'
        f'\t\t(at {x} {y})\n'
        f"\t\t(attr exclude_from_pos_files exclude_from_bom)\n"
        f'\t\t(fp_text reference "{ref}" (at 0 -3) (layer "F.SilkS") hide\n'
        f"\t\t\t(effects (font (size 1 1) (thickness 0.15)))\n"
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f"\t\t)\n"
        f'\t\t(fp_text value "NPTH_3.2mm" (at 0 3) (layer "F.Fab") hide\n'
        f"\t\t\t(effects (font (size 1 1) (thickness 0.15)))\n"
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f"\t\t)\n"
        f'\t\t(pad "1" np_thru_hole circle (at 0 0) (size {HOLE_DIA} {HOLE_DIA}) '
        f'(drill {HOLE_DIA}) (layers "*.Cu" "*.Mask") (uuid "{pad_uuid}"))\n'
        f'\t\t(uuid "{fp_uuid}")\n'
        f"\t)\n"
    )


# ------------------------------------------------------------- MLCC footprint

def mlcc_pad_positions(pkg, mlcc_x, mlcc_y, orientation):
    """Return (pad1_xy, pad2_xy) in board coordinates. pad1 = '+' terminal,
    pad2 = '-' terminal, per the convention documented in
    design/PCB_CAD_ASSUMPTIONS.md.

    Uses KiCad's actual footprint-rotation convention: positive angle
    rotates CLOCKWISE in the stored (x, y-down) frame, i.e.
        world = (fx + lx*cos(theta) + ly*sin(theta),
                 fy - lx*sin(theta) + ly*cos(theta))
    This was confirmed empirically against real `kicad-cli pcb drc` output
    on 2026-08-16 (see pcb/NET_CONNECTIVITY_REVIEW.md) after the original
    CCW-assumed formula produced real DRIVE+/DRIVE- shorts on every 90-deg
    board: KiCad placed pad "1" (net DRIVE_SENSE_PLUS, local x=-pitch/2) at
    the *larger*-y position for orientation=90, not the smaller one.
    """
    pitch = PACKAGES[pkg]["pitch"]
    theta = math.radians(orientation)

    def rotate(lx, ly):
        wx = mlcc_x + lx * math.cos(theta) + ly * math.sin(theta)
        wy = mlcc_y - lx * math.sin(theta) + ly * math.cos(theta)
        return (round(wx, 3), round(wy, 3))

    pad1 = rotate(-pitch / 2, 0)
    pad2 = rotate(pitch / 2, 0)
    return pad1, pad2


def mlcc_footprint(variant, pkg, mlcc_x, mlcc_y, orientation):
    spec = PACKAGES[pkg]
    pad_w, pad_h = spec["pad_w"], spec["pad_h"]
    pitch = spec["pitch"]
    # local pad offsets before rotation: pad "1" at -pitch/2, pad "2" at +pitch/2
    # along the footprint's local X axis; footprint rotation handles orientation
    rot = 90 if orientation == 90 else 0
    fp_uuid = new_uuid()
    return (
        f'\t(footprint "SC4:C_{pkg}_Local" (layer "F.Cu")\n'
        f"\t\t(at {mlcc_x} {mlcc_y} {rot})\n"
        f"\t\t(attr smd)\n"
        # reference/value silkscreen hidden: MLCC sits in the "active region"
        # (x > 15mm), where PCB_FABRICATION_SPEC.md section 7 forbids
        # non-essential silkscreen
        f'\t\t(fp_text reference "MLCC1" (at 0 -1.5) (layer "F.SilkS") hide\n'
        f"\t\t\t(effects (font (size 1 1) (thickness 0.15)))\n"
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f"\t\t)\n"
        f'\t\t(fp_text value "C_{pkg}" (at 0 1.5) (layer "F.Fab") hide\n'
        f"\t\t\t(effects (font (size 1 1) (thickness 0.15)))\n"
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f"\t\t)\n"
        f'\t\t(pad "1" smd rect (at {-pitch/2} 0) (size {pad_w} {pad_h}) '
        f'(layers "F.Cu" "F.Paste" "F.Mask") (net 1 "{NET_PLUS}") (uuid "{new_uuid()}"))\n'
        f'\t\t(pad "2" smd rect (at {pitch/2} 0) (size {pad_w} {pad_h}) '
        f'(layers "F.Cu" "F.Paste" "F.Mask") (net 2 "{NET_MINUS}") (uuid "{new_uuid()}"))\n'
        f'\t\t(model "{PACKAGE_3D_MODELS[pkg]}"\n'
        f"\t\t\t(offset (xyz 0 0 0))\n"
        f"\t\t\t(scale (xyz 1 1 1))\n"
        f"\t\t\t(rotate (xyz 0 0 0))\n"
        f"\t\t)\n"
        f'\t\t(uuid "{fp_uuid}")\n'
        f"\t)\n"
    )


# -------------------------------------------------------------- edge contacts

def edge_pad_footprint(name, x, y, net_num, net_name):
    fp_uuid = new_uuid()
    return (
        f'\t(footprint "SC4:EdgeContact_2.5mm_Round" (layer "F.Cu")\n'
        f"\t\t(at {x} {y})\n"
        f"\t\t(attr smd)\n"
        # allowed silkscreen (variant ID only, per assumptions doc) is drawn
        # separately as a board-level gr_text, not per-pad, so hide fp text
        f'\t\t(fp_text reference "{name}" (at 0 -2) (layer "F.SilkS") hide\n'
        f"\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))\n"
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f"\t\t)\n"
        f'\t\t(fp_text value "EdgeContact" (at 0 2) (layer "F.Fab") hide\n'
        f"\t\t\t(effects (font (size 0.8 0.8) (thickness 0.12)))\n"
        f'\t\t\t(uuid "{new_uuid()}")\n'
        f"\t\t)\n"
        f'\t\t(pad "1" smd circle (at 0 0) (size {EDGE_PAD_DIA} {EDGE_PAD_DIA}) '
        f'(layers "F.Cu" "F.Mask") (net {net_num} "{net_name}") (uuid "{new_uuid()}"))\n'
        f'\t\t(uuid "{fp_uuid}")\n'
        f"\t)\n"
    )


# --------------------------------------------------------------------- routing

def _seg(p0, p1, width, net_num):
    return (
        f'\t(segment (start {p0[0]} {p0[1]}) (end {p1[0]} {p1[1]}) (width {width}) '
        f'(layer "F.Cu") (net {net_num}) (uuid "{new_uuid()}"))\n'
    )


def route_traces(pkg, mlcc_x, mlcc_y, orientation):
    """Return the gerber/segment text for all 4 traces (DRIVE+, SENSE+,
    SENSE-, DRIVE-), routed so that no two different-net segments touch or
    overlap except at their shared MLCC pad. See
    design/PCB_CAD_ASSUMPTIONS.md for the routing rule.
    """
    spec = PACKAGES[pkg]
    pad1, pad2 = mlcc_pad_positions(pkg, mlcc_x, mlcc_y, orientation)  # pad1='+', pad2='-'
    out = []

    if orientation == 90:
        # For orientation=90, KiCad's actual (confirmed) rotation places pad1
        # ('+') and pad2 ('-') at mlcc_y +/- pitch/2 -- which one is upper
        # depends on the variant (for S90/W90 pad1 ends up upper), and for
        # W90 specifically (mlcc_y=20) both targets fall *between* the '+'
        # group's edge pads (12.5/17.5) and the '-' group's edge pads
        # (22.5/27.5), so EITHER group's straight vertical descent/ascent
        # passes directly through the other's target point. This was proven
        # to have no crossing-free solution using straight lines confined to
        # x <= mlcc_x (both groups' combined paths necessarily span the full
        # x-range, and one group's target sits inside the other's transit
        # span, in both directions for W90) -- confirmed by exhausting the
        # lane-ordering options against real `kicad-cli pcb drc` output; see
        # pcb/NET_CONNECTIVITY_REVIEW.md.
        #
        # Fix: give the '-' group (SENSE-, DRIVE-) a detour that overshoots
        # past the MLCC's x position (using board area the '+' group never
        # touches, since '+' group's whole path stays at x <= mlcc_x) and
        # approaches its pad from beyond it. This is topologically clean
        # for both the "targets below all edge pads" (S90/S0 family) and
        # "targets straddle the two edge-pad groups" (W90) cases, with no
        # case-detection needed.
        overshoot_x = mlcc_x + 3.0

        plus_names = [n for n in EDGE_PADS if n[0] in ("DRIVE+", "SENSE+")]
        for i, (name, edge_y) in enumerate(plus_names):
            net_num, net_name = 1, NET_PLUS
            width = DRIVE_TRACE_W if name == "DRIVE+" else SENSE_TRACE_W
            sx = mlcc_x - 6 + i
            p0 = (EDGE_PAD_X, edge_y)
            p1 = (sx, edge_y)
            p2 = (sx, pad1[1])
            p3 = pad1
            out.append(_seg(p0, p1, width, net_num))
            out.append(_seg(p1, p2, width, net_num))
            out.append(_seg(p2, p3, width, net_num))

        minus_names = [n for n in EDGE_PADS if n[0] in ("SENSE-", "DRIVE-")]
        for i, (name, edge_y) in enumerate(minus_names):
            net_num, net_name = 2, NET_MINUS
            width = DRIVE_TRACE_W if name == "DRIVE-" else SENSE_TRACE_W
            ox = overshoot_x + i  # distinct overshoot lane per trace
            p0 = (EDGE_PAD_X, edge_y)
            p1 = (ox, edge_y)
            p2 = (ox, pad2[1])
            p3 = pad2
            out.append(_seg(p0, p1, width, net_num))
            out.append(_seg(p1, p2, width, net_num))
            out.append(_seg(p2, p3, width, net_num))
    else:
        # orientation 0: pads differ in X only, pad1 ('+') is nearer the edge,
        # pad2 ('-') is farther -> the '-' group must detour around pad1's
        # footprint (this is the "only where necessary" extra complexity)
        staging_x = {name: mlcc_x - 8 + i for i, (name, _) in enumerate(EDGE_PADS)}
        pad_h = spec["pad_h"]
        # clearance from pad1's edge to the detour trace's NEAR edge, not its
        # centerline: half the (wider, 0.5mm) DRIVE- trace width, plus a
        # margin above KiCad's default 0.2mm min clearance. The original
        # 0.3mm-from-centerline version left only 0.05mm actual clearance
        # (confirmed by real kicad-cli DRC: required 0.2mm, actual 0.05mm)
        # because it didn't account for the trace's own half-width.
        detour_y = mlcc_y + pad_h / 2 + DRIVE_TRACE_W / 2 + 0.3
        for name, edge_y in EDGE_PADS:
            sx = staging_x[name]
            p0 = (EDGE_PAD_X, edge_y)
            p1 = (sx, edge_y)
            if name in ("DRIVE+", "SENSE+"):
                net_num, net_name, width = 1, NET_PLUS, (DRIVE_TRACE_W if name == "DRIVE+" else SENSE_TRACE_W)
                p2 = (sx, mlcc_y)
                p3 = pad1
                out.append(_seg(p0, p1, width, net_num))
                out.append(_seg(p1, p2, width, net_num))
                out.append(_seg(p2, p3, width, net_num))
            else:
                net_num, net_name, width = 2, NET_MINUS, (DRIVE_TRACE_W if name == "DRIVE-" else SENSE_TRACE_W)
                p2 = (sx, detour_y)
                p3 = (pad2[0], detour_y)
                p4 = pad2
                out.append(_seg(p0, p1, width, net_num))
                out.append(_seg(p1, p2, width, net_num))
                out.append(_seg(p2, p3, width, net_num))
                out.append(_seg(p3, p4, width, net_num))

    return "".join(out)


# ------------------------------------------------------------------ silkscreen

def variant_label(variant):
    x, y = VARIANT_LABEL_POS
    return (
        f'\t(gr_text "{variant}" (at {x} {y} 0) (layer "F.SilkS")\n'
        f"\t\t(effects (font (size 1 1) (thickness 0.15)))\n"
        f'\t\t(uuid "{new_uuid()}")\n'
        f"\t)\n"
    )


# --------------------------------------------------------------------- .kicad_mod

def kicad_mod_mlcc(pkg):
    spec = PACKAGES[pkg]
    pad_w, pad_h, pitch = spec["pad_w"], spec["pad_h"], spec["pitch"]
    return (
        f'(footprint "C_{pkg}_Local"\n'
        f"\t(version 20221018)\n"
        '\t(generator "sc4-modeling-generate_pcb.py")\n'
        '\t(layer "F.Cu")\n'
        f'\t(descr "Local nominal IPC-7351 land pattern for {pkg}, per design/PCB_FABRICATION_SPEC.md section 4")\n'
        f'\t(pad "1" smd rect (at {-pitch/2} 0) (size {pad_w} {pad_h}) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
        f'\t(pad "2" smd rect (at {pitch/2} 0) (size {pad_w} {pad_h}) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
        f'\t(model "{PACKAGE_3D_MODELS[pkg]}"\n'
        f"\t\t(offset (xyz 0 0 0))\n"
        f"\t\t(scale (xyz 1 1 1))\n"
        f"\t\t(rotate (xyz 0 0 0))\n"
        f"\t)\n"
        f")\n"
    )


def kicad_mod_edge_contact():
    return (
        '(footprint "EdgeContact_2.5mm_Round"\n'
        "\t(version 20221018)\n"
        '\t(generator "sc4-modeling-generate_pcb.py")\n'
        '\t(layer "F.Cu")\n'
        '\t(descr "Round hand-solder edge contact pad, assumption per design/PCB_CAD_ASSUMPTIONS.md")\n'
        f'\t(pad "1" smd circle (at 0 0) (size {EDGE_PAD_DIA} {EDGE_PAD_DIA}) (layers "F.Cu" "F.Mask"))\n'
        ")\n"
    )


def kicad_mod_npth():
    return (
        '(footprint "NPTH_3.2mm"\n'
        "\t(version 20221018)\n"
        '\t(generator "sc4-modeling-generate_pcb.py")\n'
        '\t(layer "F.Cu")\n'
        '\t(descr "Non-plated 3.2mm mounting hole, per design/PCB_FABRICATION_SPEC.md section 3")\n'
        f'\t(pad "1" np_thru_hole circle (at 0 0) (size {HOLE_DIA} {HOLE_DIA}) (drill {HOLE_DIA}) (layers "*.Cu" "*.Mask"))\n'
        ")\n"
    )


# ------------------------------------------------------------------------ main

def build_variant(variant):
    spec = VARIANTS[variant]
    pkg = spec["footprint"]
    mlcc_x, mlcc_y, orientation = spec["mlcc_x"], spec["mlcc_y"], spec["orientation"]

    parts = [header(["", NET_PLUS, NET_MINUS])]
    parts.append(edge_cuts())
    for i, (hx, hy) in enumerate(HOLES, start=1):
        parts.append(mounting_hole(f"H{i}", hx, hy))
    parts.append(mlcc_footprint(variant, pkg, mlcc_x, mlcc_y, orientation))
    for name, y in EDGE_PADS:
        net_num = 1 if name in ("DRIVE+", "SENSE+") else 2
        net_name = NET_PLUS if net_num == 1 else NET_MINUS
        parts.append(edge_pad_footprint(name, EDGE_PAD_X, y, net_num, net_name))
    parts.append(route_traces(pkg, mlcc_x, mlcc_y, orientation))
    parts.append(variant_label(variant))
    parts.append(")\n")

    return "".join(parts)


def main():
    lib_dir = os.path.join(PCB_DIR, "SC4.pretty")
    os.makedirs(lib_dir, exist_ok=True)
    for pkg in PACKAGES:
        with open(os.path.join(lib_dir, f"C_{pkg}_Local.kicad_mod"), "w") as f:
            f.write(kicad_mod_mlcc(pkg))
    with open(os.path.join(lib_dir, "EdgeContact_2.5mm_Round.kicad_mod"), "w") as f:
        f.write(kicad_mod_edge_contact())
    with open(os.path.join(lib_dir, "NPTH_3.2mm.kicad_mod"), "w") as f:
        f.write(kicad_mod_npth())
    print(f"wrote local footprint library: {lib_dir}")

    for variant in VARIANTS:
        vdir = os.path.join(PCB_DIR, variant)
        os.makedirs(os.path.join(vdir, "manufacturing"), exist_ok=True)
        os.makedirs(os.path.join(vdir, "renders"), exist_ok=True)
        pcb_text = build_variant(variant)
        out_path = os.path.join(vdir, f"{variant}.kicad_pcb")
        with open(out_path, "w") as f:
            f.write(pcb_text)
        print(f"wrote {out_path} ({len(pcb_text)} bytes)")


if __name__ == "__main__":
    main()
