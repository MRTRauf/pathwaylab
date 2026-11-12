"""Exploratory Phase 03 random-intercept analysis; see the written analysis plan."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from .audit import verify_original
from .data import read_zenodo_csv
from .eda import analyze, read_dictionary

SOURCE = "REAL Zenodo 10.5281/zenodo.18986229 | retrospective exploratory analysis"
DAY = "C(md_day, Treatment(reference=-1))"


def training_sample(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Exclude DIA 0 and report complete-case selection; never infer status meanings."""
    if frame.empty or set(frame.source) != {"zenodo_real"}:
        raise ValueError("Real-only observations required")
    if frame.duplicated(["player_id", "date"]).any():
        raise ValueError("Duplicate player/date requires source review")
    training = frame.loc[frame.md_day.ne(0)].copy()
    if training.HSR.lt(0).any() or np.isinf(training.HSR).any():
        raise ValueError("Negative/nonfinite HSR")
    selected = training.dropna(subset=["HSR", "player_id", "date", "md_day", "position"])
    # Whitelist eliminates ratios and status from the modelling frame.
    selected = selected[["player_id", "date", "microcycle", "md_day", "position", "HSR"]]
    selected = selected.sort_values(["player_id", "date"]).reset_index(drop=True)
    selected["y"] = np.log1p(selected.HSR)
    return selected, {
        "total_rows": len(frame),
        "excluded_dia0": int(frame.md_day.eq(0).sum()),
        "training_before_complete_case": len(training),
        "excluded_missing": len(training) - len(selected),
        "n": len(selected),
        "players": selected.player_id.nunique(),
        "zero_hsr": int(selected.HSR.eq(0).sum()),
    }


def fit_intercept(
    data: pd.DataFrame, formula: str, name: str, source: str = SOURCE
) -> tuple[Any, dict, list[dict]]:
    """Fit REML with explicit attempts; failed attempts and warnings are retained."""
    import statsmodels.formula.api as smf

    attempts = []
    result = None
    for method in ["powell", "bfgs"]:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                model = smf.mixedlm(formula, data, groups=data.player_id, missing="raise")
                rank = int(np.linalg.matrix_rank(model.exog))
                if rank != model.exog.shape[1]:
                    raise ValueError("Nonidentifiable fixed-effect design")
                candidate = model.fit(reml=True, method=method, maxiter=1000, disp=False)
                attempt = {
                    "model": name,
                    "optimizer": method,
                    "converged": bool(candidate.converged),
                    "exception": None,
                }
                result = candidate
            except Exception as exc:
                attempt = {
                    "model": name,
                    "optimizer": method,
                    "converged": False,
                    "exception": f"{type(exc).__name__}: {exc}",
                }
            attempt["warnings"] = [f"{type(w.message).__name__}: {w.message}" for w in caught]
            attempts.append(attempt)
        if attempt["converged"] and np.isfinite(result.llf):
            break
    summary = {
        "model": name,
        "formula": formula,
        "n": len(data),
        "players": data.player_id.nunique(),
        "source": source,
        "converged": False,
        "icc": np.nan,
        "between_variance": np.nan,
        "residual_variance": np.nan,
        "boundary": True,
        "ci_usable": False,
    }
    if result is not None:
        between = float(result.cov_re.iloc[0, 0])
        residual = float(result.scale)
        icc = between / (between + residual)
        messages = " ".join(w for a in attempts for w in a["warnings"])
        summary.update(
            converged=bool(result.converged),
            icc=icc,
            between_variance=between,
            residual_variance=residual,
            boundary=icc < 1e-6,
            log_likelihood=float(result.llf),
            design_rank=int(np.linalg.matrix_rank(result.model.exog)),
            ci_usable=bool(
                result.converged
                and icc >= 1e-6
                and np.isfinite(result.bse_fe).all()
                and "Hessian" not in messages
            ),
        )
    return result, summary, attempts


def coefficients(result: Any, summary: dict) -> list[dict]:
    """Approximate model-based Wald intervals, not small-cluster robust intervals."""
    if result is None:
        return []
    rows = []
    for term, value in result.fe_params.items():
        se = float(result.bse_fe[term])
        rows.append(
            {
                "model": summary["model"],
                "term": term,
                "estimate": float(value),
                "se": se,
                "lower95": float(value - 1.96 * se) if summary["ci_usable"] else np.nan,
                "upper95": float(value + 1.96 * se) if summary["ci_usable"] else np.nan,
                "ci_usable": summary["ci_usable"],
                "source": summary["source"],
            }
        )
    return rows


def residual_table(data: pd.DataFrame, result: Any, name: str) -> pd.DataFrame:
    """Conditional fitted values on transformed scale; not out-of-sample predictions."""
    table = data.copy()
    table["model"] = name
    table["fitted"] = result.fittedvalues.to_numpy()
    table["residual"] = table.y - table.fitted
    table["standardized"] = table.residual / np.sqrt(result.scale)
    table["source"] = SOURCE
    return table


def run_inference(raw: Path, dest: Path, report: Path | None = None) -> dict:
    """Run prespecified exploratory models and sensitivity checks on verified originals."""
    digest = verify_original(raw)
    dictionary = read_dictionary(raw.with_name("DataDictionary.xlsx"))
    frame = read_zenodo_csv(raw)
    eda_tables, audit = analyze(frame)
    data, selection = training_sample(frame)
    dest.mkdir(parents=True, exist_ok=True)
    for name in ["coverage", "player_cycles", "cycle_overlaps", "date_gaps"]:
        eda_tables[name].to_csv(dest / f"{name}.csv", index=False)
    support = frame.groupby(["md_day", "status"]).agg(
        n=("HSR", "size"), players=("player_id", "nunique")
    )
    support.to_csv(dest / "day_status_support.csv")
    frame.groupby(["player_id", "status"]).size().rename("n").to_csv(dest / "player_status.csv")
    models, effects, attempts, diagnostics, residuals = [], [], [], [], {}

    def fit(sample: pd.DataFrame, formula: str, name: str) -> Any:
        result, summary, log = fit_intercept(sample, formula, name)
        models.append(summary)
        effects.extend(coefficients(result, summary))
        attempts.extend(log)
        if result is not None and summary["converged"] and not summary["boundary"]:
            table = residual_table(sample, result, name)
            residuals[name] = table
            diagnostics.append(
                {
                    "model": name,
                    "skew": stats.skew(table.residual),
                    "excess_kurtosis": stats.kurtosis(table.residual),
                    "abs_standardized_gt3": int(table.standardized.abs().gt(3).sum()),
                    "n": len(table),
                    "source": SOURCE,
                }
            )
        return result

    fit(data, "y ~ 1", "M1_log_null")
    day_ok = data.groupby("md_day").player_id.nunique().ge(3).all() and -1 in data.md_day.values
    if not day_ok:
        raise ValueError("Insufficient recorded-day support for Model 2")
    fit(data, f"y ~ {DAY}", "M2_log_day")
    pos_counts = data.groupby("position").player_id.nunique()
    pos_ok = data.groupby("player_id").position.nunique().eq(1).all() and pos_counts.ge(3).all()
    if pos_ok:
        fit(data, f"y ~ {DAY} + C(position)", "M3_log_day_position")
    threshold = float(data.HSR.quantile(0.99))
    samples = {
        "S_sqrt_day": data.assign(y=np.sqrt(data.HSR)),
        "S_trim99_day": data.loc[data.HSR.le(threshold)],
        "S_coverage60_day": data.loc[
            data.player_id.isin(data.groupby("player_id").size().loc[lambda s: s.ge(60)].index)
        ],
        "S_central_dates_day": data.loc[data.date.between("2023-10-01", "2024-04-30")],
    }
    for name, sample in samples.items():
        fit(sample.copy(), f"y ~ {DAY}", name)
    for player in sorted(data.player_id.unique()):
        sample = data.loc[data.player_id.ne(player)]
        result, summary, log = fit_intercept(sample, f"y ~ {DAY}", f"LOO_{player}")
        models.append(summary)
        effects.extend(coefficients(result, summary))
        attempts.extend(log)
    model_table = pd.DataFrame(models)
    (dest / "fit_attempts.json").write_text(json.dumps(attempts, indent=2), encoding="utf-8")
    effect_table = pd.DataFrame(effects)
    model_table.to_csv(dest / "models.csv", index=False)
    effect_table.to_csv(dest / "fixed_effects.csv", index=False)
    influence = effect_table.loc[effect_table.model.str.startswith("LOO")].merge(
        effect_table.loc[effect_table.model.eq("M2_log_day"), ["term", "estimate"]],
        on="term",
        suffixes=("", "_primary"),
    )
    influence["absolute_change"] = (influence.estimate - influence.estimate_primary).abs()
    influence.to_csv(dest / "leave_player_influence.csv", index=False)
    pd.DataFrame(diagnostics).to_csv(dest / "diagnostics.csv", index=False)
    baseline = data.HSR.agg(["mean", "median", "std", "min", "max"]).to_dict()
    baseline.update(n=len(data), players=int(data.player_id.nunique()), source=SOURCE)
    diag_days = []
    lag = []
    for name, table in residuals.items():
        table.to_csv(dest / f"residuals_{name}.csv", index=False)
        daily = table.groupby("md_day").residual.agg(["size", "std"])
        daily["model"] = name
        diag_days.append(daily.reset_index())
        for player, group in table.groupby("player_id"):
            lag.append(
                {
                    "model": name,
                    "player": player,
                    "n_pairs": len(group) - 1,
                    "lag1_r": group.residual.corr(group.residual.shift()),
                    "source": SOURCE,
                }
            )
    if not diag_days:
        raise RuntimeError("No usable fits; retained models.csv and fit_attempts.json")
    pd.concat(diag_days).to_csv(dest / "residual_day_sd.csv", index=False)
    pd.DataFrame(lag).to_csv(dest / "residual_lag.csv", index=False)
    metadata = {
        "source": SOURCE,
        "csv_md5": digest,
        "dictionary": dictionary,
        "dictionary_md5": verify_original(
            raw.with_name("DataDictionary.xlsx"), "DataDictionary.xlsx"
        ),
        "selection": selection,
        "audit": audit,
        "baseline": baseline,
        "status_meanings": "UNKNOWN: paper describes groups but dictionary does not map T/S",
        "trim99_threshold_m": threshold,
        "position_model_supported": bool(pos_ok),
        "attempts": attempts,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["numpy", "pandas", "scipy", "statsmodels", "patsy", "matplotlib"]
        },
        "python": platform.python_version(),
    }
    (dest / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )
    from .inference_output import export_outputs

    export_outputs(dest, data, residuals, model_table, effect_table, metadata, report)
    verify_original(raw)
    manifest = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in dest.iterdir()
        if p.is_file() and p.name != "manifest.json"
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if not model_table.iloc[0].converged or model_table.iloc[0].boundary:
        raise RuntimeError("Primary random-intercept model failed; inspect retained outputs")
    print(
        f"[inference] {len(data)} observations; {selection['players']} players; "
        f"{model_table.converged.sum()}/{len(models)} converged fits; checksum unchanged"
    )
    return metadata
