"""Shared parameters and the source -> plate -> coupling -> response chain
described in README section 1:

    voltage
      -> relative MLCC source at f and 2f
      -> PCB mode coupling
      -> PCB vibration response
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.signal import find_peaks

from plate import Plate
import source as src
from response import frequency_sweep


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

    # relative strength of the 2f source vs f, used when real d/M
    # coefficients are not supplied (source.normalized_source)
    r_harmonic: float = 0.3

    n_modes_m: int = 4
    n_modes_n: int = 4
    n_freq_points: int = 400


def build_plate(params: Params) -> Plate:
    return Plate(a=params.pcb_L, b=params.pcb_W, h=params.pcb_h,
                 E=params.E_pcb, rho=params.rho_pcb, nu=params.nu_pcb,
                 damping=params.damping)


def get_modes(params: Params, plate: Optional[Plate] = None, f_max: Optional[float] = None):
    plate = plate if plate is not None else build_plate(params)
    return plate.modes(params.n_modes_m, params.n_modes_n, f_max=f_max)


def default_freqs(params: Params) -> np.ndarray:
    return np.linspace(params.f_min, params.f_max, params.n_freq_points)


def refine_freq_grid(params: Params, resonances, coarse_n: int = 150,
                      fine_span_frac: float = 0.08, fine_n: int = 25) -> np.ndarray:
    """Coarse scan over [f_min, f_max], with extra points concentrated near
    predicted resonances (README section 2, run_sweep.py).
    """
    coarse = np.linspace(params.f_min, params.f_max, coarse_n)
    chunks = [coarse]
    for f_res in resonances:
        if params.f_min <= f_res <= params.f_max:
            span = max(fine_span_frac * f_res, 5.0)
            chunks.append(np.linspace(f_res - span, f_res + span, fine_n))
    freqs = np.unique(np.clip(np.concatenate(chunks), params.f_min, params.f_max))
    return np.sort(freqs)


def evaluate(params: Params, x_frac: Optional[float] = None, y_frac: Optional[float] = None,
             orientation_deg: Optional[float] = None, freqs: Optional[np.ndarray] = None,
             source_f: Optional[float] = None, source_2f: Optional[float] = None) -> dict:
    """Run the full chain for one PCB geometry / MLCC position / orientation."""
    plate = build_plate(params)
    modes = get_modes(params, plate)

    x_frac = params.mlcc_x_frac if x_frac is None else x_frac
    y_frac = params.mlcc_y_frac if y_frac is None else y_frac
    orientation_deg = params.orientation_deg if orientation_deg is None else orientation_deg

    if source_f is None or source_2f is None:
        s_f, s_2f = src.normalized_source(params.r_harmonic)
        source_f = s_f if source_f is None else source_f
        source_2f = s_2f if source_2f is None else source_2f

    if freqs is None:
        resonances = [md.f_n for md in modes]
        freqs = refine_freq_grid(params, resonances, coarse_n=params.n_freq_points)

    resp_f, resp_2f = frequency_sweep(plate, modes, x_frac, y_frac, orientation_deg,
                                       freqs, source_f, source_2f)
    return {
        "plate": plate,
        "modes": modes,
        "freqs": freqs,
        "resp_f": resp_f,
        "resp_2f": resp_2f,
    }


def find_resonance_peaks(freqs, response, prominence_frac: float = 0.05) -> np.ndarray:
    """Pick resonance peaks out of a frequency response curve."""
    response = np.asarray(response)
    if response.size == 0 or response.max() <= 0:
        return np.array([])
    prominence = prominence_frac * response.max()
    idx, _ = find_peaks(response, prominence=prominence)
    return np.asarray(freqs)[idx]
