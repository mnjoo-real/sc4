# Singing capacitor — pre-experiment numerical model

## PCB ordering — start here

A validated PCB fabrication package for all 5 board variants exists under
[`pcb/`](pcb/). This section is a navigation index only — the files linked
below are the source of truth; nothing here duplicates their content.

**Start here:**
[`pcb/v0.3.1_FABRICATION_PACKAGE_SUMMARY.md`](pcb/v0.3.1_FABRICATION_PACKAGE_SUMMARY.md)

This is the top-level summary of the current PCB fabrication package and
records whether each board variant has passed the required KiCad/DRC/
Gerber/drill/visual checks.

For detailed per-board validation — including the authoritative
`READY_FOR_JLCPCB` status for each variant — see
[`pcb/FABRICATION_REVIEW.md`](pcb/FABRICATION_REVIEW.md). **Only order a
board whose entry there is marked ready.**

### The five board variants

    S90-0402
    S90-0603
    S90-0805
    W90-0603
    S0-0603

### Where the actual files are, per variant

| what | where | for |
|---|---|---|
| Editable KiCad source | `pcb/<variant>/<variant>.kicad_pcb` | opening/editing in KiCad |
| Raw Gerber + drill files | `pcb/<variant>/manufacturing/gerbers/` | inspection, not direct upload |
| **JLCPCB upload archive** | `pcb/<variant>/manufacturing/<variant>_JLCPCB_Gerber.zip` | **upload this to JLCPCB** |
| Gerber verification images | `pcb/<variant>/manufacturing/gerber_verification/` | checking the export against the design before ordering |
| KiCad 3D renders | `pcb/<variant>/renders/` | visual sanity-check, not fabrication input |

**The `*_JLCPCB_Gerber.zip` file is the file to upload to JLCPCB.** Do not
upload the `.kicad_pcb`/`.kicad_pro` source files, the PNG renders, or the
DRC/validation reports — those are for review, not fabrication input.

The five current upload archives:

- [`pcb/S90-0402/manufacturing/S90-0402_JLCPCB_Gerber.zip`](pcb/S90-0402/manufacturing/S90-0402_JLCPCB_Gerber.zip)
- [`pcb/S90-0603/manufacturing/S90-0603_JLCPCB_Gerber.zip`](pcb/S90-0603/manufacturing/S90-0603_JLCPCB_Gerber.zip)
- [`pcb/S90-0805/manufacturing/S90-0805_JLCPCB_Gerber.zip`](pcb/S90-0805/manufacturing/S90-0805_JLCPCB_Gerber.zip)
- [`pcb/W90-0603/manufacturing/W90-0603_JLCPCB_Gerber.zip`](pcb/W90-0603/manufacturing/W90-0603_JLCPCB_Gerber.zip)
- [`pcb/S0-0603/manufacturing/S0-0603_JLCPCB_Gerber.zip`](pcb/S0-0603/manufacturing/S0-0603_JLCPCB_Gerber.zip)

### Before ordering — read in this order

1. [`pcb/v0.3.1_FABRICATION_PACKAGE_SUMMARY.md`](pcb/v0.3.1_FABRICATION_PACKAGE_SUMMARY.md) — current fabrication-package summary.
2. [`pcb/FABRICATION_REVIEW.md`](pcb/FABRICATION_REVIEW.md) — detailed per-board validation, `READY_FOR_JLCPCB` status, and the Gerber/drill/render file map.
3. [`design/jlcpcb_order_settings.csv`](design/jlcpcb_order_settings.csv) — the JLCPCB fabrication options to select on the quote/order page (material, layers, thickness, copper weight, surface finish, etc.).
4. [`design/pcb_quantity_plan.csv`](design/pcb_quantity_plan.csv) — planned bare-PCB order quantities, per variant.
5. [`design/board_population_plan.csv`](design/board_population_plan.csv) — how the ordered boards are intended to be populated with MLCCs for the experiment.
6. [`design/PCB_FABRICATION_SPEC.md`](design/PCB_FABRICATION_SPEC.md) — detailed fabrication/design rationale and the common board specification.
7. [`design/PCB_CAD_ASSUMPTIONS.md`](design/PCB_CAD_ASSUMPTIONS.md) — fabrication/CAD parameters not originally fixed in v0.3.0, and the assumptions/fixes made while generating the KiCad files.

**⚠ Quantity check before the final order:** `pcb_quantity_plan.csv` is the
order-quantity source; `board_population_plan.csv` is the specimen
population source, and should be checked against it before the final
purchase. As of this writing they **do not agree for S90-0603**:
`board_population_plan.csv` calls for 15 populated S90-0603 specimens
(R×3, C1×2, C2×2, V1×2, V2×2, V3×2, N1×2), but
`pcb_quantity_plan.csv` currently plans to order only 5 S90-0603 boards.
The other four variants (S90-0402, S90-0805, W90-0603, S0-0603) agree
(5 planned = 5 needed each). Before placing the final order, verify that
the fabrication quantity plan covers the specimen population plan — this
README does not resolve that inconsistency, and the quantity was not
guessed here.

### Placing the order

1. Open `pcb/v0.3.1_FABRICATION_PACKAGE_SUMMARY.md`.
2. Confirm the desired board is marked ready in `pcb/FABRICATION_REVIEW.md`.
3. Open `design/jlcpcb_order_settings.csv`.
4. Open `design/pcb_quantity_plan.csv` (and cross-check against
   `board_population_plan.csv` per the warning above).
5. Upload that variant's `*_JLCPCB_Gerber.zip` to JLCPCB.
6. Confirm that JLCPCB correctly detects the board (outline, layer count,
   size).
7. Apply the fabrication options from `jlcpcb_order_settings.csv`.
8. Set the quantity from the current quantity plan.
9. Inspect the online Gerber preview (checklist below).
10. Only then proceed to fabrication/payment.

`design/jlcpcb_order_settings.csv` remains the source of truth for the
actual option selections — the JLCPCB UI's exact labels aren't reproduced
here.

### What to check in the JLCPCB Gerber viewer

Before paying, visually compare JLCPCB's preview against this repository's
verified artifacts and confirm, at minimum:

- board outline appears correct,
- four mounting holes are present,
- the MLCC footprint is present at the intended position,
- S90 vs. S0 orientation is visibly different where intended,
- top copper traces are present,
- there is no unexpected bottom copper,
- solder-mask openings are present over the intended pads,
- no obvious trace or outline is missing.

Reference images for this comparison:

- `pcb/<variant>/manufacturing/gerber_verification/` — most relevant for
  fabrication inspection, since these are rendered directly from the
  exported Gerbers:
  `<variant>_composite_top.png`, `<variant>_top_copper.png`,
  `<variant>_solder_mask.png`, `<variant>_silkscreen.png`,
  `<variant>_edge_cuts.png`
- `pcb/<variant>/renders/` — real KiCad top/bottom/perspective 3D renders
  (useful, but decorative relative to the Gerber-verification images above)
- [`pcb/PCB_5_VARIANT_COMPARISON.png`](pcb/PCB_5_VARIANT_COMPARISON.png) — all five variants at the same scale, for a quick overview

### Bare PCB vs. assembly

The `*_JLCPCB_Gerber.zip` files are **PCB fabrication files only**.
Uploading one orders a **bare PCB** — MLCC assembly is **not** included.
See [`design/board_population_plan.csv`](design/board_population_plan.csv)
for the intended capacitor population per board. Assembly (PCBA) is a
separate deliverable, not covered by this package.

### Directory map

```
pcb/
├── v0.3.1_FABRICATION_PACKAGE_SUMMARY.md
├── FABRICATION_REVIEW.md
├── PCB_5_VARIANT_COMPARISON.png
├── S90-0402/
│   ├── S90-0402.kicad_pcb
│   ├── manufacturing/
│   │   ├── S90-0402_JLCPCB_Gerber.zip   <- upload this to JLCPCB
│   │   ├── gerbers/
│   │   ├── drc_report.txt
│   │   ├── drill_report.txt
│   │   └── gerber_verification/
│   └── renders/
├── S90-0603/
├── S90-0805/
├── W90-0603/
└── S0-0603/
```

```
design/
├── jlcpcb_order_settings.csv
├── pcb_quantity_plan.csv
├── board_population_plan.csv
├── PCB_FABRICATION_SPEC.md
└── PCB_CAD_ASSUMPTIONS.md
```

---

A lightweight simulation for planning a *singing capacitor* experiment before
ordering the PCB and MLCCs.

The goal is **not** to predict the exact sound level of a commercial capacitor.
Instead, the model is used to decide:

- what PCB size and thickness to order,
- where to place the MLCC on the PCB,
- which orientation to use,
- what frequency range to sweep,
- and which conditions should produce a strong or weak vibration response.

The model deliberately keeps only the physics needed for those design choices.

---

## 1. The physics being modelled

A Class-II ceramic MLCC such as X5R or X7R deforms when an electric field is
applied. The first-order electromechanical model is

    S = dE + M E²

where `S` is strain, `d` is the piezoelectric coefficient, `M` is the
electrostrictive coefficient, and `E` is the electric field.

For

    E(t) = E_DC + E_AC cos(ωt)

the strain contains two important vibration components:

    A₁ cos(ωt),        A₁ = (d + 2 M E_DC) E_AC
    A₂ cos(2ωt),       A₂ = ½ M E_AC²

so an electrical excitation at frequency `f` can mechanically excite the PCB
at both

    f          fundamental
    2f         second harmonic

The second harmonic is important because it can hit a PCB resonance even when
the electrical excitation frequency itself does not.

For the first version of the simulation, the exact `d` and `M` of a commercial
MLCC are **not required**. The capacitor is treated as a relative vibration
source with configurable strengths at `f` and `2f`.

### PCB resonance

The PCB is approximated as a rectangular thin plate.

Its bending rigidity is

    D = E h³ / [12(1 − ν²)]

where `E` is the effective Young's modulus of the PCB, `h` is PCB thickness,
and `ν` is Poisson's ratio.

For a simply supported rectangular plate with length `a` and width `b`,

    φ_mn(x,y) = sin(mπx/a) sin(nπy/b)

and the natural frequencies are

    ω_mn = π² √(D / ρh) · (m²/a² + n²/b²)

    f_mn = ω_mn / 2π

This is not intended to reproduce a real clamped PCB exactly. It is sufficient
for finding the main trends:

- a larger PCB gives lower resonant frequencies,
- a thicker PCB gives higher resonant frequencies,
- different MLCC positions couple differently to each mode.

### MLCC position and orientation

The MLCC does not excite every PCB mode equally.

For a simple point-force source,

    coupling ∝ φ_mn(x_c, y_c)

so a capacitor near a modal antinode excites that mode strongly, while one near
a node excites it weakly.

The soldered MLCC also acts approximately like a small force couple / moment.
For that case the coupling is related to the slope of the mode shape:

    x-oriented MLCC:  coupling ∝ ∂φ_mn/∂x
    y-oriented MLCC:  coupling ∝ ∂φ_mn/∂y

This is why rotating the same MLCC by 90° can change the PCB vibration.

The simulation therefore focuses on the chain

    voltage
      ↓
    relative MLCC source at f and 2f
      ↓
    PCB mode coupling
      ↓
    PCB vibration response

rather than trying to model every internal ceramic layer.

---

## 2. What the code actually does

### MLCC source (`source.py`)

The capacitor is represented by two harmonic source components:

    source_f  = C₁ · A₁
    source_2f = C₂ · A₂

For the initial model, `C₁` and `C₂` are simply configurable scale factors.

If real electromechanical coefficients are unavailable, the code can instead
use normalized source strengths such as

    source_f  = 1
    source_2f = r_harmonic

so PCB design can be studied independently of the uncertain absolute MLCC
vibration amplitude.

The important output is therefore **relative response**, not absolute SPL.

### PCB (`plate.py`)

The PCB is an isotropic rectangular thin plate with configurable

    length
    width
    thickness
    Young's modulus
    density
    Poisson ratio
    damping

The code computes the first several `(m,n)` modes analytically.

The default reference geometry is the one used in Kim et al. (2019):

    100 mm × 40 mm × 1.0 mm

This is only a baseline. The simulation sweeps several nearby geometries to find
a board that has clear resonances in the experimental frequency range.

### Coupling (`coupling.py`)

For each candidate MLCC position and orientation, the code evaluates how
strongly the source couples to every PCB mode.

The main scan is

    x/a = 0.20, 0.35, 0.50, 0.65, 0.80
    y/b = 0.25, 0.50, 0.75
    orientation = 0°, 90°

This produces both

- a **high-coupling position** for a clear singing-capacitor demonstration,
- and a **low-coupling position** that can be used as a control.

### Frequency response (`response.py`)

Each PCB mode is treated as a damped harmonic oscillator:

    q_n(ω) =
        Q_n /
        [m_n(ω_n² − ω² + i 2ζ_n ω_n ω)]

The modal responses are summed to obtain relative PCB displacement and velocity.

The simulation evaluates the response at both

    f
    2f

for each electrical excitation frequency.

The main plotted quantity is PCB velocity amplitude, used only as a
**vibration / acoustic-noise proxy**.

No acoustic radiation model is included.

### Sweep (`run_sweep.py`)

The first design sweep varies

    PCB length       60, 80, 100 mm
    PCB width        30, 40 mm
    PCB thickness    0.8, 1.0, 1.6 mm

and scans excitation frequencies over

    200–3000 Hz

with a coarse step first, followed by a finer scan near predicted resonances.

After the PCB geometry is selected, the code scans MLCC position and orientation.

The simulation is therefore used in this order:

    1. choose PCB geometry
    2. find PCB resonances
    3. choose MLCC position
    4. compare 0° and 90° orientation
    5. choose useful excitation frequencies
    6. define strong-response and weak-response experimental conditions

---

## 3. Validation (`test_model.py`)

The model only needs simple checks because it is an experiment-design tool, not
a high-fidelity FEM solver.

| check | expected result |
|---|---|
| increasing PCB length | resonant frequencies decrease |
| increasing PCB thickness | resonant frequencies increase |
| mode shape at supported edge | approximately zero |
| MLCC placed at a modal node | weak point-force coupling |
| MLCC placed at an antinode | strong point-force coupling |
| rotate MLCC by 90° | x/y moment coupling changes |
| increase damping | resonance peak becomes lower and broader |
| electrostrictive source | response can appear at `2f` |

The code should also reproduce the analytical strain amplitudes

    A₁ = (d + 2 M E_DC) E_AC
    A₂ = ½ M E_AC²

for a synthetic test case.

Synthetic coefficients are used only to check the equations; they must not be
presented as properties of a real commercial MLCC.

---

## 4. Outputs

### `fig1_modes.png`

The first PCB mode shapes and their natural frequencies for the baseline

    100 × 40 × 1 mm

board.

This shows which PCB modes lie inside the planned excitation range.

### `fig2_geometry_sweep.png`

Predicted resonant frequencies for different PCB sizes and thicknesses.

This is the main figure for deciding **which PCB to order**.

A useful board should have:

- at least a few resonances inside the measurable frequency range,
- resonances separated enough to identify experimentally,
- and no extreme sensitivity to small geometry changes.

### `fig3_frequency_response.png`

Relative PCB vibration versus electrical excitation frequency.

Both mechanical components are shown:

    response at f
    response at 2f

A strong peak occurs when either `f` or `2f` approaches a PCB resonance.

This figure determines which frequency ranges should be scanned more densely in
the real experiment.

### `fig4_position_map.png`

Heatmap of predicted vibration versus MLCC position.

This is used to choose

- one high-response capacitor location,
- one low-response control location.

### `fig5_orientation.png`

Comparison of the same MLCC position at

    0°
    90°

to determine whether orientation should be included as an experimental variable.

### `recommended_setup.csv`

Final summary produced by the sweep:

| parameter | recommended value |
|---|---|
| PCB length | simulation result |
| PCB width | simulation result |
| PCB thickness | simulation result |
| MLCC x-position | simulation result |
| MLCC y-position | simulation result |
| MLCC orientation | simulation result |
| main frequency range | simulation result |
| resonance frequencies | simulation result |
| strong-response condition | simulation result |
| control condition | simulation result |

The code should not fill this table with hard-coded recommendations. Values are
written only after the sweep has been run.

---

## 5. Running it

```bash
pip install numpy scipy matplotlib pandas

python test_model.py
python run_modes.py
python run_sweep.py geometry
python run_sweep.py position
python run_sweep.py all
```

All figures and tables are written to

```text
out/
```

Suggested repository structure:

```text
singing-capacitor/
│
├── README.md
├── model.py
├── source.py
├── plate.py
├── coupling.py
├── response.py
├── test_model.py
├── run_modes.py
├── run_sweep.py
└── out/
```

The main parameters should be collected in one dataclass:

```python
from dataclasses import dataclass

@dataclass
class Params:
    pcb_L: float = 0.100
    pcb_W: float = 0.040
    pcb_h: float = 0.001

    E_pcb: float = 20e9
    rho_pcb: float = 1850.0
    nu_pcb: float = 0.13
    damping: float = 0.02

    mlcc_x_frac: float = 0.50
    mlcc_y_frac: float = 0.50
    orientation_deg: float = 0.0

    f_min: float = 200.0
    f_max: float = 3000.0
```

The exact effective FR-4 material constants are uncertain, so these values are
configuration parameters rather than fixed physical truths.

---

## 6. Known limitations — worth stating in a report

* The PCB is an **isotropic simply supported thin plate**. A real FR-4 PCB is
  anisotropic and the experimental bolts/clamps change its natural frequencies.
  The model should therefore be used for geometry selection and qualitative
  trends, not exact resonance prediction.

* The MLCC is represented as a **lumped harmonic source**, not as hundreds of
  dielectric and electrode layers. This is deliberate: the purpose is to choose
  the experimental PCB and setup before the exact commercial MLCC properties
  are known.

* Exact piezoelectric and electrostrictive coefficients of commercial MLCCs are
  usually unavailable. Unless experimentally measured values are supplied, the
  simulation should compare **relative source amplitudes**, not claim absolute
  capacitor vibration.

* Solder geometry is not explicitly modelled. Its effect is absorbed into the
  equivalent source / moment coupling.

* The first model does not calculate sound pressure. PCB velocity is used as a
  proxy for how strongly the board is likely to radiate sound.

* Absolute resonance frequencies will shift after the real PCB is manufactured
  and mounted. After the first PCB is measured, the effective material and
  damping parameters can be calibrated and the simulation rerun.

---

## 7. What this simulation must decide before ordering

The model is successful if it answers these practical questions:

1. Should the PCB be approximately `60`, `80`, or `100 mm` long?
2. Should its thickness be `0.8`, `1.0`, or `1.6 mm`?
3. Which resonances fall inside the planned excitation range?
4. Where should the MLCC be soldered for a strong response?
5. Where should a control MLCC be soldered for a weak response?
6. Does rotating the MLCC by 90° produce a useful difference?
7. Which electrical frequencies should be scanned densely in the real test?
8. Is the response dominated by the fundamental `f`, the second harmonic `2f`,
   or both?

Once these are answered, the PCB can be ordered and the detailed MLCC
comparison can be designed around the selected board.

The key principle is:

    keep the model only as complicated as necessary
    to make the experimental setup decision.
