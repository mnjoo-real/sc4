"""How strongly a soldered MLCC couples to each PCB mode.

Two coupling laws are implemented (README section 1):

- a simple point-force source, coupling ~ phi_mn(x_c, y_c) -- strong near
  an antinode, weak near a node;
- a small force couple / moment, appropriate for a soldered part, where
  coupling depends on the local slope of the mode shape and therefore on
  MLCC orientation:

      x-oriented MLCC:  coupling ~ dphi_mn/dx
      y-oriented MLCC:  coupling ~ dphi_mn/dy
"""

import numpy as np

from plate import Plate


def point_force_coupling(plate: Plate, m: int, n: int, x_frac: float, y_frac: float) -> float:
    """coupling ~ phi_mn(x_c, y_c) for a simple point-force source."""
    x = x_frac * plate.a
    y = y_frac * plate.b
    return plate.mode_shape(m, n, x, y)


def moment_coupling(plate: Plate, m: int, n: int, x_frac: float, y_frac: float,
                     orientation_deg: float) -> float:
    """coupling for a soldered MLCC acting as a small force couple / moment.

    orientation_deg = 0   -> x-oriented MLCC, coupling ~ dphi/dx
    orientation_deg = 90  -> y-oriented MLCC, coupling ~ dphi/dy

    Intermediate angles blend the two components, so this also covers the
    general in-between orientation.
    """
    x = x_frac * plate.a
    y = y_frac * plate.b
    dphi_dx, dphi_dy = plate.mode_shape_grad(m, n, x, y)
    theta = np.radians(orientation_deg)
    return np.cos(theta) * dphi_dx + np.sin(theta) * dphi_dy


def mode_coupling(plate: Plate, m: int, n: int, x_frac: float, y_frac: float,
                   orientation_deg: float) -> float:
    """Coupling used for the main position/orientation sweep.

    A soldered MLCC couples to the board mainly through the solder-joint
    moment (this is what makes orientation matter), so this is the
    moment coupling.
    """
    return moment_coupling(plate, m, n, x_frac, y_frac, orientation_deg)
