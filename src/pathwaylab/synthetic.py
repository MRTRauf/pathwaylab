"""Generate an explicitly fake teaching dataset; never present demo findings as sports evidence."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def generate_demo(seed: int = 42, players: int = 20, microcycles: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    positions = ["CB", "FB", "CM", "WM", "FW"]
    days = [-4, -3, -2, -1, 0, 1]
    factors = {-4: 0.68, -3: 0.83, -2: 0.53, -1: 0.30, 0: 1.30, 1: 0.25}
    records = []
    for player in range(1, players + 1):
        position = positions[(player - 1) % len(positions)]
        ability = rng.normal(1.0, 0.1)
        for micro in range(1, microcycles + 1):
            starter = bool(rng.uniform() < 0.65)
            for day in days:
                base = 4900 * ability * factors[day] * rng.lognormal(mean=0, sigma=0.13)
                if day == 0:
                    base *= 1.00 if starter else 0.23
                if day == 1:
                    base *= 0.65 if starter else 1.65
                hsr = max(0, base * (0.035 if position == "CB" else 0.065) * rng.uniform(0.7, 1.3))
                records.append(
                    {
                        "date": (
                            date(2025, 8, 1) + timedelta(days=7 * (micro - 1) + day + 4)
                        ).isoformat(),
                        "player_id": f"P{player:02d}",
                        "position": position,
                        "microcycle": micro,
                        "md_day": day,
                        "status": "T" if starter else "S",
                        "TD": round(base, 2),
                        "HSR": round(hsr, 2),
                        "SPR": round(hsr * rng.uniform(0.3, 0.65), 2),
                        "ACC": int(base / 70 * rng.uniform(0.7, 1.25)),
                        "DCC": int(base / 75 * rng.uniform(0.7, 1.25)),
                        "HMLD": round(base * rng.uniform(0.14, 0.24), 2),
                        "source": "SYNTHETIC",
                    }
                )
    return pd.DataFrame(records)


def write_demo(path: str | Path, seed: int = 42) -> Path:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    generate_demo(seed=seed).to_csv(dest, index=False)
    return dest
