"""Phase 04: actual-date, rolling one-step forecasts with strict past-only features."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .audit import verify_original
from .data import LOAD_METRICS, read_zenodo_csv
from .eda import analyze, read_dictionary

SOURCE = "REAL Zenodo 10.5281/zenodo.18986229 | next observed training HSR"
FEATURES = [f"lag_{m}" for m in LOAD_METRICS] + [
    "rolling_mean",
    "rolling_sd",
    "history_n",
    "gap_days",
    "weekday_sin",
    "weekday_cos",
]
CALENDAR = ["gap_days", "weekday_sin", "weekday_cos"]


def session_features(frame: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Create target-indexed history; current/future physical loads never enter X."""
    if window < 2:
        raise ValueError("History window must be >=2")
    if frame.empty or set(frame.source) != {"zenodo_real"}:
        raise ValueError("Nonempty real-only data required")
    if frame[["date", "player_id", "md_day"]].isna().any().any():
        raise ValueError("Missing temporal keys")
    if frame.duplicated(["player_id", "date"]).any():
        raise ValueError("Ambiguous duplicate player/date; no ordering invented")
    d = frame.loc[frame.md_day.ne(0)].sort_values(["player_id", "date"]).copy()
    if d[LOAD_METRICS].lt(0).any().any() or np.isinf(d[LOAD_METRICS]).any().any():
        raise ValueError("Invalid physical loads")
    g = d.groupby("player_id", sort=False)
    out = d[["player_id", "date", "position", "microcycle"]].copy()
    out["target_hsr"] = d.HSR
    out["history_date"] = g.date.shift(1)
    for metric in LOAD_METRICS:
        out[f"lag_{metric}"] = g[metric].shift(1)
    out["rolling_mean"] = g.HSR.transform(lambda s: s.shift().rolling(window, min_periods=1).mean())
    out["rolling_sd"] = g.HSR.transform(lambda s: s.shift().rolling(window, min_periods=2).std())
    out["history_n"] = g.cumcount()
    out["gap_days"] = (out.date - out.history_date).dt.days
    angle = 2 * np.pi * out.date.dt.dayofweek / 7
    out["weekday_sin"], out["weekday_cos"] = np.sin(angle), np.cos(angle)
    if (
        not out.loc[out.history_date.notna(), "history_date"]
        .lt(out.loc[out.history_date.notna(), "date"])
        .all()
    ):
        raise ValueError("History date must precede target date")
    return out.sort_values(["date", "player_id"]).reset_index(drop=True)


def temporal_folds(rows: pd.DataFrame) -> list[tuple[str, pd.DataFrame, pd.DataFrame]]:
    """Three expanding validations plus untouched final 20% of global target dates."""
    dates = np.sort(rows.date.unique())
    if len(dates) < 30:
        raise ValueError("Need >=30 target dates for this evaluation protocol")
    boundary = len(dates) - int(np.ceil(len(dates) * 0.2))
    dev = dates[:boundary]
    windows = np.array_split(dev[len(dev) // 2 :], 3)
    result = []
    for i, window in enumerate(windows, 1):
        train = rows.loc[rows.date.lt(window[0])].copy()
        valid = rows.loc[rows.date.isin(window)].copy()
        result.append((f"validation_{i}", train, valid))
    result.append(
        (
            "test",
            rows.loc[rows.date.lt(dates[boundary])].copy(),
            rows.loc[rows.date.ge(dates[boundary])].copy(),
        )
    )
    for _, train, valid in result:
        if train.date.max() >= valid.date.min():
            raise AssertionError("Target date overlap")
    return result


def baseline_predictions(train: pd.DataFrame, evaluation: pd.DataFrame) -> dict[str, np.ndarray]:
    """Historical baselines with training-label median cold-start fallback."""
    median = float(train.target_hsr.median())
    return {
        "global_median": np.full(len(evaluation), median),
        "last_hsr": evaluation.lag_HSR.fillna(median).to_numpy(),
        "rolling_mean": evaluation.rolling_mean.fillna(median).to_numpy(),
    }


def estimator(name: str, alpha: float = 10):
    """Fresh preprocessing/model instance for each temporal training fold."""
    if name == "ridge":
        return make_pipeline(
            SimpleImputer(strategy="median", keep_empty_features=True),
            StandardScaler(),
            Ridge(alpha=alpha),
        )
    if name != "tree":
        raise ValueError(name)
    return make_pipeline(
        SimpleImputer(strategy="median", keep_empty_features=True),
        HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_iter=100,
            max_leaf_nodes=7,
            min_samples_leaf=30,
            l2_regularization=10,
            early_stopping=False,
            random_state=42,
        ),
    )


def error_metrics(actual: np.ndarray, prediction: np.ndarray) -> dict:
    """All errors in original metres; signed bias is prediction minus observation."""
    actual, prediction = np.asarray(actual), np.asarray(prediction)
    if actual.shape != prediction.shape or not np.isfinite(prediction).all():
        raise ValueError("Invalid prediction shape or nonfinite predictions")
    error = prediction - actual
    return {
        "n": len(actual),
        "mae_m": float(np.abs(error).mean()),
        "rmse_m": float(np.sqrt(np.square(error).mean())),
        "median_ae_m": float(np.median(np.abs(error))),
        "bias_m": float(error.mean()),
    }


def feature_audit() -> pd.DataFrame:
    """Document allowed and rejected candidates, including prospective assumptions."""
    rows = []
    for feature in FEATURES:
        calendar = feature in CALENDAR
        rows.append(
            {
                "feature": feature,
                "source_variable": feature[4:]
                if feature.startswith("lag_")
                else "HSR/date/history",
                "calculation": "previous observation"
                if feature.startswith("lag_")
                else {
                    "rolling_mean": "shift(1) then rolling prior-3 mean",
                    "rolling_sd": "shift(1) then rolling prior-3 sample SD",
                    "history_n": "count preceding recorded training observations",
                    "gap_days": "target date minus previous observed date",
                    "weekday_sin": "sin(2*pi*target weekday/7)",
                    "weekday_cos": "cos(2*pi*target weekday/7)",
                }[feature],
                "availability": "before target, assuming its date is known"
                if calendar
                else "after previous calendar-date observations completed",
                "allowed": True,
                "risk": "date/scheduling known at origin assumed"
                if calendar
                else "requires prior results available by next date",
                "source": SOURCE,
            }
        )
    for feature in [
        "current_loads",
        "RATIO*",
        "season_player_mean/max",
        "status_T/S",
        "DIA/DIACat",
        "microcycle",
        "current_position",
        "future_gap",
    ]:
        rows.append(
            {
                "feature": feature,
                "source_variable": feature,
                "calculation": "not computed",
                "availability": "post-session or unverified",
                "allowed": False,
                "risk": "target/future leakage or unverified availability",
                "source": SOURCE,
            }
        )
    return pd.DataFrame(rows)


def run_temporal_forecast(raw: Path, dest: Path, report: Path | None = None) -> dict:
    """Select on development windows, then score a single frozen chronological holdout."""
    csv_md5 = verify_original(raw)
    dictionary = read_dictionary(raw.with_name("DataDictionary.xlsx"))
    frame = read_zenodo_csv(raw)
    _, audit = analyze(frame)
    features = session_features(frame)
    rows = features.loc[features.history_n.ge(1) & features.target_hsr.notna()].copy()
    folds = temporal_folds(rows)
    dest.mkdir(parents=True, exist_ok=True)
    feature_audit().to_csv(dest / "feature_availability.csv", index=False)
    features.assign(source=SOURCE).to_csv(dest / "historical_features.csv", index=False)
    manifest = []
    assignments = []
    for fold, train, valid in folds:
        for role, subset in [("train", train), ("evaluation", valid)]:
            manifest.append(
                {
                    "fold": fold,
                    "role": role,
                    "start": str(subset.date.min().date()),
                    "end": str(subset.date.max().date()),
                    "n": len(subset),
                    "players": subset.player_id.nunique(),
                    "dates": subset.date.nunique(),
                    "cycle_ids_annotation_only": subset.microcycle.nunique(),
                    "source": SOURCE,
                }
            )
            assignments.append(subset[["player_id", "date"]].assign(fold=fold, role=role))
    pd.DataFrame(manifest).to_csv(dest / "split_manifest.csv", index=False)
    pd.concat(assignments).to_csv(dest / "split_assignments.csv", index=False)
    validation_predictions = []

    def evaluate(
        fold: str,
        train: pd.DataFrame,
        valid: pd.DataFrame,
        alpha: float,
        columns: list[str] = FEATURES,
    ) -> pd.DataFrame:
        predictions = baseline_predictions(train, valid)
        for name in ["ridge", "tree"]:
            model = estimator(name, alpha)
            model.fit(train[columns], train.target_hsr)
            predictions[name] = np.maximum(0, model.predict(valid[columns]))
        records = []
        for name, pred in predictions.items():
            if not np.isfinite(pred).all():
                raise ValueError("Nonfinite predictions")
            records.append(
                valid[
                    [
                        "player_id",
                        "date",
                        "position",
                        "microcycle",
                        "history_n",
                        "lag_HSR",
                        "target_hsr",
                    ]
                ].assign(fold=fold, model=name, prediction_m=pred, source=SOURCE)
            )
        return pd.concat(records, ignore_index=True)

    # Small Ridge grid scored only on development labels. Tree configuration is fixed.
    tuning = []
    for alpha in [1.0, 10.0, 100.0]:
        candidate = []
        for fold, train, valid in folds[:-1]:
            model = estimator("ridge", alpha)
            model.fit(train[FEATURES], train.target_hsr)
            pred = np.maximum(0, model.predict(valid[FEATURES]))
            candidate.append(pd.DataFrame({"actual": valid.target_hsr, "pred": pred}))
        pooled = pd.concat(candidate)
        tuning.append(
            {"alpha": alpha, **error_metrics(pooled.actual, pooled.pred), "source": SOURCE}
        )
    tuning_table = pd.DataFrame(tuning)
    alpha = float(tuning_table.sort_values(["mae_m", "alpha"]).iloc[0].alpha)
    tuning_table.to_csv(dest / "ridge_tuning.csv", index=False)
    for fold, train, valid in folds[:-1]:
        validation_predictions.append(evaluate(fold, train, valid, alpha))
    development = pd.concat(validation_predictions, ignore_index=True)
    selection = {
        name: error_metrics(g.target_hsr, g.prediction_m)["mae_m"]
        for name, g in development.loc[development.model.isin(["ridge", "tree"])].groupby("model")
    }
    chosen = min(selection, key=selection.get)
    # This decision is written before test prediction or scoring.
    (dest / "selection.json").write_text(
        json.dumps(
            {"alpha": alpha, "chosen_ml": chosen, "validation_mae_m": selection, "seed": 42},
            indent=2,
        ),
        encoding="utf-8",
    )
    test_name, test_train, test = folds[-1]
    holdout = evaluate(test_name, test_train, test, alpha)
    predictions = pd.concat([development, holdout], ignore_index=True)
    predictions["error_m"] = predictions.prediction_m - predictions.target_hsr
    predictions.to_csv(dest / "predictions.csv", index=False)
    scores = []
    for (fold, name), g in predictions.groupby(["fold", "model"]):
        scores.append(
            {
                "fold": fold,
                "model": name,
                **error_metrics(g.target_hsr, g.prediction_m),
                "players": g.player_id.nunique(),
                "dates": g.date.nunique(),
                "source": SOURCE,
            }
        )
    score_table = pd.DataFrame(scores)
    score_table.to_csv(dest / "scores.csv", index=False)
    test_scores = score_table.loc[score_table.fold.eq("test")].set_index("model")
    comparisons = []
    for ml in ["ridge", "tree"]:
        for base in ["global_median", "last_hsr", "rolling_mean"]:
            difference = test_scores.loc[base, "mae_m"] - test_scores.loc[ml, "mae_m"]
            comparisons.append(
                {
                    "model": ml,
                    "baseline": base,
                    "mae_improvement_m": difference,
                    "relative_improvement_percent": 100
                    * difference
                    / test_scores.loc[base, "mae_m"],
                    "source": SOURCE,
                }
            )
    pd.DataFrame(comparisons).to_csv(dest / "test_comparisons.csv", index=False)
    sensitivities = []
    features7 = session_features(frame, window=7).set_index(["player_id", "date"])
    for fold, train, valid in folds[:-1]:
        threshold = train.target_hsr.quantile(0.99)
        for variant in ["history7", "history_ge3", "nonextreme", "calendar_free"]:
            tr, va, cols = train.copy(), valid.copy(), FEATURES
            if variant == "history7":
                for target in [tr, va]:
                    aligned = features7.reindex(
                        pd.MultiIndex.from_frame(target[["player_id", "date"]])
                    )
                    target[["rolling_mean", "rolling_sd"]] = aligned[
                        ["rolling_mean", "rolling_sd"]
                    ].to_numpy()
            elif variant == "history_ge3":
                va = va.loc[va.history_n.ge(3)]
            elif variant == "nonextreme":
                va = va.loc[va.target_hsr.le(threshold)]
            else:
                cols = [c for c in FEATURES if c not in CALENDAR]
            # Frozen main settings; variants never select hyperparameters or use test scores.
            model = estimator(chosen, alpha)
            model.fit(tr[cols], tr.target_hsr)
            pred = np.maximum(0, model.predict(va[cols]))
            sensitivities.append(
                {
                    "variant": variant,
                    "fold": fold,
                    "model": chosen,
                    "threshold_m": float(threshold) if variant == "nonextreme" else None,
                    **error_metrics(va.target_hsr, pred),
                    "source": SOURCE,
                }
            )
    pd.DataFrame(sensitivities).to_csv(dest / "validation_sensitivities.csv", index=False)
    metadata = {
        "source": SOURCE,
        "csv_md5": csv_md5,
        "dictionary_md5": verify_original(
            raw.with_name("DataDictionary.xlsx"), "DataDictionary.xlsx"
        ),
        "dictionary": dictionary,
        "audit": audit,
        "features": FEATURES,
        "alpha": alpha,
        "chosen_ml": chosen,
        "random_seed": 42,
        "primary_rows": len(rows),
        "first_observations_excluded": int(features.history_n.eq(0).sum()),
        "missing_targets_excluded": int(
            features.loc[features.history_n.ge(1)].target_hsr.isna().sum()
        ),
        "feature_policy": "strictly earlier calendar date; rolling one-step history updates",
        "tree_settings": estimator("tree").steps[-1][1].get_params(),
        "versions": {
            p: importlib.metadata.version(p)
            for p in ["numpy", "pandas", "scikit-learn", "matplotlib"]
        },
    }
    (dest / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    from .forecast_output import export_forecast

    export_forecast(dest, predictions, score_table, metadata, report)
    verify_original(raw)
    checksums = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in dest.iterdir()
        if p.is_file() and p.name != "manifest.json"
    }
    (dest / "manifest.json").write_text(json.dumps(checksums, indent=2), encoding="utf-8")
    print(
        f"[forecast] {len(rows)} targets; {len(test)} test observations; chosen ML={chosen}; "
        f"alpha={alpha}; original checksum unchanged"
    )
    return metadata
