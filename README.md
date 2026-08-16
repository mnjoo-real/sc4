# Singing Capacitor Pre-Experiment Simulation

## Purpose

This repository is a **pre-experiment simulation framework for MLCC (multilayer ceramic capacitor) acoustic-noise experiments**.

The immediate goal is **not** to predict absolute sound-pressure level (SPL) with high accuracy. The goal is to use a physics-based reduced-order model to decide, *before purchasing parts*, which combinations of:

- MLCC dielectric class,
- capacitance,
- package size,
- rated voltage,
- PCB geometry,
- MLCC position and orientation,
- DC bias,
- AC amplitude, and
- excitation frequency

are most informative to test experimentally.

The simulation should help answer three practical questions:

1. Under which electrical conditions is MLCC electromechanical excitation expected to become large?
2. Under which PCB geometries and placements does that excitation couple strongly to PCB resonance?
3. What is the smallest practical set of MLCCs and PCBs that still allows major experimental factors to be separated?

This project should therefore be treated primarily as an **experiment-design and candidate-screening tool**, not as a production-grade acoustic solver.

---

# 1. Instructions for the Coding Agent

This README is intended to be sufficiently explicit for an autonomous coding agent such as Claude Code.

## 1.1 Implementation priorities

Implement the project in this order:

1. Reproduce the electromechanical strain equations.
2. Verify the expected fundamental and second-harmonic behavior numerically.
3. Implement an analytical rectangular-plate modal model.
4. Reproduce literature benchmark geometries.
5. Add frequency, voltage, PCB-geometry, position, and orientation sweeps.
6. Add an equivalent mechanical-source abstraction.
7. Rank candidate experimental conditions.
8. Only after the reduced-order model is validated, consider higher-fidelity FEM or acoustic-radiation modeling.

Do **not** start with full 3D FEM.

## 1.2 Do not invent missing material parameters

Commercial MLCC datasheets generally do not provide all of the following:

- dielectric-layer thickness,
- number of active layers,
- active-region geometry,
- $d_{31}$, $d_{33}$,
- $M_{31}$, $M_{33}$,
- effective electromechanical source moment.

If a required parameter is not available from a literature benchmark or an explicitly provided dataset:

- expose it as a configuration parameter,
- assign it a clearly labeled placeholder or normalized value,
- run sensitivity analysis if appropriate,
- never silently fabricate a “realistic” constant,
- never claim SKU-level absolute prediction from such a placeholder.

All outputs must distinguish:

- **literature-derived values**,
- **user-configured assumptions**,
- **normalized/model parameters**, and
- **post-experiment calibrated parameters**.

## 1.3 Units

Use SI units internally.

Recommended conventions:

```text
length              m
frequency           Hz
angular frequency   rad/s
voltage             V
electric field      V/m
strain              dimensionless
force               N
moment              N·m
mass                kg
velocity            m/s
Young's modulus     Pa
density             kg/m^3
```

Configuration files may accept convenient engineering units such as `mm`, `uF`, or `V`, but conversion to SI must occur at the input boundary.

## 1.4 Reproducibility

Every sweep must write the exact configuration used to the result directory.

Each run should record at least:

```text
timestamp
git commit if available
input configuration
model version
assumption set
random seed if any
output file paths
```

The core model should be deterministic unless stochastic uncertainty analysis is explicitly enabled.

---

# 2. Physical Model Overview

The singing-capacitor phenomenon is modeled as the following chain:

```text
Applied voltage
      ↓
Electric field inside the dielectric
      ↓
Piezoelectric + electrostrictive strain
      ↓
MLCC body deformation
      ↓
Force / moment transmitted through solder joints
      ↓
PCB modal vibration
      ↓
Air radiation
      ↓
Acoustic noise
```

The first implementation should contain three submodels:

```text
[Model A] MLCC electromechanical model
        ↓
[Model B] Equivalent mechanical-source model
        ↓
[Model C] PCB modal-response model
```

A full acoustic-radiation model is intentionally deferred.

---

# 3. Literature Basis

The simulation architecture is based on the following literature.

## 3.1 Kim, Kim, and Kim (2019)

**Dynamic analysis of multilayer ceramic capacitor for vibration reduction of printed circuit board**

DOI: `10.1007/s12206-019-0311-4`

Use this paper primarily for **Model A**.

Relevant concepts:

- BaTiO$_3$-based MLCC strain modeled as the sum of piezoelectric and electrostrictive contributions.
- Separation of the fundamental and second-harmonic strain components under combined AC and DC excitation.
- Effective piezoelectric coefficient under DC bias.
- Relationship between MLCC body deformation, solder reaction forces, and PCB vibration.
- Importance of PCB mode shape and MLCC structural geometry.
- Reference MLCC:
  - X5R
  - $10\,\mu\text{F}$
  - 0402 / 1005 metric
  - body dimensions approximately $1.0 \times 0.5 \times 0.5$ mm.
- Reference PCB geometry:
  - $100 \times 40 \times 1$ mm.

This paper is the primary source for the electromechanical equations in Sections 4–7.

---

## 3.2 Ko et al. (2017)

**Identification of the electromechanical material properties of a multilayer ceramic capacitor**

DOI: `10.1111/ijac.12649`

Use this paper conceptually for later parameter identification.

Relevant concept:

- Piezoelectric and electrostrictive coefficients can be separated using measured fundamental and second-harmonic vibration components.

This becomes important after experimental data are available and the model is calibrated.

---

## 3.3 Ohm et al. (2018)

**Control of electromechanical properties of multilayer ceramic capacitors for vibration reduction**

DOI: `10.1111/jace.15358`

Relevant concepts:

- Class-II ferroelectric MLCC vibration is controlled by electromechanical material properties.
- Piezoelectric and electrostrictive contributions have different voltage dependence.
- Material-level electromechanical behavior strongly affects vibration.

---

## 3.4 Yan et al. (2023)

**A Methodology for Predicting Acoustic Noise From Singing Capacitors in Mobile Devices**

DOI: `10.1109/TEMC.2023.3280922`

Use this paper primarily for the architecture of **Model C**.

Relevant concepts:

- Represent the PCB as a modal mechanical system.
- Evaluate harmonic response using modal superposition.
- Treat total capacitor-noise prediction as a chain combining:
  1. electrical excitation,
  2. MLCC electrical-to-mechanical conversion, and
  3. PCB vibration transfer.

---

## 3.5 Ding et al. (2024)

**Multilayer Ceramic Capacitor Vibration Source Model Library Development**

DOI: `10.1109/TEMC.2024.3397610`

Use this paper primarily for **Model B**.

Relevant concepts:

- Avoid modeling hundreds of internal MLCC layers for every commercial component.
- Replace the detailed MLCC with an **equivalent mechanical moment source** acting through the mounting region.
- Parameterize source strength as a function of:
  - frequency,
  - DC bias,
  - AC amplitude.
- Use a source-model library for candidate screening.

This is highly aligned with the purpose of this repository.

---

## 3.6 Kim et al. (2024)

**Acoustic-noise reduction in printed circuit boards based on location and direction of multilayer ceramic capacitors**

DOI: `10.1007/s12206-024-0704-x`

Relevant concept:

- MLCC position and orientation on the PCB can significantly alter coupling to PCB modes.

Therefore, `position` and `orientation` must be explicit sweep variables.

---

# 4. Model A — MLCC Electromechanical Strain

## 4.1 Electrical excitation

Model the applied voltage as

$$
V(t)
=
V_{\mathrm{DC}}
+
V_{\mathrm{AC}}\cos(\omega t).
$$

If the effective dielectric-layer thickness is $t_d$,

$$
E(t)=\frac{V(t)}{t_d}.
$$

Thus,

$$
E(t)
=
E_{\mathrm{DC}}
+
E_{\mathrm{AC}}\cos(\omega t),
$$

where

$$
E_{\mathrm{DC}}
=
\frac{V_{\mathrm{DC}}}{t_d},
\qquad
E_{\mathrm{AC}}
=
\frac{V_{\mathrm{AC}}}{t_d}.
$$

### Important limitation

For a commercial MLCC, $t_d$ is often unavailable from the datasheet.

Therefore, absolute electric-field prediction must only be used when:

1. a literature benchmark provides the necessary structure,
2. the parameter is explicitly supplied,
3. the value is treated as an assumed sensitivity parameter, or
4. the model has been calibrated against measurement.

Do not infer dielectric-layer thickness from package dimensions.

---

# 5. Piezoelectric and Electrostrictive Strain

Kim et al. (2019) use the strain model

$$
\boxed{
S=dE+ME^2
}
$$

where:

- $S$: mechanical strain,
- $E$: electric field,
- $d$: piezoelectric coefficient,
- $M$: electrostrictive coefficient.

Substituting the combined DC and AC electric field gives

$$
S(t)
=
d
\left(
E_{\mathrm{DC}}+E_{\mathrm{AC}}\cos\omega t
\right)
+
M
\left(
E_{\mathrm{DC}}+E_{\mathrm{AC}}\cos\omega t
\right)^2.
$$

Using

$$
\cos^2\omega t
=
\frac12
\left(
1+\cos2\omega t
\right),
$$

the strain can be written as

$$
\boxed{
S(t)
=
S_0
+
A_1\cos\omega t
+
A_2\cos2\omega t
}
$$

with

$$
S_0
=
dE_{\mathrm{DC}}
+
ME_{\mathrm{DC}}^2
+
\frac12ME_{\mathrm{AC}}^2,
$$

$$
\boxed{
A_1
=
\left(
d+2ME_{\mathrm{DC}}
\right)
E_{\mathrm{AC}}
}
$$

and

$$
\boxed{
A_2
=
\frac12ME_{\mathrm{AC}}^2.
}
$$

---

# 6. Physical Interpretation of the Harmonics

## 6.1 Fundamental component

The component at the excitation frequency $f$ has amplitude

$$
A_1
=
\left(
d+2ME_{\mathrm{DC}}
\right)
E_{\mathrm{AC}}.
$$

Therefore, the fundamental contains both:

- piezoelectric contribution, and
- DC-bias-dependent electrostrictive contribution.

At fixed material parameters and DC bias, the first-order model predicts approximately

$$
A_1 \propto E_{\mathrm{AC}}.
$$

---

## 6.2 Second harmonic

The component at $2f$ has amplitude

$$
A_2
=
\frac12ME_{\mathrm{AC}}^2.
$$

Within this model, the second harmonic originates from electrostriction.

The expected scaling is

$$
A_2 \propto E_{\mathrm{AC}}^2.
$$

This makes the $2f$ component particularly useful for checking whether the nonlinear electromechanical model has been implemented correctly.

---

# 7. Effective Piezoelectric Coefficient

For a fixed DC bias, define

$$
\boxed{
d_{\mathrm{eff}}
=
d+2ME_{\mathrm{DC}}.
}
$$

Then

$$
A_1
=
d_{\mathrm{eff}}E_{\mathrm{AC}}.
$$

This quantity should be implemented explicitly because it is useful for plotting and for interpreting DC-bias sweeps.

Recommended function:

```python
def effective_piezoelectric_coefficient(d, M, E_dc):
    ...
```

---

# 8. Directional Deformation

An MLCC should not be modeled as a body that expands and contracts isotropically.

If the dielectric electric-field direction is treated as axis 3, directional strains may be written schematically as

$$
S_3
=
d_{33}E
+
M_{33}E^2,
$$

$$
S_1
=
d_{31}E
+
M_{31}E^2.
$$

The first reduced-order implementation should therefore support at least two deformation channels:

```text
S_T : thickness-direction strain
S_L : longitudinal/head-direction strain
```

These channels may initially be normalized or parameterized independently.

Do not assume numerical values for $d_{31}$, $d_{33}$, $M_{31}$, or $M_{33}$ unless they are explicitly provided.

---

# 9. Model A Outputs

For every electrical condition, compute and store at least:

```text
frequency_Hz
omega_rad_s
Vdc_V
Vac_V
E_dc_V_m
E_ac_V_m
S0
A1
A2
H2_H1
d_eff
```

where

$$
H2\_H1
=
\left|
\frac{A_2}{A_1}
\right|.
$$

Handle $A_1 \approx 0$ safely.

Do not allow divide-by-zero warnings to silently propagate into ranking logic.

---

# 10. Model B — Equivalent Mechanical Source

A commercial MLCC contains many dielectric and electrode layers. Modeling the complete internal structure for every candidate is not appropriate for the first-stage screening model.

Instead, represent the MLCC as an equivalent source applied to the PCB.

The preferred reduced-order abstraction is an **equivalent moment pair**.

---

# 11. Equivalent-Moment Extraction Concept

A source-model identification relation may be written as

$$
\boxed{
M_{\mathrm{eq}}
=
\frac{v_m}{v_s}
M_{\mathrm{unit}}
}
$$

where:

- $v_m$: measured PCB velocity with the real MLCC,
- $v_s$: simulated PCB velocity under a known unit moment,
- $M_{\mathrm{unit}}$: known simulated unit moment,
- $M_{\mathrm{eq}}$: identified equivalent MLCC moment.

Before hardware measurements exist, $v_m$ is unavailable.

Therefore, pre-purchase simulation must support two source modes.

## Mode B1 — Normalized physics source

Use a configurable mapping from Model-A quantities such as $A_1$ and $A_2$ to normalized source magnitudes.

Example conceptual mapping:

```text
source_at_f  ∝ A1
source_at_2f ∝ A2
```

The proportionality constants must be explicitly labeled as normalized or assumed.

## Mode B2 — Literature-inspired source library

Implement the source-model structure from Ding et al. as a configurable reduced-order model.

Do not treat coefficients from one capacitor family as universal.

---

# 12. Literature-Inspired Simplified Source Model

A convenient source structure is

$$
M(V_{\mathrm{DC}},f)
=
a(V_{\mathrm{DC}})f
+
b(V_{\mathrm{DC}}).
$$

With a reference AC amplitude,

$$
\boxed{
M
\left(
V_{\mathrm{DC}},
V_{\mathrm{AC}},
f
\right)
=
\frac{V_{\mathrm{AC}}}
{V_{\mathrm{AC,ref}}}
\left[
a(V_{\mathrm{DC}})f
+
b(V_{\mathrm{DC}})
\right].
}
$$

The implementation should represent `a(Vdc)` and `b(Vdc)` as configurable functions or interpolation tables.

Recommended API:

```python
class EquivalentMomentModel:
    def moment(self, frequency_hz, vdc_v, vac_v):
        ...
```

### Important limitation

This equation is a **reduced source-model form**, not a universal constitutive law for all MLCCs.

Do not use it to claim absolute cross-vendor prediction unless the coefficients were identified for those parts.

---

# 13. Why Use a Moment Source?

MLCC deformation does not transfer to the PCB as a single vertical point force.

The two solder terminations can form a force couple, generating a rotational moment.

A simple conceptual approximation is

$$
M_{\mathrm{eq}}
\approx
F_{\mathrm{eq}}
d_{\mathrm{pad}},
$$

where:

- $F_{\mathrm{eq}}$: equivalent force magnitude,
- $d_{\mathrm{pad}}$: separation between the effective force locations.

This is one reason package geometry and orientation can alter PCB coupling.

The package size itself is not sufficient to determine the true source strength.

---

# 14. Model C — PCB Dynamics

Represent the PCB as a damped mechanical system:

$$
\boxed{
[M]\ddot{u}
+
[C]\dot{u}
+
[K]u
=
F.
}
$$

Modal analysis is based on

$$
\boxed{
([K]-\omega_n^2[M])\phi_n=0.
}
$$

For each mode, determine:

```text
natural frequency
mode shape
modal mass
damping ratio
source coupling
```

The first implementation should use an analytical thin-plate model.

---

# 15. First PCB Model — Rectangular Thin Plate

Use a rectangular isotropic thin-plate approximation before implementing FEM.

Let:

```text
a      PCB length
b      PCB width
h      PCB thickness
E_pcb  effective Young's modulus
rho    effective density
nu     effective Poisson ratio
```

The bending rigidity is

$$
\boxed{
D
=
\frac{E_{\mathrm{pcb}}h^3}
{12(1-\nu^2)}.
}
$$

For a simply supported rectangular plate,

$$
\boxed{
\phi_{mn}(x,y)
=
\sin\left(
\frac{m\pi x}{a}
\right)
\sin\left(
\frac{n\pi y}{b}
\right)
}
$$

and

$$
\boxed{
\omega_{mn}
=
\pi^2
\sqrt{
\frac{D}{\rho h}
}
\left(
\frac{m^2}{a^2}
+
\frac{n^2}{b^2}
\right).
}
$$

Then

$$
f_{mn}
=
\frac{\omega_{mn}}{2\pi}.
$$

### Interpretation

This model is intended for:

- resonance-order estimation,
- PCB-geometry sensitivity,
- mode-shape visualization,
- MLCC position/orientation screening.

It is **not** expected to reproduce bolt-constrained experimental natural frequencies exactly.

---

# 16. Harmonic Modal Response

For a mode $n$, use the frequency-domain generalized coordinate

$$
q_n(\omega)
=
\frac{Q_n}
{
m_n
\left[
\omega_n^2
-
\omega^2
+
j2\zeta_n\omega_n\omega
\right]
}.
$$

where:

- $Q_n$: generalized modal excitation,
- $m_n$: modal mass,
- $\zeta_n$: modal damping ratio.

The total displacement is

$$
w(x,y,\omega)
=
\sum_n
\phi_n(x,y)q_n(\omega).
$$

Velocity is

$$
\boxed{
v(x,y,\omega)
=
j\omega w(x,y,\omega).
}
$$

The implementation must keep complex-valued response until amplitude or RMS quantities are explicitly computed.

---

# 17. MLCC Position Coupling

For a point-force approximation,

$$
Q_n
\propto
F\phi_n(x_c,y_c),
$$

where $(x_c,y_c)$ is the capacitor location.

Therefore:

- near a modal node: weak coupling,
- near an antinode: strong coupling.

This is why capacitor location must be swept explicitly.

---

# 18. MLCC Orientation Coupling

For an equivalent moment, coupling depends on the spatial derivative of the mode shape.

For an x-directed rotational source,

$$
Q_{mn}
\propto
M_{\mathrm{eq}}
\left.
\frac{\partial\phi_{mn}}{\partial x}
\right|_{(x_c,y_c)}.
$$

For a y-directed rotational source,

$$
Q_{mn}
\propto
M_{\mathrm{eq}}
\left.
\frac{\partial\phi_{mn}}{\partial y}
\right|_{(x_c,y_c)}.
$$

Therefore, rotating the same MLCC by $90^\circ$ may change the excited modal spectrum.

The code must treat orientation as a model input, not as metadata.

---

# 19. Acoustic Output — Use Vibration Proxies First

Do not implement full acoustic FEM in the first version.

Use PCB vibration metrics as acoustic-noise proxies.

## 19.1 Point velocity

$$
Score_1(f)
=
\left|
v(x_{\mathrm{obs}},y_{\mathrm{obs}},f)
\right|.
$$

## 19.2 Surface RMS velocity

$$
Score_2(f)
=
\sqrt{
\frac{1}{A}
\int_A
|v(x,y,f)|^2
\,dA
}.
$$

Approximate the surface integral numerically on a regular grid.

## 19.3 Broadband vibration score

$$
Score_3
=
\sqrt{
\sum_f
w_f
Score_2(f)^2
}.
$$

Initially use

```text
w_f = 1
```

unless a specific weighting is explicitly configured.

Do not call these quantities SPL.

---

# 20. Separate Two Simulation Modes

The repository should expose two conceptually distinct workflows.

## 20.1 Physics Sweep

Purpose:

```text
understand voltage, bias, and harmonic generation
```

Inputs:

```text
d
M
dielectric thickness
Vdc
Vac
frequency
```

Outputs:

```text
S0
A1
A2
A2/A1
d_eff
```

---

## 20.2 Experiment-Design Sweep

Purpose:

```text
select PCB geometry, package, position, orientation, and excitation conditions
```

Inputs:

```text
source model
package geometry
pad separation
PCB geometry
PCB support model
MLCC position
MLCC orientation
damping
frequency
```

Outputs:

```text
modal frequencies
mode shapes
PCB velocity spectrum
peak velocity
surface RMS velocity
candidate ranking
```

---

# 21. Literature Benchmarks

The project should contain benchmark configurations separate from general sweep configurations.

## 21.1 Kim et al. (2019) MLCC benchmark

```yaml
name: kim_2019_mlcc

capacitor:
  dielectric: X5R
  capacitance_uF: 10.0
  package: "0402"
  body_mm: [1.0, 0.5, 0.5]

excitation:
  frequency_Hz: 2000
  Vac_pp_V: 1.6
  Vdc_V:
    start: 0.0
    stop: 2.8
    step: 0.4
```

The paper analyzes the fundamental component at 2 kHz and the second harmonic at 4 kHz.

### AC-amplitude convention warning

The literature benchmark reports peak-to-peak AC voltage.

Internally, the mathematical model should use a clearly defined amplitude convention.

The code must never mix:

```text
peak
peak-to-peak
RMS
```

without explicit conversion.

Add utility functions for all conversions.

---

## 21.2 Kim et al. (2019) PCB benchmark

```yaml
name: kim_2019_pcb

pcb:
  length_mm: 100
  width_mm: 40
  thickness_mm: 1.0
```

Use this as the first geometry benchmark.

---

## 21.3 Ding et al. source-model region

Use the literature source-model range only as a benchmark/reference region.

```yaml
name: ding_2024_reference_region

source_model:
  frequency_Hz:
    min: 200
    max: 3000

  Vac_ref_V: 0.1

  Vdc_V:
    min: 0.0
    max: 6.3
```

Do not assume that every future candidate MLCC obeys the same identified coefficients.

---

# 22. Initial Electrical Sweep

Start with the following grid.

## Frequency

```yaml
frequency:
  start_Hz: 200
  stop_Hz: 3000
  coarse_step_Hz: 25
```

After identifying resonances, optionally refine locally using:

```text
2–5 Hz spacing
```

The architecture should allow extension to a broader audible-frequency range later.

## DC bias

Initial grid:

```yaml
Vdc_V:
  - 0
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6
```

For a real component, automatically reject configurations exceeding the component's configured rated voltage.

## AC amplitude

Initial grid:

```yaml
Vac_V:
  - 0.02
  - 0.05
  - 0.10
  - 0.25
  - 0.50
```

The configuration must state whether these are:

```text
peak
peak-to-peak
RMS
```

Default to one convention globally and convert at input boundaries.

---

# 23. Candidate MLCC Factor Grid

Treat the following as candidate experimental factors:

```text
dielectric class
capacitance
package
rated voltage
vendor
series
part number
```

Initial candidate levels:

```yaml
dielectric:
  - C0G_NP0
  - X7R
  - X5R

package:
  - "0402"
  - "0603"
  - "0805"

capacitance_uF:
  - 1.0
  - 4.7
  - 10.0
  - 22.0

rated_voltage_V:
  - 6.3
  - 10
  - 16
```

Not all combinations will exist commercially.

The simulation should therefore operate on a **candidate table**, not on the full Cartesian product after real part numbers are introduced.

---

# 24. Interpretation of C0G/NP0

C0G/NP0 is useful as a low-electromechanical-coupling control group.

However, high-capacitance C0G/NP0 parts may not exist in the same capacitance/package combinations as X5R/X7R.

Therefore:

- use C0G/NP0 as a **negative or low-coupling control**,
- do not automatically interpret a C0G-vs-X5R comparison as a perfect one-factor dielectric comparison if capacitance or construction also differs.

The final experiment matrix should explicitly record confounded factors.

---

# 25. Factor-Isolation Strategy for Purchasing

Do not purchase every combination.

Construct overlapping comparison groups.

## Group A — Dielectric comparison

Hold package approximately constant where possible:

```text
C0G/NP0
X7R
X5R
```

Prefer matched capacitance and rated voltage when commercially available.

## Group B — Capacitance comparison

Hold constant:

```text
dielectric
package
rated voltage
vendor/series when possible
```

Vary capacitance.

## Group C — Package comparison

Hold constant:

```text
dielectric
capacitance
rated voltage
vendor/series when possible
```

Vary:

```text
0402
0603
0805
```

## Group D — Rated-voltage comparison

Hold constant:

```text
dielectric
capacitance
package
vendor/series when possible
```

Vary rated voltage.

Different voltage ratings may correspond to different internal geometries, so this is experimentally relevant even when nominal capacitance is unchanged.

---

# 26. Target Number of MLCC SKUs

The initial design target is approximately:

```text
8–10 unique MLCC SKUs
```

This is a planning target, not a hard requirement.

The ranking script should prefer a compact set that covers multiple comparison groups simultaneously.

---

# 27. PCB Geometry Sweep

Initial PCB geometry grid:

```yaml
pcb_length_mm:
  - 60
  - 80
  - 100

pcb_width_mm:
  - 30
  - 40

pcb_thickness_mm:
  - 0.8
  - 1.0
  - 1.6
```

For each geometry, evaluate:

1. Which modal frequencies fall inside the target excitation band?
2. Are useful resonances sufficiently separated to identify experimentally?
3. How sensitive is response to MLCC position?
4. How sensitive is response to orientation?
5. How sensitive is the resonance prediction to support assumptions?
6. Is the geometry practical to fabricate and mount?

Always include the $100 \times 40 \times 1$ mm literature reference geometry.

---

# 28. Boundary Conditions

Boundary conditions are expected to be a major source of modeling uncertainty.

The framework should support at least:

```text
simply_supported
edge_clamped
four_point_or_bolt_constrained
```

Implementation order:

1. `simply_supported` analytical model,
2. lightweight numerical model for alternative boundaries,
3. optional FEM only if required later.

A PCB design whose predicted behavior changes excessively under small boundary-condition changes should receive a lower robustness score.

---

# 29. MLCC Position Sweep

Use normalized coordinates first.

```yaml
x_over_a:
  - 0.20
  - 0.35
  - 0.50
  - 0.65
  - 0.80

y_over_b:
  - 0.25
  - 0.50
  - 0.75
```

Orientation:

```yaml
orientation_deg:
  - 0
  - 90
```

The position sweep should identify both:

- high-coupling locations,
- low-coupling control locations near modal nodes or low-gradient regions.

These may later become separate PCB footprints or separate experimental boards.

---

# 30. Recommended Experimental PCB Roles

If practical, distinguish two board roles.

## 30.1 PCB A — Source Characterization Board

Purpose:

```text
minimize PCB-resonance ambiguity and observe MLCC/local vibration behavior
```

Desired properties:

- relatively small board,
- strong and reproducible support,
- consistent mounting geometry,
- capacitor placed at a controlled reference location.

The exact geometry should be selected by simulation rather than assumed.

## 30.2 PCB B — Singing / Resonance Board

Purpose:

```text
deliberately allow MLCC excitation to couple to measurable PCB resonances
```

Use

```text
100 × 40 × 1 mm FR-4
```

as the initial literature-inspired baseline, then modify geometry based on the modal sweep.

---

# 31. Repository Structure

Use the following initial structure:

```text
singing-capacitor-sim/
│
├── README.md
├── pyproject.toml
├── requirements.txt
│
├── config/
│   ├── defaults.yaml
│   ├── pcb.yaml
│   ├── excitation.yaml
│   ├── sweep.yaml
│   └── benchmarks/
│       ├── kim_2019_mlcc.yaml
│       ├── kim_2019_pcb.yaml
│       └── ding_2024_reference.yaml
│
├── data/
│   ├── capacitor_candidates.csv
│   ├── literature_benchmarks.csv
│   └── README.md
│
├── src/
│   └── singing_capacitor/
│       ├── __init__.py
│       ├── units.py
│       ├── electromechanical.py
│       ├── source_model.py
│       ├── plate_modal.py
│       ├── coupling.py
│       ├── response.py
│       ├── sweeps.py
│       ├── scoring.py
│       └── io.py
│
├── scripts/
│   ├── 01_validate_harmonics.py
│   ├── 02_pcb_modal_sweep.py
│   ├── 03_voltage_frequency_sweep.py
│   ├── 04_position_orientation_sweep.py
│   └── 05_rank_experiment_matrix.py
│
├── tests/
│   ├── test_units.py
│   ├── test_electromechanical.py
│   ├── test_plate_modal.py
│   ├── test_coupling.py
│   └── test_response.py
│
└── results/
    ├── figures/
    ├── sweeps/
    ├── logs/
    └── recommendations/
```

---

# 32. Python Dependencies

Minimum:

```text
numpy
scipy
pandas
matplotlib
pyyaml
```

Recommended for development:

```text
pytest
```

Do not add a heavy FEM dependency in the initial implementation.

---

# 33. Core Data Structures

Prefer small typed dataclasses.

Suggested objects:

```python
@dataclass
class ElectricalExcitation:
    frequency_hz: float
    vdc_v: float
    vac_v: float
    vac_convention: str

@dataclass
class ElectromechanicalMaterial:
    d: float | None
    M: float | None
    dielectric_thickness_m: float | None

@dataclass
class PCBGeometry:
    length_m: float
    width_m: float
    thickness_m: float
    youngs_modulus_pa: float
    density_kg_m3: float
    poisson_ratio: float

@dataclass
class MLCCPlacement:
    x_m: float
    y_m: float
    orientation_deg: float
```

The exact names may be adjusted, but units must remain unambiguous.

---

# 34. Script 01 — `01_validate_harmonics.py`

## Goal

Verify that the electromechanical equations are implemented correctly.

Generate:

### Plot A — Time-domain strain

```text
S(t)
```

### Plot B — FFT

The spectrum should show:

```text
f
2f
```

for a case where both coefficients are nonzero.

### Plot C — Fundamental scaling

```text
A1 vs Vac
```

### Plot D — Second-harmonic scaling

```text
A2 vs Vac^2
```

### Plot E — DC-bias dependence

```text
A1 vs Vdc
d_eff vs Vdc
```

## Acceptance criteria

Automated tests must confirm numerically that:

$$
A_1
=
(d+2ME_{\mathrm{DC}})E_{\mathrm{AC}}
$$

and

$$
A_2
=
\frac12ME_{\mathrm{AC}}^2.
$$

For fixed $E_{\mathrm{DC}}$:

- `A1` is linear in `E_ac`,
- `A2` is quadratic in `E_ac`.

The FFT peak frequencies must fall within one FFT bin of the analytical expectation.

---

# 35. Script 02 — `02_pcb_modal_sweep.py`

For every PCB geometry:

1. compute modal frequencies,
2. compute mode shapes,
3. save a mode table,
4. save mode-shape plots,
5. identify modes inside the configured frequency band.

Required output:

```text
mode_table.csv
mode_01.png
mode_02.png
...
```

Recommended table columns:

```text
pcb_id
m
n
frequency_Hz
modal_mass_kg
boundary_condition
```

If modal mass is not yet implemented analytically, store it as a clearly labeled normalized value rather than omitting the distinction.

---

# 36. Script 03 — `03_voltage_frequency_sweep.py`

Conceptual loop:

```python
for capacitor in capacitors:
    for vdc in vdc_grid:
        for vac in vac_grid:
            for frequency in frequency_grid:
                ...
```

For each condition compute:

```text
A1
A2
source magnitude at f
source magnitude at 2f
PCB response at f
PCB response at 2f
```

## Important harmonic rule

An electrical input at frequency $f$ can create a mechanical response at both:

```text
f
2f
```

through the strain model.

Do not collapse these into a single scalar before response calculation.

Store them as separate frequency-domain components.

If total time-domain response is reconstructed later, combine complex components consistently.

---

# 37. Script 04 — `04_position_orientation_sweep.py`

For each:

```text
PCB
MLCC position
MLCC orientation
mode
```

compute:

```text
modal coupling coefficient
peak point velocity
surface RMS velocity
dominant mode
dominant response frequency
```

Generate heatmaps for:

```text
x position
y position
orientation
→ response score
```

The heatmaps should make it possible to select:

- a loud/high-coupling placement,
- a quiet/low-coupling control placement.

---

# 38. Script 05 — `05_rank_experiment_matrix.py`

The ranking system must not simply choose the loudest conditions.

Experimental design needs at least three categories.

## 38.1 High-response condition

A condition expected to produce a clear measurable signal.

## 38.2 Low-response control

A condition expected to suppress response.

## 38.3 Discriminative condition

A condition where two candidate capacitor classes or two model hypotheses predict substantially different behavior.

A generic score may be written as

$$
Score
=
w_1S_{\mathrm{source}}
+
w_2S_{\mathrm{board}}
+
w_3S_{\mathrm{harmonic}}
+
w_4S_{\mathrm{robustness}}
+
w_5S_{\mathrm{discrimination}}.
$$

Do not hard-code weights into the physics module.

Weights belong in configuration.

---

# 39. Robustness Scoring

Because absolute parameters are uncertain, rank candidate designs partly by robustness.

For each candidate PCB/placement, perturb:

```text
PCB effective modulus
PCB density
damping ratio
support condition
source scale
position tolerance
```

within configurable ranges.

A robust candidate should remain qualitatively useful under these perturbations.

Examples:

- a resonance remains within the target frequency band,
- the loud placement remains louder than the control placement,
- the predicted orientation effect does not reverse under small parameter changes.

---

# 40. Final Simulation Outputs

The pipeline should generate the following recommendation files.

## `recommended_capacitors.csv`

Columns:

```text
part_id
vendor
series
part_number
dielectric
capacitance_uF
package
rated_voltage_V
comparison_groups
assumption_level
predicted_source_score
reason_for_selection
```

## `recommended_pcb.csv`

Columns:

```text
pcb_id
length_mm
width_mm
thickness_mm
support
mlcc_x_over_a
mlcc_y_over_b
orientation_deg
predicted_resonance_Hz
predicted_vibration_score
robustness_score
reason_for_selection
```

## `recommended_excitation.csv`

Columns:

```text
condition_id
Vdc_V
Vac_V
Vac_convention
frequency_Hz
predicted_f_response
predicted_2f_response
purpose
```

## `experiment_matrix.csv`

Each row should represent one actual experimental run.

Recommended columns:

```text
run_id
pcb_id
part_id
position_id
orientation_deg
Vdc_V
Vac_V
Vac_convention
frequency_Hz
comparison_group
control_or_test
notes
```

---

# 41. Initial Global Sweep Configuration

Use the following as a starting point:

```yaml
frequency:
  start_Hz: 200
  stop_Hz: 3000
  coarse_step_Hz: 25
  resonance_refine_step_Hz: 5

Vdc_V:
  - 0
  - 1
  - 2
  - 3
  - 4
  - 5
  - 6

Vac:
  convention: peak
  values_V:
    - 0.02
    - 0.05
    - 0.10
    - 0.25
    - 0.50

pcb:
  length_mm:
    - 60
    - 80
    - 100

  width_mm:
    - 30
    - 40

  thickness_mm:
    - 0.8
    - 1.0
    - 1.6

placement:
  x_over_a:
    - 0.20
    - 0.35
    - 0.50
    - 0.65
    - 0.80

  y_over_b:
    - 0.25
    - 0.50
    - 0.75

  orientation_deg:
    - 0
    - 90
```

Do not assume that every combination must be run at full resolution.

Use coarse screening first, then local refinement.

---

# 42. Recommended First Baseline

To minimize parameter interactions in the first implementation, begin with:

```text
PCB geometry       100 × 40 × 1 mm
MLCC position      center
MLCC orientation   longitudinal
frequency range    200–3000 Hz
```

Initially vary only:

```text
Vdc
Vac
source-model parameters
```

After Model A and the baseline PCB response are validated, enable:

```text
PCB geometry
position
orientation
```

This order makes debugging and interpretation substantially easier.

---

# 43. Validation Strategy

## Stage 1 — Mathematical validation

Verify the closed-form relationships:

$$
A_1 \propto E_{\mathrm{AC}}
$$

for fixed $E_{\mathrm{DC}}$, and

$$
A_2 \propto E_{\mathrm{AC}}^2.
$$

Also verify:

$$
d_{\mathrm{eff}}
=
d+2ME_{\mathrm{DC}}.
$$

---

## Stage 2 — Harmonic sanity check

For a synthetic parameter set with nonzero $d$ and $M$:

- generate the time-domain strain,
- FFT the waveform,
- verify peaks at $f$ and $2f$,
- compare FFT amplitudes against the analytical expressions.

This stage should use synthetic coefficients specifically chosen for numerical clarity.

Synthetic coefficients must be labeled as synthetic.

---

## Stage 3 — Literature-condition sanity check

Use the Kim et al. benchmark condition:

```text
X5R
10 μF
0402
2 kHz excitation
DC-bias sweep
```

Compare only trends that are supported by the available model and supplied literature data.

Do not claim exact reproduction unless the required material coefficients and structural parameters are actually provided.

---

## Stage 4 — PCB modal sanity check

Run the $100 \times 40 \times 1$ mm PCB geometry.

Check:

- modal ordering,
- expected dependence on length/width/thickness,
- mode-shape symmetry,
- position dependence.

If numerical frequencies differ from a particular experiment, investigate:

```text
boundary condition
effective material properties
PCB anisotropy
mounting stiffness
```

before adjusting arbitrary scale factors.

---

## Stage 5 — Post-Purchase Calibration

After hardware is available:

1. choose one reference MLCC,
2. choose one reference PCB,
3. measure vibration at a well-defined electrical condition,
4. estimate:
   - source scale,
   - equivalent moment,
   - effective damping,
5. predict additional voltage/frequency conditions,
6. compare predictions with measurements.

Only after this stage should the model be used for stronger SKU-level quantitative claims.

---

# 44. Automated Test Requirements

At minimum, tests should cover:

## Electromechanical model

- zero field gives expected zero dynamic strain,
- `M = 0` removes the second harmonic,
- `d = 0, Vdc = 0` removes the fundamental in the ideal scalar model,
- `A1` analytical expression matches time-domain extraction,
- `A2` analytical expression matches time-domain extraction.

## Unit conversion

- peak ↔ peak-to-peak,
- peak ↔ RMS for sinusoidal signals,
- mm ↔ m,
- µF parsing if used in data ingestion.

## Plate model

- modal frequency decreases as plate length increases,
- modal frequency increases as thickness increases,
- mode shape is zero at simply supported edges,
- mode indices are handled deterministically.

## Coupling

- point-force coupling is near zero at a modal node,
- orientation changes x-gradient vs y-gradient coupling,
- mirrored positions behave consistently for symmetric modes.

## Frequency response

- response peaks near modal resonance,
- increasing damping lowers and broadens the resonance peak,
- no NaN/Inf values propagate into ranking outputs.

---

# 45. Important Limitations

## 45.1 Commercial MLCC material coefficients are usually unavailable

The reduced-order physics model cannot automatically rank real commercial part numbers by absolute vibration solely from ordinary datasheet fields.

---

## 45.2 Internal construction matters

Two components with the same nominal:

```text
capacitance
package
dielectric code
rated voltage
```

can still differ in:

```text
dielectric composition
grain structure
layer thickness
number of layers
active-region dimensions
cover-layer dimensions
electrode geometry
```

Therefore, store `vendor`, `series`, and `part_number` as first-class identifiers.

---

## 45.3 Solder joints matter

The solder geometry and pad geometry affect the transfer path from MLCC deformation to PCB vibration.

In the first model, absorb this uncertainty into the equivalent-source abstraction.

Later, introduce mounting parameters only after experimental data justify doing so.

---

## 45.4 FR-4 is not perfectly isotropic

The first analytical plate model uses an effective isotropic approximation.

This is acceptable for screening, but not for final high-accuracy prediction.

Do not silently interpret the effective modulus as a fundamental FR-4 constant.

---

## 45.5 Boundary conditions are uncertain

Experimental supports, bolts, clamps, fixtures, and soldered connections can shift natural frequencies.

Treat support modeling as a sensitivity variable.

---

## 45.6 Absolute SPL is outside the first implementation

Absolute acoustic prediction would require additional modeling of:

```text
surface-to-air coupling
radiation efficiency
acoustic boundary conditions
enclosure geometry
microphone location
room response
```

The first version reports vibration proxies only.

---

# 46. Questions the Simulation Must Answer Before Purchasing Hardware

Before the final purchasing decision, the simulation should produce defensible answers to at least the following:

1. Which PCB dimensions place useful resonances inside the selected frequency band?
2. Which PCB thickness gives a measurable but not excessively dense modal spectrum?
3. Where should the MLCC be placed for maximum modal coupling?
4. Where should a low-coupling control placement be located?
5. How strongly does a $90^\circ$ MLCC rotation change response?
6. Does the fundamental $f$ component or the second harmonic $2f$ overlap more strongly with a PCB resonance?
7. Which DC-bias range is most informative for separating electromechanical behavior?
8. How many AC-amplitude levels are needed to distinguish approximately linear $A_1$ scaling from quadratic $A_2$ scaling?
9. Which package-size comparison is most informative?
10. Which capacitor comparison groups can share the same SKUs?
11. Which candidate PCB designs remain useful under support/damping uncertainty?
12. Which exact condition should be measured first for post-purchase calibration?

---

# 47. Recommended Implementation Milestones

## Milestone 1 — Electromechanical Core

Implement:

```text
units
voltage conversion
electric field
strain waveform
A1
A2
d_eff
FFT validation
```

Deliverables:

```text
src/singing_capacitor/electromechanical.py
scripts/01_validate_harmonics.py
tests/test_electromechanical.py
```

**Stop and validate before proceeding.**

---

## Milestone 2 — Analytical PCB Modal Model

Implement:

```text
plate bending rigidity
natural frequencies
mode shapes
modal visualization
```

Deliverables:

```text
src/singing_capacitor/plate_modal.py
scripts/02_pcb_modal_sweep.py
tests/test_plate_modal.py
```

---

## Milestone 3 — Source-to-Mode Coupling

Implement:

```text
point-force coupling
x-directed moment coupling
y-directed moment coupling
position sweep
orientation sweep
```

Deliverables:

```text
src/singing_capacitor/coupling.py
tests/test_coupling.py
```

---

## Milestone 4 — Harmonic PCB Response

Implement:

```text
modal damping
complex frequency response
response at f
response at 2f
point velocity
surface RMS velocity
```

Deliverables:

```text
src/singing_capacitor/response.py
scripts/03_voltage_frequency_sweep.py
tests/test_response.py
```

---

## Milestone 5 — Experiment-Design Sweep

Implement:

```text
PCB geometry sweep
position/orientation sweep
coarse-to-fine frequency sweep
result tables
heatmaps
```

Deliverables:

```text
src/singing_capacitor/sweeps.py
scripts/04_position_orientation_sweep.py
```

---

## Milestone 6 — Candidate Ranking

Implement:

```text
response score
robustness score
discrimination score
comparison-group coverage
recommendation tables
```

Deliverables:

```text
src/singing_capacitor/scoring.py
scripts/05_rank_experiment_matrix.py
results/recommendations/
```

---

## Milestone 7 — Literature-Based Equivalent Source Model

Only after the normalized pipeline works:

- add the Ding-style equivalent-moment model,
- keep it modular,
- load coefficient tables from data/config files,
- do not embed paper-specific fitted coefficients in core physics code.

---

## Milestone 8 — Real-Part Candidate Integration

After candidate commercial parts are selected:

1. populate `capacitor_candidates.csv`,
2. mark which fields are datasheet-derived,
3. mark which electromechanical fields are unknown,
4. build overlapping comparison groups,
5. rerun ranking,
6. generate the final purchase shortlist.

---

# 48. Definition of Done for the Pre-Purchase Simulator

The initial simulator is complete when it can:

- reproduce the analytical $f$ and $2f$ strain components,
- compute rectangular-PCB modal frequencies and mode shapes,
- calculate position- and orientation-dependent coupling,
- calculate complex harmonic PCB response,
- perform coarse and refined parameter sweeps,
- distinguish literature values from assumptions,
- rank high-response, low-response, and discriminative conditions,
- output a compact MLCC/PCB/excitation recommendation matrix,
- run automated tests without failure,
- reproduce all generated results from saved configuration files.

Absolute SPL prediction is **not** part of this definition of done.

---

# 49. Core Modeling Principle

Do not model the capacitor as a black box that “produces sound when voltage is applied.”

Preserve the physical chain:

$$
\boxed{
V
\rightarrow
E
\rightarrow
S
\rightarrow
M_{\mathrm{eq}}
\rightarrow
\text{PCB modal response}
\rightarrow
\text{vibration proxy}
}
$$

This separation is essential because an observed spectral peak may originate from different mechanisms:

- nonlinear MLCC electromechanical deformation,
- fundamental or second-harmonic generation,
- PCB resonance,
- source-to-mode spatial coupling,
- MLCC orientation,
- mounting and boundary conditions.

The purpose of the simulator is to make those mechanisms separable enough that the eventual experiment can test them systematically.

---

# 50. Immediate Next Action for Claude Code

Start with **Milestone 1 only**.

Create:

```text
src/singing_capacitor/units.py
src/singing_capacitor/electromechanical.py
scripts/01_validate_harmonics.py
tests/test_units.py
tests/test_electromechanical.py
config/benchmarks/kim_2019_mlcc.yaml
```

Requirements:

1. Implement voltage-amplitude convention conversion.
2. Implement $E(t)$, $S(t)$, $A_1$, $A_2$, and $d_{\mathrm{eff}}$.
3. Generate a synthetic waveform and FFT.
4. Verify analytical and numerical harmonic amplitudes.
5. Save all figures and CSV outputs under `results/`.
6. Use synthetic electromechanical coefficients unless literature-derived values are explicitly provided.
7. Label synthetic coefficients clearly in output metadata.
8. Add tests before moving to the PCB model.

Do not proceed to Milestone 2 until Milestone 1 tests pass.
