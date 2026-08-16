# PCB variants — v0.3.0 pre-purchase design

This document defines the three physical PCB variants to order, based on the
v0.2.0 simulation result (`out/final_pcb_recommendation.txt`,
`out/pcb_candidate_comparison.csv`):

- PCB outline: **100 mm x 40 mm**, thickness **1.0 mm**
- predicted strong position: `x/a=0.50, y/b=0.25`, orientation 90 deg
- predicted weak/control position: `x/a=0.20, y/b=0.50`, orientation 90 deg
- predicted strong/control response ratio: **4.9x**
- predicted 0 deg / 90 deg orientation response ratio: **1.8x** (90 deg stronger)
- predicted resonances: **1090, 1541, 2293 Hz** (modes (1,1), (2,1), (3,1))

These numbers come from the existing reduced-order model (isotropic
simply-supported thin plate + lumped MLCC source, see `README.md`). They are
**guides for where to place the MLCC and which frequencies to scan first**,
not exact experimental predictions. The real resonances, once clamped/mounted
and manufactured, will shift from these values — see "Known limitations" in
`README.md` section 6.

## Common specification (all three variants)

All three boards share everything except MLCC placement and orientation, so
that any measured difference between boards can be attributed to position /
orientation rather than to an uncontrolled difference in the board itself.

- **Outline**: 100 mm x 40 mm rectangular PCB.
- **Thickness**: 1.0 mm PCB stack-up (spec thickness; actual manufactured
  thickness should be recorded per board once received, since resonances
  depend on it).
- **Mounting scheme**: support the board at its four corners on compliant
  (soft rubber / foam) point standoffs, not rigid clamps or screws directly
  into the copper. A compliant point support at the corners approximates the
  simply-supported boundary condition assumed by the model far better than a
  rigid clamp, which stiffens the edges and shifts resonances upward
  unpredictably. Mount all three boards identically.
- **Electrical connection strategy**: bring drive leads in at one short edge
  of the board, away from the MLCC, using thin flexible lead wire
  (30-32 AWG). Anchor the wires near the edge with a small dab of adhesive
  or tape for strain relief. This keeps the added mass/stiffness/damping of
  the wiring away from the vibrating region, per the "wires near the edge,
  not near the MLCC" principle below.
- **Test-pad strategy**: provide two dedicated test pads immediately at the
  MLCC solder joints (Kelvin-style, i.e. separate from the current-carrying
  drive pads where practical) for direct oscilloscope probing of the actual
  DUT voltage. Do not rely on the function-generator's displayed voltage —
  see the "DUT voltage" principle below.

## Variant S90 — primary strong-response board

- MLCC center: **x = 50 mm, y = 10 mm** (`x/a=0.50, y/b=0.25`)
- Orientation: **90 deg**
- Purpose: the primary board for the singing-capacitor demonstration and for
  comparing candidate MLCCs. Predicted to produce the strongest vibration
  response of the three variants.
- This is the board that receives the full excitation sweep (broad, then
  dense) and that every capacitor-property candidate is tested on.

## Variant W90 — position-control board

- MLCC center: **x = 20 mm, y = 20 mm** (`x/a=0.20, y/b=0.50`)
- Orientation: **90 deg**
- Purpose: same orientation as S90, but placed near a predicted low-coupling
  position. Used with the reference MLCC only, to validate that the
  simulated ~4.9x strong/control contrast actually shows up experimentally.
  A "weak" board that still sings strongly would indicate the coupling
  model, not just its absolute predictions, needs revisiting.

## Variant S0 — orientation-control board

- MLCC center: **x = 50 mm, y = 10 mm** (`x/a=0.50, y/b=0.25`) — identical
  position to S90
- Orientation: **0 deg**
- Purpose: isolates the effect of MLCC orientation from position, holding
  position fixed at the S90 site. Used with the reference MLCC only, to
  validate the simulated ~1.8x orientation contrast (90 deg stronger than
  0 deg at this position).

See `pcb_coordinates.csv` for the machine-readable version of this table.

## Experimental principles (apply to all variants and all runs)

- **Wire placement**: external wires attach near the PCB edge, not near the
  vibrating MLCC — added mass, stiffness, and damping from the wiring would
  otherwise distort the very vibration being measured.
- **DUT voltage**: measure the voltage directly across the capacitor (at the
  dedicated test pads), not the function-generator's dial/display setting.
  Cable impedance, contact resistance, and the capacitor's own reactive
  loading mean the function-generator setting is not necessarily the actual
  MLCC voltage.
- **Drive current**: account for the capacitive drive current
  `I_peak = 2 * pi * f * C * V_peak`. This current rises linearly with
  frequency and with the MLCC's capacitance, and can be substantial at the
  top of the swept range for a large-capacitance MLCC — check it against the
  function generator's/amplifier's output current limit before driving at
  the higher end of the 200-3000 Hz range or at high V_peak.
- **Sweep order**: first perform a broad experimental frequency sweep
  (200-3000 Hz) to find the actual PCB resonances, since the simulated
  1090/1541/2293 Hz values are guides only. Then perform dense sweeps
  centered on the measured resonances, and separately around half those
  frequencies, to test for possible 2f electrostrictive excitation.
- **Reference vs. candidate testing**: use one reference MLCC on S90, W90,
  and S0 to validate the simulated position and orientation effects. Test
  all other capacitor-property candidates primarily on S90, once the
  reference measurements confirm the board behaves as predicted.
- **No part numbers yet**: candidate capacitors are referred to only as
  placeholders (e.g. `TBD-1`, `TBD-2`) until the board-level behavior above
  has been validated experimentally. Do not commit to specific commercial
  MLCC part numbers at this stage.

See `PRE_PURCHASE_DESIGN.md` for the full pre-purchase rationale and
`excitation_plan.csv` / `experiment_matrix_template.csv` for the runnable
sweep and logging plan.
