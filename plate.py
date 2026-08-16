"""Rectangular thin-plate model of the PCB.

The PCB is approximated as an isotropic, simply supported rectangular thin
plate (see README section 1). This is deliberately a low-fidelity model:
it is meant to guide PCB geometry / MLCC placement decisions, not to
reproduce a real clamped board exactly.
"""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np


def bending_rigidity(E: float, h: float, nu: float) -> float:
    """D = E h^3 / [12(1 - nu^2)]"""
    return E * h ** 3 / (12.0 * (1.0 - nu ** 2))


def natural_frequency(m: int, n: int, a: float, b: float, D: float, rho: float, h: float) -> float:
    """f_mn for a simply supported rectangular plate."""
    omega_mn = np.pi ** 2 * np.sqrt(D / (rho * h)) * (m ** 2 / a ** 2 + n ** 2 / b ** 2)
    return omega_mn / (2.0 * np.pi)


def mode_shape(m: int, n: int, a: float, b: float, x, y):
    """phi_mn(x, y) = sin(m*pi*x/a) * sin(n*pi*y/b)"""
    return np.sin(m * np.pi * x / a) * np.sin(n * np.pi * y / b)


def mode_shape_grad(m: int, n: int, a: float, b: float, x, y):
    """(dphi_mn/dx, dphi_mn/dy) at (x, y)."""
    dphi_dx = (m * np.pi / a) * np.cos(m * np.pi * x / a) * np.sin(n * np.pi * y / b)
    dphi_dy = (n * np.pi / b) * np.sin(m * np.pi * x / a) * np.cos(n * np.pi * y / b)
    return dphi_dx, dphi_dy


@dataclass
class Mode:
    m: int
    n: int
    f_n: float
    omega_n: float
    modal_mass: float


@dataclass
class Plate:
    a: float          # length (m)
    b: float          # width (m)
    h: float          # thickness (m)
    E: float           # effective Young's modulus (Pa)
    rho: float          # density (kg/m^3)
    nu: float          # Poisson ratio
    damping: float = 0.02  # modal damping ratio, applied to every mode

    def __post_init__(self):
        self.D = bending_rigidity(self.E, self.h, self.nu)

    def natural_frequency(self, m: int, n: int) -> float:
        return natural_frequency(m, n, self.a, self.b, self.D, self.rho, self.h)

    def mode_shape(self, m: int, n: int, x, y):
        return mode_shape(m, n, self.a, self.b, x, y)

    def mode_shape_grad(self, m: int, n: int, x, y):
        return mode_shape_grad(m, n, self.a, self.b, x, y)

    def modal_mass(self, m: int, n: int) -> float:
        """Generalized mass for the unit-amplitude sin*sin mode shape:
        rho*h * integral(phi_mn^2) over the plate = rho*h*a*b/4.
        """
        return self.rho * self.h * self.a * self.b / 4.0

    def modes(self, m_max: int = 4, n_max: int = 4, f_max: Optional[float] = None) -> List[Mode]:
        """First few (m, n) modes, sorted by natural frequency."""
        modes = []
        for m in range(1, m_max + 1):
            for n in range(1, n_max + 1):
                f_n = self.natural_frequency(m, n)
                if f_max is not None and f_n > f_max:
                    continue
                modes.append(Mode(m=m, n=n, f_n=f_n, omega_n=2 * np.pi * f_n,
                                   modal_mass=self.modal_mass(m, n)))
        modes.sort(key=lambda md: md.f_n)
        return modes
