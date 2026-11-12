"""Regression checks for audit-confirmed output isolation and demo access defects."""

from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest


def test_default_dashboard_cannot_select_local_research(monkeypatch):
    """Public-safe mode must not expose local research through a viewer widget."""
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    import pathwaylab.dashboard_data as gps
    import pathwaylab.event_dashboard as events

    monkeypatch.delenv("PATHWAYLAB_ENABLE_LOCAL_RESEARCH", raising=False)
    monkeypatch.setattr(gps, "load_research", lambda *a: pytest.fail("Read local GPS"))
    monkeypatch.setattr(events, "load_event_artifacts", lambda *a: pytest.fail("Read local events"))
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app/streamlit_app.py"), default_timeout=30
    ).run()
    assert not app.sidebar.selectbox
    assert any("Synthetic only" in item.value for item in app.sidebar.markdown)
    for section in app.sidebar.radio[0].options:
        assert section[:2].isdigit()
        app.sidebar.radio[0].set_value(section[3:]).run()
        assert not app.exception and not app.error
        assert any("SYNTHETIC - DEMONSTRATION ONLY" in x.value for x in app.warning)


def test_event_output_directory_does_not_rewrite_research(tmp_path, monkeypatch):
    """Artificial event-panel fixture; no genuine player rows or research results."""
    from pathwaylab.event_output import event_outputs
    from pathwaylab.events import METRICS, historical_panel

    monkeypatch.setattr("pathwaylab.event_output.SOURCE", "SYNTHETIC - DEMONSTRATION ONLY")
    monkeypatch.chdir(tmp_path)
    research = tmp_path / "research"
    research.mkdir()
    names = ["EVENT_DATA_SELECTION.md", "EVENT_DATA_AUDIT.md", "PLAYER_TRAJECTORY_FINDINGS.md"]
    for name in names:
        (research / name).write_text("preserve existing research", encoding="utf-8")
    rows = []
    for number in range(20):
        rows.append(
            {
                "player_id": 1,
                "player_name": "SYNTHETIC FIXTURE",
                "team_id": 1,
                "team_name": "Arsenal fixture",
                "match_id": number,
                "match_date": (date(2018, 1, 1) + timedelta(days=number)).isoformat(),
                "season_name": "2018/2019" if number < 10 else "2019/2020",
                "position": "Fixture",
                "minutes": 90.0,
                **{metric: float(number + 1) for metric in METRICS},
                **{metric + "_per90": float(number + 1) for metric in METRICS},
                "source": "SYNTHETIC - DEMONSTRATION ONLY",
            }
        )
    panel = historical_panel(pd.DataFrame(rows))
    manifest = {
        "sha": "synthetic-fixture",
        "discovery": [
            {
                "competition_name": "Fixture",
                "competition_id": 1,
                "season_name": "fixture",
                "season_id": 1,
                "matches": 20,
                "teams": 2,
                "start": "2018-01-01",
                "end": "2018-01-20",
            }
        ],
    }
    audit = [{"match_id": n, "status": "ok", "event_rows": 1} for n in range(20)]
    destination = tmp_path / "isolated"
    destination.mkdir()
    event_outputs(panel, panel, audit, manifest, destination)
    assert (destination / "REPORT.md").is_file()
    assert "SYNTHETIC - DEMONSTRATION ONLY" in (destination / "REPORT.md").read_text(
        encoding="utf-8"
    )
    for name in names:
        assert (research / name).read_text(encoding="utf-8") == "preserve existing research"


def test_untrusted_mode_value_cannot_enable_research(monkeypatch):
    """A forged widget return value cannot override trusted server configuration."""
    pytest.importorskip("streamlit")
    from streamlit.delta_generator import DeltaGenerator
    from streamlit.testing.v1 import AppTest

    import pathwaylab.dashboard_data as gps
    import pathwaylab.event_dashboard as events

    monkeypatch.delenv("PATHWAYLAB_ENABLE_LOCAL_RESEARCH", raising=False)
    monkeypatch.setattr(gps, "load_research", lambda *a: pytest.fail("Read local GPS"))
    monkeypatch.setattr(events, "load_event_artifacts", lambda *a: pytest.fail("Read local events"))
    selectbox = DeltaGenerator.selectbox

    def forged_mode(self, label, *args, **kwargs):
        if label == "Data mode":
            return "Verified local research"
        return selectbox(self, label, *args, **kwargs)

    monkeypatch.setattr(DeltaGenerator, "selectbox", forged_mode)
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app/streamlit_app.py"), default_timeout=30
    ).run()
    assert not app.exception and not app.error
    assert any("SYNTHETIC - DEMONSTRATION ONLY" in x.value for x in app.warning)
    app.sidebar.radio[0].set_value("Player Performance Trajectories").run()
    assert not app.exception and not app.error
    assert any("SYNTHETIC - DEMONSTRATION ONLY" in x.value for x in app.warning)
