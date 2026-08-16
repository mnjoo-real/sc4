"""Design sweep: choose PCB geometry, then MLCC position and orientation,
and write the figures / recommendation table described in the README.

    python run_sweep.py geometry
    python run_sweep.py position
    python run_sweep.py all

All outputs are written to out/.
"""

import itertools
import os
import sys
from dataclasses import replace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from model import Params, build_plate, get_modes, evaluate, find_resonance_peaks

OUT_DIR = "out"

# geometry sweep (README section 2)
PCB_LENGTHS = [0.060, 0.080, 0.100]
PCB_WIDTHS = [0.030, 0.040]
PCB_THICKNESSES = [0.0008, 0.0010, 0.0016]

# MLCC position / orientation sweep (README section 2)
X_FRACS = [0.20, 0.35, 0.50, 0.65, 0.80]
Y_FRACS = [0.25, 0.50, 0.75]
ORIENTATIONS = [0.0, 90.0]


def _base_params() -> Params:
    return Params()


# ---------------------------------------------------------------- geometry


def sweep_geometry(base: Params, out_dir: str = OUT_DIR):
    """Predict resonant frequencies for candidate PCB geometries and score
    them against the criteria in the README:

    - at least a few resonances inside the excitation range,
    - resonances separated enough to identify experimentally,
    - no extreme sensitivity to small geometry changes.
    """
    records = []
    for L, W, h in itertools.product(PCB_LENGTHS, PCB_WIDTHS, PCB_THICKNESSES):
        params = replace(base, pcb_L=L, pcb_W=W, pcb_h=h)
        plate = build_plate(params)
        modes = get_modes(params, plate, f_max=params.f_max)
        f_res = sorted(md.f_n for md in modes if md.f_n >= params.f_min)

        n_in_range = len(f_res)
        if n_in_range >= 2:
            spacing = float(np.min(np.diff(f_res)))
        elif n_in_range == 1:
            spacing = params.f_max - params.f_min
        else:
            spacing = 0.0

        # sensitivity: relative shift of the lowest in-range resonance for a
        # +2% length perturbation (a fragile design would shift a lot)
        params_pert = replace(params, pcb_L=L * 1.02)
        plate_pert = build_plate(params_pert)
        modes_pert = get_modes(params_pert, plate_pert, f_max=params.f_max)
        f_pert = [md.f_n for md in modes_pert if md.f_n >= params.f_min]
        if f_res and f_pert:
            sensitivity = abs(min(f_pert) - f_res[0]) / f_res[0]
        elif f_res:
            sensitivity = 1.0
        else:
            sensitivity = 1.0

        score = n_in_range * 1000.0 + spacing - 5000.0 * sensitivity

        records.append(dict(L=L, W=W, h=h, n_in_range=n_in_range,
                             spacing_hz=spacing, sensitivity=sensitivity,
                             score=score, resonances=f_res))

    df = pd.DataFrame(records).sort_values("score", ascending=False).reset_index(drop=True)
    _plot_geometry_sweep(df, base, out_dir)
    best = df.iloc[0].to_dict()
    return df, best


def _plot_geometry_sweep(df: pd.DataFrame, base: Params, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    fig, axes = plt.subplots(1, len(PCB_WIDTHS), figsize=(6 * len(PCB_WIDTHS), 5), sharey=True)
    axes = np.atleast_1d(axes)

    for ax, W in zip(axes, PCB_WIDTHS):
        sub = df[df["W"] == W]
        for i, h in enumerate(PCB_THICKNESSES):
            rows = sub[sub["h"] == h].sort_values("L")
            color = plt.cm.viridis(i / max(1, len(PCB_THICKNESSES) - 1))
            first = True
            for _, row in rows.iterrows():
                f_res = row["resonances"]
                if not f_res:
                    continue
                ax.plot([row["L"] * 1e3] * len(f_res), f_res, "o", color=color,
                        label=f"h={h*1e3:.2g} mm" if first else None)
                first = False
        ax.axhspan(base.f_min, base.f_max, color="grey", alpha=0.12,
                    label="planned excitation range" if W == PCB_WIDTHS[0] else None)
        ax.set_title(f"width = {W*1e3:.0f} mm")
        ax.set_xlabel("PCB length (mm)")
        ax.legend(fontsize=8, loc="upper right")
    axes[0].set_ylabel("resonant frequency (Hz)")
    fig.suptitle("Predicted PCB resonances vs geometry")
    fig.tight_layout()
    path = os.path.join(out_dir, "fig2_geometry_sweep.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"wrote {path}")


# ---------------------------------------------------------------- position


def sweep_position(params: Params, out_dir: str = OUT_DIR):
    """Scan MLCC position and orientation for a fixed PCB geometry."""
    freqs = np.linspace(params.f_min, params.f_max, params.n_freq_points)

    records = []
    for x_frac, y_frac, orientation in itertools.product(X_FRACS, Y_FRACS, ORIENTATIONS):
        result = evaluate(params, x_frac=x_frac, y_frac=y_frac,
                           orientation_deg=orientation, freqs=freqs)
        peak = float(np.max(np.maximum(result["resp_f"], result["resp_2f"])))
        records.append(dict(x_frac=x_frac, y_frac=y_frac, orientation=orientation, peak=peak))

    df = pd.DataFrame(records)
    _plot_position_map(df, out_dir)
    _plot_orientation(df, out_dir)

    strong = df.loc[df["peak"].idxmax()].to_dict()
    control = df.loc[df["peak"].idxmin()].to_dict()
    return df, strong, control


def _plot_position_map(df: pd.DataFrame, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    fig, axes = plt.subplots(1, len(ORIENTATIONS), figsize=(6 * len(ORIENTATIONS), 5))
    axes = np.atleast_1d(axes)

    for ax, orientation in zip(axes, ORIENTATIONS):
        sub = df[df["orientation"] == orientation]
        pivot = sub.pivot(index="y_frac", columns="x_frac", values="peak")
        im = ax.pcolormesh(pivot.columns.values, pivot.index.values, pivot.values,
                            shading="nearest", cmap="viridis")
        ax.set_xticks(pivot.columns.values)
        ax.set_yticks(pivot.index.values)
        ax.set_title(f"orientation = {orientation:.0f} deg")
        ax.set_xlabel("x / a")
        ax.set_ylabel("y / b")
        fig.colorbar(im, ax=ax, label="peak relative velocity")
    fig.suptitle("Predicted PCB vibration vs MLCC position")
    fig.tight_layout()
    path = os.path.join(out_dir, "fig4_position_map.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"wrote {path}")


def _plot_orientation(df: pd.DataFrame, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    strong_pos = df.loc[df["peak"].idxmax()]
    sub = df[(df["x_frac"] == strong_pos["x_frac"]) & (df["y_frac"] == strong_pos["y_frac"])]
    sub = sub.sort_values("orientation")

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar([f"{o:.0f} deg" for o in sub["orientation"]], sub["peak"])
    ax.set_ylabel("peak relative velocity")
    ax.set_title(f"Orientation at x/a={strong_pos['x_frac']:.2f}, y/b={strong_pos['y_frac']:.2f}")
    fig.tight_layout()
    path = os.path.join(out_dir, "fig5_orientation.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"wrote {path}")


# --------------------------------------------------------- frequency response


def frequency_response_figure(params: Params, x_frac: float, y_frac: float,
                               orientation_deg: float, out_dir: str = OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    result = evaluate(params, x_frac=x_frac, y_frac=y_frac, orientation_deg=orientation_deg)
    freqs, resp_f, resp_2f = result["freqs"], result["resp_f"], result["resp_2f"]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(freqs, resp_f, label="response at f")
    ax.plot(freqs, resp_2f, label="response at 2f")
    ax.set_xlabel("electrical excitation frequency (Hz)")
    ax.set_ylabel("relative PCB velocity amplitude")
    ax.set_title(f"Frequency response — x/a={x_frac:.2f}, y/b={y_frac:.2f}, "
                 f"orientation={orientation_deg:.0f} deg")
    ax.legend()
    fig.tight_layout()
    path = os.path.join(out_dir, "fig3_frequency_response.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"wrote {path}")

    peaks_f = find_resonance_peaks(freqs, resp_f)
    peaks_2f = find_resonance_peaks(freqs, resp_2f)
    all_peaks = sorted(set(np.round(np.concatenate([peaks_f, peaks_2f]), 1))) if (
        len(peaks_f) or len(peaks_2f)) else []
    return result, all_peaks


# ---------------------------------------------------------------- recommendation


def write_recommendation(params: Params, strong: dict, control: dict, resonances,
                          out_dir: str = OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    rows = [
        ("PCB length", f"{params.pcb_L*1e3:.0f} mm"),
        ("PCB width", f"{params.pcb_W*1e3:.0f} mm"),
        ("PCB thickness", f"{params.pcb_h*1e3:.2g} mm"),
        ("MLCC x-position", f"x/a = {strong['x_frac']:.2f}"),
        ("MLCC y-position", f"y/b = {strong['y_frac']:.2f}"),
        ("MLCC orientation", f"{strong['orientation']:.0f} deg"),
        ("main frequency range", f"{params.f_min:.0f}-{params.f_max:.0f} Hz"),
        ("resonance frequencies",
         ", ".join(f"{f:.0f}" for f in resonances) if len(resonances) else "n/a"),
        ("strong-response condition",
         f"x/a={strong['x_frac']:.2f}, y/b={strong['y_frac']:.2f}, "
         f"orientation={strong['orientation']:.0f} deg (peak={strong['peak']:.3g})"),
        ("control condition",
         f"x/a={control['x_frac']:.2f}, y/b={control['y_frac']:.2f}, "
         f"orientation={control['orientation']:.0f} deg (peak={control['peak']:.3g})"),
    ]
    df = pd.DataFrame(rows, columns=["parameter", "recommended value"])
    path = os.path.join(out_dir, "recommended_setup.csv")
    df.to_csv(path, index=False)
    print(f"wrote {path}")
    return df


# ---------------------------------------------------------------- main


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode not in ("geometry", "position", "all"):
        print(f"unknown sweep mode: {mode!r} (expected geometry|position|all)")
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    base = _base_params()

    if mode == "geometry":
        geom_df, geom_best = sweep_geometry(base)
        print(f"best geometry: L={geom_best['L']*1e3:.0f} mm, W={geom_best['W']*1e3:.0f} mm, "
              f"h={geom_best['h']*1e3:.2g} mm ({geom_best['n_in_range']} resonances in range)")
        return

    if mode == "position":
        pos_df, strong, control = sweep_position(base)
        print(f"strong-response position: x/a={strong['x_frac']:.2f}, y/b={strong['y_frac']:.2f}, "
              f"orientation={strong['orientation']:.0f} deg")
        print(f"control position:         x/a={control['x_frac']:.2f}, y/b={control['y_frac']:.2f}, "
              f"orientation={control['orientation']:.0f} deg")
        return

    # mode == "all": run the full design chain in order
    geom_df, geom_best = sweep_geometry(base)
    print(f"best geometry: L={geom_best['L']*1e3:.0f} mm, W={geom_best['W']*1e3:.0f} mm, "
          f"h={geom_best['h']*1e3:.2g} mm ({geom_best['n_in_range']} resonances in range)")

    params = replace(base, pcb_L=geom_best["L"], pcb_W=geom_best["W"], pcb_h=geom_best["h"])

    pos_df, strong, control = sweep_position(params)
    print(f"strong-response position: x/a={strong['x_frac']:.2f}, y/b={strong['y_frac']:.2f}, "
          f"orientation={strong['orientation']:.0f} deg")
    print(f"control position:         x/a={control['x_frac']:.2f}, y/b={control['y_frac']:.2f}, "
          f"orientation={control['orientation']:.0f} deg")

    result, resonances = frequency_response_figure(
        params, strong["x_frac"], strong["y_frac"], strong["orientation"])

    write_recommendation(params, strong, control, resonances)


if __name__ == "__main__":
    main()
