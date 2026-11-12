"""Artificial leakage fixtures; only checksummed originals enter real pipeline outputs."""

import numpy as np
import pandas as pd
import pytest

from pathwaylab.data import LOAD_METRICS
from pathwaylab.forecasting import (
    FEATURES,
    baseline_predictions,
    error_metrics,
    estimator,
    session_features,
    temporal_folds,
)


def artificial_frame() -> pd.DataFrame:
    """SYNTHETIC - DEMONSTRATION ONLY; schema fixture, never a research artifact."""
    dates = pd.date_range("2024-01-01", periods=40)
    d = pd.DataFrame(
        {
            "date": np.tile(dates, 2),
            "player_id": np.repeat(["A", "B"], 40),
            "md_day": -1,
            "microcycle": 1,
            "position": "X",
            "source": "zenodo_real",
        }
    )
    for i, metric in enumerate(LOAD_METRICS):
        d[metric] = np.tile(np.arange(40), 2) + i
    return d


def test_future_and_current_perturbation_cannot_change_features():
    d = artificial_frame()
    original = session_features(d)
    cutoff = pd.Timestamp("2024-01-20")
    changed = d.copy()
    changed.loc[changed.date.ge(cutoff), LOAD_METRICS] = 99999
    perturbed = session_features(changed.sample(frac=1, random_state=42))
    earlier = original.date.le(cutoff)
    pd.testing.assert_frame_equal(original.loc[earlier, FEATURES], perturbed.loc[earlier, FEATURES])
    assert not original.loc[~earlier, FEATURES].equals(perturbed.loc[~earlier, FEATURES])
    # Same-date observations across players are never available to either origin.
    assert original.loc[original.date.eq(cutoff), "lag_HSR"].tolist() == [19, 19]


def test_alignment_zero_hsr_and_match_exclusion():
    d = artificial_frame().iloc[:5].copy()
    d.loc[1, "md_day"] = 0
    d.loc[1, "HSR"] = 9999
    d.loc[2, "HSR"] = 0
    f = session_features(d)
    assert len(f) == 4
    assert f.loc[1, "lag_HSR"] == d.loc[0, "HSR"]
    assert f.loc[2, "lag_HSR"] == 0
    assert f.loc[2, "rolling_mean"] == 0.5
    assert f.loc[2, "history_date"] == pd.Timestamp("2024-01-03")
    assert f.loc[1, "target_hsr"] == 0


def test_ambiguous_dates_and_invalid_sources_rejected():
    d = artificial_frame()
    with pytest.raises(ValueError, match="duplicate"):
        session_features(pd.concat([d, d.iloc[:1]]))
    d.loc[0, "source"] = "SYNTHETIC"
    with pytest.raises(ValueError, match="real-only"):
        session_features(d)


def test_split_global_dates_and_nonoverlapping_validation_windows():
    f = session_features(artificial_frame())
    rows = f.loc[f.history_n.ge(1)]
    folds = temporal_folds(rows)
    assert len(folds) == 4
    evaluated = set()
    for name, train, valid in folds:
        assert train.date.max() < valid.date.min()
        assert set(train.date).isdisjoint(valid.date)
        assert set(valid.date).isdisjoint(evaluated)
        evaluated.update(valid.date)
        assert valid.groupby("date").player_id.nunique().eq(2).all()
        if name != "test":
            assert valid.date.max() < folds[-1][2].date.min()


def test_preprocessing_training_only_and_unseen_player_fallback():
    f = session_features(artificial_frame())
    train, valid = f.loc[f.date.lt("2024-01-20")], f.loc[f.date.ge("2024-01-20")].copy()
    model = estimator("ridge", 1)
    model.fit(train[FEATURES], train.target_hsr)
    statistics = model.steps[0][1].statistics_.copy()
    assert statistics[0] == pytest.approx(train.lag_TD.median())
    valid[FEATURES] = 99999
    model.predict(valid[FEATURES])
    np.testing.assert_array_equal(statistics, model.steps[0][1].statistics_)
    unseen = f.iloc[:1].copy().assign(player_id="UNSEEN", lag_HSR=np.nan, rolling_mean=np.nan)
    for prediction in baseline_predictions(train, unseen).values():
        assert prediction[0] == train.target_hsr.median()


def test_sparse_rolling_history_and_no_target_covariates():
    f = session_features(artificial_frame())
    a = f.loc[f.player_id.eq("A")].reset_index(drop=True)
    assert a.loc[0, "history_n"] == 0
    assert pd.isna(a.loc[0, "rolling_mean"])
    assert a.loc[1, "rolling_mean"] == 1
    assert pd.isna(a.loc[1, "rolling_sd"])
    assert a.loc[3, "rolling_mean"] == 2
    assert set(FEATURES).isdisjoint(
        {"target_hsr", "HSR", "status", "md_day", "microcycle", "position"}
    )
    assert not any("RATIO" in name for name in FEATURES)


def test_original_unit_metrics_and_invalid_predictions():
    scores = error_metrics(np.array([0, 100]), np.array([10, 80]))
    assert scores["mae_m"] == 15
    assert scores["rmse_m"] == pytest.approx(np.sqrt(250))
    assert scores["bias_m"] == -5
    with pytest.raises(ValueError, match="Invalid"):
        error_metrics(np.array([0]), np.array([np.inf]))


def test_deterministic_models():
    f = session_features(artificial_frame())
    train = f.loc[f.history_n.ge(1)]
    for name in ["ridge", "tree"]:
        predictions = [
            estimator(name).fit(train[FEATURES], train.target_hsr).predict(train[FEATURES])
            for _ in range(2)
        ]
        np.testing.assert_allclose(*predictions)
