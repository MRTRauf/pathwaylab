"""Prevent obvious scientific and engineering mistakes before modelling."""

from __future__ import annotations

import pandas as pd

from .data import LOAD_METRICS


def validate_sessions(frame: pd.DataFrame) -> dict:
    checks = {}
    required = ["player_id", "date", "microcycle", "md_day", "status", "position", *LOAD_METRICS]
    checks["missing_required_columns"] = sorted(set(required) - set(frame.columns))
    checks["n_rows"] = int(len(frame))
    checks["n_players"] = int(frame["player_id"].nunique()) if "player_id" in frame else 0
    checks["n_microcycles"] = int(frame["microcycle"].nunique()) if "microcycle" in frame else 0
    checks["duplicate_player_day"] = (
        int(frame.duplicated(["player_id", "date"]).sum())
        if set(["player_id", "date"]).issubset(frame)
        else None
    )
    checks["negative_load_rows"] = (
        int(frame[LOAD_METRICS].lt(0).any(axis=1).sum())
        if set(LOAD_METRICS).issubset(frame)
        else None
    )
    checks["missing_load_cells"] = (
        int(frame[LOAD_METRICS].isna().sum().sum()) if set(LOAD_METRICS).issubset(frame) else None
    )
    checks["source_labels"] = (
        sorted(map(str, frame["source"].unique())) if "source" in frame else ["unknown"]
    )
    return checks


def make_microcycle_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Next OBSERVED microcycle prediction, never concurrent or patient health inference.

    Inputs available only after the current observed microcycle ends.
    Target is the subsequent observed microcycle's training HSR in meters.
    Match rows (md_day == 0) are excluded from training totals.
    """
    data = frame.copy()
    training = data.loc[data["md_day"] != 0].copy()
    training["is_starter"] = training["status"].eq("T").astype(int)
    sums = training.groupby(["player_id", "position", "microcycle"], as_index=False).agg(
        train_hsr=("HSR", "sum"),
        train_td=("TD", "sum"),
        train_spr=("SPR", "sum"),
        train_acc=("ACC", "sum"),
        n_training_sessions=("md_day", "count"),
        starter_share=("is_starter", "mean"),
        last_session_date=("date", "max"),
    )
    sums = sums.sort_values(["player_id", "microcycle"]).reset_index(drop=True)
    sums["next_train_hsr"] = sums.groupby("player_id")["train_hsr"].shift(-1)
    sums["next_microcycle"] = sums.groupby("player_id")["microcycle"].shift(-1)
    sums["prior_hsr_mean3"] = sums.groupby("player_id")["train_hsr"].transform(
        lambda s: s.shift(1).rolling(3, min_periods=1).mean()
    )
    sums["microcycle_gap"] = sums["next_microcycle"] - sums["microcycle"]
    sums = sums.loc[sums["next_train_hsr"].notna()].copy()
    return sums
