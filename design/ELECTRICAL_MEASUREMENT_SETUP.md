# Electrical drive and measurement setup — v0.3.0-D

This is the electrical and measurement protocol for the pre-purchase
experimental design. It does not change the numerical model or the v0.2.0
simulation results (`out/`), and it does not change the PCB fabrication
spec (`PCB_FABRICATION_SPEC.md`) — it defines how those boards are driven
and measured once built.

## 1. Drive architecture

```
Function generator (DC-coupled output, Vdc offset + Vac_peak)
    OUT+ ----> DRIVE+ pad ----> MLCC (+ terminal)
    OUT- ----> DRIVE- pad ----> MLCC (- terminal) ----> common ground
                                                          = generator ground
                                                          = oscilloscope reference

Kelvin sense taps at the MLCC pads (see PCB_FABRICATION_SPEC.md section 5):
    MLCC (+ terminal) ----> SENSE+ pad ----> scope CH1
    MLCC (- terminal) ----> SENSE- pad ----> scope CH2

    V_DUT(t) = CH1(t) - CH2(t)     preferred, when 2 channels are captured
    V_DUT(t) ~= CH1(t)             acceptable if only 1 channel is available,
                                    since DRIVE- = ground and SENSE- should
                                    sit within a small tolerance of 0 V;
                                    verify that tolerance at least once per
                                    session by capturing SENSE- alone
```

The direct function-generator drive shown above is the default and baseline
for every run in this design. **No external power amplifier is used unless
the measured DUT voltage waveform shows amplitude collapse, clipping, or
current-limit behavior** (see section 6 for how to recognize that, and
section 8 for the fallback amplifier spec — not a selection or purchase).

## 2. Voltage convention

**All stored AC amplitudes use V_peak, not V_pp and not V_rms.** Record and
report V_peak consistently across every file in this design package.

Initial excitation levels to step through, in order (start at the lowest and
escalate only as the protocol calls for it):

| Vac_peak (V) | Vdc (V) |
|---|---|
| 0.05 | 0 |
| 0.10 | 1 |
| 0.25 | 2 |
| 0.50 | 2.8 |

These are independent lists (any Vac_peak may be paired with any Vdc), not a
fixed 1:1 pairing — subject to the voltage-budget rule below.

**The experimental voltage is the actual measured `V_DUT` (from the SENSE
traces), not the function-generator's displayed setting.** Cable/contact
resistance and the capacitor's own reactive loading mean the two are not
guaranteed to match, especially as frequency and drive current rise.

### Voltage budget (hard rule)

```
|Vdc| + Vac_peak  <=  capacitor rated voltage
```

Check this **before** every run, using the *planned* generator setting (as
a conservative pre-check) and again using the *measured* `V_DUT` once
captured. Do not drive a condition that violates this for the capacitor
under test. Example: the most extreme combination in the table above,
Vdc=2.8 V with Vac_peak=0.50 V, requires |Vdc|+Vac_peak = 3.3 V of rated
voltage headroom — skip that combination for any capacitor rated below
3.3 V.

## 3. Drive current

```
I_peak = 2 * pi * f * C * V_peak
```

Estimate `I_peak` for the capacitor's nominal `C` before every sweep,
across the frequency and voltage range about to be run, and compare against
the guidance in section 5. Worked example at `V_peak = 0.50 V` (the highest
initial level) for illustrative generic capacitance values (not specific
part numbers):

| C | I_peak @ 200 Hz | I_peak @ 3000 Hz | I_peak @ 20000 Hz |
|---|---|---|---|
| 1 nF | 0.001 mA | 0.009 mA | 0.063 mA |
| 10 nF | 0.006 mA | 0.094 mA | 0.628 mA |
| 100 nF | 0.063 mA | 0.942 mA | 6.283 mA |
| 1 uF | 0.628 mA | 9.425 mA | 62.832 mA |
| 10 uF | 6.283 mA | 94.248 mA | 628.319 mA |

A 1 uF-class capacitor crosses the 25 mA Stage-1 guideline (section 5)
around ~8 kHz at 0.50 V_peak — well inside the 3-20 kHz high band. This is
exactly the kind of condition the direct-drive-by-default policy is meant
to catch: if the measured `V_DUT` waveform collapses or clips near there,
that is the trigger to consider the fallback amplifier, not to keep pushing
the function generator past its comfortable output range.

## 4. Acoustic and vibration measurement

**Primary measurement — calibrated microphone:**

- calibrated measurement microphone, sensitivity/calibration on file,
- positioned 100 mm vertically above PCB center, pointing down at the
  board,
- identical position and fixture for every run and every board variant
  (see `measurement_geometry.csv` — the mic tracks PCB center, not MLCC
  position, so board-to-board comparisons are not confounded by a moving
  microphone).

**Optional validation — LDV:** a laser Doppler vibrometer may be used for
spot validation of the model's mechanical-velocity prediction, independent
of the acoustic path. Not required for any baseline run.

**Not required in the baseline:** an accelerometer is not required. Adding
one later is a possible extension, not part of this design.

## 5. Frequency protocol

### Stage 1 — broad resonance search

| band | range | step |
|---|---|---|
| low | 200-3000 Hz | 25 Hz |
| high | 3000-20000 Hz | 100 Hz |

- Use the lowest available excitation level (0.05 V_peak) by default;
  escalate only if signal-to-noise in the microphone recording is
  insufficient to identify peaks.
- Keep peak current approximately <= 25 mA where practical (check with the
  `I_peak` formula above against the capacitor actually mounted).
- This scan is for **locating resonances only** — it is not a quantitative
  capacitor comparison. Do not draw capacitor-property conclusions from
  Stage-1 amplitudes.

### Stage 2 — dense scan

For every resonance `fr` found in Stage 1, on that same board:

- scan `fr +/- 100 Hz`, 2-5 Hz step,
- also scan around `fr / 2` (same +/-100 Hz window and 2-5 Hz step), to
  test for second-harmonic (2f) electrostrictive excitation.

See `excitation_plan.csv` for the per-board Stage 1 bands and the
parametrized Stage 2 rule (Stage 2 bands are centered on the *measured*
`fr`, which is not known until Stage 1 has been run on that board).

## 6. Per-frequency-point procedure

1. Set the condition (frequency, Vac_peak, Vdc).
2. Settle 0.5 s.
3. Record 2.0 s.
4. Save the raw microphone waveform.
5. Extract the measured DUT voltage (from the SENSE+/SENSE- capture).
6. Extract acoustic amplitude at `f`.
7. Extract acoustic amplitude at `2f`.

See `data_schema.csv` for the exact fields this produces and
`run_protocol.md` for the full session-level procedure this step sits
inside of.

### Amplifier-fallback trigger

Stop and flag for review (do not automatically add an amplifier — this
design only records the fallback spec, per section 8) if, while direct-driving
from the function generator, any of the following is observed in the
measured `V_DUT` waveform:

- **amplitude collapse**: measured `V_DUT` amplitude fails to track the
  commanded generator level as frequency or drive level increases (e.g.
  drops by a large fraction of the expected value with no corresponding
  drop in generator setting),
- **clipping**: the captured waveform is visibly flat-topped rather than
  sinusoidal,
- **current-limit behavior**: the function generator indicates an overload
  / current-limit condition, or `V_DUT` fails to rise with generator
  amplitude at the top of its range.

## 7. Background noise

At the start of **every measurement session**, before any board is driven:

- record at least 10 s of background noise from the microphone with the
  function generator off.

Store this alongside the session's data (see `data_schema.csv`,
`background_reference_id`) so every measured acoustic amplitude in that
session can be compared against the actual noise floor it was taken
against.

## 8. Grounding

- Generator ground = DRIVE- = oscilloscope reference. This is a single
  shared ground node for the baseline (direct function-generator drive)
  setup.
- **Do not float a grounded oscilloscope by disconnecting protective
  earth.** This is a shock hazard and is not needed here, since the
  baseline drive is not floating.
- **If a future floating amplifier is introduced, require a proper
  differential or isolated measurement method** (isolated probe, isolated
  scope input, or a true differential probe across SENSE+/SENSE-) instead
  of lifting ground on any instrument. This design does not select or use
  a floating amplifier.

## 9. Commissioning-only current shunt

An optional 0.1 ohm low-side shunt may be inserted in the DRIVE- return
path **for commissioning only**, to cross-check `I_peak` against the
predicted value from section 3.

**Caveat:** inserting the shunt breaks the "DRIVE- = ground" identity that
the single-ended `V_DUT` measurement in section 1 relies on — the shunt's
own voltage drop appears between true generator ground and the board's
DRIVE-/SENSE- node while current flows. Treat shunt-based current
measurement as a **separate calibration step**: measure directly across the
shunt for that step, then remove the shunt before resuming normal
`V_DUT` / acoustic data collection runs.

## 10. Files in this directory (v0.3.0-D)

| file | contents |
|---|---|
| `ELECTRICAL_MEASUREMENT_SETUP.md` | this file |
| `equipment_requirements.csv` | instrumentation list, required vs. optional, key specs |
| `excitation_plan.csv` | Stage 1 / Stage 2 frequency-sweep plan (updated to the 200 Hz-20 kHz, fr +/-100 Hz protocol) |
| `measurement_geometry.csv` | microphone (and optional LDV) position relative to PCB center |
| `run_protocol.md` | full session-level operating procedure |
| `data_schema.csv` | field-by-field schema for the recorded per-run / per-frequency-point data |

## 11. Open items — not decided here

- No external amplifier is selected or purchased; only its fallback spec is
  recorded (the "external power amplifier (fallback only)" row of
  `equipment_requirements.csv`).
- No commercial MLCC part numbers are chosen; capacitor identity remains
  `REF` / `TBD-n` per `experiment_matrix_template.csv`.
- Exact microphone/preamp model, oscilloscope model, and function generator
  model are equipment decisions left to `equipment_requirements.csv`'s
  spec rows, not fixed here.
