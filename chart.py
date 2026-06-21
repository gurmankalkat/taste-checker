"""
chart.py — render one agreement chart from score.py output.

Saves to output/agreement.png.

DATA CONTRACT
─────────────
score.py must produce a dict with exactly these keys and pass it to render():

    {
        "n_total":               int,    # items with a parsed model verdict (denominator for detection rates)
        "n_clean":               int,    # human-labeled clean (subset of n_total)
        "n_clash":               int,    # human-labeled undertone_clash (subset of n_total)
        "detection_agreement":   float,  # fraction where model verdict matches human label (overall)
        "miss_rate":             float,  # fraction of clash items model called clean  ← headline
        "false_positive_rate":   float,  # fraction of clean items model called flawed
        "localization_rate":     float,  # fraction of (human=clash AND model=flawed) where is_undertone_clash=True
        "n_localization_eligible": int,  # denominator for localization_rate
    }

All float fields are in [0, 1]. If n_localization_eligible is 0,
score.py should set localization_rate to None; render() will show "n/a".

USAGE
─────
From score.py:
    import chart
    chart.render(scores)

Standalone smoke-test with dummy data:
    python chart.py
"""

import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUTPUT_PATH = pathlib.Path("output/agreement.png")


def render(scores: dict, output_path: pathlib.Path = OUTPUT_PATH) -> None:
    """Render the agreement chart and save to output_path."""
    output_path.parent.mkdir(exist_ok=True)

    det_agree = scores["detection_agreement"]
    miss       = scores["miss_rate"]
    fp         = scores["false_positive_rate"]
    loc        = scores["localization_rate"]   # may be None
    n          = scores["n_total"]
    n_clash    = scores["n_clash"]
    n_clean    = scores["n_clean"]
    n_elig     = scores["n_localization_eligible"]

    fig, (ax_det, ax_loc) = plt.subplots(
        1, 2,
        figsize=(9, 4.2),
        gridspec_kw={"width_ratios": [3, 1.4]},
    )
    fig.subplots_adjust(left=0.06, right=0.97, top=0.78, bottom=0.20, wspace=0.48)

    # ── detection axis ────────────────────────────────────────────────────────
    det_labels = ["overall\nagreement", "miss rate\n(clash → clean)", "false positive\n(clean → flawed)"]
    det_values = [det_agree, miss, fp]
    # green = want high; red = headline miss; orange = FP (different failure mode than miss)
    det_colors = ["#4a7c59", "#c0392b", "#d4820a"]

    bars = ax_det.bar(det_labels, det_values, color=det_colors, width=0.5, zorder=2)
    ax_det.set_ylim(0, 1.10)
    ax_det.set_yticks([0, 0.25, 0.50, 0.75, 1.0])
    ax_det.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8)
    ax_det.set_title("Detection", fontsize=10, fontweight="bold", pad=10)
    ax_det.axhline(0.5, color="#cccccc", linewidth=0.8, linestyle="--", zorder=1)
    ax_det.yaxis.grid(True, color="#eeeeee", linewidth=0.6, zorder=0)
    ax_det.set_axisbelow(True)
    ax_det.tick_params(axis="x", labelsize=8, length=0)
    ax_det.spines["top"].set_visible(False)
    ax_det.spines["right"].set_visible(False)
    ax_det.spines["left"].set_color("#cccccc")
    ax_det.spines["bottom"].set_color("#cccccc")

    for bar, val in zip(bars, det_values):
        ax_det.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.025,
            f"{val:.0%}",
            ha="center", va="bottom", fontsize=9, fontweight="bold", color="#222222",
        )

    ax_det.text(
        0.5, -0.26,
        f"n={n} scored   ({n_clash} clash, {n_clean} clean)",
        ha="center", va="top", transform=ax_det.transAxes,
        fontsize=8, color="#666666",
    )

    # ── localization axis ─────────────────────────────────────────────────────
    loc_display = loc if loc is not None else 0.0
    ax_loc.bar(["localization\nrate"], [loc_display], color="#2471a3", width=0.42, zorder=2)
    ax_loc.set_ylim(0, 1.10)
    ax_loc.set_yticks([0, 0.25, 0.50, 0.75, 1.0])
    ax_loc.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=8)
    ax_loc.set_title("Localization", fontsize=10, fontweight="bold", pad=10)
    ax_loc.axhline(0.5, color="#cccccc", linewidth=0.8, linestyle="--", zorder=1)
    ax_loc.yaxis.grid(True, color="#eeeeee", linewidth=0.6, zorder=0)
    ax_loc.set_axisbelow(True)
    ax_loc.tick_params(axis="x", labelsize=8, length=0)
    ax_loc.spines["top"].set_visible(False)
    ax_loc.spines["right"].set_visible(False)
    ax_loc.spines["left"].set_color("#cccccc")
    ax_loc.spines["bottom"].set_color("#cccccc")

    label_text = f"{loc:.0%}" if loc is not None else "n/a"
    ax_loc.text(
        0, loc_display + 0.025,
        label_text,
        ha="center", va="bottom", fontsize=9, fontweight="bold", color="#222222",
    )

    denom_note = f"n={n_elig}" if n_elig > 0 else "n=0 (no eligible items)"
    ax_loc.text(
        0.5, -0.26,
        f"{denom_note}\n(clash + model=flawed)",
        ha="center", va="top", transform=ax_loc.transAxes,
        fontsize=8, color="#666666",
    )

    # ── figure-level note ─────────────────────────────────────────────────────
    fig.text(
        0.5, 0.97,
        "Localization: of clash items the model flagged flawed, fraction where it named the undertone conflict (is_undertone_clash=True)",
        ha="center", va="top", fontsize=7.5, color="#555555", style="italic",
    )

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Chart saved to {output_path}")


# ── smoke test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    dummy = {
        "n_total": 11,
        "n_clean": 5,
        "n_clash": 6,
        "detection_agreement": 0.73,
        "miss_rate": 0.33,
        "false_positive_rate": 0.20,
        "localization_rate": 0.75,
        "n_localization_eligible": 4,
    }
    render(dummy)
