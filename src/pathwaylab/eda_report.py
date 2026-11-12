"""Generate narrative findings directly from the same tables used in EDA figures."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from .eda import SOURCE, markdown_table


def findings_report(
    tables: dict[str, pd.DataFrame], metadata: dict, dest: Path, report_path: Path
) -> str:
    """Render source-linked findings with numeric statements derived from tables."""
    audit = metadata["audit"]
    overall = tables["overall"]
    train = overall.loc[overall.scope.eq("training")]
    hsr = train.loc[train.metric.eq("HSR")].iloc[0]
    day = tables["day_status"]
    selected = day.loc[day.md_day.isin([0, 1, 2]) & day.metric.isin(["TD", "HSR"])]
    player = tables["player"]
    player_hsr = player.loc[player.metric.eq("HSR")].sort_values("mean")
    within = tables["variability"].set_index("metric").loc["HSR"]
    month = tables["monthly"]
    month_hsr = month.loc[month.metric.eq("HSR")].sort_values("month")
    coverage = tables["coverage"]
    extremes = [player_hsr.iloc[0], player_hsr.iloc[-1]]
    findings = []
    for code in [0, 1, 2]:
        strata = day.loc[day.md_day.eq(code) & day.metric.eq("HSR")].set_index("status")
        if {"T", "S"}.issubset(strata.index):
            t, s = strata.loc["T"], strata.loc["S"]
            direction = "higher" if t["mean"] > s["mean"] else "lower"
            findings.append(
                f"- DIA {code:+d}: T mean HSR {t['mean']:.2f} m "
                f"(n={t.n_valid}, P={t.n_players}) versus S {s['mean']:.2f} m "
                f"(n={s.n_valid}, P={s.n_players}); T is {direction} in this stratum."
            )
    pattern_text = "\n".join(findings)
    columns = ["metric", "unit", "n_valid", "n_players", "mean", "sd", "median", "q1", "q3"]
    links = []
    interpretations = [
        "The training/match distributions differ in coverage and shape. Staff can use these to "
        "check exposure ranges; minutes and duration prevent intensity comparisons. No "
        "distribution test was performed.",
        "Day-specific status patterns are quantified above. They may help staff describe observed "
        "recovery/top-up schedules, but do not establish the purpose or effectiveness of "
        "individual sessions.",
        "HSR comparisons hold recorded day and status separate. Staff can inspect role-specific "
        "coverage without pooling incompatible days; small player groups, role assignment "
        "and minutes remain confounders.",
        "Training-only boxes describe each status group's observed exposure distribution. These "
        "are not matched player comparisons; day mix and changing status can shift the "
        "pooled boxes.",
        "All player trajectories use actual dates and expose gaps. They support coverage review; "
        "point patterns cannot identify fatigue, adaptations, fitness or causal responses "
        "to training.",
        "Players' raw SDs describe variation in their recorded training rows. Session design and "
        "day/status mix can dominate these SDs; high variability does not imply unstable "
        "readiness or poor performance.",
        "The pooled matrix describes co-occurring external-load measures. Staff can check "
        "redundant "
        "summaries, but repeated observations and shared session exposure prevent causal "
        "or independent-sample interpretation.",
        "Unequal row and cycle counts show how strongly a pooled mean can weight "
        "particular players. "
        "No observation does not imply non-attendance; no attendance roster or true "
        "session identifier is supplied.",
        "Calendar/day cells describe observed month-specific HSR. Staff can inspect "
        "schedule coverage, "
        "but changing player/status composition and sparse cells can mimic seasonal "
        "change. No trend test was performed.",
    ]
    for item, interpretation in zip(metadata["figures"], interpretations):
        path = Path(os.path.relpath(dest / "figures" / item["file"], report_path.parent)).as_posix()
        links.append(
            f"### {item['title']}\n\n![{item['title']}]({path})\n\n"
            f"{item['caption']}\n\n{interpretation}\n"
        )
    table_path = Path(os.path.relpath(dest / "tables", report_path.parent)).as_posix()
    position_hsr = tables["position"].loc[
        tables["position"].scope.eq("training") & tables["position"].metric.eq("HSR")
    ]
    day_table = markdown_table(
        selected, ["md_day", "status", "metric", "unit", "n_valid", "n_players", "mean", "median"]
    )
    variance_table = markdown_table(
        tables["variability"],
        [
            "metric",
            "unit",
            "n_valid",
            "n_players",
            "pooled_within_sd",
            "between_player_mean_sd",
            "between_ss_fraction",
        ],
    )
    return f"""# Phase 02 — exploratory football load profiling

## Research objective and provenance

How do observed external GPS loads differ across recorded days, player positions,
status groups and individuals? This is exploratory, descriptive analysis of
**{SOURCE}**. All numerical findings below are calculated from the original CSV;
table rows carry the same source label. There are no new statistical tests,
model fits, random splits, predictions or cross-source identity joins.

Dataset: [Zenodo v1](https://zenodo.org/records/18986229),
[DOI 10.5281/zenodo.18986229](https://doi.org/10.5281/zenodo.18986229).
Creator: Alejandro Rodríguez-Fernández. Original source access: 2026-11-12;
local re-verification: {metadata["verification_date"]}.
CSV MD5 `{metadata["csv_md5"]}`; dictionary MD5 `{metadata["dictionary_md5"]}`.
Publication authors: Alejandro Sierra-Casas, Daniel Castillo, Filipe Manuel Clemente,
Alejandro Rodríguez-Fernández (2026), Data 11(4), 84;
[publication and acquisition methods](https://doi.org/10.3390/data11040084).
The paper explicitly states dataset CC BY 4.0; Zenodo's Rights section was blank
at access. Raw files remain gitignored pending redistribution review.
This is an unrelated public team dataset, with no club affiliation claimed.

## Dataset scope and integrity

- {audit["n_rows"]} player-session rows, {audit["n_players"]} anonymized players,
  {audit["n_microcycles"]} observed microcycle IDs; {audit["date_start"]} to {audit["date_end"]}.
- {audit["n_training_rows"]} training rows (DIA != 0), {audit["n_match_rows"]} match rows
  (DIA 0); {audit["training_dates"]} training dates and {audit["match_dates"]} match dates.
  Dates and rows cannot establish numbers of distinct team sessions; no session ID is supplied.
- {audit["missing_load_cells"]} missing load cells, {audit["negative_load_rows"]} negative-load
  rows, {audit["exact_duplicate_rows"]} exact duplicates and {audit["duplicate_player_day"]}
  additional same-player/date rows. No values were imputed, deleted or winsorized.
  See [per-column missingness]({table_path}/missingness.csv).
- T rows: {audit["status_frequencies"].get("T", 0)};
  S rows: {audit["status_frequencies"].get("S", 0)}.
  {audit["player_cycles_multiple_statuses"]} of {audit["player_cycles_total"]} observed
  player-cycle groups contain both status codes: **status must not be assumed fixed
  within every player/microcycle**. Status is retained per observation.
- Player coverage spans {coverage.n_rows.min()}–{coverage.n_rows.max()} rows and
  {coverage.n_cycles.min()}–{coverage.n_cycles.max()} observed IDs.
- Missing cycle IDs within the observed integer range: {audit["missing_cycle_ids_in_range"]}.
  There are {audit["adjacent_player_cycle_overlaps"]} of
  {audit["adjacent_player_cycle_pairs"]} adjacent observed player-cycle pairs
  whose date intervals overlap or touch, so sorting cycle IDs does not guarantee a
  disjoint temporal sequence. See [cycle overlaps]({table_path}/cycle_overlaps.csv).
- {audit["player_date_gaps_gt1"]} of {audit["player_date_intervals"]}
  successive observed player-date intervals exceed one day;
  maximum {audit["max_player_date_gap_days"]} days. These are gaps in observations,
  not evidence of injury or missed training. Calendar-time plots use sorted FECHA dates.

The **31 observed IDs versus 30 published microcycles** discrepancy remains unresolved,
including sparse cycle 21 and overlapping match dates. The paper's 144 training
sessions cannot be equated with {audit["training_dates"]} distinct training dates.
No cycle IDs or dates were repaired. See the Phase 01 `REAL_DATA_AUDIT.md` for evidence.

## Definitions and methods

The verified XLSX dictionary was re-read: it supplies 20 field descriptions but no
FECHA entry, units, thresholds or category mappings. Descriptions are preserved in
`metadata.json`. TD/HSR/SPR/HMLD use metres; ACC/DCC use event counts, based on the
paper. It reports 10 Hz GPS/100 Hz accelerometry, HSR >19.8 km/h, sprint >25.2 km/h,
HMLD >25.5 W/kg, and acceleration/deceleration magnitude >3 m/s²; deceleration sign
wording is ambiguous. Exact source field names remain in tables. Position codes
CEN/LAT/MED/EXT/DEL are not relabelled with unverified translations.
T/S are interpreted as starter/non-starter from Spanish abbreviations and the
paper, with observed ESTCat 1/0; minutes are unavailable to independently validate
the paper's starter (>60 min and starting) / non-starter (<35 min) definitions.
Day codes are retained, rather than assigned to a reconstructed match calendar.

Means are row-weighted; n means valid metric rows and P means distinct contributing
players. Rows are repeated measurements, not independent participants. Each CSV
reports row, player, date, valid and missing counts where applicable. Medians,
quartiles, sample SD (ddof=1), and ranges describe distributions; no standard errors
or confidence intervals are implied. Missing metrics are excluded only from that
metric's denominator; they are never filled. Training and match summaries are separate.
Within/between summaries use training only. Pooled within-player SD is
sqrt(sum((x - player mean)^2)/(N-P)); between-player SD is the sample SD of player
means with equal player weight. Between-SS fraction uses observation-weighted
between SS divided by total SS: **it is not an adjusted ICC**. These quantities
mix days, status, minutes and schedule effects. Correlations are pairwise-complete
Pearson correlations of training rows; they mix within- and between-player associations.
All full-season descriptive summaries are retrospective and must not be reused as
historical predictors. RATIO* full-season-normalized columns are omitted entirely.

## Main computed findings

### Training-load distributions

{markdown_table(train, columns)}

Mean training HSR is {hsr["mean"]:.2f} m per valid recorded row
(n={hsr.n_valid}, P={hsr.n_players}), median {hsr["median"]:.2f} m,
IQR {hsr.q1:.2f}–{hsr.q3:.2f} m. These are external session exposures, not
duration-normalized intensity, physical capacity or suggested targets.

### Recorded day and status patterns

{pattern_text}

{day_table}

These raw absolute-load comparisons can be discussed alongside the paper's
match/recovery/top-up descriptions. They do not reproduce its ratio analyses or
mixed-effects tests. Direction agreement would not validate a causal explanation.
Players may contribute to both statuses on different observations; counts overlap.

### Playing-position and player profiles

Training HSR by original position code (unadjusted; use day/status figure for context):

{markdown_table(position_hsr, ["position", "n_valid", "n_players", "mean", "median", "sd"])}

Observed player-mean training HSR ranges from {extremes[0]["mean"]:.2f} m
({extremes[0].player_id}, n={extremes[0].n_valid}) to {extremes[1]["mean"]:.2f} m
({extremes[1].player_id}, n={extremes[1].n_valid}). This range is not a player ranking:
minutes, positions, day/status composition and unequal coverage differ.
Training HSR pooled within-player SD is {within.pooled_within_sd:.2f} m;
SD of player means is {within.between_player_mean_sd:.2f} m.
The observation-weighted between-SS fraction is {within.between_ss_fraction:.4f},
a raw decomposition, not a repeatability estimate adjusted for context.

{variance_table}

### Calendar patterns and outlier review

Monthly training HSR below uses actual dates, not a presumed continuous cycle index:

{markdown_table(month_hsr, ["month", "n_valid", "n_players", "n_dates", "mean", "median"])}

These pooled month means can change because of coverage and day/status mixture.
The calendar/day heatmap and month/day/status CSV expose this confounding.
No seasonal trend, longitudinal improvement or load response has been tested.

Pooled original-data IQR screening (all rows, no exclusions) flags HSR in
{audit["load_screen"]["HSR"]["iqr_flag_rows"]} rows. HSR ranges
{audit["load_screen"]["HSR"]["min"]:.0f}–{audit["load_screen"]["HSR"]["max"]:.0f} m;
{audit["load_screen"]["HSR"]["zero_rows"]} rows have zero HSR. All remain in tables
and figures. IQR screens are distribution checks, not physiological impossibility
thresholds. Distance-over-TD violations: {audit["distance_order_violations"]}.
Full six-metric ranges/zeros/IQR counts are in metadata's audit.

## Figures and football interpretation

Every figure carries the real source DOI and explanatory caption. Comparisons are
descriptive throughout; no apparent difference is labelled statistically significant.

{"".join(links)}

## Methodological limitations and alternative explanations

1. Session duration and match minutes are unavailable. Larger raw distances can
   reflect longer exposure rather than greater intensity; per-minute rates cannot
   be computed. Recovery and top-up session duration may systematically differ.
2. Player/position and day/status composition changes across comparisons. Tactical
   roles, schedule, opposition and coaches' selection decisions are unmeasured.
   Stratification reduces some pooling but cannot isolate status or position effects.
3. Repeated observations, unequal coverage and selection/exclusion rules mean
   high-coverage players dominate row-weighted means. Missing calendar dates or
   player-cycles are not missing-value cells and cannot be treated as zero loads.
4. Single-team, small-player observational sample; no independent replication or
   inference here. Original exclusions may select healthier/fully participating
   sessions. There are no injury, readiness, fatigue or development outcome labels.
5. Ambiguous category mappings, variable status inside cycles and cycle/date
   inconsistencies remain. The paper's session counts cannot repair the CSV.
6. Season-wide ratios and retrospective player averages contain future information
   if used to predict earlier observations. This EDA trains no model or scaler.
   External datasets refer to unlinked people; no cross-source joins are permitted.

## Research readiness and next questions

- **GitHub README:** verified coverage, code/units caveats and sourced day/status
  HSR figure are suitable as descriptive examples, with row and player counts.
- **Portfolio website:** use source-labelled distributions and trajectories with
  captions explaining unequal exposure and gaps; no performance-impact claims.
- **Preliminary proposal:** show the reproducible audit and ask whether day/status
  associations persist after accounting for player and session exposure. Present
  session-ID, minutes, codebook and cycle clarification as data requirements.
- **Future longitudinal modelling:** tables, within-player summaries and observed
  status variation inform model specification. Clarify cycle/date semantics and
  minutes first; inspect sparse strata before any repeated-measures inference.
  Calendar-ordered descriptive analysis is ready; clean cycle-based forecasting
  and unqualified longitudinal claims are not established by this phase.

Phase 02 is ready for methodological review. Phase 03 has not been implemented
or run. No causal, health, talent or player-development findings are claimed.

## Reproduction and artifact index

From the project root, after installation and source download:

```bash
python scripts/download_zenodo.py --verify-only --with-dictionary
python -m pathwaylab.cli --mode eda --raw data/raw/DataSetTMr.csv
pytest -q
python -m pathwaylab.cli --mode zenodo --raw data/raw/DataSetTMr.csv
python -m pathwaylab.cli --mode demo
```

Default EDA output: `outputs/eda/`; findings: `research/EDA_FINDINGS.md`.
There are {len(tables)} CSV tables in [tables]({table_path}), nine source-labelled
PNG figures, metadata with dictionary/QA evidence, this generated report, and a
SHA-256 artifact manifest. Re-running EDA regenerates both reports from tables;
no handwritten numerical findings are required. Original CSV checksum is verified
before and after execution. No new dependency was added.
"""
