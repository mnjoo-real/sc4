# Experiment phases — v0.3.0-E

This defines Phase 0 (resonance identification) through Phase 8 of the final
pre-purchase experiment plan. It builds on `pcb_variants.md` (v0.3.0),
`PCB_FABRICATION_SPEC.md` (v0.3.0-C), and `ELECTRICAL_MEASUREMENT_SETUP.md` /
`run_protocol.md` (v0.3.0-D) without changing any of them. The concrete,
row-level plan is `final_experiment_matrix.csv`; this file is the narrative
walkthrough of how that matrix was built, including the judgment calls made
to turn the phase descriptions into concrete rows.

## Conventions carried forward, unchanged

- All AC amplitudes are V_peak (`ELECTRICAL_MEASUREMENT_SETUP.md` section 2).
- The controlled voltage is the **actual measured** `V_DUT`, not the
  generator setting. The operator adjusts the generator so measured Vac is
  within **+/-2%** of the target value in every row below.
- Voltage budget: `|Vdc| + Vac_peak <= capacitor rated voltage`, checked
  before every run (`ELECTRICAL_MEASUREMENT_SETUP.md` section 2). All
  target levels used in Phases 1-8 (max |Vdc|+Vac_peak = 2.8+0.10 = 2.9 V in
  Phase 8) are comfortably under every rated voltage in the population
  (10-50 V), so no combination needs to be skipped for this design.
- Per-measurement-point procedure is unchanged: settle 0.5 s, record 2.0 s,
  save the raw microphone waveform, record actual `V_DUT`, extract acoustic
  response at `f` and at `2f` (`run_protocol.md` section 5).
- Record at least 10 s of background noise at the start of every session
  (`run_protocol.md` section 2).
- Do not invent numerical values for fr1/fr2/fr3 anywhere in this design —
  every row that depends on them carries a symbolic label
  (`fr1`, `fr2`, `fr3`, `fr1/2`, `fr2/2`, `fr3/2`, `fr_star`, `fr_star/2`)
  and an explicit "measured value ... not yet available" placeholder instead
  of a number.

## Phase 0 — Resonance identification (must run first)

- Specimen: **S90-0603-R-01** only.
- Vdc = 0 V, measured Vac = 0.02 V_peak.
- 200-3000 Hz at 25 Hz step, then 3000-20000 Hz at 100 Hz step.
- Output: identify the three primary, well-separated resonances within
  200-3000 Hz as **fr1, fr2, fr3**, and the strongest of the three as
  **fr_star**. The 3000-20000 Hz band is scanned for context but does not
  define fr1/fr2/fr3 (those are defined "within 200-3000 Hz" per spec).
- `fr1, fr2, fr3, fr1/2, fr2/2, fr3/2` become **the standard
  six-frequency set** used by every phase below.

This is a single run on a single specimen. It is not repeated per board or
per phase — see the go/no-go gate (`go_no_go_criteria.md`) for how
resonance *reproducibility* across the other R specimens is checked without
re-running a full broad sweep on each one.

## Phase 1 — Reference position/orientation validation

- Specimens: all **9** reference boards — S90-0603-R-01/02/03,
  W90-0603-R-01/02/03, S0-0603-R-01/02/03.
- Condition: **the standard six-frequency set**, Vac = 0.10 V_peak,
  Vdc = 0 V.

**Judgment call**: the phase description ("Reference R on S90, W90, and S0,
3 physical replicates each. Purpose: validate position and orientation
effects") does not restate a frequency/voltage condition. Since section
"All main MLCC-property comparisons use ... the standard six-frequency set"
immediately follows it, and Phase 1's own purpose is a comparison (S90 vs
W90 for position, S90 vs S0 for orientation) that needs to be measured on
the same footing as every later comparison, this design applies the
standard condition (0.10 V_peak / 0 V / six-frequency set) to Phase 1 as
well. This is stated explicitly here so it can be corrected if a different
condition was intended for Phase 1 specifically.

54 rows (9 specimens x 6 frequencies), all new measurements.

## Go/no-go gate

Placed here, after Phase 1 and before Phase 2. See `go_no_go_criteria.md`
for the full operationalized criteria. Do not proceed past this point
without a "go."

## Phase 2 — Package comparison (P1 0402 vs R 0603 vs P2 0805)

- New specimens: S90-0402-P1-01/02/03, S90-0805-P2-01/02/03 (6 specimens x
  6 frequencies = 36 new rows).
- Reused: the S90-0603-R-01/02/03 data already collected in Phase 1 serves
  as the 0603 arm (18 rows, tagged `Reused from Phase 1` in the matrix) —
  no new physical measurement, since it is the same condition on the same
  specimens.
- Condition: standard six-frequency set, Vac = 0.10 V_peak, Vdc = 0 V.

## Phase 3 — Capacitance comparison (C1 0.1uF vs R 1uF vs C2 10uF)

- New specimens: S90-0603-C1-01/02, S90-0603-C2-01/02 (4 specimens x 6
  frequencies = 24 new rows).
- Reused: S90-0603-R-01/02/03 from Phase 1 (18 rows) as the 1 uF arm.
- Condition: standard six-frequency set, Vac = 0.10 V_peak, Vdc = 0 V.

Note the group sizes are intentionally unequal (2 replicates for C1/C2,
3 for R) — this is expected in a non-factorial, reuse-driven design.

## Phase 4 — Rated-voltage comparison (R 10V vs V1 16V vs V2 25V vs V3 50V)

- New specimens: S90-0603-V1-01/02, V2-01/02, V3-01/02 (6 specimens x 6
  frequencies = 36 new rows).
- Reused: S90-0603-R-01/02/03 from Phase 1 (18 rows) as the 10 V arm.
- Condition: standard six-frequency set, Vac = 0.10 V_peak, Vdc = 0 V.

## Phase 5 — Dielectric comparison (P2 X5R vs D1 X7R, matched 0805/1uF/10V)

- New specimens: S90-0805-D1-01/02 (2 specimens x 6 frequencies = 12 new
  rows).
- Reused: S90-0805-P2-01/02/03 from Phase 2 (18 rows) as the X5R arm — same
  specimens, same condition, already measured there.
- Condition: standard six-frequency set, Vac = 0.10 V_peak, Vdc = 0 V.

## Phase 6 — C0G negative control (N1)

- Specimens: S90-0603-N1-01/02.
- **Required** baseline: standard six-frequency set, Vac = 0.10 V_peak,
  Vdc = 0 V (12 rows, new).
- **Optional** sensitivity run: same 2 specimens, same standard
  six-frequency set (assumed — the spec does not restate a frequency set for
  the optional run, so this design reuses the standard one for
  comparability), at Vac = 0.50 V_peak, **only if** the baseline response is
  below reliable acoustic SNR (12 rows, optional, new).
- **Do not treat the optional 0.50 V_peak result as a direct quantitative
  comparison with the X5R parts** measured at 0.10 V_peak elsewhere in this
  design — it exists only to confirm C0G shows negligible response even
  when pushed harder, not to be plotted on the same amplitude axis as the
  X5R comparisons.

## Phase 7 — AC-amplitude sweep (3 reference specimens)

- Specimens: S90-0603-R-01/02/03.
- Frequencies: `fr_star` and `fr_star/2` only (not the full six-set).
- Vdc = 0 V. Vac = 0.05, 0.10, 0.25, 0.50 V_peak.
- 24 conditions (3 specimens x 2 frequencies x 4 levels).

**Reuse**: because `fr_star` is by definition one of {fr1, fr2, fr3} and
`fr_star/2` is one of {fr1/2, fr2/2, fr3/2}, the Vac = 0.10 V_peak / Vdc = 0 V
point at both frequencies, on these same 3 specimens, is structurally
guaranteed to already exist in the Phase 1 data — regardless of which of
fr1/fr2/fr3 turns out to be fr_star. Those 6 rows are tagged `Reused from
Phase 1`; the other 18 (Vac = 0.05, 0.25, 0.50) are new.

## Phase 8 — DC-bias sweep (3 reference specimens)

- Specimens: S90-0603-R-01/02/03.
- Frequencies: `fr_star` and `fr_star/2`.
- Vac = 0.10 V_peak. Vdc = 0, 1, 2, 2.8 V.
- 24 conditions (3 specimens x 2 frequencies x 4 levels).

**Reuse**: by the same argument as Phase 7, the Vdc = 0 V point (at
Vac = 0.10 V_peak, both frequencies, same 3 specimens) is structurally
identical to a Phase 1 measurement. Those 6 rows are tagged `Reused from
Phase 1`; the other 18 (Vdc = 1, 2, 2.8) are new.

**Note**: the single condition Vac = 0.10 V_peak / Vdc = 0 V at `fr_star`
and `fr_star/2` on S90-0603-R-01/02/03 is therefore shared by Phase 1,
Phase 7, and Phase 8 simultaneously — it is measured once, in Phase 1, and
referenced by both later phases.

## Row totals (from `final_experiment_matrix.csv`)

| phase | rows | new | reused |
|---|---|---|---|
| 0 - resonance ID | 2 | 2 | 0 |
| 1 - position/orientation | 54 | 54 | 0 |
| 2 - package | 54 | 36 | 18 (Phase 1) |
| 3 - capacitance | 42 | 24 | 18 (Phase 1) |
| 4 - rated voltage | 54 | 36 | 18 (Phase 1) |
| 5 - dielectric | 30 | 12 | 18 (Phase 2) |
| 6 - C0G control | 24 (12 required + 12 optional) | 24 | 0 |
| 7 - AC-amplitude sweep | 24 | 18 | 6 (Phase 1) |
| 8 - DC-bias sweep | 24 | 18 | 6 (Phase 1) |
| **total** | **308** | **224** | **84** |

212 rows are both new and required (224 new minus the 12 new-but-optional
Phase 6 rows).
