"""Validation checks for the singing-capacitor design model (README section 3).

This is an experiment-design tool, not a high-fidelity FEM solver, so the
checks only confirm the expected qualitative trends and the analytical
formulas used by source.py / plate.py. Synthetic coefficients are used only
to exercise the equations; they are not properties of a real MLCC.

    python test_model.py
"""

import numpy as np

from plate import Plate
from coupling import point_force_coupling, moment_coupling
from source import strain_amplitudes
from model import Params, evaluate


def _baseline_plate():
    return Plate(a=0.100, b=0.040, h=0.001, E=20e9, rho=1850.0, nu=0.13, damping=0.02)


def test_length_decreases_resonance():
    plate_short = Plate(a=0.060, b=0.040, h=0.001, E=20e9, rho=1850.0, nu=0.13, damping=0.02)
    plate_long = Plate(a=0.100, b=0.040, h=0.001, E=20e9, rho=1850.0, nu=0.13, damping=0.02)
    assert plate_long.natural_frequency(1, 1) < plate_short.natural_frequency(1, 1)


def test_thickness_increases_resonance():
    plate_thin = Plate(a=0.100, b=0.040, h=0.0008, E=20e9, rho=1850.0, nu=0.13, damping=0.02)
    plate_thick = Plate(a=0.100, b=0.040, h=0.0016, E=20e9, rho=1850.0, nu=0.13, damping=0.02)
    assert plate_thick.natural_frequency(1, 1) > plate_thin.natural_frequency(1, 1)


def test_mode_shape_zero_at_supported_edges():
    plate = _baseline_plate()
    for x in (0.0, plate.a):
        assert abs(plate.mode_shape(1, 1, x, plate.b / 2)) < 1e-9
    for y in (0.0, plate.b):
        assert abs(plate.mode_shape(1, 1, plate.a / 2, y)) < 1e-9


def test_point_force_weak_at_node():
    plate = _baseline_plate()
    # mode (2,1) has a nodal line at x/a = 0.5
    node = point_force_coupling(plate, 2, 1, 0.50, 0.50)
    antinode = point_force_coupling(plate, 2, 1, 0.25, 0.50)
    assert abs(node) < 1e-9
    assert abs(antinode) > abs(node)


def test_point_force_strong_at_antinode():
    plate = _baseline_plate()
    antinode = point_force_coupling(plate, 1, 1, 0.50, 0.50)
    off_center = point_force_coupling(plate, 1, 1, 0.10, 0.50)
    assert abs(antinode) > abs(off_center)


def test_orientation_changes_moment_coupling():
    plate = _baseline_plate()
    c0 = moment_coupling(plate, 2, 1, 0.30, 0.40, orientation_deg=0.0)
    c90 = moment_coupling(plate, 2, 1, 0.30, 0.40, orientation_deg=90.0)
    assert abs(c0) > 1e-9 and abs(c90) > 1e-9
    assert not np.isclose(c0, c90)


def test_damping_lowers_and_broadens_peak():
    params_low = Params(damping=0.01)
    params_high = Params(damping=0.08)
    freqs = np.linspace(params_low.f_min, params_low.f_max, 600)

    result_low = evaluate(params_low, freqs=freqs)
    result_high = evaluate(params_high, freqs=freqs)

    peak_low = result_low["resp_f"].max()
    peak_high = result_high["resp_f"].max()
    assert peak_high < peak_low

    def half_power_width(resp):
        peak = resp.max()
        idx = np.where(resp >= peak / np.sqrt(2))[0]
        return freqs[idx[-1]] - freqs[idx[0]]

    assert half_power_width(result_high["resp_f"]) > half_power_width(result_low["resp_f"])


def test_electrostrictive_source_appears_at_2f():
    params = Params()
    freqs = np.linspace(params.f_min, params.f_max, 600)
    result = evaluate(params, x_frac=0.30, y_frac=0.40, orientation_deg=0.0,
                       source_f=0.0, source_2f=1.0, freqs=freqs)
    assert np.allclose(result["resp_f"], 0.0)
    assert result["resp_2f"].max() > 0.0


def test_strain_amplitude_formulas():
    d, M, E_dc, E_ac = 3.0e-10, 5.0e-16, 2.0e6, 5.0e5
    A1, A2 = strain_amplitudes(d, M, E_dc, E_ac)
    expected_A1 = (d + 2 * M * E_dc) * E_ac
    expected_A2 = 0.5 * M * E_ac ** 2
    assert np.isclose(A1, expected_A1)
    assert np.isclose(A2, expected_A2)


def _all_tests():
    return [(name, fn) for name, fn in sorted(globals().items())
            if name.startswith("test_") and callable(fn)]


def main():
    tests = _all_tests()
    failures = []
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as exc:
            failures.append(name)
            print(f"FAIL  {name}: {exc}")
        except Exception as exc:  # unexpected error
            failures.append(name)
            print(f"ERROR {name}: {exc!r}")

    print(f"\n{len(tests) - len(failures)}/{len(tests)} passed")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
