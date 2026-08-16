# PCB fabrication and ordering specification — v0.3.0-C

## Status — read this first

This document is a **layout and ordering specification**, not a Gerber
package. It is meant to be handed to an EDA tool (KiCad / Altium / Eagle) to
draw the board. **Do not generate, export, or submit Gerbers / production
files from this document alone.** Before ordering:

1. Build the layout in an EDA tool from the geometry in this spec and
   `pcb_coordinates.csv`.
2. Run DRC against the target fab's capability (see "Manufacturing
   constraints" below).
3. Visually review the layout (copper, silkscreen, drill, outline) against
   this spec.

Only after that visual/DRC review should Gerbers be generated and an order
placed. No Gerbers exist as part of this deliverable.

This spec does not change the numerical model. It translates the already
finalized experimental design (`pcb_variants.md`, `PRE_PURCHASE_DESIGN.md`,
v0.2.0 simulation results) into orderable PCB designs.

## 1. Relationship to the experimental design

`pcb_variants.md` (v0.3.0) defined three experimental roles: S90 (primary
strong-response board), W90 (position-control), S0 (orientation-control).
This spec fabricates **five PCB designs**, because S90 is produced in three
MLCC footprint sizes to additionally check whether package size itself
affects the response, while W90 and S0 use a single footprint (0603) to
match whatever reference MLCC package is used for position/orientation
validation:

| variant | role | footprint | MLCC center (mm) | long-axis orientation |
|---|---|---|---|---|
| S90-0402 | primary, strong-response | 0402 | (50, 10) | 90 deg |
| S90-0603 | primary, strong-response | 0603 | (50, 10) | 90 deg |
| S90-0805 | primary, strong-response | 0805 | (50, 10) | 90 deg |
| W90-0603 | position-control | 0603 | (20, 20) | 90 deg |
| S0-0603  | orientation-control | 0603 | (50, 10) | 0 deg |

See `pcb_variants.csv` for the machine-readable version of this table and
`pcb_coordinates.csv` for full pad-level geometry.

## 2. Coordinate convention

- Origin: bottom-left corner of the board.
- `x`: 0-100 mm, the long (100 mm) direction.
- `y`: 0-40 mm, the short (40 mm) direction.
- Orientation 0 deg: MLCC long axis (the axis through its two terminals)
  parallel to `x`.
- Orientation 90 deg: MLCC long axis parallel to `y`.

This matches the `x/a`, `y/b`, `orientation_deg` convention already used by
the simulation (`model.py`, `coupling.py`) and by `pcb_variants.md`.

## 3. Shared board specification (all five variants)

| item | value |
|---|---|
| Material | FR-4 |
| Layers | 2 |
| Outline | 100 x 40 mm |
| Thickness | 1.0 mm |
| Copper weight | 1 oz (outer layers) |
| Surface finish | ENIG |
| Copper pours | none |
| Bottom-layer copper | none (component/routing on top layer only) |
| Vias | none |
| Mounting holes | 4x NPTH, 3.2 mm diameter |
| Mounting hole locations | (5, 5), (95, 5), (5, 35), (95, 35) mm |

The mounting holes are unplated (NPTH) and identical across all five
variants, so all boards mount on the same fixture with the same compliant
corner standoffs described in `pcb_variants.md`.

## 4. MLCC footprints

Each variant uses **only its own nominal single-size footprint** for its
named package. Do not design a universal/combined pad pattern sized to fit
multiple packages — that changes solder-joint fillet geometry and effective
mechanical stiffness/coupling, which this experiment depends on being
representative of a normal, single-size solder joint.

The land-pattern dimensions below are **nominal/typical IPC-7351 "Nominal"
(Level B) numbers, provided as a layout starting point.** They must be
confirmed against the actual footprint library used in the EDA tool (e.g.
KiCad's standard `*_1005Metric` / `*_1608Metric` / `*_2012Metric` chip
footprints) before layout — do not hand-enter these into Gerbers directly.

| package | body size (L x W, mm) | pad size (mm) | pad pitch, center-to-center (mm) | reference courtyard (mm) |
|---|---|---|---|---|
| 0402 (1005 metric) | 1.0 x 0.5 | 0.6 x 0.6 | 1.0 | ~1.6 x 0.8 |
| 0603 (1608 metric) | 1.6 x 0.8 | 0.9 x 1.0 | 1.6 | ~2.4 x 1.2 |
| 0805 (2012 metric) | 2.0 x 1.25 | 1.2 x 1.45 | 1.9 | ~2.9 x 1.8 |

Two-pad footprint per variant, centered on the MLCC center coordinate and
rotated per its orientation (pads split along the long axis by the pitch
above). Computed pad centers for all five variants are in
`pcb_coordinates.csv`.

## 5. Electrical routing

### Four-wire (Kelvin) edge interface

All external electrical contact is a row of four solder pads near the left
edge (`x` small), in this order: **DRIVE+, SENSE+, SENSE-, DRIVE-**. No
connector component (header, JST, etc.) is placed on the board — wires are
soldered directly to these pads, so no connector mass/stiffness is added to
the vibrating structure.

Suggested reference pad row (to be confirmed in EDA, not final):

| pad | x (mm) | y (mm) |
|---|---|---|
| DRIVE+ | 5 | 12.5 |
| SENSE+ | 5 | 17.5 |
| SENSE- | 5 | 22.5 |
| DRIVE- | 5 | 27.5 |

This keeps the whole interface within the `x <= 15 mm` edge keepout strip
(section 7) and clear of the two left mounting holes at (5, 5) and (5, 35)
by >= 7.5 mm.

### Trace widths

- DRIVE+ / DRIVE- traces: **0.5 mm**.
- SENSE+ / SENSE- traces: **0.2 mm**.

Both are comfortably above typical 2-layer fab minimum trace width
(~0.09-0.15 mm depending on fab) and well above what's needed to carry the
capacitive drive current `I_peak = 2*pi*f*C*V_peak` at these excitation
frequencies and voltages — trace width here is set by manufacturability and
robustness, not current-carrying capacity.

### Kelvin sensing rule (implements "DUT voltage must be measured directly
across the capacitor")

**SENSE+ and SENSE- must originate directly at the MLCC pad copper**, not
as a branch off the DRIVE+/DRIVE- trace at some other point. If SENSE+ taps
the DRIVE+ trace anywhere between the edge and the MLCC, the measured
voltage includes the DRIVE trace's own resistive/inductive drop and the
"direct across the capacitor" principle is violated. Route SENSE+/SENSE- as
separate, thin (0.2 mm) traces from the MLCC pad back to the edge, alongside
but not merged with, the DRIVE traces.

Because MLCC position differs by variant (S90/S0 at x=50 mm, W90 at
x=20 mm), trace lengths from the edge interface to the MLCC differ across
variants. This is expected and acceptable: it is internal copper (negligible
added mass), not external wiring, so it does not violate the "wires near the
edge, not near the MLCC" principle, which concerns the mass/stiffness loading
of the external lead wires at their solder point — that solder point (the
edge pad row) is identical across all variants.

## 6. Design rule: no connectors, no vias, no bottom copper, no pours

- No connector components (headers, JST, etc.) anywhere on the board.
- No vias — this is a single-side (top layer) routed design; the bottom
  layer carries no copper at all.
- No copper pour / plane on either layer.

These rules keep the board's mass and stiffness distribution close to the
bare-FR4 assumption in the simulation (`README.md` section 1), and avoid an
unmodeled ground-plane or via-field stiffening effect near the vibrating
region.

## 7. Keepout / active-region rule

Split the board into two regions along `x`:

- **Edge strip, `x` in [0, 15] mm**: the four-wire interface pads, their
  immediate escape traces, and board/variant identification silkscreen
  (e.g. "S90-0603", a rev letter) are allowed here.
- **Active region, `x` in (15, 100] mm, full `y`**: copper is limited to
  the DRIVE/SENSE traces routed to the MLCC and the MLCC footprint pads
  themselves. No copper pour, no additional components, no fiducials, and
  no non-essential silkscreen (logos, outlines, revision text) are placed
  in the active region.

This keeps unmodeled copper/silkscreen mass out of the part of the board
where the plate's mode shapes have significant amplitude.

## 8. Manufacturing constraints check (informational, confirm at order time)

| item | this design | typical 2-layer FR-4 fab capability | margin |
|---|---|---|---|
| min trace width | 0.2 mm (sense) | ~0.09-0.15 mm | comfortable |
| min trace spacing | not yet routed — confirm in EDA | ~0.09-0.15 mm | confirm after layout |
| board thickness | 1.0 mm | standard range ~0.4-2.0 mm | within range |
| NPTH hole diameter | 3.2 mm | standard min NPTH ~0.3 mm | comfortable |
| layers | 2 | standard | n/a |
| surface finish | ENIG | standard option | n/a |

These are typical prototype-fab figures, not a specific fab's guaranteed
capability — reconfirm against the chosen fab house's current design rules
before finalizing the layout. See `jlcpcb_order_settings.csv` for the
JLCPCB-specific version of this check.

## 9. Files in this directory (v0.3.0-C additions)

| file | contents |
|---|---|
| `PCB_FABRICATION_SPEC.md` | this file |
| `pcb_variants.csv` | one row per orderable PCB design, fabrication-level attributes |
| `pcb_coordinates.csv` | MLCC center, orientation, footprint pitch, and computed pad coordinates per variant |
| `jlcpcb_order_settings.csv` | shared order-form settings and capability checks |
| `pcb_quantity_plan.csv` | planned order quantity per variant, with the reasoning split out |

(`pcb_variants.md`, `pcb_coordinates.csv` from v0.3.0, `PRE_PURCHASE_DESIGN.md`,
`excitation_plan.csv`, `experiment_matrix_template.csv` remain the
experimental-design layer this spec builds on. Note `pcb_coordinates.csv` is
superseded by the v0.3.0-C version in this same path, now at footprint-level
granularity.)

## 10. Open items before ordering

- Draw the layout in an EDA tool and run DRC (this spec is not a substitute).
- Confirm the four IPC nominal footprints against the actual EDA library
  parts used.
- Decide solder mask color, silkscreen color, and panelization with the fab
  (cosmetic / logistic, does not affect the experiment).
- Confirm current fab capability numbers in section 8 against the specific
  fab house and process selected at order time.
