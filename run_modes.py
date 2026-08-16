"""Generate fig1_modes.png: baseline PCB mode shapes and natural frequencies.

    python run_modes.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from model import Params, build_plate, get_modes

OUT_DIR = "out"
N_MODES_SHOWN = 6


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    params = Params()  # baseline: 100 x 40 x 1.0 mm (Kim et al. 2019)
    plate = build_plate(params)
    modes = get_modes(params, plate)[:N_MODES_SHOWN]

    nx, ny = 60, 30
    xs = np.linspace(0, plate.a, nx)
    ys = np.linspace(0, plate.b, ny)
    X, Y = np.meshgrid(xs, ys)

    ncols = 3
    nrows = int(np.ceil(len(modes) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows))
    axes = np.atleast_1d(axes).ravel()

    for ax, mode in zip(axes, modes):
        Z = plate.mode_shape(mode.m, mode.n, X, Y)
        ax.pcolormesh(X * 1e3, Y * 1e3, Z, shading="auto", cmap="RdBu_r", vmin=-1, vmax=1)
        in_range = params.f_min <= mode.f_n <= params.f_max
        marker = " *" if in_range else ""
        ax.set_title(f"({mode.m},{mode.n})  f={mode.f_n:.0f} Hz{marker}")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        ax.set_aspect("equal")

    for ax in axes[len(modes):]:
        ax.axis("off")

    fig.suptitle(
        f"Baseline PCB {plate.a*1e3:.0f}x{plate.b*1e3:.0f}x{plate.h*1e3:.1f} mm — first modes "
        f"(* = inside {params.f_min:.0f}-{params.f_max:.0f} Hz excitation range)"
    )
    fig.tight_layout()
    out_path = os.path.join(OUT_DIR, "fig1_modes.png")
    fig.savefig(out_path, dpi=150)
    print(f"wrote {out_path}")

    for mode in modes:
        in_range = params.f_min <= mode.f_n <= params.f_max
        flag = "  <-- in excitation range" if in_range else ""
        print(f"  mode ({mode.m},{mode.n}): f = {mode.f_n:8.1f} Hz{flag}")


if __name__ == "__main__":
    main()
