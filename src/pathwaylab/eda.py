"""Phase 02 descriptive tables. No imputation, inference, ratios or forecasting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pandas as pd

from .audit import RECORD, build_audit, verify_original
from .data import LOAD_METRICS, read_zenodo_csv

SOURCE = "Zenodo 10.5281/zenodo.18986229 | REAL DATA | descriptive only"
UNITS = {m: "count" if m in {"ACC", "DCC"} else "m" for m in LOAD_METRICS}
NAMES = {
    "TD": "Total distance",
    "HSR": "High-speed running distance",
    "SPR": "Sprint distance",
    "ACC": "Accelerations",
    "DCC": "Decelerations",
    "HMLD": "High metabolic load distance",
}


def summarize(frame: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    """Row-weighted metric summaries; report nonmissing denominators separately."""
    records = []
    iterator = (
        frame.groupby(groups, observed=True, dropna=False, sort=True) if groups else [((), frame)]
    )
    for key, group in iterator:
        key = key if isinstance(key, tuple) else (key,)
        for metric in LOAD_METRICS:
            values = group[metric].dropna()
            records.append(
                {
                    **dict(zip(groups, key)),
                    "metric": metric,
                    "unit": UNITS[metric],
                    "n_rows": len(group),
                    "n_group_players": group.player_id.nunique(),
                    "n_group_dates": group.date.nunique(),
                    "n_players": group.loc[values.index].player_id.nunique(),
                    "n_dates": group.loc[values.index].date.nunique(),
                    "n_valid": len(values),
                    "n_missing": int(group[metric].isna().sum()),
                    "mean": values.mean(),
                    "sd": values.std(ddof=1),
                    "median": values.median(),
                    "q1": values.quantile(0.25),
                    "q3": values.quantile(0.75),
                    "min": values.min(),
                    "max": values.max(),
                    "source": SOURCE,
                }
            )
    return pd.DataFrame(records)


def variability(frame: pd.DataFrame) -> pd.DataFrame:
    """Raw within-player pooled SD and equal-player SD of means; not adjusted ICC."""
    records = []
    for metric in LOAD_METRICS:
        valid = frame.loc[frame[metric].notna()]
        means = valid.groupby("player_id")[metric].mean()
        counts = valid.groupby("player_id")[metric].size()
        residual = valid[metric] - valid.groupby("player_id")[metric].transform("mean")
        within_ss = float(residual.pow(2).sum())
        between_ss = float((counts * (means - valid[metric].mean()).pow(2)).sum())
        denominator = len(valid) - len(means)
        total_ss = within_ss + between_ss
        records.append(
            {
                "metric": metric,
                "unit": UNITS[metric],
                "n_valid": len(valid),
                "n_players": len(means),
                "within_df": denominator,
                "pooled_within_sd": np.sqrt(within_ss / denominator) if denominator else np.nan,
                "between_player_mean_sd": means.std(ddof=1),
                "total_sd": valid[metric].std(ddof=1),
                "within_ss": within_ss,
                "between_ss": between_ss,
                "between_ss_fraction": between_ss / total_ss if total_ss else np.nan,
                "source": SOURCE,
            }
        )
    return pd.DataFrame(records)


def analyze(frame: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], dict]:
    """Build explicit training/match strata, coverage and actual-calendar diagnostics."""
    if frame.empty or set(frame.source) != {"zenodo_real"}:
        raise ValueError("EDA requires nonempty real-only source labels")
    data = frame.sort_values(["player_id", "date", "microcycle"]).copy()
    data["scope"] = np.where(data.md_day.eq(0), "match", "training")
    data["month"] = data.date.dt.strftime("%Y-%m")
    training = data.loc[data.scope.eq("training")]
    audit = build_audit(data)
    if (
        audit["negative_load_rows"]
        or audit["unknown_status_rows"]
        or audit["unknown_position_rows"]
        or audit["unknown_day_rows"]
    ):
        raise ValueError("Unexpected values/codes; review ingestion audit before EDA")
    all_summary = summarize(data, [])
    all_summary.insert(0, "scope", "all")
    tables = {
        "overall": pd.concat([all_summary, summarize(data, ["scope"])], ignore_index=True),
        "day_status": summarize(data, ["md_day", "status"]),
        "position": summarize(data, ["scope", "position"]),
        "position_day_status": summarize(data, ["position", "md_day", "status"]),
        "status": summarize(data, ["scope", "status"]),
        "player": summarize(training, ["player_id", "position"]),
        "variability": variability(training),
        "monthly_day_status": summarize(training, ["month", "md_day", "status"]),
        "monthly": summarize(training, ["month"]),
        "missingness": pd.DataFrame(
            {
                "column": data.columns,
                "n_missing": data.isna().sum().values,
                "n_rows": len(data),
                "source": SOURCE,
            }
        ),
    }
    status = data.groupby(["player_id", "microcycle"]).agg(
        n_rows=("status", "size"),
        n_statuses=("status", "nunique"),
        status_codes=("status", lambda x: "/".join(sorted(x.unique()))),
        first_date=("date", "min"),
        last_date=("date", "max"),
    )
    tables["player_cycles"] = status.reset_index().assign(source=SOURCE)
    coverage = data.groupby("player_id").agg(
        n_rows=("date", "size"),
        n_dates=("date", "nunique"),
        n_cycles=("microcycle", "nunique"),
        start=("date", "min"),
        end=("date", "max"),
    )
    coverage["training_rows"] = (
        training.groupby("player_id").size().reindex(coverage.index, fill_value=0)
    )
    tables["coverage"] = coverage.reset_index().assign(source=SOURCE)
    gaps = data[["player_id", "date"]].drop_duplicates().sort_values(["player_id", "date"])
    gaps["previous_date"] = gaps.groupby("player_id").date.shift()
    gaps["gap_days"] = (gaps.date - gaps.previous_date).dt.days
    tables["date_gaps"] = gaps.loc[gaps.gap_days.gt(1)].assign(source=SOURCE)
    cycle_ranges = status.reset_index().sort_values(["player_id", "microcycle"])
    cycle_ranges["previous_cycle"] = cycle_ranges.groupby("player_id").microcycle.shift()
    cycle_ranges["previous_end"] = cycle_ranges.groupby("player_id").last_date.shift()
    tables["cycle_overlaps"] = cycle_ranges.loc[
        cycle_ranges.first_date.le(cycle_ranges.previous_end)
    ].assign(source=SOURCE)
    correlations = []
    for left in LOAD_METRICS:
        for right in LOAD_METRICS:
            pair = training[[left, right]] if left != right else training[[left]]
            pair = pair.dropna()
            correlations.append(
                {
                    "metric_x": left,
                    "metric_y": right,
                    "n_pairs": len(pair),
                    "n_players": training.loc[pair.index].player_id.nunique(),
                    "pearson_r": pair[left].corr(pair[right]),
                    "source": SOURCE,
                }
            )
    tables["correlations"] = pd.DataFrame(correlations)
    audit["n_training_rows"] = len(training)
    audit["n_match_rows"] = int(data.scope.eq("match").sum())
    audit["player_cycles_total"] = len(status)
    audit["player_cycles_multiple_statuses"] = int(status.n_statuses.gt(1).sum())
    audit["adjacent_player_cycle_overlaps"] = len(tables["cycle_overlaps"])
    audit["adjacent_player_cycle_pairs"] = int(cycle_ranges.previous_cycle.notna().sum())
    audit["player_date_gaps_gt1"] = len(tables["date_gaps"])
    audit["player_date_intervals"] = int(gaps.previous_date.notna().sum())
    audit["max_player_date_gap_days"] = int(gaps.gap_days.max())
    return tables, audit


def read_dictionary(path: Path) -> dict[str, str]:
    """Read source XLSX descriptions with standard-library XML, preserving wording."""
    verify_original(path, "DataDictionary.xlsx")
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with ZipFile(path) as workbook:
        strings = [
            "".join(item.itertext())
            for item in ET.fromstring(workbook.read("xl/sharedStrings.xml")).findall("s:si", ns)
        ]
        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        rows = [
            [strings[int(cell.find("s:v", ns).text)] for cell in row if cell.get("t") == "s"]
            for row in sheet.findall(".//s:row", ns)
        ]
    return {row[0]: row[1] for row in rows if len(row) == 2}


def markdown_table(table: pd.DataFrame, columns: list[str]) -> str:
    """Render tables without an optional tabulate dependency."""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in table[columns].itertuples(index=False, name=None):
        cells = [f"{v:.2f}" if isinstance(v, (float, np.floating)) else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def run_eda(raw: Path, dest: Path, report_path: Path | None = None) -> dict:
    """Verify original files, write tables/figures/report, and recheck original bytes."""
    csv_md5 = verify_original(raw)
    dictionary = raw.with_name("DataDictionary.xlsx")
    descriptions = read_dictionary(dictionary)
    tables, audit = analyze(read_zenodo_csv(raw))
    dest.mkdir(parents=True, exist_ok=True)
    table_dir = dest / "tables"
    table_dir.mkdir(exist_ok=True)
    for name, table in tables.items():
        table.to_csv(table_dir / f"{name}.csv", index=False)
    metadata = {
        "source": RECORD,
        "doi": "10.5281/zenodo.18986229",
        "verification_date": pd.Timestamp.now(tz="Europe/Paris").date().isoformat(),
        "csv_md5": csv_md5,
        "dictionary_md5": verify_original(dictionary, dictionary.name),
        "dictionary_descriptions": descriptions,
        "units": UNITS,
        "units_source": "https://doi.org/10.3390/data11040084 (not specified in dictionary)",
        "excluded_ratio_columns": [
            c
            for c in pd.read_csv(raw, sep=";", nrows=0, encoding="utf-8-sig").columns
            if c.startswith("RATIO")
        ],
        "audit": audit,
    }
    from .eda_plots import export_eda_figures
    from .eda_report import findings_report

    figures = export_eda_figures(read_zenodo_csv(raw), tables, dest / "figures")
    metadata["figures"] = figures
    # Explicit metadata accompanies every machine-readable table and figure.
    (dest / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )
    report = findings_report(tables, metadata, dest, dest / "REPORT.md")
    (dest / "REPORT.md").write_text(report, encoding="utf-8")
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            findings_report(tables, metadata, dest, report_path), encoding="utf-8"
        )
    verify_original(raw)
    expected = [table_dir / f"{name}.csv" for name in tables]
    expected += [dest / "figures" / f["file"] for f in figures]
    if not all(path.is_file() and path.stat().st_size > 0 for path in expected):
        raise RuntimeError("Missing or empty EDA outputs")
    manifest = {
        str(path.relative_to(dest)).replace("\\", "/"): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in [*expected, dest / "metadata.json", dest / "REPORT.md"]
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"[eda] CHECKSUM OK; {audit['n_rows']} rows; {audit['n_players']} players; "
        f"{len(tables)} tables; {len(figures)} figures. No inference or forecasts."
    )
    print(f"Outputs: {dest.resolve()}")
    return metadata
