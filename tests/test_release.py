"""Offline public-demo checks: no local research data or fitted models needed."""

from pathlib import Path

import pytest


def test_public_demo_never_loads_real_research(monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    import pathwaylab.dashboard_data as loader

    monkeypatch.setattr(loader, "load_research", lambda *a: pytest.fail("Demo loaded real data"))
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app/streamlit_app.py"), default_timeout=30
    ).run()
    for section in app.sidebar.radio[0].options:
        app.sidebar.radio[0].set_value(section).run()
        assert not app.exception and not app.error
        assert any("SYNTHETIC - DEMONSTRATION ONLY" in w.value for w in app.warning)


def test_missing_real_artifacts_fail_gracefully(tmp_path, monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    import pathwaylab.dashboard_data as loader

    monkeypatch.setenv("PATHWAYLAB_ENABLE_LOCAL_RESEARCH", "1")
    monkeypatch.setattr(loader, "ROOT", tmp_path)
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app/streamlit_app.py"), default_timeout=30
    ).run()
    app.sidebar.selectbox[0].set_value("Verified local research").run()
    assert not app.exception
    assert app.error and "unavailable" in app.error[0].value
