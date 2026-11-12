"""Computed Phase 04 findings and source-labelled original-unit diagnostics."""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .eda import markdown_table
from .forecasting import SOURCE, error_metrics

PALETTE = {
    "global_median": "#222222",
    "last_hsr": "#999999",
    "rolling_mean": "#CC79A7",
    "ridge": "#0072B2",
    "tree": "#D55E00",
}


def export_forecast(
    dest: Path, predictions: pd.DataFrame, scores: pd.DataFrame, meta: dict, report: Path | None
) -> None:
    """Summarize fair paired evaluation; no iid confidence intervals or utility claims."""
    p = predictions.copy()
    p["date"] = pd.to_datetime(p.date)
    p["month"] = p.date.dt.strftime("%Y-%m")
    p["week"] = p.date.dt.to_period("W-SUN").dt.start_time
    p["historical_load_band"] = pd.cut(
        p.lag_HSR,
        [-np.inf, 100, 300, np.inf],
        labels=["prior <=100 m", "prior 100–300 m", "prior >300 m"],
    )
    groups = []
    for grouping in ["player_id", "position", "month", "historical_load_band", "date", "week"]:
        for (fold, model, value), g in p.groupby(["fold", "model", grouping], observed=True):
            groups.append(
                {
                    "fold": fold,
                    "model": model,
                    "group_type": grouping,
                    "group": str(value),
                    **error_metrics(g.target_hsr, g.prediction_m),
                    "players": g.player_id.nunique(),
                    "dates": g.date.nunique(),
                    "source": SOURCE,
                }
            )
    subgroup = pd.DataFrame(groups)
    subgroup.to_csv(dest / "subgroup_errors.csv", index=False)
    test = p.loc[p.fold.eq("test")]
    chosen = meta["chosen_ml"]
    selected = test.loc[test.model.eq(chosen)].copy()
    final = scores.loc[scores.fold.eq("test")]
    comparisons = pd.read_csv(dest / "test_comparisons.csv")
    manifests = pd.read_csv(dest / "split_manifest.csv")
    figures = []

    def save(fig: plt.Figure, name: str, caption: str) -> None:
        fig.text(0.025, 0.055, caption, fontsize=9)
        fig.text(0.025, 0.015, SOURCE, fontsize=9)
        fig.tight_layout(rect=(0.01, 0.13, 0.99, 0.95))
        fig.savefig(dest / name, dpi=180)
        plt.close(fig)
        figures.append((name, caption))

    with plt.rc_context({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(11, 6))
        color_map = {"ridge": "#0072B2", "tree": "#D55E00"}
        ax.bar(final.model, final.mae_m, color=[color_map.get(m, "#888888") for m in final.model])
        ax.set(ylabel="MAE (m)", title=f"Chronological holdout errors | n={len(selected)}")
        save(
            fig,
            "01_holdout_mae.png",
            "Same target observations for all methods. "
            "ML selection used validation only; lower error is better.",
        )
        fig, ax = plt.subplots(figsize=(12, 6))
        for name, g in scores.groupby("model"):
            ordered = g.set_index("fold").reindex(
                ["validation_1", "validation_2", "validation_3", "test"]
            )
            ax.plot(ordered.index, ordered.mae_m, marker="o", label=name, color=PALETTE[name])
        ax.legend(ncol=3)
        ax.set(ylabel="MAE (m)", title="Expanding-window validation and final holdout")
        save(
            fig,
            "02_fold_mae.png",
            "Fold sizes/dates in split_manifest.csv. "
            "Validation supported model selection; it is not an independent test.",
        )
        fig, axes = plt.subplots(1, 2, figsize=(13, 6))
        axes[0].scatter(selected.target_hsr, selected.prediction_m, s=12, alpha=0.45)
        maximum = max(selected.target_hsr.max(), selected.prediction_m.max())
        axes[0].plot([0, maximum], [0, maximum], color="black", linestyle="--")
        axes[0].set(
            xlabel="Observed HSR (m)", ylabel="Predicted HSR (m)", title="Observed versus predicted"
        )
        axes[1].hist(selected.error_m, bins=25, color="#0072B2")
        axes[1].axvline(0, color="black", linestyle="--")
        axes[1].set(
            xlabel="Prediction minus observation (m)",
            ylabel="Observations",
            title="Signed error distribution",
        )
        fig.suptitle(
            f"Validation-selected {chosen} | test n={len(selected)}, "
            f"P={selected.player_id.nunique()}"
        )
        save(
            fig,
            "03_prediction_diagnostics.png",
            "Original metres, nonnegative predictions. "
            "Errors describe forecasting performance, not fatigue or injury risk.",
        )
        player_scores = subgroup.loc[subgroup.fold.eq("test") & subgroup.group_type.eq("player_id")]
        fig, ax = plt.subplots(figsize=(13, 6))
        for name in ["global_median", "last_hsr", "rolling_mean", chosen]:
            g = player_scores.loc[player_scores.model.eq(name)].sort_values("group")
            ax.plot(g.group, g.mae_m, marker="o", label=name, color=PALETTE[name])
        ax.tick_params(axis="x", rotation=50)
        ax.legend()
        ax.set(ylabel="MAE (m)", title="Holdout errors by anonymous player")
        save(
            fig,
            "04_player_errors.png",
            "Unequal player counts; see subgroup_errors.csv. "
            "Player errors are not physical capacity or talent rankings.",
        )
        fig, ax = plt.subplots(figsize=(13, 6))
        for name in ["global_median", "last_hsr", "rolling_mean", chosen]:
            g = subgroup.loc[
                subgroup.fold.eq("test") & subgroup.group_type.eq("date") & subgroup.model.eq(name)
            ]
            ax.plot(pd.to_datetime(g.group), g.mae_m, marker=".", label=name, color=PALETTE[name])
        ax.legend()
        ax.set(
            ylabel="Date-level MAE (m)",
            xlabel="Actual target date",
            title="Time-ordered holdout errors",
        )
        save(
            fig,
            "05_date_errors.png",
            "Each point pools players on one team date; "
            "shared-date and serial dependence remain. No confidence bands.",
        )

    # Descriptive paired gains by player and date: does any gain concentrate in a few groups?
    gains = []
    for group_type in ["player_id", "date"]:
        subset = subgroup.loc[subgroup.fold.eq("test") & subgroup.group_type.eq(group_type)]
        pivot = subset.pivot(index="group", columns="model", values="mae_m")
        for base in ["global_median", "last_hsr", "rolling_mean"]:
            for group, difference in (pivot[base] - pivot[chosen]).items():
                gains.append(
                    {
                        "group_type": group_type,
                        "group": group,
                        "chosen_ml": chosen,
                        "baseline": base,
                        "mae_gain_m": difference,
                        "source": SOURCE,
                    }
                )
    gains = pd.DataFrame(gains)
    gains.to_csv(dest / "paired_group_gains.csv", index=False)
    counts = (
        gains.groupby(["group_type", "baseline"])
        .mae_gain_m.agg(
            groups="size",
            positive_groups=lambda s: int(s.gt(0).sum()),
            minimum="min",
            maximum="max",
        )
        .reset_index()
    )
    features = pd.read_csv(dest / "historical_features.csv")
    horizon = features.loc[features.history_n.ge(1), "gap_days"].describe().to_frame("gap_days")
    horizon.to_csv(dest / "observed_horizon.csv")
    sensitivities = pd.read_csv(dest / "validation_sensitivities.csv")
    weekly = subgroup.loc[
        subgroup.fold.eq("test") & subgroup.group_type.eq("week") & subgroup.model.eq(chosen)
    ]
    split_columns = [
        "fold",
        "role",
        "start",
        "end",
        "n",
        "players",
        "dates",
        "cycle_ids_annotation_only",
    ]
    metric_columns = ["model", "n", "players", "dates", "mae_m", "rmse_m", "median_ae_m", "bias_m"]
    comparison_columns = ["model", "baseline", "mae_improvement_m", "relative_improvement_percent"]
    fold_columns = ["fold", "model", "n", "mae_m", "rmse_m", "bias_m"]
    count_columns = ["group_type", "baseline", "groups", "positive_groups", "minimum", "maximum"]
    chosen_score = final.loc[final.model.eq(chosen)].iloc[0]
    strongest_baseline = (
        final.loc[final.model.isin(["global_median", "last_hsr", "rolling_mean"])]
        .sort_values("mae_m")
        .iloc[0]
    )
    selected_comparison = comparisons.loc[
        comparisons.model.eq(chosen) & comparisons.baseline.eq(strongest_baseline.model)
    ].iloc[0]
    chosen_validation = scores.loc[~scores.fold.eq("test") & scores.model.eq(chosen)]
    text = f"""# Phase 04 — leakage-aware session forecasting

## Research question, target and provenance

Can past recorded training loads forecast HSR at the next observed training session
more accurately than historical baselines? Source for all results: **{SOURCE}**.
[Original record](https://zenodo.org/records/18986229), DOI 10.5281/zenodo.18986229.
Creator Alejandro Rodríguez-Fernández; publication Sierra-Casas, Castillo, Clemente
and Rodríguez-Fernández (2026), Data 11(4), 84,
[paper/methods](https://doi.org/10.3390/data11040084). Original access 2026-11-12.
Paper states dataset CC BY 4.0; record Rights text was blank. Raw files stay ignored.
CSV MD5 `{meta["csv_md5"]}`; dictionary MD5 `{meta["dictionary_md5"]}`.

The protocol was written before fitting. This user's next-session target supersedes
the starter prompt's next-microcycle target; the old demo remains unchanged.
Unit: one recorded player/date observation, conditional on its occurrence. Forecast
origin immediately before the target session; all physical features come from strictly
earlier dates. No true session identifiers or within-day timestamps are supplied.
There are {meta["audit"]["duplicate_player_day"]} duplicate player/date rows; no aggregation
or invented sequencing is needed. Dates are Excel serials converted from 1899-12-30.

Verified {meta["audit"]["n_rows"]} source rows, {meta["audit"]["n_players"]} players,
{meta["audit"]["n_microcycles"]} cycle IDs,
{meta["audit"]["date_start"]}–{meta["audit"]["date_end"]}.
Exclude {meta["audit"]["n_match_rows"]} DIA-0 rows from targets and histories;
remaining {meta["audit"]["n_training_rows"]} rows are provisionally training. DIA-0
interpretation is source-consistent, not independently verified by a separate flag.
Exclude {meta["first_observations_excluded"]} first observations without prior training
history, and {meta["missing_targets_excluded"]} missing targets. Primary forecast rows:
**{meta["primary_rows"]}**. Prior first observations remain available as history.
Gaps span {horizon.loc["min", "gap_days"]:.0f}–{horizon.loc["max", "gap_days"]:.0f} days,
median {horizon.loc["50%", "gap_days"]:.0f}; not a fixed daily forecast.

The 31-versus-30 cycle discrepancy is retained. There are
{meta["audit"]["adjacent_player_cycle_overlaps"]} overlapping/touching adjacent
player-cycle ranges. We do not repair them: calendar dates, not IDs, define order.
Missing observation periods are not inferred as missed attendance or injuries.

## Feature availability and evaluation

Used: {", ".join(meta["features"])}. Each physical lag is shifted before rolling;
rolling mean/SD use up to three strictly prior training observations. No current loads,
RATIO*, full-season means/maxima, T/S, DIA, cycle IDs, current position or future gaps
are features. Position codes only describe posthoc errors. Calendar features assume
the target date is known before the session. Dictionary lacks units and code mappings;
HSR metres follow the paper. T/S football meanings remain unverified.
See feature_availability.csv for calculations, timing and risks.

All players share target-date boundaries. Chronological splits:

{markdown_table(manifests, split_columns)}

Preprocessing/model fitting uses training labels only. Histories may use completed
earlier validation/test observations: **rolling one-step evaluation**, not a batch
multi-session forecast. Same-date observations never enter features. Historical-window
overlap uses legitimate past data, so no extra embargo is applied. Model selection
never uses final test scores. Split assignments identify every train/evaluation row.

Ridge alpha selected on pooled three-fold validation MAE: {meta["alpha"]}.
Tree: seven maximum leaves, 100 iterations, learning rate .05, min leaf 30, L2=10,
random seed 42, no random early-stopping split. No target transformation; clip negative
predictions to zero. Validation-selected ML: **{chosen}**, frozen before test prediction.
All methods score identical targets. Global median uses training targets; persistence
and rolling mean fall back to that median if no valid player history is available.
Validation scores supported selection and are not independent confirmatory evidence.

## Final holdout results (metres)

{markdown_table(final, metric_columns)}

{markdown_table(comparisons, comparison_columns)}

Validation-selected {chosen}: holdout MAE {chosen_score.mae_m:.6f} m and RMSE
{chosen_score.rmse_m:.6f} m. Against the strongest holdout baseline
({strongest_baseline.model}), MAE improvement is {selected_comparison.mae_improvement_m:.6f} m
({selected_comparison.relative_improvement_percent:.6f}%). This comparison describes
one held-out period; it does not establish deployment utility or generalization.

Positive improvement means lower MAE than that baseline; negative means deterioration.
Exact full-precision values are in scores.csv/test_comparisons.csv. Bias is prediction
minus observation. No MAPE is used because HSR includes zeros. Both ML methods are
reported without selecting a new model from final-test results.

## Temporal stability, concentration and sensitivity

{markdown_table(scores.loc[~scores.fold.eq("test")], fold_columns)}

The selected ML's validation MAE spans {chosen_validation.mae_m.min():.4f}–
{chosen_validation.mae_m.max():.4f} m. The table retains any folds where another ML
or baseline performs better; pooled selection does not imply a win in every period.

For the validation-selected ML, paired holdout improvement counts/ranges:

{markdown_table(counts, count_columns)}

These summarize whether gains are broad across dates/players; they are not
independent significance tests. Subgroup CSVs include player, original position,
month, prior-HSR band, actual date and calendar-week metrics with denominators.
No unverified status or session-category comparison is presented.
There are {len(weekly)} test calendar-week blocks; selected-model weekly MAE spans
{weekly.mae_m.min():.4f}–{weekly.mae_m.max():.4f} m. With few, unequal, serially
dependent blocks and 20 shared-team players, no reliable confidence interval is
claimed. Fold/block ranges are descriptive variability, not resampled precision.

Prespecified validation-only sensitivities, using frozen main-model settings:

{markdown_table(sensitivities, ["variant", "fold", "model", "n", "mae_m", "rmse_m"])}

History7 changes only the historical window. History>=3 restricts evaluation to
better observed histories. Nonextreme excludes evaluation values above each fold's
training-only 99th percentile for diagnostics, not because they are errors.
Calendar-free omits weekday and elapsed-gap predictors. All choices were specified
before fitting; none are selected using holdout performance. Questionable DIA/status
schedule features stay excluded throughout. No claim that schedule metadata is verified.

## Football interpretation and limitations

Historical loads support this limited benchmark, but ML must be judged against all
three baselines above; a loss is a valid result. Error differences vary across periods
and players. No external operational tolerance is provided, so these errors cannot
establish coaching usefulness or deployment readiness. Next observed training rows
are selected retrospectively; participation and observation mechanisms can bias the
sample. Predictions assume previous sessions' outputs would have been processed by
the next date; actual processing latency is unavailable.

Only one unrelated team and 20 players, unequal histories, shared dates, irregular
gaps, zeros/skewness, missing schedule/minutes/duration and unverified code meanings
limit generalization. Raw load is not intensity. Cycle inconsistencies remain; no
fixed-week inference is made. Hypothetical future linked event/tracking/fitness data
would require consent, valid same-player identifiers and temporal availability
audits; current unlinked public sources must not be joined by identity.
No injury risk, readiness, fatigue, academy development, causal training effect,
fitness prescription or Brøndby collaboration claim. No private Brøndby data used.

## Reproduction and readiness

`python -m pathwaylab.cli --mode forecast --raw data/raw/DataSetTMr.csv`
generates tables, predictions, metadata/versions, five PNGs and artifact checksums
under outputs/forecast/, and both research findings documents. Source checksums
are verified before/after. Leakage tests cover future-value perturbations,
same-day exclusion, chronology, preprocessing isolation and history fallbacks.
No feature importance is claimed: causal interpretation would be unsupported.
The benchmark is ready for descriptive presentation; Phase 05 must preserve these
limits and the frozen evaluation. Phase 05 was not started; no coaching deployment.

"""

    def render(path: Path) -> str:
        images = []
        for filename, caption in figures:
            link = Path(os.path.relpath(dest / filename, path.parent)).as_posix()
            images.append(f"![{filename}]({link})\n\n{caption}\n\n")
        return text + "## Diagnostic figures\n\n" + "".join(images)

    paths = [dest / "REPORT.md"]
    if report:
        paths += [report, report.with_name("FORECAST_EVALUATION.md")]
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(path), encoding="utf-8")
