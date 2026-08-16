"""Frequency response of the PCB to the MLCC source.

Each PCB mode is treated as a damped harmonic oscillator (README section 2):

    q_n(w) = Q_n / [m_n (w_n^2 - w^2 + i 2 zeta_n w_n w)]

Modal responses are summed (in quadrature) to obtain a relative PCB
vibration amplitude. This is a proxy for vibration / acoustic-noise
strength, not an absolute sound pressure level.
"""

import numpy as np

from coupling import mode_coupling


def modal_response(Q: complex, omega: float, omega_n: float, modal_mass: float, zeta: float) -> complex:
    denom = modal_mass * (omega_n ** 2 - omega ** 2 + 1j * 2 * zeta * omega_n * omega)
    return Q / denom


def velocity_amplitude(plate, modes, x_frac: float, y_frac: float, orientation_deg: float,
                        source_amplitude: float, omega: float) -> float:
    """Relative PCB velocity amplitude at a single excitation frequency,
    summed in quadrature across the retained modes.
    """
    total_sq = 0.0
    for mode in modes:
        c = mode_coupling(plate, mode.m, mode.n, x_frac, y_frac, orientation_deg)
        Q = c * source_amplitude
        q = modal_response(Q, omega, mode.omega_n, mode.modal_mass, plate.damping)
        v = 1j * omega * q
        total_sq += abs(v) ** 2
    return float(np.sqrt(total_sq))


def frequency_sweep(plate, modes, x_frac: float, y_frac: float, orientation_deg: float,
                     freqs, source_f: float, source_2f: float):
    """Relative PCB vibration vs electrical excitation frequency, evaluated
    at both the fundamental (f) and the second harmonic (2f).
    """
    freqs = np.asarray(freqs, dtype=float)
    resp_f = np.empty_like(freqs)
    resp_2f = np.empty_like(freqs)
    for i, f_exc in enumerate(freqs):
        omega_f = 2 * np.pi * f_exc
        omega_2f = 2 * np.pi * (2.0 * f_exc)
        resp_f[i] = velocity_amplitude(plate, modes, x_frac, y_frac, orientation_deg, source_f, omega_f)
        resp_2f[i] = velocity_amplitude(plate, modes, x_frac, y_frac, orientation_deg, source_2f, omega_2f)
    return resp_f, resp_2f
