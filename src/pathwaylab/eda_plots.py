"""Publication-size Matplotlib figures for descriptive real-data EDA."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import LOAD_METRICS
from .eda import NAMES, SOURCE, UNITS

COLORS = {"T": "#0072B2", "S": "#D55E00"}  # Okabe-Ito palette
LABELS = {"T": "T: starter interpretation", "S": "S: non-starter interpretation"}


def export_eda_figures(
    frame: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
    dest: Path,
) -> list[dict[str, str]]:
    """Plot retained values; no confidence intervals or inferred match schedules."""
    dest.mkdir(parents=True, exist_ok=True)
    figures = []
    training = frame.loc[frame.md_day.ne(0)]
    match = frame.loc[frame.md_day.eq(0)]
    style = {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.18,
        "figure.facecolor": "white",
    }

    def save(fig: plt.Figure, name: str, title: str, caption: str) -> None:
        fig.suptitle(title, fontsize=17, fontweight="bold", y=0.985)
        fig.text(0.025, 0.035, caption, fontsize=9, va="bottom")
        fig.text(0.025, 0.014, SOURCE, fontsize=9, color="#444444")
        fig.tight_layout(rect=(0.01, 0.09, 0.99, 0.95))
        fig.savefig(dest / name, dpi=200, facecolor="white")
        plt.close(fig)
        figures.append({"file": name, "title": title, "caption": caption})

    def annotate_count(ax: plt.Axes, row: Any, others: pd.DataFrame, status: str) -> None:
        """Put each row count outside the pair of means to avoid colliding labels."""
        other = others.loc[others.md_day.eq(row.md_day) & others.status.ne(status), "mean"]
        above = (
            status == "T" if other.empty or row.mean == other.iloc[0] else row.mean > other.iloc[0]
        )
        if row.mean < 0.05 * ax.get_ylim()[1]:
            above = True  # Keep near-zero count labels away from the x-axis.
        ax.annotate(
            str(row.n_valid),
            (row.md_day, row.mean),
            xytext=(0, 7 if above else -13),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color=COLORS[status],
        )

    with plt.rc_context(style):
        fig, axes = plt.subplots(2, 3, figsize=(14, 9))
        for ax, metric in zip(axes.flat, LOAD_METRICS):
            bins = np.histogram_bin_edges(frame[metric].dropna(), bins=30)
            for subset, color, label in [
                (training, COLORS["T"], "Training"),
                (match, COLORS["S"], "Match (DIA 0)"),
            ]:
                values = subset[metric].dropna()
                ax.hist(
                    values,
                    bins=bins,
                    histtype="step",
                    linewidth=1.8,
                    color=color,
                    label=f"{label}: n={len(values)}",
                )
            ax.set(
                title=NAMES[metric],
                xlabel=f"{metric} ({UNITS[metric]})",
                ylabel="Player-session rows",
            )
            ax.legend(fontsize=8)
        save(
            fig,
            "01_load_distributions.png",
            "Observed physical-load distributions",
            f"{len(frame)} repeated rows from {frame.player_id.nunique()} players. "
            "Counts, not densities; unequal training/match coverage. No outliers removed.",
        )

        fig, axes = plt.subplots(2, 3, figsize=(14, 9))
        days = tables["day_status"]
        for ax, metric in zip(axes.flat, LOAD_METRICS):
            for status in ["T", "S"]:
                group = days.loc[days.metric.eq(metric) & days.status.eq(status)].sort_values(
                    "md_day"
                )
                ax.plot(
                    group.md_day,
                    group["mean"],
                    marker="o",
                    color=COLORS[status],
                    label=LABELS[status],
                )
                for row in group.itertuples():
                    annotate_count(ax, row, days.loc[days.metric.eq(metric)], status)
            ax.set(
                title=NAMES[metric],
                xlabel="Recorded DIA code (0 = match)",
                ylabel=f"Mean {metric} ({UNITS[metric]})",
                xticks=sorted(frame.md_day.unique()),
            )
        axes.flat[0].legend(fontsize=8)
        save(
            fig,
            "02_microcycle_profile.png",
            "Physical load by recorded day and status",
            "Labels = valid row counts; each mean pools repeated observations. Lines join "
            "day codes, not actual dates.\n"
            "T/S interpretations follow the paper; code mappings and match anchors remain "
            "provisional.",
        )

        positions = sorted(frame.position.unique())
        fig, axes = plt.subplots(2, 3, figsize=(14, 9), sharex=True, sharey=True)
        for ax, position in zip(axes.flat, positions):
            base = frame.loc[frame.position.eq(position)]
            for status in ["T", "S"]:
                group = tables["position_day_status"]
                group = group.loc[
                    group.position.eq(position) & group.metric.eq("HSR") & group.status.eq(status)
                ].sort_values("md_day")
                ax.plot(
                    group.md_day,
                    group["mean"],
                    marker="o",
                    color=COLORS[status],
                    label=LABELS[status],
                )
                for row in group.itertuples():
                    others = tables["position_day_status"]
                    others = others.loc[others.position.eq(position) & others.metric.eq("HSR")]
                    annotate_count(ax, row, others, status)
            ax.set(
                title=f"{position}: {base.player_id.nunique()} players, {len(base)} rows",
                xlabel="Recorded DIA code",
                ylabel="Mean HSR (m)",
                xticks=sorted(frame.md_day.unique()),
            )
            ax.tick_params(axis="x", labelbottom=True)
        for ax in list(axes.flat)[len(positions) :]:
            ax.axis("off")
        axes.flat[0].legend(fontsize=8)
        save(
            fig,
            "03_position_day_status.png",
            "Position-specific HSR by recorded day and status",
            "Original position codes retained; labels = valid row counts. Shared axes; no "
            "position rankings or causal effects.\n"
            "Day/status strata reduce mixing but do not adjust for minutes, player "
            "composition or calendar context.",
        )

        fig, axes = plt.subplots(2, 3, figsize=(14, 9))
        for ax, metric in zip(axes.flat, LOAD_METRICS):
            values = [training.loc[training.status.eq(s), metric].dropna() for s in ["T", "S"]]
            boxes = ax.boxplot(
                values, patch_artist=True, widths=0.5, flierprops={"markersize": 2, "alpha": 0.4}
            )
            for patch, status in zip(boxes["boxes"], ["T", "S"]):
                patch.set_facecolor(COLORS[status])
                patch.set_alpha(0.6)
            ax.set_xticks(
                [1, 2],
                [
                    f"{s}\nn={len(v)}, P={training.loc[v.index].player_id.nunique()}"
                    for s, v in zip(["T", "S"], values)
                ],
            )
            ax.set(title=NAMES[metric], ylabel=f"{metric} ({UNITS[metric]})")
        save(
            fig,
            "04_status_distributions.png",
            "Training-load distributions by recorded status",
            "DIA 0 excluded. Boxes: median and IQR; whiskers: 1.5 IQR; all fliers shown. n "
            "= valid rows, P = players.\n"
            "T = starter, S = non-starter interpretation. Day mix differs; players may "
            "contribute to both groups.",
        )

        players = sorted(training.player_id.unique())
        ncols = 4
        nrows = int(np.ceil(len(players) / ncols))
        fig, axes = plt.subplots(
            nrows, ncols, figsize=(16, max(4, 2.3 * nrows)), sharex=True, sharey=True, squeeze=False
        )
        for ax, player in zip(axes.flat, players):
            group = training.loc[training.player_id.eq(player)].sort_values("date")
            for status in ["T", "S"]:
                subset = group.loc[group.status.eq(status)]
                ax.scatter(subset.date, subset.HSR, s=9, alpha=0.65, color=COLORS[status])
            ax.set(title=f"{player}: n={group.HSR.notna().sum()}", ylabel="HSR (m)")
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
            ax.tick_params(axis="x", labelsize=8)
        for ax in list(axes.flat)[len(players) :]:
            ax.axis("off")
        save(
            fig,
            "05_player_trajectories.png",
            "Individual training HSR observations in calendar time",
            "All players; actual FECHA dates sorted; common axes; points only, with no "
            "interpolation across unobserved dates.\n"
            "Blue = T; orange = S. No duration normalization; apparent changes may reflect "
            "session mix or coverage.",
        )

        fig, axes = plt.subplots(2, 3, figsize=(14, 10))
        for ax, metric in zip(axes.flat, LOAD_METRICS):
            group = (
                tables["player"].loc[tables["player"].metric.eq(metric)].sort_values("player_id")
            )
            ax.barh(group.player_id, group.sd, color=COLORS["T"], alpha=0.8)
            for y, row in enumerate(group.itertuples()):
                if pd.notna(row.sd):
                    ax.text(row.sd, y, f"  {row.n_valid}", va="center", fontsize=7)
            ax.set(title=NAMES[metric], xlabel=f"Within-player sample SD ({UNITS[metric]})")
            ax.tick_params(axis="y", labelsize=8)
        save(
            fig,
            "06_within_player_variability.png",
            "Raw within-player training-load variability",
            "Bar labels = valid training rows per player. SD uses n-1; no estimates for "
            "n<2. All recorded training days pooled.\n"
            "Day/status, minutes and missing coverage confound comparisons. Not a measure "
            "of fatigue or player quality.",
        )

        corr = (
            tables["correlations"]
            .pivot(index="metric_x", columns="metric_y", values="pearson_r")
            .reindex(index=LOAD_METRICS, columns=LOAD_METRICS)
        )
        n_pairs = (
            tables["correlations"]
            .pivot(index="metric_x", columns="metric_y", values="n_pairs")
            .reindex(index=LOAD_METRICS, columns=LOAD_METRICS)
        )
        fig, ax = plt.subplots(figsize=(9, 8))
        mesh = ax.imshow(corr, vmin=-1, vmax=1, cmap="BrBG")
        for y, left in enumerate(LOAD_METRICS):
            for x, right in enumerate(LOAD_METRICS):
                value = corr.loc[left, right]
                ax.text(
                    x,
                    y,
                    f"{value:.2f}\nn={n_pairs.loc[left, right]}",
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white" if abs(value) > 0.65 else "black",
                )
        ax.set_xticks(range(6), LOAD_METRICS)
        ax.set_yticks(range(6), LOAD_METRICS)
        ax.grid(False)
        fig.colorbar(mesh, ax=ax, label="Pooled Pearson r (unitless)", shrink=0.8)
        save(
            fig,
            "07_metric_correlations.png",
            "Descriptive correlations among training GPS measures",
            f"Training only: {len(training)} rows, {training.player_id.nunique()} players. "
            f"Pairwise complete rows; n shown per cell.\n"
            "Pooled repeated observations; mixes within- and between-player associations. "
            "No p-values or causal interpretation.",
        )

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        coverage = tables["coverage"]
        axes[0].bar(coverage.player_id, coverage.n_rows, color=COLORS["T"])
        axes[0].set(title="Observed player-session rows", ylabel="Rows (training + match)")
        axes[0].tick_params(axis="x", rotation=60)
        counts = tables["player_cycles"].n_rows
        axes[1].hist(
            counts, bins=np.arange(0.5, counts.max() + 1.5, 1), color=COLORS["S"], rwidth=0.85
        )
        axes[1].set(
            title=f"Rows per observed player-cycle (n={len(counts)})",
            xlabel="Player-session rows per player-cycle",
            ylabel="Observed player-cycles",
        )
        save(
            fig,
            "08_observation_coverage.png",
            "Unequal observation coverage across players and cycles",
            "No team session identifier or attendance roster exists; row counts do not "
            "establish training attendance.\n"
            f"{len(frame)} rows; {frame.player_id.nunique()} players; "
            f"{frame.microcycle.nunique()} distinct cycle IDs. Unobserved cycles are not "
            f"zeros.",
        )

        monthly = training.groupby([training.date.dt.strftime("%Y-%m"), "md_day"]).HSR.agg(
            ["mean", "count"]
        )
        means = monthly["mean"].unstack("md_day").sort_index()
        counts = monthly["count"].unstack("md_day").reindex_like(means)
        fig, ax = plt.subplots(figsize=(12, 7))
        mesh = ax.imshow(means, cmap="cividis", aspect="auto")
        for y in range(len(means)):
            for x in range(len(means.columns)):
                if pd.notna(means.iloc[y, x]):
                    ax.text(
                        x,
                        y,
                        f"{means.iloc[y, x]:.0f}\nn={counts.iloc[y, x]:.0f}",
                        ha="center",
                        va="center",
                        fontsize=9,
                        bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none"},
                    )
        ax.set_xticks(range(len(means.columns)), means.columns)
        ax.set_yticks(range(len(means)), means.index)
        ax.set(xlabel="Recorded DIA code (training only)", ylabel="Actual calendar month")
        ax.grid(False)
        fig.colorbar(mesh, ax=ax, label="Mean HSR (m)")
        save(
            fig,
            "09_calendar_day_profile.png",
            "Training HSR across actual months and recorded day codes",
            "Cell labels = mean HSR (m) and valid row n; empty cells are unobserved. "
            "Status and player composition may change.\n"
            "Calendar month is not microcycle ID. No trend test or longitudinal effect "
            "estimate is implied.",
        )
    return figures
