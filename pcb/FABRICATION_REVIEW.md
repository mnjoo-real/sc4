# PCB fabrication review — v0.3.1

## Environment status (read this first)

**KiCad is not installed in this environment.** Checked and confirmed
absent: `kicad-cli` (and `kicad-cli8`/`kicad-cli9`) on PATH, the `pcbnew`
Python module, `/Applications/KiCad*`, and via `brew list` / `brew list
--cask`.

As a direct consequence, per the task's explicit instructions for this
case:

- **No board here is marked `READY_FOR_JLCPCB`.** None can be, because the
  readiness bar requires DRC with no errors, layer-by-layer Gerber
  inspection, and visual footprint verification — none of which are
  possible without KiCad.
- **No Gerbers, no Excellon drill files, and no `*_JLCPCB_Gerber.zip` were
  generated.** Faking them (e.g. hand-writing Gerber-like text without a
  real plotting engine) would be worse than not having them, and was not
  done.
- **No KiCad-rendered PNGs (top/bottom/3D/copper/mask/silk/drill plots)
  were generated**, for the same reason. What's in each `renders/`
  directory instead is a clearly-labeled, non-KiCad geometry
  sanity-check diagram (see below) — explicitly not a substitute.
- **`.kicad_pcb` board source files were still created** (5 of them, one
  per variant), per the instruction to do this "if possible." They were
  built by direct S-expression text generation
  (`pcb/generate_pcb.py`), not via KiCad's own `pcbnew` API, and **have
  never been opened or parsed by real KiCad**. Treat them as a best-effort
  draft that needs to be opened and reviewed in actual KiCad before any
  further step.

## What was done instead

1. **`pcb/generate_pcb.py`** — builds all 5 `.kicad_pcb` files plus a local
   footprint library (`pcb/SC4.pretty/`) directly from the same coordinate
   data as `design/pcb_coordinates.csv`. See
   `design/PCB_CAD_ASSUMPTIONS.md` for every fabrication parameter this
   had to assume vs. one that was already fixed by v0.3.0.
2. **`pcb/validate_pcb.py`** — a hand-written parser and geometry/
   connectivity checker (**not KiCad DRC**) that checks every item in the
   task's "Validation requirements" list against the generated files by
   parsing their own S-expression text. Its output is saved per variant at
   `pcb/<variant>/manufacturing/validation_report.txt`. Result: **all
   checks pass on all 5 variants** (see table below) — this confirms the
   generator produced internally self-consistent geometry, not that the
   files are valid/DRC-clean KiCad files.
3. **`pcb/generate_schematics.py`** — matplotlib diagrams (explicitly
   filenamed `*_NOT_A_KICAD_RENDER.png`) showing board outline, holes,
   pads, and routed traces to scale, as a visual cross-check of the same
   coordinate data. Not a KiCad render, not photorealistic, no copper/mask
   color accuracy — a geometry sanity check only.

## Per-board record

All 5 variants share: 100 x 40 mm outline, FR-4, 2 layers, 1.0 mm nominal
thickness, 1 oz copper, ENIG, no copper pours, no B.Cu routing, no vias, no
onboard connectors, 4x NPTH 3.2 mm mounting holes at (5,5) (95,5) (5,35)
(95,35) mm.

### S90-0402

| item | value |
|---|---|
| MLCC center | (50, 10) mm |
| Orientation | 90 deg |
| Footprint | 0402 (pad 0.6x0.6mm, pitch 1.0mm) |
| Hole coordinates | (5,5) (95,5) (5,35) (95,35) mm, dia 3.2mm |
| Edge-pad geometry | round, dia 2.5mm, at (5,12.5)/(5,17.5)/(5,22.5)/(5,27.5) mm |
| Routing | direct 3-segment L-route per net (no detour needed; see PCB_CAD_ASSUMPTIONS.md item 3) |
| Custom validator result | **PASS** (13/13 checks) |
| Real KiCad DRC | **not run** — KiCad unavailable |
| Gerber filenames | **not generated** |
| Drill filename | **not generated** |
| Board dimensions | 100 x 40 mm (confirmed from generated Edge.Cuts geometry) |
| READY_FOR_JLCPCB | **NO** |

### S90-0603

| item | value |
|---|---|
| MLCC center | (50, 10) mm |
| Orientation | 90 deg |
| Footprint | 0603 (pad 0.9x1.0mm, pitch 1.6mm) |
| Hole coordinates | (5,5) (95,5) (5,35) (95,35) mm, dia 3.2mm |
| Edge-pad geometry | round, dia 2.5mm, at (5,12.5)/(5,17.5)/(5,22.5)/(5,27.5) mm |
| Routing | direct 3-segment L-route per net |
| Custom validator result | **PASS** (13/13 checks) |
| Real KiCad DRC | **not run** — KiCad unavailable |
| Gerber filenames | **not generated** |
| Drill filename | **not generated** |
| Board dimensions | 100 x 40 mm |
| READY_FOR_JLCPCB | **NO** |

### S90-0805

| item | value |
|---|---|
| MLCC center | (50, 10) mm |
| Orientation | 90 deg |
| Footprint | 0805 (pad 1.2x1.45mm, pitch 1.9mm) |
| Hole coordinates | (5,5) (95,5) (5,35) (95,35) mm, dia 3.2mm |
| Edge-pad geometry | round, dia 2.5mm, at (5,12.5)/(5,17.5)/(5,22.5)/(5,27.5) mm |
| Routing | direct 3-segment L-route per net |
| Custom validator result | **PASS** (13/13 checks) |
| Real KiCad DRC | **not run** — KiCad unavailable |
| Gerber filenames | **not generated** |
| Drill filename | **not generated** |
| Board dimensions | 100 x 40 mm |
| READY_FOR_JLCPCB | **NO** |

### W90-0603

| item | value |
|---|---|
| MLCC center | (20, 20) mm |
| Orientation | 90 deg |
| Footprint | 0603 (pad 0.9x1.0mm, pitch 1.6mm) |
| Hole coordinates | (5,5) (95,5) (5,35) (95,35) mm, dia 3.2mm |
| Edge-pad geometry | round, dia 2.5mm, at (5,12.5)/(5,17.5)/(5,22.5)/(5,27.5) mm |
| Routing | direct 3-segment L-route per net (shorter run than S90/S0, since MLCC is closer to the edge at x=20mm) |
| Custom validator result | **PASS** (13/13 checks) |
| Real KiCad DRC | **not run** — KiCad unavailable |
| Gerber filenames | **not generated** |
| Drill filename | **not generated** |
| Board dimensions | 100 x 40 mm |
| READY_FOR_JLCPCB | **NO** |

### S0-0603

| item | value |
|---|---|
| MLCC center | (50, 10) mm |
| Orientation | 0 deg |
| Footprint | 0603 (pad 0.9x1.0mm, pitch 1.6mm) |
| Hole coordinates | (5,5) (95,5) (5,35) (95,35) mm, dia 3.2mm |
| Edge-pad geometry | round, dia 2.5mm, at (5,12.5)/(5,17.5)/(5,22.5)/(5,27.5) mm |
| Routing | **4-segment detour route** for SENSE-/DRIVE- (only variant needing this — see PCB_CAD_ASSUMPTIONS.md item 3) |
| Custom validator result | **PASS** (13/13 checks) |
| Real KiCad DRC | **not run** — KiCad unavailable |
| Gerber filenames | **not generated** |
| Drill filename | **not generated** |
| Board dimensions | 100 x 40 mm |
| READY_FOR_JLCPCB | **NO** |

## Custom validator checks (all 5 variants, all pass)

Run via `python3 pcb/validate_pcb.py`. For each variant: board dimensions,
mounting-hole count/centers/diameter, correct MLCC footprint used, MLCC
center/orientation exact, no vias, no copper zones, no B.Cu tracks/pad
layers, trace widths are only 0.5mm or 0.2mm, both widths present, all 4
labeled interface pads reach the intended MLCC terminal (net-connectivity
check), and no two different-net F.Cu segments touch or cross anywhere
except at their one legitimate shared MLCC-pad point.

**This is not KiCad DRC.** It cannot check: footprint-library validity as
KiCad's own parser would see it, courtyard overlap, silkscreen-over-copper,
KiCad's actual clearance/creepage rules, annular ring rules, or whether the
file even opens in KiCad without error.

## What a human needs to do next (in order)

1. Install KiCad (7 or newer recommended for `kicad-cli`).
2. Open each `pcb/<variant>/<variant>.kicad_pcb` and fix whatever the real
   KiCad parser flags on load (expected: this file was hand-generated and
   has never been parsed by KiCad before).
3. Run `kicad-cli pcb drc` on each board; resolve any errors (warnings
   should be reviewed and summarized, per the task brief) before proceeding.
4. Visually inspect each board in KiCad's 3D viewer and 2D editor —
   specifically confirm MLCC footprint position/orientation, edge-pad
   placement/clearance from the mounting holes, and that the DRIVE+/SENSE+
   and DRIVE-/SENSE- merged-net simplification (`PCB_CAD_ASSUMPTIONS.md`
   item 4) is acceptable, or upgrade it to a proper 4-net + net-tie
   implementation.
5. Export Gerbers (F.Cu, F.Mask, F.Silkscreen, Edge.Cuts, plus any other
   layer that turns out to actually carry data) and Excellon drill files
   from KiCad directly — not from a separate custom geometry
   implementation, per the task brief.
6. Zip exactly the fabrication-needed files into
   `pcb/<variant>/manufacturing/<variant>_JLCPCB_Gerber.zip`.
7. Only after steps 3-6 are clean should any board be marked
   `READY_FOR_JLCPCB`.

## Files in this directory

```
pcb/
├── generate_pcb.py                        generator (source of truth for all 5 boards)
├── validate_pcb.py                        custom geometry/connectivity checker (not KiCad DRC)
├── generate_schematics.py                 non-KiCad geometry sanity-check diagrams
├── PCB_5_VARIANT_LAYOUT_SCHEMATIC_NOT_A_KICAD_RENDER.png
├── FABRICATION_REVIEW.md                  this file
├── SC4.pretty/                            local footprint library (.kicad_mod files)
└── <variant>/
    ├── <variant>.kicad_pcb                board source, unvalidated by real KiCad
    ├── manufacturing/
    │   └── validation_report.txt          custom validator output (not DRC)
    └── renders/
        └── <variant>_layout_schematic_NOT_A_KICAD_RENDER.png
```
