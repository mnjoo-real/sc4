# v0.3.0 pre-purchase summary (A-E)

This is the top-level index for the complete pre-purchase design package.
It does not introduce new content — it ties together v0.3.0-A through -E and
tells a reader where to look for detail. The numerical model
(`README.md`, `model.py`, `source.py`, `plate.py`, `coupling.py`,
`response.py`) and the v0.2.0 simulation results (`out/`) are unchanged
throughout this entire design phase.

## The chain

| stage | what it produced | files |
|---|---|---|
| v0.2.0 | PCB geometry decision (100x40x1.0 mm) via simulation + robustness sweep | `out/final_pcb_recommendation.txt`, `out/pcb_candidate_comparison.csv` |
| v0.3.0-A | 3 experimental roles: S90 (strong), W90 (position-control), S0 (orientation-control) | `pcb_variants.md`, `PRE_PURCHASE_DESIGN.md` |
| v0.3.0-C | 5 fabrication designs (S90 split into 0402/0603/0805) + layout/ordering spec | `PCB_FABRICATION_SPEC.md`, `pcb_variants.csv`, `pcb_coordinates.csv`, `jlcpcb_order_settings.csv`, `pcb_quantity_plan.csv` |
| v0.3.0-D | Electrical drive/measurement protocol (Kelvin sensing, mic geometry, frequency-sweep protocol, data schema) | `ELECTRICAL_MEASUREMENT_SETUP.md`, `equipment_requirements.csv`, `measurement_geometry.csv`, `run_protocol.md`, `data_schema.csv` |
| v0.3.0-E | Final board population, unique specimens, complete non-factorial experiment matrix, go/no-go gate | `board_population_plan.csv`, `specimen_registry.csv`, `final_experiment_matrix.csv`, `experiment_phases.md`, `go_no_go_criteria.md` |

`excitation_plan.csv` was written in v0.3.0-D and superseded in place in
v0.3.0-D itself (Stage 1/Stage 2 protocol); `pcb_quantity_plan.csv` (v0.3.0-C,
generic per-footprint counts) is now superseded in practice by
`board_population_plan.csv` (v0.3.0-E, exact per-role counts) — both are
kept for their original purpose (ordering-form quantity vs. capacitor
population), but the authoritative "what capacitor goes on which board"
answer is `board_population_plan.csv` / `specimen_registry.csv`.

## Final board population (35 boards, 35 unique specimens)

| variant | boards | roles (qty) |
|---|---|---|
| S90-0603 | 15 | R(3), C1(2), C2(2), V1(2), V2(2), V3(2), N1(2) |
| S90-0402 | 5 | P1(3), spare(2) |
| S90-0805 | 5 | P2(3), D1(2) |
| W90-0603 | 5 | R(3), spare(2) |
| S0-0603 | 5 | R(3), spare(2) |

Reference part: **R = 0603ZD105KAT2A** (X5R, 1 uF, 10 V, 0603) — the only
specific commercial part number in this entire design. Every other role
(C1, C2, V1, V2, V3, N1, P1, P2, D1) is specified only by dielectric /
capacitance / rated voltage / package and marked `TBD` for part number —
**no other commercial MLCC part numbers are chosen at this stage.**

Every specimen has a unique ID (`specimen_id` in `specimen_registry.csv`,
e.g. `S90-0603-R-01`). No PCB is ever assumed to be desoldered and reused
with a different MLCC.

## Required vs. optional runs

From `final_experiment_matrix.csv` (308 rows total):

- **296 rows are required**: Phase 0 (2), Phase 1 (54), Phase 2 (54),
  Phase 3 (42), Phase 4 (54), Phase 5 (30), Phase 6 baseline (12), Phase 7
  (24), Phase 8 (24).
- **12 rows are optional**: Phase 6's 0.50 V_peak C0G sensitivity check,
  run only if the baseline (0.10 V_peak) response is below reliable
  acoustic SNR. Its result must not be treated as a direct quantitative
  comparison against the X5R parts.
- Of the required rows, **212 require a new physical measurement**; the
  remaining **84** are the same physical condition already captured
  elsewhere (66 reused from Phase 1, 18 reused from Phase 2) and are
  referenced rather than re-measured, per the non-factorial design.

## Measurements that depend on fr1/fr2/fr3

**Every row except Phase 0** depends on fr1, fr2, and/or fr3 — Phase 0 is
what defines them; every later phase uses the standard six-frequency set
(`fr1, fr2, fr3, fr1/2, fr2/2, fr3/2`) or the `fr_star`/`fr_star/2` pair
derived from them. This is by design: the entire experiment matrix is built
on top of a single resonance-identification run (`experiment_phases.md`
Phase 0), not on the v0.2.0 simulation's predicted 1090/1541/2293 Hz values,
which are guides only (`README.md` section 6; `out/final_pcb_recommendation.txt`).

**No numerical value has been substituted for fr1, fr2, or fr3 anywhere in
this design.** Every file that references them (`final_experiment_matrix.csv`
`freq_label`/`freq_spec` columns, `experiment_phases.md`,
`go_no_go_criteria.md`) uses the symbolic labels and an explicit "not yet
available" placeholder.

## Quantities that cannot be filled until the physical PCB is tested

- The literal Hz values of fr1, fr2, fr3 (and therefore fr1/2, fr2/2, fr3/2,
  fr_star, and fr_star/2) — only exist after Phase 0 is physically run.
- Every measured outcome field for every row of every phase: actual
  measured `V_DUT`, `I_peak` (measured, if the commissioning shunt is used),
  acoustic amplitude at `f`, acoustic amplitude at `2f` — see
  `data_schema.csv` for the exact fields these populate. `final_experiment_matrix.csv`
  is a plan of conditions to run, not a results table; none of its rows have
  measured data yet.
- Whether the go/no-go gate passes (`go_no_go_criteria.md`) — and therefore
  whether Phases 2-8 proceed at all.
- Which specific capacitors satisfy the `TBD` roles (C1, C2, V1, V2, V3, N1,
  P1, P2, D1) — those are chosen at order time from the stated electrical
  specs, not fixed here.

## What did not change in this phase

- No modification to the numerical model or to v0.2.0 simulation results.
- No FEM, acoustic radiation model, solder-joint model, or higher-fidelity
  MLCC physics was added at any point across v0.3.0-A through -E.
- No commercial MLCC part number was invented for any candidate role.
- No numerical resonance frequency was invented in place of fr1/fr2/fr3.

## Reading order for someone new to this package

1. `README.md` (model), `out/final_pcb_recommendation.txt` (why this PCB).
2. `pcb_variants.md`, `PRE_PURCHASE_DESIGN.md` (experimental roles).
3. `PCB_FABRICATION_SPEC.md` (what to actually fabricate).
4. `ELECTRICAL_MEASUREMENT_SETUP.md`, `run_protocol.md` (how to drive and
   measure it).
5. `board_population_plan.csv`, `specimen_registry.csv`,
   `experiment_phases.md`, `go_no_go_criteria.md`, `final_experiment_matrix.csv`
   (what to actually run, in what order, and when to stop).
