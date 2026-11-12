"""Chronological split of aggregated football microcycles with persistence baseline."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = [
    "train_hsr",
    "train_td",
    "train_spr",
    "train_acc",
    "n_training_sessions",
    "starter_share",
    "prior_hsr_mean3",
]
CAT = ["position"]


def chronological_split(
    frame: pd.DataFrame, test_fraction: float = 0.25
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Group ALL players by prediction target microcycle to prevent future-week contamination."""
    cycles = sorted(frame["next_microcycle"].unique())
    if len(cycles) < 6:
        raise ValueError("Need >=6 distinct target microcycles for chronological holdout")
    n_test = max(2, int(np.ceil(len(cycles) * test_fraction)))
    boundary = cycles[-n_test]
    train = frame.loc[frame["next_microcycle"] < boundary].copy()
    test = frame.loc[frame["next_microcycle"] >= boundary].copy()
    if train.empty or test.empty:
        raise ValueError("Empty chronological train/test partition")
    if train["next_microcycle"].max() >= test["next_microcycle"].min():
        raise AssertionError("Temporal leakage: target week overlap")
    return train, test


def run_forecast(frame: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    train, test = chronological_split(frame)
    pre = ColumnTransformer(
        [
            (
                "num",
                Pipeline([("fill", SimpleImputer(strategy="median")), ("scale", StandardScaler())]),
                NUMERIC,
            ),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
        ]
    )
    model = Pipeline([("pre", pre), ("ridge", Ridge(alpha=10.0))])
    model.fit(train[NUMERIC + CAT], train["next_train_hsr"])
    pred = model.predict(test[NUMERIC + CAT])
    baseline = test["train_hsr"].to_numpy()
    actual = test["next_train_hsr"].to_numpy()
    scores = {
        "model": "Ridge, alpha=10 (no tuning)",
        "target": "Next OBSERVED microcycle training HSR (meters)",
        "train_rows": len(train),
        "test_rows": len(test),
        "train_target_microcycles": sorted(map(int, train["next_microcycle"].unique())),
        "test_target_microcycles": sorted(map(int, test["next_microcycle"].unique())),
        "ridge_mae": float(mean_absolute_error(actual, pred)),
        "persistence_mae": float(mean_absolute_error(actual, baseline)),
        "ridge_rmse": float(np.sqrt(mean_squared_error(actual, pred))),
        "persistence_rmse": float(np.sqrt(mean_squared_error(actual, baseline))),
        "note": "Holdout evaluation is exploratory; no nested CV, no uncertainty "
        "estimates, no injury prediction.",
    }
    out = test[
        ["player_id", "position", "microcycle", "next_microcycle", "train_hsr", "next_train_hsr"]
    ].copy()
    out["ridge_prediction"] = pred
    out["persistence_prediction"] = baseline
    return scores, out
