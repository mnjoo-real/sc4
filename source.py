"""MLCC source model.

The capacitor is treated as a relative vibration source at the electrical
excitation frequency f and its second harmonic 2f (README section 1/2),
not as a detailed electromechanical model of a specific commercial part.

    S = d E + M E^2

    E(t) = E_DC + E_AC cos(wt)

    A1 = (d + 2 M E_DC) E_AC      strain amplitude at f
    A2 = (1/2) M E_AC^2            strain amplitude at 2f
"""


def strain_amplitudes(d: float, M: float, E_dc: float, E_ac: float):
    """A1, A2 from the first-order electromechanical strain model."""
    A1 = (d + 2.0 * M * E_dc) * E_ac
    A2 = 0.5 * M * E_ac ** 2
    return A1, A2


def source_from_strain(A1: float, A2: float, C1: float = 1.0, C2: float = 1.0):
    """source_f = C1 * A1, source_2f = C2 * A2

    C1, C2 are configurable scale factors used when real d and M are
    available (or being explored as configuration parameters).
    """
    return C1 * A1, C2 * A2


def normalized_source(r_harmonic: float = 0.3):
    """Normalized source strengths for when d and M are not known.

    source_f = 1, source_2f = r_harmonic, so PCB design can be studied
    independently of the uncertain absolute MLCC vibration amplitude.
    """
    return 1.0, r_harmonic
