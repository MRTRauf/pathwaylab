"""Artificial exposure fixtures have exact answers; real integration uses pinned local files."""

import copy
import json

import numpy as np
import pandas as pd
import pytest

from pathwaylab.event_source import fetch
from pathwaylab.events import historical_panel, player_match


def fixture():
    teams = []
    events = []
    for team in [1, 2]:
        lineup = [
            dict(player_id=team * 100 + i, player_name=f"fixture {team}-{i}") for i in range(12)
        ]
        teams.append(
            dict(
                team_id=team,
                team_name="Arsenal fixture" if team == 1 else "opponent",
                lineup=lineup,
            )
        )
        events.append(
            dict(
                id=f"xi{team}",
                index=team,
                period=1,
                timestamp="00:00:00",
                type=dict(name="Starting XI"),
                team=dict(id=team),
                tactics=dict(
                    lineup=[
                        dict(player=dict(id=p["player_id"]), position=dict(name="Midfield"))
                        for p in lineup[:11]
                    ]
                ),
            )
        )

    def event(id, index, period, time, kind, pid=None, **extra):
        e = dict(
            id=id,
            index=index,
            period=period,
            timestamp=time,
            type=dict(name=kind),
            team=dict(id=1),
            **extra,
        )
        if pid is not None:
            e["player"] = dict(id=pid)
        return e

    events += [
        event("pass", 3, 1, "00:10:00", "Pass", 100, **{"pass": {}}),
        event("h1", 4, 1, "00:45:00", "Half End"),
        event(
            "sub",
            5,
            2,
            "00:15:00",
            "Substitution",
            100,
            substitution=dict(replacement=dict(id=111)),
        ),
        event("shot", 6, 2, "00:20:00", "Shot", 111, shot=dict(statsbomb_xg=0.2)),
        event("h2", 7, 2, "00:45:00", "Half End"),
    ]
    return events, teams


def test_full_match_substitute_unused_and_per90():
    e, lineups = fixture()
    p, q = player_match(e, lineups)
    p = p.set_index("player_id")
    assert p.loc[101, "minutes"] == 90
    assert p.loc[100, "minutes"] == 60
    assert p.loc[111, "minutes"] == 30
    assert p.loc[211, "minutes"] == 0
    assert np.isnan(p.loc[211, "shots_per90"])
    assert p.loc[111, "shots_per90"] == 3
    assert p.loc[100, "completion_pct"] == 100
    assert p.loc[111, "xg"] == 0.2
    assert q["duration_minutes"] == 90


@pytest.mark.parametrize(
    "variant",
    ["duplicate", "missing_sub", "missing_end", "unrostered", "timeline", "lineup", "pass_field"],
)
def test_invalid_evidence_is_rejected(variant):
    e, lineups = fixture()
    if variant == "duplicate":
        e.append(copy.deepcopy(e[0]))
    if variant == "missing_sub":
        e = [x for x in e if x["id"] != "sub"]
    if variant == "missing_end":
        e = [x for x in e if x["id"] != "h2"]
    if variant == "unrostered":
        e[2]["player"]["id"] = 9999
    if variant == "timeline":
        e[5]["timestamp"] = "00:00:01"
    if variant == "lineup":
        lineups = []
    if variant == "pass_field":
        e[2].pop("pass")
    with pytest.raises(ValueError):
        player_match(e, lineups)


def test_red_card_and_added_time():
    e, lineups = fixture()
    e[-1]["timestamp"] = "00:48:00"
    e.insert(
        -1,
        dict(
            id="red",
            index=6.5,
            period=2,
            timestamp="00:30:00",
            type=dict(name="Bad Behaviour"),
            team=dict(id=1),
            player=dict(id=101),
            bad_behaviour=dict(card=dict(name="Red Card")),
        ),
    )
    p, q = player_match(e, lineups)
    p = p.set_index("player_id")
    assert p.loc[101, "minutes"] == 75
    assert p.loc[102, "minutes"] == 93


def test_optional_receipt_clock_policy_preserves_counts_and_exposure():
    """Only an unscored receipt's invalid clock may be quarantined, never an action."""
    original, lineups = fixture()
    expected, _ = player_match(original, lineups)
    changed = copy.deepcopy(original)
    changed.insert(
        3,
        dict(
            id="bad-receipt",
            index=3.5,
            period=1,
            timestamp="00:00:00.5",
            type=dict(name="Ball Receipt*"),
            team=dict(id=1),
            player=dict(id=100),
        ),
    )
    before = copy.deepcopy(changed)
    with pytest.raises(ValueError, match="timeline"):
        player_match(changed, lineups)
    actual, quality = player_match(changed, lineups, allow_invalid_receipt_time=True)
    pd.testing.assert_frame_equal(actual, expected)
    assert changed == before
    assert quality["ignored_receipt_time_ids"] == ["bad-receipt"]
    changed[3]["type"]["name"] = "Pass"
    changed[3]["pass"] = {}
    with pytest.raises(ValueError, match="timeline"):
        player_match(changed, lineups, allow_invalid_receipt_time=True)


def test_historical_windows_identity_and_future_perturbation():
    p = pd.DataFrame(
        dict(
            player_id=[1] * 7 + [2] * 7,
            match_id=list(range(14)),
            match_date=pd.date_range("2020-01-01", periods=14).astype(str),
            passes=list(range(7)) * 2,
            minutes=[90] * 14,
        )
    )
    result = historical_panel(p, 3)
    assert result.iloc[3].prior_passes_per90 == 1
    assert np.isnan(result.iloc[7].prior_passes_per90)
    modified = p.copy()
    modified.loc[5, "passes"] = 999
    changed = historical_panel(modified, 3)
    pd.testing.assert_series_equal(
        result.iloc[:6].prior_passes_per90, changed.iloc[:6].prior_passes_per90
    )


def test_json_cache_and_corruption(tmp_path, monkeypatch):
    (tmp_path / "fixture.json").write_text('[{"id":1}]')
    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *a, **k: pytest.fail("cached request accessed network")
    )
    assert fetch("fixture.json", "pinned", tmp_path) == [dict(id=1)]
    (tmp_path / "fixture.json").write_text("partial")
    with pytest.raises(json.JSONDecodeError):
        fetch("fixture.json", "pinned", tmp_path)
