# PCB fabrication review — v0.3.1

## Environment status

**KiCad 10.0.5 is installed** (`/Applications/KiCad/KiCad.app`,
`kicad-cli` confirmed working) and was used as the source of truth for
every check below: real parse/load, real DRC, real Gerber/drill export
from the KiCad engine (not a separate custom implementation), and real
`kicad-cli pcb render` 3D output. This supersedes the earlier v0.3.1 pass,
which was produced before KiCad was available and explicitly marked every
board `READY_FOR_JLCPCB: NO` for that reason.

Two real bugs were found and fixed while validating against actual KiCad
(not assumptions) — full detail in `design/PCB_CAD_ASSUMPTIONS.md` and
`pcb/NET_CONNECTIVITY_REVIEW.md`:

1. **Rotation-convention bug**: the original routing code assumed a
   counter-clockwise pad-rotation convention; KiCad's actual convention is
   clockwise in its stored (x, y-down) frame. This caused the DRIVE+/
   SENSE+ traces to land on the physical `-` pad and vice versa on every
   90-degree board — a real short, caught by `kicad-cli pcb drc`
   (`shorting_items`), not by the custom validator (which checked against
   its own, equally wrong, assumption). Fixed in `mlcc_pad_positions()`.
2. **Routing-topology bug**: after fixing (1), a *different* real crossing
   appeared — proven analytically to have no solution using simple
   monotonic-lane ordering, because the '+' and '-' groups' transit paths
   mutually cross through each other's target point (worst on W90-0603,
   where both directions conflict simultaneously). Fixed by routing the
   '-' group (SENSE-, DRIVE-) via a detour that overshoots past the MLCC's
   x-position, using board area the '+' group never touches.

No PCB coordinates, dimensions, or package assignments from v0.3.0 were
changed to fix either bug — both were pure routing/implementation issues.

## Per-board record — all verified against real KiCad

All 5 variants share: 100 x 40 mm outline, FR-4, 2 layers, 1.0 mm nominal
thickness, 1 oz copper, ENIG, no copper pours, no B.Cu routing, no vias, no
onboard connectors, 4x NPTH 3.2 mm mounting holes at (5,5) (95,5) (5,35)
(95,35) mm.

### S90-0402

| item | value |
|---|---|
| MLCC center / orientation | (50, 10) mm / 90 deg |
| Footprint | 0402 (pad 0.6x0.6mm, pitch 1.0mm), standard KiCad 3D model attached |
| KiCad parse | **PASS** |
| Custom geometry validation | **PASS** (13/13) |
| KiCad DRC errors | **0** |
| KiCad DRC warnings | 5, all `lib_footprint_mismatch` (intentional/expected — see below) |
| Gerber export | **PASS** (F.Cu, F.Mask, F.Silkscreen, Edge.Cuts + job file) |
| Drill verification | **PASS** (4 NPTH @ exact coords, 0 plated holes) |
| Visual Gerber inspection | **PASS** (per-layer + composite renders, programmatic bounds/location checks) |
| 3D visual inspection | **PASS** (top/bottom/perspective renders) |
| Gerber ZIP | `manufacturing/S90-0402_JLCPCB_Gerber.zip` |
| **READY_FOR_JLCPCB** | **YES** |

### S90-0603

| item | value |
|---|---|
| MLCC center / orientation | (50, 10) mm / 90 deg |
| Footprint | 0603 (pad 0.9x1.0mm, pitch 1.6mm), standard KiCad 3D model attached |
| KiCad parse | **PASS** |
| Custom geometry validation | **PASS** (13/13) |
| KiCad DRC errors | **0** |
| KiCad DRC warnings | 5, all `lib_footprint_mismatch` (intentional/expected) |
| Gerber export | **PASS** |
| Drill verification | **PASS** (4 NPTH @ exact coords, 0 plated holes) |
| Visual Gerber inspection | **PASS** |
| 3D visual inspection | **PASS** |
| Gerber ZIP | `manufacturing/S90-0603_JLCPCB_Gerber.zip` |
| **READY_FOR_JLCPCB** | **YES** |

### S90-0805

| item | value |
|---|---|
| MLCC center / orientation | (50, 10) mm / 90 deg |
| Footprint | 0805 (pad 1.2x1.45mm, pitch 1.9mm), standard KiCad 3D model attached |
| KiCad parse | **PASS** |
| Custom geometry validation | **PASS** (13/13) |
| KiCad DRC errors | **0** |
| KiCad DRC warnings | 5, all `lib_footprint_mismatch` (intentional/expected) |
| Gerber export | **PASS** |
| Drill verification | **PASS** (4 NPTH @ exact coords, 0 plated holes) |
| Visual Gerber inspection | **PASS** |
| 3D visual inspection | **PASS** |
| Gerber ZIP | `manufacturing/S90-0805_JLCPCB_Gerber.zip` |
| **READY_FOR_JLCPCB** | **YES** |

### W90-0603

| item | value |
|---|---|
| MLCC center / orientation | (20, 20) mm / 90 deg |
| Footprint | 0603, standard KiCad 3D model attached |
| Routing note | this is the geometrically hardest case (targets straddle both edge-pad groups — see `NET_CONNECTIVITY_REVIEW.md`); verified crossing-free by both the custom validator's segment-intersection check and real DRC |
| KiCad parse | **PASS** |
| Custom geometry validation | **PASS** (13/13) |
| KiCad DRC errors | **0** |
| KiCad DRC warnings | 5, all `lib_footprint_mismatch` (intentional/expected) |
| Gerber export | **PASS** |
| Drill verification | **PASS** (4 NPTH @ exact coords, 0 plated holes) |
| Visual Gerber inspection | **PASS** |
| 3D visual inspection | **PASS** |
| Gerber ZIP | `manufacturing/W90-0603_JLCPCB_Gerber.zip` |
| **READY_FOR_JLCPCB** | **YES** |

### S0-0603

| item | value |
|---|---|
| MLCC center / orientation | (50, 10) mm / 0 deg |
| Footprint | 0603, standard KiCad 3D model attached |
| Routing note | only board using the pad-1-bypass detour (orientation=0 case); clearance margin was tightened after real DRC found the original 0.3mm-from-centerline margin left only 0.05mm actual clearance |
| KiCad parse | **PASS** |
| Custom geometry validation | **PASS** (13/13) |
| KiCad DRC errors | **0** |
| KiCad DRC warnings | 5, all `lib_footprint_mismatch` (intentional/expected) |
| Gerber export | **PASS** |
| Drill verification | **PASS** (4 NPTH @ exact coords, 0 plated holes) |
| Visual Gerber inspection | **PASS** |
| 3D visual inspection | **PASS** |
| Gerber ZIP | `manufacturing/S0-0603_JLCPCB_Gerber.zip` |
| **READY_FOR_JLCPCB** | **YES** |

## DRC warning classification

Every board reports exactly 5 `lib_footprint_mismatch` warnings (one for
the MLCC footprint, four for the edge-contact footprints), after adding a
per-board `fp-lib-table`/`.kicad_pro` resolved the *worse* "library not
found" warning that appeared before those existed. This is **intentional
and expected**: the warning fires because the embedded footprint instance
(which carries net assignments, position, and a UUID) differs from the
bare library master copy (which has none of that, by definition — a
library part isn't wired to anything). This does not affect fabrication:
the actual copper/pad/silkscreen geometry that gets plotted into the
Gerbers comes entirely from the embedded instance, not the library master.
The mounting-hole footprint (`NPTH_3.2mm`) has no such mismatch, since it
carries no net data to differ on.

## Gerber contents (all 5 ZIPs)

Exactly the 4 requested layers plus KiCad's standard Gerber job file
(`*-job.gbrjob`, a small JSON manifest describing the layer stack — kept
since JLCPCB and most fabs use it to auto-configure the order, not an
"unnecessary empty layer"): `F.Cu`, `F.Mask`, `F.Silkscreen`,
`Edge.Cuts`, plus the Excellon drill file. No other layers were exported —
B.Cu, B.Mask, B.Silkscreen, and paste layers were confirmed empty/unused
by design and correctly excluded.

## Visual verification artifacts

Per variant, under `<variant>/renders/`:
- `<variant>_top.png`, `<variant>_bottom.png`, `<variant>_perspective.png` —
  real `kicad-cli pcb render` 3D output (high quality, floor/shadows on).
  Bottom view confirms bare substrate (no bottom copper); top/perspective
  confirm MLCC position, orientation, and package size visually, with a
  standard KiCad 3D body attached per package (0402/0603/0805) so the part
  is actually visible, not just its footprint outline.

Per variant, under `<variant>/manufacturing/gerber_verification/`:
- Per-layer PNGs (top copper, solder mask, silkscreen, edge cuts) plus a
  composite, rendered from the **actual exported Gerber files** via
  `kicad-cli pcb export svg` (the same plot engine that generated the
  Gerbers) converted to PNG — not re-renders of the source PCB.

`pcb/PCB_5_VARIANT_COMPARISON.png` — all 5 top-view renders at identical
camera/zoom settings, stacked and labeled for direct scale comparison.

## Files in this directory

```
pcb/
├── generate_pcb.py                  generator (source of truth for all 5 boards)
├── validate_pcb.py                  custom geometry/connectivity checker (pre-check, not a DRC substitute)
├── verify_gerbers.py                Gerber-file rendering + programmatic verification (Step 6)
├── render_3d.py                     kicad-cli pcb render driver (Step 7)
├── make_comparison.py               builds PCB_5_VARIANT_COMPARISON.png
├── generate_schematics.py           earlier (pre-KiCad) non-KiCad sanity diagrams, superseded by real renders
├── PCB_5_VARIANT_COMPARISON.png
├── FABRICATION_REVIEW.md            this file
├── NET_CONNECTIVITY_REVIEW.md       Step 3 net-model review
├── SC4.pretty/                      local footprint library (.kicad_mod files)
└── <variant>/
    ├── <variant>.kicad_pcb          board source, real-KiCad validated
    ├── <variant>.kicad_pro          minimal project file (enables fp-lib-table resolution)
    ├── fp-lib-table                 points the project at ../SC4.pretty
    ├── manufacturing/
    │   ├── validation_report.txt              custom validator output
    │   ├── drc_report.txt                     real kicad-cli DRC report
    │   ├── drill_report.txt                   real kicad-cli drill report
    │   ├── gerbers/                            raw exported Gerber + drill files
    │   ├── gerber_verification/                per-layer + composite PNGs, from the actual Gerbers
    │   ├── gerber_verification_report.txt      programmatic Gerber checks
    │   └── <variant>_JLCPCB_Gerber.zip         fabrication deliverable
    └── renders/
        └── <variant>_top.png, _bottom.png, _perspective.png
```

See `pcb/v0.3.1_FABRICATION_PACKAGE_SUMMARY.md` for the top-level summary
of this entire package.
