# Run protocol — v0.3.0-D

Operating procedure for a measurement session, built on
`ELECTRICAL_MEASUREMENT_SETUP.md`. Follow this in order.

## 1. Before any session

- [ ] Confirm grounding: generator ground = DRIVE- = oscilloscope reference.
      Protective earth intact on every mains-powered instrument — do not
      float the scope (`ELECTRICAL_MEASUREMENT_SETUP.md` section 8).
- [ ] Confirm the board under test and the capacitor mounted on it against
      `experiment_matrix_template.csv` / `pcb_coordinates.csv`.
- [ ] Confirm the capacitor's rated voltage is on hand, and pre-check the
      voltage budget for every level combination you intend to run:
      `|Vdc| + Vac_peak <= rated voltage`. Cross out any combination that
      fails this before starting.
- [ ] Position the microphone per `measurement_geometry.csv` (100 mm above
      PCB center, pointing down at the board). Do not reposition it between
      runs or between board variants within a session.
- [ ] If this is a commissioning session using the 0.1 ohm shunt, treat it
      as a separate step per `ELECTRICAL_MEASUREMENT_SETUP.md` section 9 —
      do not leave the shunt in place for normal data-collection runs.

## 2. Session start — background noise

- [ ] With the function generator **off**, record at least **10 s** of
      background noise from the microphone.
- [ ] Save it and note its `background_reference_id` (see `data_schema.csv`)
      — every acoustic amplitude recorded in this session is compared
      against this noise floor.

## 3. Stage 1 — broad resonance search (per board)

For the board under test, run both bands from `excitation_plan.csv`:

| band | range | step |
|---|---|---|
| low | 200-3000 Hz | 25 Hz |
| high | 3000-20000 Hz | 100 Hz |

- Start at the lowest excitation level (0.05 V_peak, Vdc=0). Escalate only
  if the microphone signal-to-noise is insufficient to see peaks — and if
  you do escalate, re-check the `I_peak` estimate (section 3 of
  `ELECTRICAL_MEASUREMENT_SETUP.md`) stays approximately <= 25 mA where
  practical, and re-check the voltage budget.
- At each frequency point, follow the per-frequency-point procedure
  (section 5 below).
- Watch for the amplifier-fallback triggers (amplitude collapse, clipping,
  current-limit behavior) throughout — see section 6 of
  `ELECTRICAL_MEASUREMENT_SETUP.md`. If observed, stop and flag for review;
  do not proceed to add an amplifier without that review.
- After the sweep, identify candidate resonances `fr` from the recorded
  acoustic amplitude vs. frequency curve. This stage is for locating
  resonances only — do not draw capacitor-comparison conclusions from it.

## 4. Stage 2 — dense scan (per measured resonance, per board)

For each `fr` identified in Stage 1, on that same board:

- scan `fr - 100 Hz` to `fr + 100 Hz`, step 2-5 Hz,
- scan `fr/2 - 100 Hz` to `fr/2 + 100 Hz`, step 2-5 Hz (2f electrostrictive
  excitation check),
- at whatever excitation level(s) the current phase of testing calls for
  (see `experiment_matrix_template.csv` for the planned reference-vs-
  candidate schedule), re-checking the voltage budget and `I_peak` guidance
  for each level used.

## 5. Per-frequency-point procedure

At every individual frequency point in Stage 1 or Stage 2:

1. Set the condition (frequency, Vac_peak, Vdc).
2. Settle **0.5 s**.
3. Record **2.0 s**.
4. Save the raw microphone waveform.
5. Extract the measured DUT voltage from the SENSE+/SENSE- capture
   (`V_DUT = CH1 - CH2`, or CH1 alone if only one channel is captured —
   see `ELECTRICAL_MEASUREMENT_SETUP.md` section 1).
6. Extract acoustic amplitude at `f`.
7. Extract acoustic amplitude at `2f`.
8. Log the row per `data_schema.csv`.

## 6. Test order across boards and capacitors

Per `pcb_variants.md` / `PRE_PURCHASE_DESIGN.md`:

1. Reference MLCC on **S90 (all 3 footprints), W90-0603, S0-0603** — Stage 1
   then Stage 2 on each — to validate the simulated position and
   orientation effects before testing anything else.
2. Only after that validation, test candidate capacitors (`TBD-1`,
   `TBD-2`, ...) primarily on the **S90** variants (Stage 1 then Stage 2
   each).

## 7. After each session

- [ ] Confirm every raw waveform file referenced in the session's log rows
      actually exists and is non-empty.
- [ ] Confirm the background-noise recording for the session is saved and
      linked (`background_reference_id`).
- [ ] Note in `notes` any deviation from this protocol (extra settle time,
      re-runs, amplifier-fallback flags, shunt commissioning steps, etc.).
