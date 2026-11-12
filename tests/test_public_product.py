"""Computed synthetic outputs, independent identities and public-product interactions."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pathwaylab.demo_data import LABEL, demo_forecast, event_cohort, load_cohort


def test_generated_cohorts_are_deterministic_and_separate():
    loads, events = load_cohort(), event_cohort()
    pd.testing.assert_frame_equal(loads, load_cohort())
    pd.testing.assert_frame_equal(events, event_cohort())
    assert loads.player_id.str.startswith("DEMO-").all()
    assert events.player_id.str.startswith("EVENT-").all()
    assert set(loads.player_id).isdisjoint(events.player_id)
    assert set(loads.source) == {"SYNTHETIC"} and set(events.source) == {LABEL}
    assert loads.player_id.nunique() == 20 and events.player_id.nunique() == 14
    assert events.minutes.gt(0).all() and events.completed_passes.le(events.passes).all()


def test_demo_metrics_match_actual_predictions_and_common_targets():
    scores, predictions, protocol = demo_forecast(load_cohort())
    targets = []
    for model, group in predictions.groupby("model"):
        errors = group.prediction_m - group.next_train_hsr
        row = scores.loc[scores.Model.eq(model)].iloc[0]
        assert row["MAE (m)"] == pytest.approx(errors.abs().mean())
        assert row["RMSE (m)"] == pytest.approx(np.sqrt((errors**2).mean()))
        targets.append(set(zip(group.player_id, group.next_microcycle)))
    assert all(value == targets[0] for value in targets)
    assert max(protocol["train_target_microcycles"]) < min(protocol["test_target_microcycles"])


def test_demo_event_history_is_shifted_and_exposure_weighted():
    group = event_cohort().loc[lambda x: x.player_id.eq("EVENT-01")]
    assert group.iloc[:3].prior_passes_per90.isna().all()
    assert group.iloc[3].prior_passes_per90 == pytest.approx(
        90 * group.iloc[:3].passes.sum() / group.iloc[:3].minutes.sum()
    )
    assert group.iloc[8].prior_passes_per90 == pytest.approx(
        90 * group.iloc[3:8].passes.sum() / group.iloc[3:8].minutes.sum()
    )


def test_public_entrypoint_blocks_research_even_with_local_flag(monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    import pathwaylab.dashboard_data as gps
    import pathwaylab.event_dashboard as events

    monkeypatch.setenv("PATHWAYLAB_ENABLE_LOCAL_RESEARCH", "1")
    monkeypatch.setenv("PATHWAYLAB_PUBLIC_DEMO", "1")
    monkeypatch.setattr(gps, "load_research", lambda *a: pytest.fail("Read research GPS"))
    monkeypatch.setattr(
        events, "load_event_artifacts", lambda *a: pytest.fail("Read research events")
    )
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app/public_demo.py"), default_timeout=30
    ).run()
    assert not app.exception and not app.error
    assert not app.sidebar.selectbox
    assert any("Synthetic only" in item.value for item in app.sidebar.markdown)
    app.sidebar.radio[0].set_value("Player Performance Trajectories").run()
    assert not app.exception and not app.error
    assert all("EVENT-" in value for value in app.selectbox[0].options)


def test_public_filters_models_navigation_and_empty_states(monkeypatch):
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    monkeypatch.delenv("PATHWAYLAB_ENABLE_LOCAL_RESEARCH", raising=False)
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app/streamlit_app.py"), default_timeout=30
    ).run()
    app.button[0].click().run()
    assert app.sidebar.radio[0].value == "Training load explorer" and not app.exception
    next(w for w in app.multiselect if w.label == "Fictional load players").set_value([]).run()
    assert any("No observations" in x.value for x in app.info)
    next(button for button in app.button if button.label == "Reset filters").click().run()
    selected = next(w for w in app.multiselect if w.label == "Fictional load players")
    assert selected.value == sorted(load_cohort().player_id.unique())[:4]
    assert not app.exception
    app.sidebar.radio[0].set_value("Forecasting lab").run()
    app.selectbox[0].set_value("Training median").run()
    scores, _, _ = demo_forecast(load_cohort())
    expected = scores.loc[scores.Model.eq("Training median"), "MAE (m)"].iloc[0]
    assert app.metric[0].value == f"{expected:.1f} m" and not app.exception
    app.sidebar.radio[0].set_value("Player Performance Trajectories").run()
    app.selectbox[1].set_value("shots").run()
    assert not app.exception and len(app.get("plotly_chart")) == 3
    app.multiselect[0].set_value([]).run()
    assert any("Select at least one" in x.value for x in app.info)
    app.sidebar.radio[0].set_value("Methods and limitations").run()
    assert not app.exception and len(app.tabs) == 3
