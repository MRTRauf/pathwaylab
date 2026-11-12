"""Source-labelled statistical figures and computed findings, with explicit caveats."""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

from .eda import markdown_table
from .inference import SOURCE


def export_outputs(
    dest: Path,
    data: pd.DataFrame,
    residuals: dict,
    models: pd.DataFrame,
    effects: pd.DataFrame,
    meta: dict,
    report_path: Path | None,
) -> None:
    """Describe estimates without claiming causal effects or future prediction."""
    main = models.loc[models.model.str.startswith("M")]
    figs = []

    def save(fig: plt.Figure, name: str, caption: str) -> None:
        fig.text(0.025, 0.055, caption, fontsize=9)
        fig.text(0.025, 0.018, SOURCE, fontsize=9)
        fig.tight_layout(rect=(0, 0.12, 1, 0.96))
        fig.savefig(dest / name, dpi=180)
        plt.close(fig)
        figs.append((name, caption))

    with plt.rc_context({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False}):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(main.model, main.between_variance, label="Between-player", color="#0072B2")
        ax.bar(
            main.model,
            main.residual_variance,
            bottom=main.between_variance,
            label="Residual within-player",
            color="#E69F00",
        )
        ax.set(
            ylabel="Variance: log(1 + HSR / 1 m), squared units",
            title=f"Random-intercept variance | N={len(data)}, P={data.player_id.nunique()}",
        )
        ax.legend()
        save(
            fig,
            "01_variance.png",
            "REML point estimates; no ICC confidence interval. "
            "Residual variance includes unmodelled context and measurement variation.",
        )
        fig, axes = plt.subplots(5, 4, figsize=(15, 12), sharex=True, sharey=True)
        for ax, (player, group) in zip(axes.flat, data.groupby("player_id")):
            ax.scatter(group.date, group.HSR, s=7, color="#0072B2")
            ax.set(title=f"{player}: n={len(group)}", ylabel="HSR (m)")
            ax.tick_params(axis="x", rotation=35, labelsize=7)
        save(
            fig,
            "02_trajectories.png",
            "Training observations by actual date. "
            "No interpolation; unequal coverage and exposure. No inherent player trait implied.",
        )
        for name in ["M1_log_null", "M2_log_day", "M3_log_day_position"]:
            if name not in residuals:
                continue
            table = residuals[name]
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            axes[0].scatter(table.fitted, table.y, s=5, alpha=0.3)
            lo = min(table.y.min(), table.fitted.min())
            hi = max(table.y.max(), table.fitted.max())
            axes[0].plot([lo, hi], [lo, hi], color="black", linestyle="--")
            axes[0].set(xlabel="Conditional fitted log1p HSR", ylabel="Observed log1p HSR")
            axes[1].scatter(table.fitted, table.residual, s=5, alpha=0.3)
            axes[1].axhline(0, color="black")
            axes[1].set(xlabel="Conditional fitted log1p HSR", ylabel="Residual (log units)")
            stats.probplot(table.residual, plot=axes[2])
            axes[2].set(xlabel="Normal theoretical quantile", ylabel="Residual (log units)")
            fig.suptitle(
                f"{name}: in-sample diagnostics | N={len(table)}, P={table.player_id.nunique()}"
            )
            save(
                fig,
                f"03_diagnostics_{name}.png",
                "Fitted values include player shrinkage "
                "intercepts; no holdout evaluation. Normal/homoscedastic assumptions need review.",
            )
        subset = effects.loc[effects.model.eq("M2_log_day") & effects.term.ne("Intercept")]
        if len(subset) and subset.ci_usable.all():
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.errorbar(
                subset.estimate,
                range(len(subset)),
                xerr=[subset.estimate - subset.lower95, subset.upper95 - subset.estimate],
                fmt="o",
                color="#0072B2",
                capsize=4,
            )
            ax.set_yticks(range(len(subset)), subset.term)
            ax.axvline(0, color="black", linestyle="--")
            ax.set(
                xlabel="Difference in expected log(1 + HSR / 1 m), reference DIA -1",
                title=f"Recorded-day contrasts | N={len(data)}, P={data.player_id.nunique()}",
            )
            save(
                fig,
                "04_day_effects.png",
                "Approximate model-based Wald 95% intervals; "
                "20 clusters, shared-date dependence and heteroscedasticity limit coverage.",
            )

    audit, sample = meta["audit"], meta["selection"]
    warning_count = sum(len(a["warnings"]) for a in meta["attempts"])
    loo = models.loc[models.model.str.startswith("LOO") & models.converged & ~models.boundary]
    diag = pd.read_csv(dest / "diagnostics.csv")
    day_sd = pd.read_csv(dest / "residual_day_sd.csv")
    sd2 = day_sd.loc[day_sd.model.eq("M2_log_day"), "std"]
    position = effects.loc[
        effects.model.eq("M3_log_day_position") & effects.term.str.startswith("C(position)")
    ]
    baseline = meta["baseline"]
    model_columns = [
        "model",
        "n",
        "players",
        "converged",
        "boundary",
        "between_variance",
        "residual_variance",
        "icc",
    ]
    effect_columns = ["term", "estimate", "se", "lower95", "upper95", "ci_usable"]
    main_effects = effects.loc[effects.model.eq("M2_log_day")]
    main_diagnostics = diag.loc[diag.model.str.startswith("M")]
    sensitivities = models.loc[models.model.str.startswith("S_")]
    null = main.loc[main.model.eq("M1_log_null")].iloc[0]
    influence = pd.read_csv(dest / "leave_player_influence.csv")
    influence = influence.loc[influence.term.ne("Intercept")].sort_values("absolute_change")
    largest = influence.iloc[-1]
    diagnostic_columns = ["model", "n", "skew", "excess_kurtosis", "abs_standardized_gt3"]
    text = f"""# Phase 03 longitudinal findings

## Verified facts and provenance

Source: **{SOURCE}**. [Zenodo record](https://zenodo.org/records/18986229),
CSV MD5 `{meta["csv_md5"]}`, dictionary MD5 `{meta["dictionary_md5"]}`;
original access 2026-11-12. Record creator Alejandro Rodríguez-Fernández.
Publication: Sierra-Casas, Castillo, Clemente and Rodríguez-Fernández (2026),
Data 11(4), 84, [paper](https://doi.org/10.3390/data11040084).
Paper states dataset CC BY 4.0; record Rights text was blank at verification.
No raw data redistribution. No Brøndby private data or affiliation.

Recomputed {audit["n_rows"]} observations, {audit["n_players"]} players, {audit["n_microcycles"]}
cycle IDs, {audit["date_start"]}–{audit["date_end"]}. DIA 0 has DIACat 0 and
{sample["excluded_dia0"]} rows (T=236, S=183) over {audit["match_dates"]} dates.
This is consistent with the paper's match-day meaning; no independent match flag
exists. Prior 'match rows' are defined by DIA 0, so numerical agreement is circular
as verification of semantics. All DIA 0 observations are excluded from training fits.

Training sample: {sample["n"]} observations, {sample["players"]} players;
{sample["excluded_missing"]} complete-case exclusions and {sample["zero_hsr"]} zero HSR values.
Zeros map to log1p=0 and are retained. {audit["duplicate_player_day"]} additional
player/date rows, {audit["missing_load_cells"]} missing load cells, and
{audit["negative_load_rows"]} negative-load rows. Coverage and gaps are in CSV tables.
Only players are grouping units, not {sample["n"]} independent subjects. Even these
players share team dates, so cross-player independence is an assumption, not a fact.

Dictionary descriptions were re-read and retained in metadata. It does not define
T/S mappings: **T/S meanings remain UNKNOWN** in this phase; no status effect is fitted.
Nineteen players have both codes across training observations; P02 has only S.
Variation within only {audit["player_cycles_multiple_statuses"]} of
{audit["player_cycles_total"]} player-cycle groups does not imply status is fixed
for a player over the season. Variation alone cannot identify an unambiguous status
effect; player, day and selection confounding remain. Position codes are original
labels with 3–5 players per code, constant within players. No translated role claims.

## Statistical questions and estimates

The written [analysis plan](STATISTICAL_ANALYSIS_PLAN.md) preceded implementation
and fitting; it is exploratory, not externally preregistered. Model 0 mean HSR:
{baseline["mean"]:.4f} m, median {baseline["median"]:.4f} m, SD {baseline["std"]:.4f} m
(N={sample["n"]}, P={sample["players"]}); no independent-row standard error.
M1 is log(1 + HSR / 1 m) ~ 1 + player random intercept. M2 adds categorical recorded
DIA codes, reference -1. M3 adds original position code, reference CEN. REML throughout;
no REML likelihood comparisons across differing fixed effects, no interactions.
Day labels describe recorded groups, not a verified reconstructed match calendar.

{markdown_table(main, model_columns)}

Primary M1 between variance {null.between_variance:.6f}, residual variance
{null.residual_variance:.6f}, ICC {null.icc:.6f}. Under this specification, most
transformed-load variation is residual within-player variation rather than a stable
player intercept. This is model-dependent: the square-root sensitivity changes ICC.

Variances are squared log units. ICC is a model-implied correlation under a shared
player intercept and independent residual assumptions. It partitions transformed
load variation, not causal attribution, player talent, fitness, or temporal stability.
M2/M3 ICCs are conditional on different fixed effects; do not equate them with the
Phase 02 raw between-SS fraction. No defensible small-cluster ICC CI is claimed.

### Fixed-effect estimates and uncertainty

{markdown_table(main_effects, effect_columns)}

{markdown_table(position, ["term", "estimate", "se", "lower95", "upper95", "ci_usable"])}

Intervals are approximate model-based Wald 95% intervals on the transformed scale,
not small-sample robust or simultaneous intervals. With only 20 players and shared
team-date exposures they may be too narrow. Position is a between-player association
assuming random intercepts independent of covariates. Residual position differences
cannot establish a role effect after full confounding control. No per-minute rates,
unbiased back-transformed metre means, significant-effect labels or causal claims.
The ci_usable flag describes numerical availability, not validated interval coverage.

## Convergence, diagnostics and sensitivity

{models.converged.sum()} of {len(models)} fitted specifications converged;
{int(models.boundary.sum())} boundary/failed specifications flagged.
{warning_count} captured warning messages; every attempt/error is in metadata.json.
Optimizer fallback is specified in the plan. No failed attempt is discarded from logs.

{markdown_table(main_diagnostics, diagnostic_columns)}

M2 residual SD by day ranges {sd2.min():.4f}–{sd2.max():.4f} log units.
The normal Q-Q and residual plots must be considered alongside these values:
log1p retains a spike at zero and cannot guarantee normal, equal-variance errors.
Residual tails, changing spread and shared dates limit Gaussian inference.
Residual serial correlations by player use consecutive observed dates, which may
be irregularly separated: these are diagnostics, not AR coefficients or trend tests.

{markdown_table(sensitivities, ["model", "n", "players", "converged", "boundary", "icc"])}

Square-root sensitivity has different scale, so coefficients/variances are not
directly comparable to log1p. Upper-1% sensitivity threshold {meta["trim99_threshold_m"]:.4f} m
is an explicit diagnostic exclusion, not an error correction. Coverage sensitivity
retains >=60 rows/player. Central-date sensitivity uses 2023-10-01–2024-04-30.
Exact N and P above; all original observations remain in the primary models.
All {len(models.loc[models.model.str.startswith("LOO")])} leave-player-out fits are
retained; {len(loo)} converged nonboundary fits give M2 ICC range
{loo.icc.min():.4f}–{loo.icc.max():.4f}. This is a sensitivity range, **not a CI**.
Their complete fixed coefficients permit inspection of influential players.
Largest absolute leave-player-out change in a day coefficient:
{largest.absolute_change:.6f} log units for {largest.term}, fit {largest.model}.
All changes are in leave_player_influence.csv; this is a diagnostic, not a test.

## Football interpretation and limits

The variance components describe how consistent observed transformed training
loads are within player under this model. Recorded-day associations can help staff
describe scheduling differences; they do not show that altering a schedule improves
performance. Conditional estimates describe these data only. Random intercepts are
shrunken exposure summaries, not inherent attributes. Temporal profile stability
is not established by an exchangeable intercept model; trajectories show coverage,
and no time slope is fitted because calendar/day/selection mixture is unresolved.

Important unresolved limits: 31 IDs versus 30 published microcycles; overlapping
cycle/date intervals; no session ID, duration or playing minutes; uncertain T/S and
position translations; unequal coverage and excluded injury/return-to-play periods
in the source; single team, only 20 players; common-date dependence, residual
heteroscedasticity/heavy tails and unmodelled serial dependence. No inference about
injury risk, readiness, fatigue, future performance, development or causal effects.
No RATIO* predictors or cross-source joins. All summaries are retrospective.

Phase 03 is a reproducible exploratory baseline, with qualified model-based
uncertainty. Phase 04 is **not ready for an unqualified cycle-based temporal split**:
resolve or explicitly handle actual-date/cycle inconsistencies first, verify target
ordering, and keep all feature construction past-only. Phase 04 was not started.

## Outputs and reproduction

Run `python scripts/run_inference.py` after `python -m pip install -e '.[dev,research]'`.
Outputs: `outputs/inference/` CSV model/effect/diagnostic/coverage tables, attempt
logs and versions in metadata, source-labelled PNGs, REPORT.md and checksum manifest.
Findings are regenerated here and in INFERENCE_FINDINGS.md. Run `pytest -q`, real
ingestion, EDA and synthetic demo to verify existing functionality.

"""

    def render(path: Path) -> str:
        plan_link = Path(
            os.path.relpath(Path("research/STATISTICAL_ANALYSIS_PLAN.md"), path.parent)
        ).as_posix()
        parts = [
            text.replace("](STATISTICAL_ANALYSIS_PLAN.md)", f"]({plan_link})"),
            "## Figures\n\n",
        ]
        for name, caption in figs:
            link = Path(os.path.relpath(dest / name, path.parent)).as_posix()
            parts.append(f"![{name}]({link})\n\n{caption}\n\n")
        return "".join(parts)

    for path in [dest / "REPORT.md", *([report_path] if report_path else [])]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(path), encoding="utf-8")
    if report_path:
        alias = report_path.with_name("INFERENCE_FINDINGS.md")
        alias.write_text(render(alias), encoding="utf-8")
