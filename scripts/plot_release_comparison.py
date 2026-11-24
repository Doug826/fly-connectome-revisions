"""Draw the v630 vs v783 left MN9 figure from the saved spike files.

Usage, from any folder:
    python scripts/plot_release_comparison.py

Needs numpy, pandas, pyarrow and matplotlib.

The script first checks results/v783_comparison_17.csv against the raw
spike files. Every file must hold all 30 trials, and its left MN9 spike
and trial counts must match the table. It then draws one row per cell
type, showing the mean left MN9 rate in each release with a 95% interval
from resampling the 30 trials, and saves a light and a dark version in
figures/.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import NullLocator
from matplotlib.transforms import blended_transform_factory


ROOT = Path(__file__).resolve().parents[1]
RAW = {"v630": ROOT / "results" / "raw_v630", "v783": ROOT / "results" / "raw_v783"}
TABLE = ROOT / "results" / "v783_comparison_17.csv"
OUT = ROOT / "figures"
NAME = "v630_vs_v783_left_mn9"

MN9_LEFT = 720575940660219265  # The same root ID in both releases.
TRIALS = 30
TRIAL_SECONDS = 1.0
RESAMPLES = 10_000
SEED = 0  # Fixed, so the intervals and the figure come out the same on every run.

THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
              "grid": "#e1e0d9", "axis": "#c3c2b7", "v630": "#5598e7", "v783": "#104281"},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781",
             "grid": "#2c2c2a", "axis": "#383835", "v630": "#256abf", "v783": "#b7d3f6"},
}
GROUPS = ((True, "Proboscis extension seen in the lab"), (False, "No extension seen in the lab"))


def left_counts(path, experiment):
    """Return left MN9 spikes per trial, after checking the file covers all 30 trials."""
    df = pd.read_parquet(path, columns=["t", "trial", "flywire_id", "exp_name"])
    if set(df["exp_name"].unique()) != {experiment}:
        raise ValueError(f"{path.name}: the experiment name is not {experiment}")
    if set(df["trial"].unique()) != set(range(TRIALS)):
        raise ValueError(f"{path.name}: expected spike records for trials 0 to {TRIALS - 1}")
    if not df["t"].between(0, TRIAL_SECONDS, inclusive="left").all():
        raise ValueError(f"{path.name}: a spike time falls outside the trial")
    trials = df.loc[df["flywire_id"] == MN9_LEFT, "trial"].to_numpy(dtype=np.int64)
    return np.bincount(trials, minlength=TRIALS)


def load_stats():
    """Recount every cell type from the raw files and check the totals against the table."""
    table = pd.read_csv(TABLE)
    table = table[table["cell_type"] != "marge_survivor_only"]  # A side check, not one of the 17.
    rng = np.random.default_rng(SEED)
    rows = []
    for rec in table.itertuples(index=False):
        row = {"cell_type": rec.cell_type, "lab_fed": bool(rec.lab_fed)}
        for release, folder in RAW.items():
            counts = left_counts(folder / f"{rec.cell_type}_50Hz.parquet", f"{rec.cell_type}_50Hz")
            if (counts.sum() != getattr(rec, f"{release}_left_spikes")
                    or (counts > 0).sum() != getattr(rec, f"{release}_left_trials")):
                raise ValueError(f"{rec.cell_type} {release}: the counts differ from {TABLE.name}")
            rates = counts / TRIAL_SECONDS
            resampled = rng.choice(rates, size=(RESAMPLES, TRIALS)).mean(axis=1)
            row[f"{release}_mean"] = rates.mean()
            row[f"{release}_lo"], row[f"{release}_hi"] = np.percentile(resampled, [2.5, 97.5])
            row[f"{release}_call"] = bool(counts.sum() > 0)
        rows.append(row)
    stats = pd.DataFrame(rows)
    flips = stats.loc[stats["v630_call"] != stats["v783_call"], "cell_type"].tolist()
    print(f"Checked {len(stats)} cell types against {TABLE.name}: counts match.")
    print(f"Left MN9 calls that changed between releases: {flips if flips else 'none'}")
    return stats


def outcome(called, fed):
    if called == fed:
        return "correct"
    return "missed" if fed else "false alarm"


def layout(stats):
    """Order the rows: lab result first, then v630 rate from high to low, then name."""
    order, headers, spans, y = [], [], [], 0.0
    for fed, title in GROUPS:
        group = stats[stats["lab_fed"] == fed].assign(key=lambda d: d["cell_type"].str.casefold())
        group = group.sort_values(["v630_mean", "v783_mean", "key"], ascending=[False, False, True])
        headers.append((y, f"{title} ({len(group)} cell types)"))
        first = y + 1
        for name in group["cell_type"]:
            y += 1
            order.append((y, name))
        spans.append((first - 0.5, y + 0.5))
        y += 1.6
    return order, headers, spans, y - 1.6 + 0.6


def draw(stats, theme, path):
    c = THEMES[theme]
    plt.rcParams.update({"font.family": "sans-serif",
                         "font.sans-serif": ["Helvetica", "Arial", "Liberation Sans", "DejaVu Sans"],
                         "font.size": 9})
    order, headers, spans, y_end = layout(stats)
    by_name = stats.set_index("cell_type")

    row_in, top_in, bottom_in, width = 0.27, 1.55, 0.95, 8.6
    plot_h = (y_end + 0.7) * row_in
    height = top_in + plot_h + bottom_in
    fig = plt.figure(figsize=(width, height), facecolor=c["surface"])
    fx = lambda inches: inches / width
    fy = lambda inches: inches / height

    left_in, strip_in, gap_in, text_in = 1.35, 0.45, 0.12, 1.05
    main_left = left_in + strip_in + gap_in
    main_w = width - main_left - text_in - 0.3
    ax0 = fig.add_axes([fx(left_in), fy(bottom_in), fx(strip_in), fy(plot_h)])
    ax1 = fig.add_axes([fx(main_left), fy(bottom_in), fx(main_w), fy(plot_h)], sharey=ax0)
    ax2 = fig.add_axes([fx(main_left + main_w + 0.25), fy(bottom_in), fx(text_in), fy(plot_h)],
                       sharey=ax0)

    for ax in (ax0, ax1, ax2):
        ax.set_facecolor(c["surface"])
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(c["axis"])
        ax.spines["bottom"].set_linewidth(0.8)
        ax.tick_params(length=0, labelcolor=c["ink2"], labelsize=8.5)
    ax2.spines["bottom"].set_visible(False)
    ax2.set_xticks([])
    ax2.set_xlim(0, 1)
    ax1.tick_params(labelleft=False)
    ax2.tick_params(labelleft=False)
    ax0.set_ylim(y_end, -0.7)  # Inverted, so the first row is at the top.
    ax0.set_yticks([y for y, _ in order])
    ax0.set_yticklabels([name for _, name in order], color=c["ink"], fontsize=9)
    ax0.tick_params(axis="y", pad=8)

    # The 0 column holds cell types with no left MN9 spike in any trial.
    ax0.set_xlim(-1, 1)
    ax0.set_xticks([0])
    ax0.set_xticklabels(["0"])
    ax1.set_xscale("log")
    ax1.set_xlim(0.1, 150)
    ax1.set_xticks([0.1, 1, 10, 100])
    ax1.set_xticklabels(["0.1", "1", "10", "100"])
    ax1.xaxis.set_minor_locator(NullLocator())
    ax1.set_xlabel("Left MN9 firing rate (spikes per second, log scale)", color=c["ink2"],
                   fontsize=9, labelpad=7)
    for top, bottom in spans:
        ax0.vlines([0], top, bottom, color=c["grid"], lw=0.8, zorder=0)
        ax1.vlines([0.1, 10, 100], top, bottom, color=c["grid"], lw=0.8, zorder=0)
        ax1.vlines([1], top, bottom, color=c["axis"], lw=0.8, zorder=0)
    breaks = dict(marker=[(-1, -1.6), (1, 1.6)], markersize=7, linestyle="none", color=c["axis"],
                  mec=c["axis"], mew=0.8, clip_on=False)
    ax0.plot([1], [0], transform=ax0.transAxes, **breaks)
    ax1.plot([0], [0], transform=ax1.transAxes, **breaks)

    marker = dict(marker="o", markersize=6.5, linestyle="none", zorder=3)
    for y, name in order:
        r = by_name.loc[name]
        for release, dy in (("v630", -0.17), ("v783", 0.17)):
            mean, lo, hi = r[f"{release}_mean"], r[f"{release}_lo"], r[f"{release}_hi"]
            ax, x = (ax0, 0.0) if mean == 0 else (ax1, mean)
            if mean > 0:
                ax1.hlines(y + dy, max(lo, 0.1), hi, color=c[release], lw=1.5, capstyle="round",
                           zorder=2)
            if release == "v630":
                ax.plot([x], [y + dy], markerfacecolor=c["surface"], markeredgecolor=c["v630"],
                        markeredgewidth=1.6, **marker)
            else:
                ax.plot([x], [y + dy], markerfacecolor=c["v783"], markeredgecolor=c["surface"],
                        markeredgewidth=1.0, **marker)
        o630 = outcome(r["v630_call"], r["lab_fed"])
        o783 = outcome(r["v783_call"], r["lab_fed"])
        label = o630 if o630 == o783 else f"{o630} in v630, {o783} in v783"
        ax2.text(0, y, label, color=c["ink2"], fontsize=8.5, va="center")

    across = blended_transform_factory(fig.transFigure, ax0.transData)
    for y, text in headers:
        fig.text(fx(0.3), y, text, transform=across, color=c["ink"], fontsize=9.5,
                 fontweight="bold", va="center")
    ax2.text(0, headers[0][0], "Model vs lab", color=c["ink"], fontsize=9, fontweight="bold",
             va="center")

    top = lambda inches: 1 - inches / height
    fig.text(fx(0.3), top(0.42), "Left MN9 feeding calls are unchanged from FlyWire v630 to v783",
             color=c["ink"], fontsize=12.5, fontweight="bold")
    fig.text(fx(0.3), top(0.58),
             "Left MN9 firing in the Shiu et al. (2024) brain model when each cell type is stimulated at 50 Hz.\n"
             "Mean of 30 one-second trials per release, with 95% intervals from resampling the trials.\n"
             "The model predicts feeding if left MN9 spikes at all, so the 0 column holds the no-feeding calls.",
             color=c["ink2"], fontsize=9, va="top", linespacing=1.5)
    handles = [
        Line2D([0], [0], color=c["v630"], lw=1.5, marker="o", markersize=6.5,
               markerfacecolor=c["surface"], markeredgecolor=c["v630"], markeredgewidth=1.6),
        Line2D([0], [0], color=c["v783"], lw=1.5, marker="o", markersize=6.5,
               markerfacecolor=c["v783"], markeredgecolor=c["surface"], markeredgewidth=1.0),
    ]
    fig.legend(handles, ["FlyWire v630", "FlyWire v783"], loc="upper left",
               bbox_to_anchor=(fx(0.22), top(1.17)), ncol=2, frameon=False, fontsize=9,
               labelcolor=c["ink"], handlelength=2.4, columnspacing=2.0)
    fig.text(fx(0.3), fy(0.12),
             "Model code: philshiu/Drosophila_brain_model at commit 91bdd1e. One unseeded 30-trial batch per release.\n"
             "The stronger gridline at 1 Hz marks the stricter >1 Hz rule. Data: results/raw_v630 and results/raw_v783.",
             color=c["muted"], fontsize=7.5, linespacing=1.5)

    fig.savefig(path, dpi=200, facecolor=c["surface"])
    plt.close(fig)
    print(f"Saved {path.relative_to(ROOT)}")


def main():
    stats = load_stats()
    OUT.mkdir(exist_ok=True)
    draw(stats, "light", OUT / f"{NAME}.png")
    draw(stats, "dark", OUT / f"{NAME}_dark.png")


if __name__ == "__main__":
    main()
