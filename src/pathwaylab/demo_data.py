"""Independent fictional demonstration cohorts; no research files are read here."""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from .model import chronological_split, run_forecast
from .quality import make_microcycle_features
from .synthetic import generate_demo

SEED = 42
LABEL = "SYNTHETIC - DEMONSTRATION ONLY"
PUBLIC_LABEL = "SYNTHETIC DEMONSTRATION - NOT REAL PLAYER DATA"
LOAD_SOURCE = f"{LABEL} | independent load generator | seed {SEED}"
EVENT_SOURCE = f"{LABEL} | independent event fixture | seed {SEED + 1}"


def load_cohort(seed: int = SEED) -> pd.DataFrame:
    """Reuse the tested toy generator with clearly fictional display identities."""
    frame = generate_demo(seed=seed).copy()
    frame["date"] = pd.to_datetime(frame.date)
    frame["player_id"] = frame.player_id.str.replace("P", "DEMO-", regex=False)
    return frame


def demo_forecast(loads: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Compute the existing demo's next-observed-block benchmark, not real MAEs.

    A block is a synthetic microcycle's cumulative non-match HSR. All players
    share target-block cutoffs. The separate real study predicts one session.
    """
    blocks = make_microcycle_features(loads)
    train, test = chronological_split(blocks)
    protocol, predictions = run_forecast(blocks)
    values = {
        "Ridge": predictions.ridge_prediction.to_numpy(),
        "Last block": predictions.persistence_prediction.to_numpy(),
        "Training median": np.full(len(test), train.next_train_hsr.median()),
    }
    rows, panels = [], []
    for name, prediction in values.items():
        errors = prediction - predictions.next_train_hsr.to_numpy()
        rows.append(
            {
                "Model": name,
                "MAE (m)": float(np.abs(errors).mean()),
                "RMSE (m)": float(np.sqrt((errors**2).mean())),
                "Targets": len(errors),
            }
        )
        panels.append(predictions.assign(model=name, prediction_m=prediction, error_m=errors))
    return pd.DataFrame(rows), pd.concat(panels, ignore_index=True), protocol


def event_cohort(seed: int = SEED + 1) -> pd.DataFrame:
    """Simulate counts/exposure for a separate, entirely fictional event cohort."""
    rng = np.random.default_rng(seed)
    positions = ["Defence", "Midfield", "Attack"]
    records = []
    for sn, season in enumerate(["Demo season A", "Demo season B"]):
        for fixture in range(15):
            for player in range(1, 15):
                if rng.uniform() < 0.12:
                    continue
                minutes = int(rng.choice([35, 60, 75, 90], p=[0.12, 0.18, 0.25, 0.45]))
                role = positions[(player - 1) % len(positions)]
                base = {"Defence": 45, "Midfield": 57, "Attack": 29}[role]
                factor = 1 + 0.12 * np.sin(fixture / 3 + player) + 0.03 * sn
                passes = int(rng.poisson(base * minutes / 90 * factor))
                records.append(
                    {
                        "player_id": f"EVENT-{player:02d}",
                        "position": role,
                        "season": season,
                        "match_id": sn * 100 + fixture,
                        "date": date(2024 + sn, 8, 15) + timedelta(days=fixture * 7),
                        "minutes": minutes,
                        "passes": passes,
                        "completed_passes": int(rng.binomial(passes, 0.82)),
                        "shots": int(
                            rng.poisson((2.5 if role == "Attack" else 0.8) * minutes / 90)
                        ),
                        "carries": int(rng.poisson(14 * minutes / 90)),
                        "tackles": int(rng.poisson(2.3 * minutes / 90)),
                        "interceptions": int(rng.poisson(1.4 * minutes / 90)),
                        "source": LABEL,
                    }
                )
    frame = pd.DataFrame(records).sort_values(["player_id", "date"]).reset_index(drop=True)
    frame["date"] = pd.to_datetime(frame.date)
    for metric in ["passes", "completed_passes", "shots", "carries", "tackles", "interceptions"]:
        frame[metric + "_per90"] = 90 * frame[metric] / frame.minutes
    grouped = frame.groupby("player_id")
    numerator = grouped.passes.transform(lambda s: s.shift().rolling(5, min_periods=3).sum())
    denominator = grouped.minutes.transform(lambda s: s.shift().rolling(5, min_periods=3).sum())
    frame["prior_passes_per90"] = 90 * numerator / denominator
    return frame
