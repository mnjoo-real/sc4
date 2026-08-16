# Go/no-go criteria — v0.3.0-E

**Placement**: after Phase 1 (reference position/orientation validation),
before Phase 2 (start of the full capacitor-property dataset). See
`experiment_phases.md`.

## The three checks

Per the design brief: do not proceed to the full capacitor-property dataset
(Phases 2-8) if there is no reproducible PCB resonance, no reproducible
position effect, and no reproducible orientation effect.

**Interpretation note**: this design treats the three checks as
independently gating — a "no-go" on *any one* of them is sufficient to stop
(standard practice for a validation gate: an experiment shouldn't proceed to
a full comparison campaign if any one of its foundational assumptions
hasn't checked out, even if the other two look fine). If a stricter reading
was intended (stop only if *all three* simultaneously fail), that changes
the gate significantly and should be corrected explicitly — flagging it here
rather than silently picking one.

### 1. Reproducible PCB resonance

- Phase 0 (S90-0603-R-01) establishes fr1, fr2, fr3 from a full broad sweep.
- Phase 1 does not repeat a full broad sweep on every other specimen (see
  `experiment_phases.md`). Instead, treat resonance as reproducible if the
  other two S90-0603-R specimens (R-02, R-03) show a clear, elevated
  acoustic response at or near fr1, fr2, and fr3 (the same set points
  already being measured in Phase 1's standard six-frequency set) relative
  to that session's background-noise floor.
- **Suggested check** (adjust to the noise floor actually observed —
  this number is a starting point, not a value given in the design brief):
  peak acoustic amplitude at each of fr1/fr2/fr3 is at least ~6 dB above
  the session's background-noise recording, for both R-02 and R-03.
- **No-go** if R-02 or R-03 shows no such elevated response at the expected
  set points (suggesting the resonance seen on R-01 was a one-off, not a
  property of the board design).

### 2. Reproducible position effect

- Compare S90-0603-R-01/02/03 (strong position) against
  W90-0603-R-01/02/03 (weak/control position) at the standard condition
  (0.10 V_peak, 0 V, standard six-frequency set).
- **Go** if S90 response is consistently higher than W90 response across the
  replicate pairs (matching the predicted ~4.9x strong/control ratio
  direction from `out/final_pcb_recommendation.txt` — the magnitude is a
  simulation guide only, not a pass/fail threshold; only the *direction and
  consistency* of the effect is being checked here).
- **No-go** if the S90/W90 difference is inconsistent across replicates or
  absent.

### 3. Reproducible orientation effect

- Compare S90-0603-R-01/02/03 (90 deg) against S0-0603-R-01/02/03 (0 deg,
  same position) at the standard condition.
- **Go** if S90 response is consistently higher than S0 response across the
  replicate pairs (matching the predicted ~1.8x orientation ratio direction
  from `out/final_pcb_recommendation.txt`, direction/consistency only, not a
  magnitude threshold).
- **No-go** if the S90/S0 difference is inconsistent across replicates or
  absent.

## Decision

- **Go**: all three checks pass. Proceed to Phase 2 onward per
  `experiment_phases.md` / `final_experiment_matrix.csv`.
- **No-go**: any check fails. Do not proceed to Phases 2-8. Instead:
  1. Re-check the electrical setup against `ELECTRICAL_MEASUREMENT_SETUP.md`
     (grounding, Kelvin sense wiring, mic position per
     `measurement_geometry.csv`).
  2. Re-check the physical mounting against `PCB_FABRICATION_SPEC.md`
     section 3 (compliant corner standoffs, not rigid clamping).
  3. Re-run Phase 1 once the above are confirmed.
  4. If still no-go after a confirmed re-run, this is a finding about the
     reduced-order model's applicability (README.md section 6, "Known
     limitations"), not just a setup error, and should be reported as such
     before any further boards/capacitors are purchased or tested.

## What this gate does not check

This gate validates the *board-level* behavior (resonance existence,
position sensitivity, orientation sensitivity) using the reference
capacitor only. It does not validate any capacitor-property comparison
(package, capacitance, rated voltage, dielectric) — those are exactly what
Phases 2-6 are for, and are only meaningful once this gate has passed.
