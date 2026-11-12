"""Load either synthetic demonstration data or the public Zenodo soccer GPS dataset.

Real Zenodo schema observed at DOI 10.5281/zenodo.18986229:
FECHA;PlayerID;POS;POSCat;MICRO;DIA;DIACat;ESTATUS;ESTCat;TD;HSR;SPR;ACC;DCC;HMLD;RATIO...
FECHA is an Excel serial day. Comma decimals; semicolon separator.
RATIO* use maximum match demand over the ENTIRE season and are excluded from predictive features.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED = {
    "FECHA",
    "PlayerID",
    "POS",
    "MICRO",
    "DIA",
    "ESTATUS",
    "TD",
    "HSR",
    "SPR",
    "ACC",
    "DCC",
    "HMLD",
}
LOAD_METRICS = ["TD", "HSR", "SPR", "ACC", "DCC", "HMLD"]


def read_zenodo_csv(path: str | Path) -> pd.DataFrame:
    """Strict adapter for the REAL original CSV. Do not mix synthetic data into this file."""
    frame = pd.read_csv(
        path, sep=";", decimal=",", encoding="utf-8-sig", na_values=["NA", "N/A", ""]
    )
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(
            f"Missing Zenodo columns: {sorted(missing)}. Check separator and encoding."
        )
    frame = frame.copy()
    for col in [
        "FECHA",
        "PlayerID",
        "MICRO",
        "DIA",
        *LOAD_METRICS,
        *[c for c in frame if c.startswith("RATIO")],
    ]:
        original = frame[col]
        frame[col] = pd.to_numeric(original, errors="coerce")
        if (original.notna() & frame[col].isna()).any() or np.isinf(frame[col]).any():
            raise ValueError(f"Malformed numeric values in {col}")
    if frame[["FECHA", "PlayerID", "MICRO", "DIA"]].isna().any().any():
        raise ValueError("Missing or malformed key identifiers/date/microcycle/day")
    for col in ["FECHA", "PlayerID", "MICRO", "DIA"]:
        if frame[col].mod(1).ne(0).any():
            raise ValueError(f"Expected integer values in {col}")
    if frame[["POS", "ESTATUS"]].isna().any().any():
        raise ValueError("Missing position/status codes")
    frame["date"] = pd.to_datetime(frame["FECHA"], unit="D", origin="1899-12-30")
    frame["player_id"] = "P" + frame["PlayerID"].astype(int).astype(str).str.zfill(2)
    frame["position"] = frame["POS"].astype(str).str.strip()
    frame["microcycle"] = frame["MICRO"].astype(int)
    frame["md_day"] = frame["DIA"].astype(int)
    frame["status"] = frame["ESTATUS"].astype(str).str.strip()
    frame["source"] = "zenodo_real"
    return frame.sort_values(["player_id", "date", "microcycle", "md_day"]).reset_index(drop=True)


def read_synthetic_csv(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["date"])
    missing = {
        "player_id",
        "position",
        "microcycle",
        "md_day",
        "status",
        "source",
        *LOAD_METRICS,
    } - set(frame.columns)
    if missing:
        raise ValueError(f"Synthetic file missing: {sorted(missing)}")
    if set(frame["source"].unique()) != {"SYNTHETIC"}:
        raise ValueError("Synthetic adapter requires every row marked SYNTHETIC")
    return frame.sort_values(["player_id", "date"]).reset_index(drop=True)
