# Pre-purchase experimental design — v0.3.0

This is the final design package to review before ordering PCBs and MLCCs
for the singing-capacitor experiment. It carries forward the v0.2.0
simulation result as a fixed design basis and does not change the physics
model — see `README.md` for the model itself and `out/` for the v0.2.0
sweep results this design is built on.

## 1. Design basis (from v0.2.0)

Source: `out/final_pcb_recommendation.txt`, `out/pcb_candidate_comparison.csv`.

| parameter | value |
|---|---|
| PCB outline | 100 mm x 40 mm |
| PCB thickness | 1.0 mm |
| strong-response MLCC position | x/a=0.50, y/b=0.25 (x=50 mm, y=10 mm) |
| strong-response orientation | 90 deg |
| weak-control MLCC position | x/a=0.20, y/b=0.50 (x=20 mm, y=20 mm) |
| predicted resonances | 1090, 1541, 2293 Hz |
| predicted resonance spacing | 451, 752 Hz |
| predicted strong/control response ratio | 4.9x |
| predicted 0deg/90deg orientation ratio | 1.8x (90 deg stronger) |

These predictions come from an isotropic simply-supported thin-plate model
with a lumped MLCC source (README.md section 1). They are guides for board
geometry and MLCC placement, not exact experimental predictions — real
resonances will shift once the board is manufactured and mounted (README.md
section 6, "Known limitations").

**This design step does not add fidelity to that model.** No FEM, acoustic
radiation model, solder-joint model, or detailed MLCC electromechanical
model is introduced here. The task at this stage is translating an already-
decided PCB geometry and placement/orientation strategy into an orderable,
testable design.

## 2. What to order: three PCB variants

| variant | MLCC center (x, y) | orientation | purpose |
|---|---|---|---|
| **S90** | 50 mm, 10 mm | 90 deg | primary strong-response board; all capacitor candidates tested here |
| **W90** | 20 mm, 20 mm | 90 deg | position-control board; reference MLCC only |
| **S0**  | 50 mm, 10 mm | 0 deg  | orientation-control board; reference MLCC only |

All three share the same 100x40 mm outline, 1.0 mm thickness spec, mounting
scheme, electrical connection strategy, and test-pad strategy — only MLCC
placement/orientation differs. Full rationale and the shared specification
are in `pcb_variants.md`; machine-readable coordinates are in
`pcb_coordinates.csv`.

Order enough copies of each variant to allow for at least one spare per
variant (manufacturing tolerance and handling damage are the main risk at
this thickness) — decide the exact panel/quantity with the PCB vendor once
this design is reviewed; that is a purchasing decision, not a modeling one.

## 3. Experimental principles

These apply to every board and every run, and are restated in full (with
the reasoning behind each) in `pcb_variants.md`:

1. External wires attach near the PCB edge, not near the vibrating MLCC.
2. DUT voltage is measured directly across the capacitor, not read off the
   function generator, since the generator setting is not necessarily the
   actual MLCC voltage.
3. Account for the capacitive drive current `I_peak = 2*pi*f*C*V_peak` when
   choosing drive levels, especially near the top of the swept range.
4. Sweep order: broad experimental sweep first (to find the actual PCB
   resonances), then dense sweeps around the measured resonances and around
   half those frequencies (to test for 2f electrostrictive excitation).
5. Use one reference MLCC on S90, W90, and S0 to validate the simulated
   position and orientation effects before testing anything else.
6. Test all other capacitor-property candidates primarily on S90.
7. No commercial MLCC part numbers are chosen yet — candidates are tracked
   as placeholders (`TBD-1`, `TBD-2`, ...) until the reference measurements
   validate the board design.

## 4. Sweep and data-logging plan

- `excitation_plan.csv` — the frequency-sweep plan: phase 1 is a broad
  200-3000 Hz sweep on all three boards to locate actual resonances; phase 2
  is a dense sweep on S90 around each predicted resonance and each predicted
  half-resonance (provisional, to be recentered on the measured values);
  phase 3 repeats the dense sweep on W90 and S0 once phase 1 gives the
  measured resonance to center on.
- `experiment_matrix_template.csv` — one row per planned (board, capacitor,
  frequency-band) combination, with the measurement columns left blank to
  fill in during testing (drive voltage, measured DUT voltage, predicted
  `I_peak`, and the measured vibration response). Pre-populated with the
  reference MLCC across all three boards and three candidate placeholders
  on S90.

## 5. Files in this directory

| file | contents |
|---|---|
| `pcb_variants.md` | full per-variant rationale, shared spec, and the experimental principles above |
| `pcb_coordinates.csv` | machine-readable MLCC position/orientation per variant |
| `excitation_plan.csv` | broad + dense frequency-sweep plan per board |
| `experiment_matrix_template.csv` | blank run log to fill in during testing |
| `PRE_PURCHASE_DESIGN.md` | this file |

## 6. Open decisions before placing the order

These are purchasing/logistics decisions, not modeling ones, and are left
for explicit sign-off rather than assumed:

- exact PCB vendor, stack-up/copper spec, and quantity per variant,
- connector/pad footprint for the drive leads and test pads,
- which reference MLCC to use for the position/orientation validation
  (its capacitance should be roughly representative of the eventual
  candidates, so the `I_peak` estimate for phase-1/2 testing is realistic).
