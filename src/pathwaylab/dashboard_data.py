"""Read-only artifact verification for the local research dashboard; never fit models."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .audit import verify_original
from .data import read_zenodo_csv
from .forecasting import error_metrics

ROOT = Path(__file__).resolve().parents[2]
SOURCE = "REAL DATA | Zenodo DOI 10.5281/zenodo.18986229"
CAUTION = (
    "Retrospective exploratory research; repeated observations, not "
    "independent players. No injury, readiness, fatigue or development "
    "labels. No club affiliation."
)
SETUP = (
    "Run source download, --mode eda, scripts/run_inference.py and --mode "
    "forecast from the project root. No synthetic fallback is used."
)


def revision(root: Path) -> tuple:
    """Invalidate cache when inputs change or disappear."""
    paths = []
    for name in ["data/raw", "outputs/eda", "outputs/inference", "outputs/forecast"]:
        paths.extend(p for p in (root / name).rglob("*") if p.is_file())
    return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in sorted(paths))


def required(frame: pd.DataFrame, columns: set[str]) -> None:
    if not columns.issubset(frame):
        raise ValueError(f"Artifact schema missing {sorted(columns - set(frame))}")


def load_research(root: Path = ROOT) -> dict:
    """Verify source bytes, artifact hashes, paired targets and original-unit scores."""
    try:
        digest = verify_original(root / "data/raw/DataSetTMr.csv")
        verify_original(root / "data/raw/DataDictionary.xlsx", "DataDictionary.xlsx")
        for phase in ["eda", "inference", "forecast"]:
            directory = root / "outputs" / phase
            manifest = json.loads((directory / "manifest.json").read_text())
            for name, checksum in manifest.items():
                path = (directory / name).resolve()
                if not path.is_relative_to(directory.resolve()):
                    raise ValueError("Unsafe manifest path")
                if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
                    raise ValueError(f"Artifact hash mismatch: {phase}/{name}")
        directory = root / "outputs/forecast"
        meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        if meta.get("csv_md5") != digest or not meta.get("source", "").startswith("REAL Zenodo"):
            raise ValueError("Real-data provenance mismatch")
        data = read_zenodo_csv(root / "data/raw/DataSetTMr.csv")
        p = pd.read_csv(directory / "predictions.csv", parse_dates=["date"])
        scores = pd.read_csv(directory / "scores.csv")
        required(p, {"fold", "model", "player_id", "date", "target_hsr", "prediction_m", "source"})
        required(scores, {"fold", "model", "mae_m", "rmse_m", "n", "bias_m", "median_ae_m"})
        if not p.source.str.startswith("REAL Zenodo").all():
            raise ValueError("Synthetic or unknown prediction source")
        truth = data.loc[data.md_day.ne(0), ["player_id", "date", "HSR"]]
        for fold, cohort in p.groupby("fold"):
            targets = []
            for name, g in cohort.groupby("model"):
                if g.duplicated(["player_id", "date"]).any():
                    raise ValueError("Duplicate predictions")
                joined = g.merge(
                    truth, on=["player_id", "date"], how="left", validate="many_to_one"
                )
                if not np.allclose(joined.target_hsr, joined.HSR):
                    raise ValueError("Prediction target mismatch")
                if g.prediction_m.lt(0).any():
                    raise ValueError("Negative predictions")
                targets.append(set(zip(g.player_id, g.date)))
                saved = scores.loc[scores.fold.eq(fold) & scores.model.eq(name)]
                if len(saved) != 1:
                    raise ValueError("Missing/duplicate saved model scores")
                for metric, actual in error_metrics(g.target_hsr, g.prediction_m).items():
                    if not np.isclose(saved.iloc[0][metric], actual, rtol=1e-9, atol=1e-8):
                        raise ValueError(f"Saved score mismatch: {name}/{metric}")
            if len(targets) != 5 or any(t != targets[0] for t in targets):
                raise ValueError("Models have mismatched evaluation targets")
        return dict(
            data=data,
            predictions=p,
            scores=scores,
            metadata=meta,
            splits=pd.read_csv(directory / "split_manifest.csv"),
            models=pd.read_csv(root / "outputs/inference/models.csv"),
            availability=pd.read_csv(directory / "feature_availability.csv"),
        )
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Research artifacts unavailable/invalid: {exc}. {SETUP}") from exc


def filter_training(
    data: pd.DataFrame, players: list, positions: list, start, end, days: list
) -> pd.DataFrame:
    """Filter observations, never saved model scores."""
    return data.loc[
        data.md_day.ne(0)
        & data.player_id.isin(players)
        & data.position.isin(positions)
        & data.date.between(pd.Timestamp(start), pd.Timestamp(end))
        & data.md_day.isin(days)
    ].copy()
