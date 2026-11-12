"""Synthetic statistical smoke checks; fixtures are SYNTHETIC - DEMONSTRATION ONLY."""

import numpy as np
import pandas as pd
import pytest

from pathwaylab.inference import coefficients, fit_intercept, training_sample


def test_selection_retains_zeros_and_rejects_invalid_data():
    data = pd.DataFrame(
        {
            "player_id": ["a", "a", "a"],
            "date": pd.date_range("2024-01-01", periods=3),
            "microcycle": [1] * 3,
            "md_day": [0, -1, 1],
            "HSR": [999, 0, np.nan],
            "position": ["X"] * 3,
            "source": ["zenodo_real"] * 3,
            "RATIOHSR": [1] * 3,
            "status": ["T"] * 3,
        }
    )
    sample, log = training_sample(data)
    assert sample.HSR.tolist() == [0]
    assert sample.y.tolist() == [0]
    assert log["excluded_dia0"] == 1 and log["excluded_missing"] == 1
    assert "RATIOHSR" not in sample and "status" not in sample
    data.loc[1, "HSR"] = -1
    with pytest.raises(ValueError, match="Negative"):
        training_sample(data)
    data.loc[1, "HSR"] = 0
    with pytest.raises(ValueError, match="Duplicate"):
        training_sample(pd.concat([data, data.iloc[:1]]))
    data.loc[0, "source"] = "SYNTHETIC"
    with pytest.raises(ValueError, match="Real-only"):
        training_sample(data)


def test_synthetic_random_intercept_smoke():
    pytest.importorskip("statsmodels")
    rng = np.random.default_rng(19)
    group = np.repeat(np.arange(16), 30)
    data = pd.DataFrame(
        {"player_id": group, "y": rng.normal(0, 1, 16)[group] + rng.normal(0, 0.4, len(group))}
    )
    result, info, attempts = fit_intercept(
        data, "y ~ 1", "SYNTHETIC_TEST", source="SYNTHETIC - DEMONSTRATION ONLY"
    )
    assert info["converged"]
    assert 0.5 < info["icc"] < 0.99
    assert info["icc"] == pytest.approx(
        info["between_variance"] / (info["between_variance"] + info["residual_variance"])
    )
    assert attempts[0]["exception"] is None
    effect = coefficients(result, info)[0]
    assert effect["lower95"] < effect["estimate"] < effect["upper95"]


def test_failed_fit_is_visible():
    pytest.importorskip("statsmodels")
    frame = pd.DataFrame({"player_id": [1, 1, 2, 2], "y": [1, 2, 3, 4]})
    result, info, attempts = fit_intercept(frame, "y ~ missing_predictor", "bad")
    assert result is None and not info["converged"]
    assert len(attempts) == 2
    assert all(a["exception"] for a in attempts)
    assert coefficients(result, info) == []
