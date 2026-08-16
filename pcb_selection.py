"""Final PCB candidate comparison and robustness pass, ahead of ordering.

This uses only the existing reduced-order model (plate.py / coupling.py /
response.py / source.py) -- no FEM, no acoustic radiation model, no
detailed solder or MLCC-layer physics. The goal here is the PCB ordering
decision, not improving the physics model.

It answers: is the geometry-sweep winner (currently 100x40x0.8 mm, picked
mainly because it has the most resonances in range) actually the best
experimental choice once response strength and robustness are considered
too, compared against the next-best candidates such as 100x40x1.0 mm.

    python pcb_selection.py

Writes:
    out/fig6_pcb_robustness.png
    out/pcb_candidate_comparison.csv
    out/final_pcb_recommendation.txt
"""

import os
from dataclasses import replace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from model import Params, build_plate, get_modes, evaluate
from run_sweep import sweep_geometry, compute_position_scan

OUT_DIR = "out"

N_CANDIDATES = 5                        # top-N from the existing geometry-sweep score
MUST_INCLUDE = [(0.100, 0.040, 0.0008),  # the two boards under direct comparison
                 (0.100, 0.040, 0.0010)]

E_FACTORS = [0.8, 1.0, 1.2]              # E_pcb: nominal +/- 20%
DAMPING_VALUES = [0.01, 0.02, 0.04]
POSITION_OFFSETS_MM = [-1.0, 0.0, 1.0]   # MLCC placement tolerance

ORIENTATION_USEFUL_RATIO = 1.15          # 0/90 deg peak ratio above this counts as "useful"


def _base_params() -> Params:
    return Params()


# --------------------------------------------------------- candidate selection


def select_candidates(base: Params):
    """Top geometry-sweep candidates, always including the two boards the
    user asked to compare directly even if they fall outside the top-N.
    """
    geom_df, _ = sweep_geometry(base)  # reuses the existing sweep; also (re)writes fig2
    top = geom_df.head(N_CANDIDATES).copy()

    for L, W, h in MUST_INCLUDE:
        already_in = ((np.isclose(top["L"], L) & np.isclose(top["W"], W) & np.isclose(top["h"], h)).any())
        if not already_in:
            row = geom_df[np.isclose(geom_df["L"], L) & np.isclose(geom_df["W"], W)
                           & np.isclose(geom_df["h"], h)]
            top = pd.concat([top, row], ignore_index=True)

    return top.reset_index(drop=True)


# --------------------------------------------------------- per-candidate summary


def evaluate_candidate(base: Params, geom_row) -> dict:
    """Nominal resonance / response / position / orientation summary for one
    PCB geometry, at nominal material and damping values.
    """
    params = replace(base, pcb_L=geom_row["L"], pcb_W=geom_row["W"], pcb_h=geom_row["h"])
    pos_df = compute_position_scan(params)

    strong = pos_df.loc[pos_df["peak"].idxmax()]
    control = pos_df.loc[pos_df["peak"].idxmin()]
    strong_control_ratio = strong["peak"] / control["peak"] if control["peak"] > 0 else np.inf

    same_pos = pos_df[(pos_df["x_frac"] == strong["x_frac"]) & (pos_df["y_frac"] == strong["y_frac"])]
    peak_by_orientation = same_pos.set_index("orientation")["peak"]
    orientation_ratio = (peak_by_orientation.max() / peak_by_orientation.min()
                          if peak_by_orientation.min() > 0 else np.inf)
    better_orientation = float(peak_by_orientation.idxmax())

    f_res = sorted(geom_row["resonances"])
    spacings = np.diff(f_res) if len(f_res) >= 2 else np.array([])
    min_spacing = float(spacings.min()) if len(spacings) else float("nan")

    return dict(
        L=geom_row["L"], W=geom_row["W"], h=geom_row["h"],
        resonances=f_res, n_resonances=len(f_res),
        min_spacing_hz=min_spacing, spacings_hz=spacings.tolist(),
        max_response=float(pos_df["peak"].max()),
        strong_x=float(strong["x_frac"]), strong_y=float(strong["y_frac"]),
        strong_orientation=float(strong["orientation"]), strong_peak=float(strong["peak"]),
        control_x=float(control["x_frac"]), control_y=float(control["y_frac"]),
        control_orientation=float(control["orientation"]), control_peak=float(control["peak"]),
        strong_control_ratio=float(strong_control_ratio),
        orientation_ratio=float(orientation_ratio),
        better_orientation_deg=better_orientation,
    )


# --------------------------------------------------------- robustness sweep


def robustness_sweep(candidate: dict):
    """Lightweight one-factor-at-a-time robustness check around the nominal
    strong-response configuration for one PCB candidate:
    E_pcb +/- 20%, damping in {0.01, 0.02, 0.04}, MLCC placement +/- 1 mm.
    """
    base_params = replace(Params(), pcb_L=candidate["L"], pcb_W=candidate["W"], pcb_h=candidate["h"])
    x0, y0, orient0 = candidate["strong_x"], candidate["strong_y"], candidate["strong_orientation"]

    rows = []

    # E_pcb: does the resonance count / position inside the band survive?
    for factor in E_FACTORS:
        params = replace(base_params, E_pcb=base_params.E_pcb * factor)
        plate = build_plate(params)
        modes = get_modes(params, plate, f_max=params.f_max)
        n_in_range = sum(1 for md in modes if md.f_n >= params.f_min)
        result = evaluate(params, x_frac=x0, y_frac=y0, orientation_deg=orient0)
        peak = float(max(result["resp_f"].max(), result["resp_2f"].max()))
        rows.append(dict(factor="E_pcb", value=factor, n_in_range=n_in_range, peak=peak))

    # damping: how much does the peak drop as damping rises?
    for zeta in DAMPING_VALUES:
        params = replace(base_params, damping=zeta)
        result = evaluate(params, x_frac=x0, y_frac=y0, orientation_deg=orient0)
        peak = float(max(result["resp_f"].max(), result["resp_2f"].max()))
        rows.append(dict(factor="damping", value=zeta, n_in_range=candidate["n_resonances"], peak=peak))

    # MLCC placement tolerance: +/- 1 mm around the nominal strong position
    dx_frac_per_mm = 1.0e-3 / base_params.pcb_L
    dy_frac_per_mm = 1.0e-3 / base_params.pcb_W
    for dx_mm in POSITION_OFFSETS_MM:
        x_frac = float(np.clip(x0 + dx_mm * dx_frac_per_mm, 0.02, 0.98))
        result = evaluate(base_params, x_frac=x_frac, y_frac=y0, orientation_deg=orient0)
        peak = float(max(result["resp_f"].max(), result["resp_2f"].max()))
        rows.append(dict(factor="x_offset_mm", value=dx_mm, n_in_range=candidate["n_resonances"], peak=peak))
    for dy_mm in POSITION_OFFSETS_MM:
        y_frac = float(np.clip(y0 + dy_mm * dy_frac_per_mm, 0.02, 0.98))
        result = evaluate(base_params, x_frac=x0, y_frac=y_frac, orientation_deg=orient0)
        peak = float(max(result["resp_f"].max(), result["resp_2f"].max()))
        rows.append(dict(factor="y_offset_mm", value=dy_mm, n_in_range=candidate["n_resonances"], peak=peak))

    df = pd.DataFrame(rows)

    e_rows = df[df["factor"] == "E_pcb"]
    nominal_n = candidate["n_resonances"]
    resonance_count_stability = (e_rows["n_in_range"].min() / nominal_n) if nominal_n else 0.0

    damping_rows = df[df["factor"] == "damping"]
    peak_low_zeta = damping_rows.loc[damping_rows["value"] == min(DAMPING_VALUES), "peak"].iloc[0]
    peak_high_zeta = damping_rows.loc[damping_rows["value"] == max(DAMPING_VALUES), "peak"].iloc[0]
    damping_peak_retention = (peak_high_zeta / peak_low_zeta) if peak_low_zeta > 0 else 0.0

    pos_rows = df[df["factor"].isin(["x_offset_mm", "y_offset_mm"])]
    peak_mean = pos_rows["peak"].mean()
    position_sensitivity = (pos_rows["peak"].std() / peak_mean) if peak_mean > 0 else np.inf

    stability = dict(
        resonance_count_stability=float(resonance_count_stability),
        damping_peak_retention=float(damping_peak_retention),
        position_sensitivity=float(position_sensitivity),
    )
    return df, stability


# --------------------------------------------------------- ranking + outputs


def _plot_robustness(candidates: list, out_dir: str = OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

    for cand in candidates:
        label = cand["label"]
        df = cand["robustness_df"]

        e_rows = df[df["factor"] == "E_pcb"].sort_values("value")
        axes[0].plot(e_rows["value"], e_rows["peak"], "o-", label=label)

        d_rows = df[df["factor"] == "damping"].sort_values("value")
        axes[1].plot(d_rows["value"], d_rows["peak"], "o-", label=label)

        x_rows = df[df["factor"] == "x_offset_mm"].sort_values("value")
        axes[2].plot(x_rows["value"], x_rows["peak"], "o-", label=label)

    axes[0].set_xlabel("E_pcb / E_pcb,nominal")
    axes[0].set_ylabel("peak relative velocity")
    axes[0].set_title("Sensitivity to effective Young's modulus")

    axes[1].set_xlabel("damping ratio")
    axes[1].set_title("Sensitivity to damping")

    axes[2].set_xlabel("MLCC x offset (mm)")
    axes[2].set_title("Sensitivity to placement tolerance (+/-1 mm)")

    for ax in axes:
        ax.legend(fontsize=7)

    fig.suptitle("PCB candidate robustness under material / damping / placement uncertainty")
    fig.tight_layout()
    path = os.path.join(out_dir, "fig6_pcb_robustness.png")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"wrote {path}")


def _describe(row) -> str:
    n_res = row["n_resonances_in_range"]
    spacing = "n/a" if np.isnan(row["min_spacing_hz"]) else f"{row['min_spacing_hz']:.0f} Hz"
    return (f"{row['PCB_length_mm']:.0f}x{row['PCB_width_mm']:.0f}x{row['PCB_thickness_mm']:.2g}mm: "
            f"{n_res} resonance{'s' if n_res != 1 else ''} ({row['resonances_hz']} Hz), "
            f"min spacing {spacing}, strong/control ratio "
            f"{row['strong_control_ratio']:.2f}x, orientation ratio {row['orientation_ratio']:.2f}x, "
            f"resonance-count stability {row['resonance_count_stability']:.2f}, "
            f"damping peak retention {row['damping_peak_retention']:.2f}, "
            f"placement sensitivity {row['position_sensitivity']:.2f}")


def _merge_intervals(intervals):
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def build_comparison_table(candidates: list) -> pd.DataFrame:
    rows = []
    for cand in candidates:
        overall_stability = (cand["resonance_count_stability"]
                              * cand["damping_peak_retention"]
                              * max(0.0, 1.0 - min(cand["position_sensitivity"], 1.0)))
        spacing = cand["min_spacing_hz"] if not np.isnan(cand["min_spacing_hz"]) else 0.0
        # composite score: response contrast x resonance separation x robustness.
        # deliberately NOT a function of resonance count alone.
        score = cand["strong_control_ratio"] * (spacing / 100.0) * overall_stability

        rows.append(dict(
            PCB_length_mm=cand["L"] * 1e3,
            PCB_width_mm=cand["W"] * 1e3,
            PCB_thickness_mm=cand["h"] * 1e3,
            n_resonances_in_range=cand["n_resonances"],
            resonances_hz=", ".join(f"{f:.0f}" for f in cand["resonances"]),
            adjacent_spacings_hz=", ".join(f"{s:.0f}" for s in cand["spacings_hz"]),
            min_spacing_hz=cand["min_spacing_hz"],
            max_response=cand["max_response"],
            strong_position=(f"x/a={cand['strong_x']:.2f}, y/b={cand['strong_y']:.2f}, "
                              f"{cand['strong_orientation']:.0f} deg"),
            control_position=(f"x/a={cand['control_x']:.2f}, y/b={cand['control_y']:.2f}, "
                               f"{cand['control_orientation']:.0f} deg"),
            strong_control_ratio=cand["strong_control_ratio"],
            orientation_ratio=cand["orientation_ratio"],
            better_orientation_deg=cand["better_orientation_deg"],
            resonance_count_stability=cand["resonance_count_stability"],
            damping_peak_retention=cand["damping_peak_retention"],
            position_sensitivity=cand["position_sensitivity"],
            overall_stability=overall_stability,
            score=score,
        ))

    df = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", np.arange(1, len(df) + 1))
    return df


def write_recommendation(winner: pd.Series, comparison_df: pd.DataFrame, out_dir: str = OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    f_min, f_max = Params().f_min, Params().f_max

    resonances = ([float(f) for f in winner["resonances_hz"].split(", ")]
                  if winner["resonances_hz"] else [])
    dense_intervals = set()
    for f_res in resonances:
        span = 0.15 * f_res
        dense_intervals.add((round(max(f_min, f_res - span)), round(min(f_max, f_res + span))))
        f_half = f_res / 2.0
        if f_min <= f_half <= f_max:
            span_half = 0.15 * f_half
            dense_intervals.add((round(max(f_min, f_half - span_half)), round(min(f_max, f_half + span_half))))
    dense_intervals = _merge_intervals(dense_intervals)

    orientation_note = ("useful (worth including as an experimental variable)"
                         if winner["orientation_ratio"] > ORIENTATION_USEFUL_RATIO
                         else "small (orientation is not a strong experimental lever here)")

    lines = [
        "Final PCB recommendation",
        "=========================",
        "",
        "Reduced-order model only (isotropic simply-supported thin plate, lumped",
        "MLCC source at f and 2f, per README.md). No FEM, acoustic radiation model,",
        "or detailed solder / MLCC-layer physics was used for this decision -- see",
        "pcb_candidate_comparison.csv for the full candidate comparison and",
        "fig6_pcb_robustness.png for the uncertainty sweep behind it.",
        "",
        "Recommended PCB geometry:",
        f"  length    = {winner['PCB_length_mm']:.0f} mm",
        f"  width     = {winner['PCB_width_mm']:.0f} mm",
        f"  thickness = {winner['PCB_thickness_mm']:.2g} mm",
        "",
        "Recommended strong-response MLCC position and orientation:",
        f"  {winner['strong_position']}",
        "",
        "Recommended weak-control MLCC position:",
        f"  {winner['control_position']}",
        "",
        "Main resonance frequencies to target experimentally (Hz):",
        f"  {winner['resonances_hz']}",
        f"  (adjacent spacings: {winner['adjacent_spacings_hz']} Hz;"
        f" minimum spacing {winner['min_spacing_hz']:.0f} Hz)",
        "",
        "Electrical excitation frequency intervals to scan more densely",
        "(around each in-range resonance, and around half that frequency since",
        "the second harmonic 2f can also excite it there):",
    ]
    lines += [f"  {a:.0f}-{b:.0f} Hz" for a, b in dense_intervals]
    lines += [
        "",
        f"Predicted strong/control response ratio: {winner['strong_control_ratio']:.2f}x",
        f"Predicted 0 deg vs 90 deg orientation response ratio: {winner['orientation_ratio']:.2f}x"
        f" (better orientation: {winner['better_orientation_deg']:.0f} deg) -- {orientation_note}",
        "",
        "Robustness under uncertainty sweep (E_pcb +/-20%, damping in {0.01,0.02,0.04},",
        "MLCC placement +/-1 mm):",
        f"  resonance-count stability : {winner['resonance_count_stability']:.2f}"
        " (fraction of in-range resonances retained under +/-20% E_pcb)",
        f"  damping peak retention    : {winner['damping_peak_retention']:.2f}"
        " (peak response at damping=0.04 relative to damping=0.01)",
        f"  placement sensitivity     : {winner['position_sensitivity']:.2f}"
        " (relative std of peak response under +/-1 mm placement error; lower is more robust)",
        "",
        "Why this PCB was selected over the alternatives:",
        "",
        f"- selected: {_describe(winner)}",
    ]
    for _, row in comparison_df.iloc[1:].iterrows():
        lines.append(f"- alternative: {_describe(row)}")

    def _find(L, W, h):
        match = comparison_df[np.isclose(comparison_df["PCB_length_mm"], L)
                               & np.isclose(comparison_df["PCB_width_mm"], W)
                               & np.isclose(comparison_df["PCB_thickness_mm"], h)]
        return match.iloc[0] if len(match) else None

    r08 = _find(100, 40, 0.8)
    r10 = _find(100, 40, 1.0)
    if r08 is not None and r10 is not None:
        lines += [
            "",
            "100x40x0.8mm vs 100x40x1.0mm (the two boards directly under comparison):",
            f"  0.8 mm (rank {r08['rank']}): {_describe(r08)}",
            f"  1.0 mm (rank {r10['rank']}): {_describe(r10)}",
        ]
        if winner["PCB_thickness_mm"] == r08["PCB_thickness_mm"]:
            lines.append("  The 0.8 mm board wins on more than resonance count alone: it also has the")
            lines.append("  larger strong/control contrast and/or better separation and robustness")
            lines.append("  once material, damping, and placement uncertainty are taken into account.")
        elif winner["PCB_thickness_mm"] == r10["PCB_thickness_mm"]:
            lines.append("  This overturns the earlier resonance-count-only pick: the 1.0 mm board gives")
            lines.append("  a weaker resonance count but a better strong/control contrast and/or more")
            lines.append("  robust behavior under the uncertainty sweep, which matters more for a clean")
            lines.append("  experimental demonstration.")
        else:
            lines.append("  Neither is the final pick: a third candidate scores higher on response")
            lines.append("  contrast, separation, and robustness combined -- see the ranked table above.")

    path = os.path.join(out_dir, "final_pcb_recommendation.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {path}")


# --------------------------------------------------------- main


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    base = _base_params()

    candidates_df = select_candidates(base)
    print(f"comparing {len(candidates_df)} PCB candidates:")
    for _, row in candidates_df.iterrows():
        print(f"  {row['L']*1e3:.0f} x {row['W']*1e3:.0f} x {row['h']*1e3:.2g} mm "
              f"(geometry score={row['score']:.0f}, {row['n_in_range']} resonances in range)")

    candidates = []
    for _, geom_row in candidates_df.iterrows():
        cand = evaluate_candidate(base, geom_row)
        cand["label"] = f"{cand['L']*1e3:.0f}x{cand['W']*1e3:.0f}x{cand['h']*1e3:.2g}mm"
        rob_df, stability = robustness_sweep(cand)
        cand.update(stability)
        cand["robustness_df"] = rob_df
        candidates.append(cand)
        print(f"  -> {cand['label']}: strong/control={cand['strong_control_ratio']:.2f}x, "
              f"orientation ratio={cand['orientation_ratio']:.2f}x, "
              f"stability(res/damp/pos)="
              f"{stability['resonance_count_stability']:.2f}/"
              f"{stability['damping_peak_retention']:.2f}/"
              f"{stability['position_sensitivity']:.2f}")

    _plot_robustness(candidates)

    comparison_df = build_comparison_table(candidates)
    csv_path = os.path.join(OUT_DIR, "pcb_candidate_comparison.csv")
    comparison_df.to_csv(csv_path, index=False)
    print(f"wrote {csv_path}")

    winner = comparison_df.iloc[0]
    print(f"\nfinal recommendation: {winner['PCB_length_mm']:.0f}x{winner['PCB_width_mm']:.0f}x"
          f"{winner['PCB_thickness_mm']:.2g}mm (score={winner['score']:.3g})")

    write_recommendation(winner, comparison_df)


if __name__ == "__main__":
    main()
