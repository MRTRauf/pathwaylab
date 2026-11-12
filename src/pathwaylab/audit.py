"""Reproducible Phase 01 integrity, coverage and anomaly audit; no modelling."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from .data import LOAD_METRICS
from .quality import validate_sessions

RECORD = "https://zenodo.org/records/18986229"
CHECKSUMS = {
    "DataSetTMr.csv": "864bfbc3f78a736f60bba764de8d4f4d",
    "DataDictionary.xlsx": "10959d59ba0ad221a0b783d618d27d53",
}


def verify_original(path: Path, name: str = "DataSetTMr.csv") -> str:
    """Verify original bytes against the MD5 published by Zenodo (not a signature)."""
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    if digest != CHECKSUMS[name]:
        raise ValueError(f"Checksum mismatch for {path}: {digest} != {CHECKSUMS[name]}")
    return digest


def build_audit(frame: pd.DataFrame) -> dict:
    """Count retained observations; flag anomalies without deleting or repairing rows."""
    if set(frame.source) != {"zenodo_real"}:
        raise ValueError("Real audit requires only zenodo_real source labels")
    qa = validate_sessions(frame)
    cycles = sorted(map(int, frame.microcycle.unique()))
    coverage = []
    for player, group in frame.groupby("player_id", sort=True):
        observed = sorted(map(int, group.microcycle.unique()))
        coverage.append(
            {
                "player_id": player,
                "rows": len(group),
                "n_microcycles": len(observed),
                "observed": observed,
                "absent_observed_team_cycles": sorted(set(cycles) - set(observed)),
            }
        )
    ranges = []
    for cycle, group in frame.groupby("microcycle", sort=True):
        ranges.append(
            {
                "microcycle": int(cycle),
                "rows": len(group),
                "players": int(group.player_id.nunique()),
                "start": str(group.date.min().date()),
                "end": str(group.date.max().date()),
                "match_dates": sorted(
                    group.loc[group.md_day.eq(0), "date"].dt.strftime("%Y-%m-%d").unique()
                ),
            }
        )
    anomalies = {}
    for metric in LOAD_METRICS:
        values = frame[metric]
        q1, q3 = values.quantile([0.25, 0.75])
        anomalies[metric] = {
            "min": float(values.min()),
            "max": float(values.max()),
            "zero_rows": int(values.eq(0).sum()),
            "iqr_flag_rows": int(
                ((values < q1 - 1.5 * (q3 - q1)) | (values > q3 + 1.5 * (q3 - q1))).sum()
            ),
        }
    mappings = {}
    for left, right in [("ESTATUS", "ESTCat"), ("POS", "POSCat"), ("DIA", "DIACat")]:
        if right in frame:
            mappings[f"{left}/{right}"] = [
                dict(zip([left, right, "rows"], row))
                for row in frame.groupby([left, right], dropna=False)
                .size()
                .reset_index()
                .itertuples(index=False, name=None)
            ]
    return {
        **qa,
        "date_start": str(frame.date.min().date()),
        "date_end": str(frame.date.max().date()),
        "missingness": {c: int(n) for c, n in frame.isna().sum().items()},
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "status_frequencies": frame.status.value_counts().to_dict(),
        "position_frequencies": frame.position.value_counts().to_dict(),
        "day_frequencies": {
            str(k): int(v) for k, v in frame.md_day.value_counts().sort_index().items()
        },
        "unknown_status_rows": int((~frame.status.isin(["T", "S"])).sum()),
        "unknown_position_rows": int(
            (~frame.position.isin(["CEN", "LAT", "MED", "EXT", "DEL"])).sum()
        ),
        "unknown_day_rows": int((~frame.md_day.isin(range(-5, 3))).sum()),
        "positions_changing_players": int(
            frame.groupby("player_id").position.nunique().gt(1).sum()
        ),
        "match_dates": int(frame.loc[frame.md_day.eq(0), "date"].nunique()),
        "training_dates": int(frame.loc[frame.md_day.ne(0), "date"].nunique()),
        "missing_cycle_ids_in_range": sorted(
            set(range(min(cycles), max(cycles) + 1)) - set(cycles)
        ),
        "player_microcycles": coverage,
        "microcycle_ranges": ranges,
        "load_screen": anomalies,
        "observed_code_pairs": mappings,
        "distance_order_violations": int(
            (frame.HSR.gt(frame.TD) | frame.SPR.gt(frame.TD) | frame.HMLD.gt(frame.TD)).sum()
        ),
    }


def write_audit(frame: pd.DataFrame, raw: Path, dest: Path) -> dict:
    """Write machine-readable evidence and a sourced Markdown audit beside it."""
    checksum = verify_original(raw)
    dictionary = raw.with_name("DataDictionary.xlsx")
    dictionary_md5 = verify_original(dictionary, dictionary.name) if dictionary.exists() else None
    audit = build_audit(frame)
    audit["provenance"] = {
        "source": RECORD,
        "doi": "10.5281/zenodo.18986229",
        "csv_md5": checksum,
        "dictionary_md5": dictionary_md5,
        "verification_date": pd.Timestamp.now(tz="Europe/Paris").date().isoformat(),
    }
    dest.mkdir(parents=True, exist_ok=True)
    evidence = json.dumps(audit, indent=2, ensure_ascii=False, allow_nan=False)
    (dest / "results.json").write_text(evidence + "\n", encoding="utf-8")
    report = f"""# Real data ingestion audit — Phase 01

Source: [{RECORD}]({RECORD}); DOI 10.5281/zenodo.18986229, v1.
Record creator: Alejandro Rodríguez-Fernández. Verification/access date:
{audit["provenance"]["verification_date"]}. CSV MD5: `{checksum}`.
Dictionary MD5: `{dictionary_md5}` (null means unavailable).

Publication: Alejandro Sierra-Casas, Daniel Castillo, Filipe Manuel Clemente and
Alejandro Rodríguez-Fernández (2026), *Daily and Accumulated Training-to-Match Load
Ratios in Professional Soccer: The Influence of Starting Status and Playing Position
Across a Full Competitive Season*, Data 11(4), 84.
[Paper and methods](https://doi.org/10.3390/data11040084).
The paper states CC BY 4.0; the record Rights section has no explicit license text.
Raw files remain excluded from git pending redistribution review.

## Computed coverage

{audit["n_rows"]} player-session rows; {audit["n_players"]} players;
{audit["n_microcycles"]} distinct microcycle IDs; dates \
{audit["date_start"]} to {audit["date_end"]}.
Status frequencies: {audit["status_frequencies"]}.
Missing load cells: {audit["missing_load_cells"]}; exact duplicate rows:
{audit["exact_duplicate_rows"]}; additional rows on the same player/date:
{audit["duplicate_player_day"]}; negative-load rows: {audit["negative_load_rows"]}.
Unique observed dates: {audit["training_dates"]} training, {audit["match_dates"]} match.
Dates count observed coverage, not the number of distinct team sessions.

## Definitions and unresolved discrepancies

The checksummed dictionary has 20 short field descriptions. It omits FECHA,
units, thresholds, and category code mappings. Observed numeric/category pairs
below are empirical associations, not a dictionary-confirmed codebook.
The paper defines starter as starting the match and playing >60 minutes, and
non-starter as <35 minutes; T/S are interpreted as titular/suplente, with observed
ESTCat 1/0 respectively. The CSV has no minutes to independently verify this.
Position codes CEN/LAT/MED/EXT/DEL are retained verbatim; English translations
and category numbers are not independently established by the dictionary.
FECHA is parsed as Excel days from 1899-12-30; DIA 0 is treated as match day,
negative values as before and positive values as after, following the paper.

Paper-supported units: TD, HSR, SPR, HMLD in metres; ACC and DCC event counts.
Thresholds: HSR >19.8 km/h, SPR >25.2 km/h, HMLD >25.5 W/kg;
high-intensity acceleration/deceleration magnitude >3 m/s² (the paper's
deceleration sign wording is ambiguous). Acquisition: 10 Hz GPS and 100 Hz
accelerometry, STATSports; warm-ups included in training, excluded from matches.

The paper reports 30 microcycles and 144 training sessions. The original CSV
instead has {audit["n_microcycles"]} cycle IDs and {audit["training_dates"]} unique training dates.
The per-cycle ranges below expose overlapping intervals and sparse cycles;
these cannot be reconciled from the dictionary. Missing cycle IDs in the
observed integer range: {audit["missing_cycle_ids_in_range"]}.
Microcycle 21 contains only two rows: P07 on 2023-12-16 (DIA 0) and
2023-12-18 (DIA +2); the same match date also appears under microcycle 23.
Microcycles 18, 24, 27, 30, 36 and 39 each span two distinct DIA-0 dates.
These are observed discrepancies, not corrections or inferred session labels.
Absent player/cycle pairs and absent dates are coverage gaps, not confirmed missed
sessions: no attendance roster or exclusion reasons are supplied. The paper
excludes injury/return-to-play observations; no such labels can be inferred here.

IQR flags below use pooled Q1−1.5×IQR / Q3+1.5×IQR only as a screening rule,
not physiological limits. Zeros and extreme observations are retained.
No rows are deleted, deduplicated, imputed or recoded in this audit.
RATIO* uses full-season maximal match demand: retrospective only, excluded from
forecast features. No synthetic rows, cross-source identity joins, new descriptive
figures, forecasts, injury/readiness/development or causal findings are produced.
Resolve cycle/date discrepancies with the depositor before temporal modelling.

## Complete computed evidence

All counts below come from the checksummed CSV, via `pathwaylab.audit.build_audit`.
Player coverage includes each player's observed cycles and absent team cycles;
per-column missingness, code pairs, load screens and cycle date ranges follow.

```json
{evidence}
```
"""
    (dest / "REPORT.md").write_text(report, encoding="utf-8")
    return audit
