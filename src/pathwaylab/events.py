"""Independent StatsBomb event-clock exposure and descriptive trajectories."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .event_source import RAW

SOURCE = "StatsBomb Open Data | independent WSL event cohort | estimated event-clock minutes"
METRICS = ["passes", "completed_passes", "shots", "xg", "carries", "tackles", "interceptions"]


def seconds(timestamp: str) -> float:
    h, m, s = map(float, timestamp.split(":"))
    if not (0 <= m < 60 and 0 <= s < 60):
        raise ValueError("Invalid timestamp")
    return h * 3600 + m * 60 + s


def player_match(
    events: list, lineups: list, *, allow_invalid_receipt_time: bool = False
) -> tuple[pd.DataFrame, dict]:
    """Reconstruct stints; optionally quarantine only an unscored receipt's clock.

    Strict chronology is the default and reproduces Phase 06. The audit sensitivity
    never alters raw timestamps, counted actions, substitutions or period endpoints.
    """
    if not events or not lineups:
        raise ValueError("Missing events/lineups")
    ids = [e["id"] for e in events]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate event IDs")
    if any(e["period"] not in [1, 2, 5] for e in events):
        raise ValueError("Extra time unsupported in selected cohort")
    durations = {}
    for period in [1, 2]:
        ends = [
            seconds(e["timestamp"])
            for e in events
            if e["period"] == period and e["type"]["name"] == "Half End"
        ]
        if not ends or max(ends) < 40 * 60:
            raise ValueError("Missing/incomplete match period")
        durations[period] = max(ends)
    end = sum(durations.values())
    roster = {}
    for team in lineups:
        for p in team["lineup"]:
            key = (team["team_id"], p["player_id"])
            if key in roster:
                raise ValueError("Duplicate roster identity")
            roster[key] = dict(
                player_id=p["player_id"],
                player_name=p["player_name"],
                team_id=team["team_id"],
                team_name=team["team_name"],
                minutes=0.0,
                position="Unknown",
                **{m: 0.0 for m in METRICS},
            )
    active, starts, stops = {}, {}, {}
    for e in events:
        if e["type"]["name"] == "Starting XI":
            if len(e["tactics"]["lineup"]) != 11:
                raise ValueError("Starting XI does not contain 11 players")
            for p in e["tactics"]["lineup"]:
                key = (e["team"]["id"], p["player"]["id"])
                if key not in roster or key in active:
                    raise ValueError("Unrostered/duplicate starter")
                active[key] = starts[key] = 0.0
                roster[key]["position"] = p["position"]["name"]
    if len(active) != 22:
        raise ValueError("Missing starting teams")
    last = -1.0
    temporary_off = 0
    xg_missing = 0
    ignored_receipt_time_ids = []
    for e in sorted(events, key=lambda x: x["index"]):
        if e["period"] == 5:
            continue
        t = seconds(e["timestamp"]) + (durations[1] if e["period"] == 2 else 0)
        kind = e["type"]["name"]
        if t > end + 1:
            raise ValueError("Contradictory event timeline")
        if t < last - 0.01:
            if (
                allow_invalid_receipt_time
                and kind == "Ball Receipt*"
                and not (
                    {"substitution", "bad_behaviour", "foul_committed", "player_off"} & e.keys()
                )
            ):
                ignored_receipt_time_ids.append(e["id"])
            else:
                raise ValueError("Contradictory event timeline")
        else:
            last = t
        if kind == "Pass" and "pass" not in e:
            raise ValueError("Missing pass attributes; completion cannot be verified")
        if "player" not in e:
            continue
        key = (e["team"]["id"], e["player"]["id"])
        if key not in roster:
            raise ValueError("Unrostered event player")
        if roster[key]["position"] == "Unknown" and "position" in e:
            roster[key]["position"] = e["position"]["name"]
        dismissed = any(
            e.get(k, {}).get("card", {}).get("name") in ["Red Card", "Second Yellow"]
            for k in ["bad_behaviour", "foul_committed"]
        )
        permanent = kind == "Player Off" and e.get("player_off", {}).get("permanent", False)
        if kind == "Player Off" and not permanent:
            temporary_off += 1
        if kind == "Substitution" or dismissed or permanent:
            if key not in active:
                raise ValueError("Exit for inactive player")
            roster[key]["minutes"] += (t - active.pop(key)) / 60
            stops[key] = t
            if kind == "Substitution":
                replacement = (key[0], e["substitution"]["replacement"]["id"])
                if replacement not in roster or replacement in starts:
                    raise ValueError("Invalid/missing replacement")
                active[replacement] = starts[replacement] = t
        metric = {
            "Pass": "passes",
            "Shot": "shots",
            "Carry": "carries",
            "Interception": "interceptions",
        }.get(kind)
        if kind == "Duel" and e.get("duel", {}).get("type", {}).get("name") == "Tackle":
            metric = "tackles"
        if metric:
            if key not in active:
                raise ValueError("Counted action by inactive player: missing substitution?")
            roster[key][metric] += 1
            if kind == "Pass" and "outcome" not in e.get("pass", {}):
                roster[key]["completed_passes"] += 1
            if kind == "Shot":
                xg = e.get("shot", {}).get("statsbomb_xg")
                if xg is None:
                    xg_missing += 1
                    roster[key]["xg"] = np.nan
                else:
                    roster[key]["xg"] += xg
    for key, start in active.items():
        roster[key]["minutes"] += (end - start) / 60
    result = pd.DataFrame(roster.values())
    for metric in METRICS:
        result[metric + "_per90"] = np.where(
            result.minutes.ge(30), 90 * result[metric] / result.minutes.replace(0, np.nan), np.nan
        )
    result["completion_pct"] = 100 * result.completed_passes / result.passes.replace(0, np.nan)
    result["source"] = SOURCE
    quality = {
        "event_rows": len(events),
        "duration_minutes": end / 60,
        "temporary_off_events": temporary_off,
        "missing_shot_xg": xg_missing,
    }
    if allow_invalid_receipt_time:
        quality["ignored_receipt_time_ids"] = ignored_receipt_time_ids
    return result, quality


def historical_panel(panel: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """Exposure-weighted strictly historical rolling passes; no future player means."""
    panel = panel.sort_values(["player_id", "match_date", "match_id"]).copy()
    g = panel.groupby("player_id")
    previous_count = g.passes.transform(
        lambda s: s.shift().rolling(window, min_periods=window).sum()
    )
    previous_minutes = g.minutes.transform(
        lambda s: s.shift().rolling(window, min_periods=window).sum()
    )
    panel["prior_passes_per90"] = 90 * previous_count / previous_minutes
    return panel


def run_events(
    root: Path = RAW,
    dest: Path = Path("outputs/events"),
    report_dir: Path | None = None,
    *,
    allow_invalid_receipt_time: bool = False,
) -> dict:
    """Reproduce event artifacts without overwriting research reports by default."""
    manifest = json.loads((root / "source_manifest.json").read_text())
    files = {r["path"]: r for r in manifest["files"]}
    panels, audit = [], []
    for item in manifest["selected"]:
        m = item["match"]
        mid = m["match_id"]
        try:
            loaded = []
            for kind in ["events", "lineups"]:
                path = f"data/{kind}/{mid}.json"
                record = files[path]
                content = (root / path).read_bytes()
                if (
                    record["status"] != "ok"
                    or hashlib.sha256(content).hexdigest() != record["sha256"]
                ):
                    raise ValueError("Missing/unverified source bytes")
                loaded.append(json.loads(content))
            panel, quality = player_match(
                *loaded, allow_invalid_receipt_time=allow_invalid_receipt_time
            )
            panel = panel.assign(
                match_id=mid,
                match_date=m["match_date"],
                season_id=item["season_id"],
                season_name=item["season_name"],
                competition_id=item["competition_id"],
            )
            panels.append(panel)
            audit.append(dict(match_id=mid, status="ok", **quality))
        except (ValueError, KeyError, OSError) as exc:
            audit.append(dict(match_id=mid, status="excluded", reason=str(exc)))
    if not panels:
        raise ValueError("No valid matches: inspect source and exposure assumptions")
    all_players = pd.concat(panels, ignore_index=True)
    primary = all_players.loc[
        all_players.team_name.str.contains("Arsenal") & all_players.minutes.ge(30)
    ].copy()
    primary = historical_panel(primary)
    dest.mkdir(parents=True, exist_ok=True)
    all_players.to_csv(dest / "player_match_all.csv", index=False)
    primary.to_csv(dest / "player_match.csv", index=False)
    pd.DataFrame(audit).to_csv(dest / "match_audit.csv", index=False)
    from .event_output import event_outputs

    if allow_invalid_receipt_time:
        manifest = {
            **manifest,
            "analysis_policy": (
                "AUDIT SENSITIVITY: ignore invalid unscored receipt clocks only; raw data unchanged"
            ),
        }
    summary = event_outputs(primary, all_players, audit, manifest, dest, report_dir=report_dir)
    (dest / "manifest.json").write_text(
        json.dumps(
            {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in dest.iterdir()
                if p.is_file() and p.name != "manifest.json"
            },
            indent=2,
        )
    )
    print(summary)
    return summary
