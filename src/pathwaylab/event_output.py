"""Computed independent-cohort summaries, sensitivities, figures and local reports."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .eda import markdown_table
from .events import SOURCE, historical_panel


def event_outputs(
    panel: pd.DataFrame,
    all_players: pd.DataFrame,
    audit: list[dict],
    manifest: dict,
    dest: Path,
    report_dir: Path | None = None,
) -> dict:
    """Write artifacts to dest; external research narratives require explicit opt-in."""

    def write_research(name: str, content: str, encoding: str = "utf-8") -> None:
        if report_dir is not None:
            report_dir.mkdir(parents=True, exist_ok=True)
            (report_dir / name).write_text(content, encoding=encoding)

    coverage = pd.DataFrame(manifest["discovery"])[
        [
            "competition_name",
            "competition_id",
            "season_name",
            "season_id",
            "matches",
            "teams",
            "start",
            "end",
        ]
    ]
    write_research(
        "EVENT_DATA_SELECTION.md",
        "# Event data selection\n\nOfficial StatsBomb commit `"
        + manifest["sha"]
        + "`. IDs read from official metadata.\n\n"
        + markdown_table(coverage, list(coverage.columns))
        + "\n\nSelected all metadata-available Arsenal WFC fixtures in the "
        "earliest two adjacent WSL seasons: "
        "2018/2019 (37/4, 20 matches), 2019/2020 (37/42, 15 matches). Bounded team cohort "
        "chosen before metric direction was examined. Download plan: 35 events plus 35 lineups, "
        "four workers, retries and caching; no full repository download. La Liga alternatives "
        "have only 35/33 available matches across 19/20 teams. Their complete coverage and player "
        "continuity are unverified; alternative lineups were not downloaded. WSL team continuity "
        "is known from metadata; stable player continuity is computed after ingestion. Newer WSL "
        "seasons expand scope or introduce a gap. These metadata counts are "
        "not proof of full seasons. "
        "No missing fixtures can be identified without an independent schedule. No dataset switch. "
        "See EVENT_DATA_AUDIT.md for exclusions and "
        "PLAYER_TRAJECTORY_FINDINGS.md for continuity.\n",
        encoding="utf-8",
    )
    audit_table = pd.DataFrame(audit).fillna("")
    write_research(
        "EVENT_DATA_AUDIT.md",
        "# Event data audit\n\nOfficial StatsBomb source, commit `" + manifest["sha"] + "`. "
        "All selected source byte hashes, URLs, match IDs, dates, seasons and download statuses "
        "are retained in data/raw/statsbomb/source_manifest.json. Both event/lineup files are "
        "required. Documentation/metadata hashes are recorded separately.\n\n"
        + markdown_table(audit_table, list(audit_table.columns))
        + "\n\nTimeline validation rejects backwards timestamps (>0.01 s) in event-index order. "
        "Example excluded match 2275044 index 2106 Ball Receipt resets to first-half 00:00:00.417. "
        "No repair is invented. Duplicate IDs, unrostered participants, missing ends, inactive "
        "counted actions and contradictory substitutions are rejected. Temporary off-field time "
        "is flagged but not subtracted: estimated event-clock minutes can "
        "overstate active exposure. "
        "No official playing-minute total independently verifies them. Unused substitutes are not "
        "zero-performance observations. No source rows are modified; excluded files stay local.\n",
        encoding="utf-8",
    )
    season = (
        panel.groupby(["player_id", "player_name", "season_name"])
        .agg(
            appearances=("match_id", "nunique"),
            minutes=("minutes", "sum"),
            passes=("passes", "sum"),
            shots=("shots", "sum"),
        )
        .reset_index()
    )
    season["passes_per90"] = 90 * season.passes / season.minutes
    season["shots_per90"] = 90 * season.shots / season.minutes
    season.to_csv(dest / "player_seasons.csv", index=False)
    continuity = season.groupby("player_id").season_name.nunique()
    eligible = season.loc[season.appearances.ge(5) & season.minutes.ge(450)]
    paired = eligible.pivot(
        index="player_id", columns="season_name", values="passes_per90"
    ).dropna()
    paired["change_per90"] = paired.iloc[:, 1] - paired.iloc[:, 0]
    paired.to_csv(dest / "paired_seasons.csv")
    peers = (
        panel.groupby(["season_name", "position"])
        .agg(
            players=("player_id", "nunique"),
            appearances=("match_id", "size"),
            minutes=("minutes", "sum"),
            passes=("passes", "sum"),
        )
        .reset_index()
    )
    peers["pooled_passes_per90"] = np.where(
        peers.players.ge(4), 90 * peers.passes / peers.minutes, np.nan
    )
    peers.to_csv(dest / "position_context.csv", index=False)
    sensitivities = []
    for threshold in [15, 30, 60]:
        subset = all_players.loc[
            all_players.team_name.str.contains("Arsenal") & all_players.minutes.ge(threshold)
        ]
        for s, g in subset.groupby("season_name"):
            sensitivities.append(
                dict(
                    variant=f"minutes_ge{threshold}",
                    season=s,
                    n=len(g),
                    players=g.player_id.nunique(),
                    minutes=g.minutes.sum(),
                    passes_per90=90 * g.passes.sum() / g.minutes.sum(),
                )
            )
    for s, g in panel.groupby("season_name"):
        matches = sorted(g.match_id.unique())
        subset = g.loc[g.match_id.isin(matches[::2])]
        sensitivities.append(
            dict(
                variant="alternating_match_ids",
                season=s,
                n=len(subset),
                players=subset.player_id.nunique(),
                minutes=subset.minutes.sum(),
                passes_per90=90 * subset.passes.sum() / subset.minutes.sum(),
            )
        )
    sensitivity = pd.DataFrame(sensitivities)
    sensitivity.to_csv(dest / "sensitivity.csv", index=False)
    # Direction of change in strictly prior window estimates, ending within each season.
    windows = []
    for w in [3, 5, 7]:
        history = historical_panel(panel, window=w)
        for (pid, s), g in history.groupby(["player_id", "season_name"]):
            vals = g.prior_passes_per90.dropna()
            if len(vals) >= 2:
                windows.append(
                    dict(
                        window=w,
                        player_id=pid,
                        season=s,
                        n=len(vals),
                        last_minus_first=vals.iloc[-1] - vals.iloc[0],
                    )
                )
    window_table = pd.DataFrame(windows)
    window_table.to_csv(dest / "window_directions.csv", index=False)
    direction = (
        window_table.assign(sign=np.sign(window_table.last_minus_first))
        .groupby(["player_id", "season"])
        .sign.agg(["size", "nunique"])
    )
    direction = direction.loc[direction["size"].ge(2)]
    summary = dict(
        source=SOURCE,
        sha=manifest["sha"],
        selected_matches=len(audit),
        valid_matches=sum(a["status"] == "ok" for a in audit),
        excluded_matches=sum(a["status"] != "ok" for a in audit),
        distinct_all_rostered_players=all_players.player_id.nunique(),
        primary_players=panel.player_id.nunique(),
        primary_appearances=len(panel),
        multi_season_players=int(continuity.ge(2).sum()),
        paired_eligible_players=len(paired),
        positive_paired_changes=int(paired.change_per90.gt(0).sum()),
        median_paired_change=float(paired.change_per90.median()),
        seasons=sorted(panel.season_name.unique()),
        event_rows=sum(a.get("event_rows", 0) for a in audit),
    )
    if "analysis_policy" in manifest:
        summary["analysis_policy"] = manifest["analysis_policy"]
    (dest / "summary.json").write_text(json.dumps(summary, indent=2))
    files = []

    def save(fig, name, caption):
        fig.text(0.02, 0.035, caption, fontsize=8)
        fig.text(0.02, 0.012, SOURCE, fontsize=8)
        fig.tight_layout(rect=(0, 0.10, 1, 0.96))
        fig.savefig(dest / name, dpi=170)
        plt.close(fig)
        files.append(name)

    fig, ax = plt.subplots(figsize=(10, 6))
    counts = panel.groupby("season_name").match_id.nunique()
    counts.plot.bar(ax=ax, color="#0072B2", rot=0)
    ax.set(title="Observed Arsenal match coverage", ylabel="Validated matches")
    save(
        fig,
        "01_coverage.png",
        f"Selected={len(audit)}; validated={summary['valid_matches']}. "
        "Incomplete observed seasons; >=30 estimated minutes per appearance.",
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(continuity, bins=[0.5, 1.5, 2.5], rwidth=0.7, color="#0072B2")
    ax.set(
        xticks=[1, 2],
        xlabel="Observed seasons per player",
        ylabel="Players",
        title=f"Primary cohort continuity | P={panel.player_id.nunique()}",
    )
    save(
        fig,
        "02_continuity.png",
        "Stable StatsBomb player IDs only; coverage/playing-time selection can "
        "produce survivorship bias.",
    )
    example = panel.groupby("player_id").size().idxmax()
    g = panel.loc[panel.player_id.eq(example)].sort_values("match_date")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.scatter(
        pd.to_datetime(g.match_date), g.passes_per90, label="Observed match", color="#0072B2"
    )
    ax.scatter(
        pd.to_datetime(g.match_date),
        g.prior_passes_per90,
        label="Prior five appearances, exposure-weighted",
        color="#D55E00",
        marker="x",
    )
    ax.legend()
    ax.set(
        ylabel="Pass attempts / 90 estimated minutes",
        title=f"Observed trajectory: {g.player_name.iloc[0]} | n={len(g)}",
    )
    save(
        fig,
        "03_trajectory.png",
        "Example chosen by most observed appearances, not largest change. "
        "Points only; no interpolation across absent coverage.",
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    if len(paired):
        ax.scatter(paired.iloc[:, 0], paired.iloc[:, 1])
        limits = [min(paired.iloc[:, :2].min()), max(paired.iloc[:, :2].max())]
        ax.plot(limits, limits, color="black", linestyle="--")
    ax.set(
        xlabel=f"{summary['seasons'][0]} passes / 90",
        ylabel=f"{summary['seasons'][1]} passes / 90",
        title=f"Paired observed-season rates | P={len(paired)}",
    )
    save(
        fig,
        "04_paired_seasons.png",
        "Require >=5 appearances and >=450 estimated minutes each season. Not "
        "causal improvement or ability change.",
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    variability = panel.groupby("player_id").passes_per90.agg(["std", "count"])
    ax.bar(variability.index.astype(str), variability["std"], color="#0072B2")
    ax.tick_params(axis="x", rotation=60)
    ax.set(
        ylabel="Within-player sample SD (passes / 90)",
        title=f"Observed involvement variability | N={len(panel)}, P={len(variability)}",
    )
    save(
        fig,
        "05_variability.png",
        "Unequal observations; roles, tactics, exposure estimates and opponent "
        "selection confound variation.",
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    for s, g in sensitivity.groupby("season"):
        ax.plot(g.variant, g.passes_per90, marker="o", label=s)
    ax.legend()
    ax.set(
        ylabel="Pooled pass attempts / 90 estimated minutes",
        title="Exposure and coverage sensitivity",
    )
    save(
        fig,
        "06_sensitivity.png",
        "Thresholds 15/30/60 minutes and every second available match ID. "
        "Descriptive perturbations; no confidence intervals.",
    )
    report = f"""# Phase 06 — observed match-performance trajectories

Independent StatsBomb lane. Source: https://github.com/hudl/open-data, pinned commit
`{manifest["sha"]}`. Accessed 2026-11-12. Raw and individual derivatives stay local.
No GPS identities or values were joined. No club affiliation. StatsBomb attribution
and official logo are required for publication; this local analysis is not published.

Question: how do observed indicators change across matches/seasons, and how do
exposure and coverage affect those summaries? Cohort: all metadata-available Arsenal
fixtures in {", ".join(summary["seasons"])}. Not a complete league-season sample.

## Computed sample and audit

```json
{json.dumps(summary, indent=2)}
```

Exposure: Starting XI to substitutions/dismissals and period-end event clocks,
including stoppage time, excluding halftime. Estimated minutes, not verified official
minutes. Unused roster players are retained with zero exposure in QA only. Main
panel requires >=30 minutes. Temporary off-field treatment is not subtracted; match
audit flags it. Missing/inconsistent event/lineup evidence excludes a match; see
match_audit.csv for every retained/excluded match and reason. Event IDs must be unique.
Player/team identity is by source ID, never name. Transfers are separate team records;
the primary team cohort cannot follow players' unobserved minutes at other clubs.

## Season rates and peer context

{
        markdown_table(
            season,
            [
                "player_id",
                "player_name",
                "season_name",
                "appearances",
                "minutes",
                "passes_per90",
                "shots_per90",
            ],
        )
    }

Source position is the initial recorded role, not a permanent talent category.
position_context.csv reports players, appearances and exposure, suppressing rates
for groups with fewer than four players. These pooled descriptions include the
individual; they are not leave-player-out percentiles or quality rankings.

## Longitudinal findings and uncertainty

Of {len(paired)} players meeting >=5 appearances and >=450 estimated minutes in
each observed season, {summary["positive_paired_changes"]} have higher later-season
pass-attempt rates. Median paired change: {summary["median_paired_change"]:.6f}
pass attempts / 90 estimated minutes. This is observed involvement change, not proven
improvement. The fixed example figure selects the most observed player by count,
not outcome. Historical windows 3/5/7 use strictly prior included appearances;
window_directions.csv retains sign changes rather than selecting a preferred window.
Among {len(direction)} player-seasons with at least two available window comparisons,
{int(direction["nunique"].gt(1).sum())} change the sign of last-minus-first historical
window rate. This heuristic uses different available window endpoints and is not
a formal trend estimator or an uncertainty interval.

{markdown_table(sensitivity, ["variant", "season", "n", "players", "minutes", "passes_per90"])}

No independent-observation CIs or complex models are fitted. Few selected matches,
unequal minutes, shared team/opponent context and within-player dependence make
precise inference unjustified. Match omission and exposure-threshold sensitivities
are descriptive, not corrections of missing coverage. Missing matches are not player
non-appearances. Counts/ratios are not objective performance quality. Role changes,
tactics, team effects, selection, survivorship, regression to mean, season coverage
and unadjusted opposition may explain changes. Patterns can motivate further video
review, not automatic recruitment or coaching decisions.

Supports: observed match trajectories and qualified multi-season involvement
comparisons. Does NOT support academy development, physical maturation, fitness,
injury, readiness, causal improvement, or professional deployment claims.

## Figures and reproducibility

Run `python scripts/run_events.py discover`, `download`, then `analyze`.
Read PLAYER_TRAJECTORY_PROTOCOL.md, EVENT_METRIC_DICTIONARY.md and source audit.
Tables/figures remain under ignored outputs/events; source bytes under ignored data/raw.
"""
    if "analysis_policy" in manifest:
        report = "**" + manifest["analysis_policy"] + "**\n\n" + report
    for name in files:
        report += f"\n![{name}](../outputs/events/{name})\n"
    write_research("PLAYER_TRAJECTORY_FINDINGS.md", report, encoding="utf-8")
    (dest / "REPORT.md").write_text(report.replace("../outputs/events/", ""), encoding="utf-8")
    return summary
