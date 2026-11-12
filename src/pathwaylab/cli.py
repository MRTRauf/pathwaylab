"""Build reproducible results and plots. Usage: python -m pathwaylab.cli --mode demo"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .audit import verify_original, write_audit
from .data import read_synthetic_csv, read_zenodo_csv
from .model import run_forecast
from .quality import make_microcycle_features, validate_sessions
from .synthetic import write_demo


def export_figures(
    sessions: pd.DataFrame, micro: pd.DataFrame, predictions: pd.DataFrame, dest: Path, source: str
):
    dest.mkdir(parents=True, exist_ok=True)
    profile = sessions.groupby(["md_day", "status"], observed=True)["HSR"].mean().unstack("status")
    ax = profile.sort_index().plot(kind="bar", figsize=(9, 4), rot=0)
    ax.set(
        title=f"Mean session HSR by match-day offset ({source})",
        xlabel="Day relative to match (0 = match)",
        ylabel="HSR distance (m)",
    )
    ax.figure.tight_layout()
    ax.figure.savefig(dest / "01_microcycle_hsr.png", dpi=160)
    plt.close(ax.figure)

    sample = micro.loc[micro["player_id"] == micro["player_id"].iloc[0]].sort_values("microcycle")
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(
        sample["microcycle"],
        sample["train_hsr"],
        marker="o",
        markersize=3,
        label="Training HSR / microcycle",
    )
    ax.set(
        xlabel="Observed microcycle ID",
        ylabel="Training HSR (m)",
        title=f"Individual load trajectory - {sample.iloc[0]['player_id']} ({source})",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(dest / "02_individual_trajectory.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(
        predictions["next_train_hsr"],
        predictions["persistence_prediction"],
        label="Persistence",
        alpha=0.55,
    )
    ax.scatter(
        predictions["next_train_hsr"], predictions["ridge_prediction"], label="Ridge", alpha=0.55
    )
    maxv = (
        max(predictions[["next_train_hsr", "persistence_prediction", "ridge_prediction"]].max())
        * 1.05
    )
    ax.plot([0, maxv], [0, maxv], linestyle="--", color="black", lw=1, label="Perfect prediction")
    ax.set(
        xlabel="Actual next microcycle training HSR (m)",
        ylabel="Predicted HSR (m)",
        title=f"Holdout predictions ({source})",
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(dest / "03_holdout_forecast.png", dpi=160)
    plt.close(fig)


def run(mode: str, raw: Path | None, out_dir: Path, findings: Path | None = None):
    if mode == "forecast":
        if raw is None or not raw.exists():
            raise FileNotFoundError("Download the original Zenodo CSV and dictionary first")
        from .forecasting import run_temporal_forecast

        run_temporal_forecast(raw, out_dir, findings)
        return
    if mode == "eda":
        if raw is None or not raw.exists():
            raise FileNotFoundError("Download the original Zenodo CSV and dictionary first")
        from .eda import run_eda

        run_eda(raw, out_dir, findings)
        return
    if mode == "demo":
        demo_path = Path("data/synthetic/demo_training_sessions.csv")
        if not demo_path.exists():
            write_demo(demo_path)
        sessions = read_synthetic_csv(demo_path)
        source = "SYNTHETIC - DEMONSTRATION ONLY"
    elif mode == "zenodo":
        if raw is None or not raw.exists():
            raise FileNotFoundError(
                "First download the Zenodo CSV: python scripts/download_zenodo.py, "
                "then use --raw data/raw/DataSetTMr.csv"
            )
        verify_original(raw)
        sessions = read_zenodo_csv(raw)
        source = "PUBLIC ZENODO (DOI: 10.5281/zenodo.18986229)"
    else:
        raise ValueError(mode)
    out_dir.mkdir(parents=True, exist_ok=True)
    if mode == "zenodo":
        qa = write_audit(sessions, raw, out_dir)
        print(
            f"[zenodo] CHECKSUM OK; {qa['n_rows']} sessions; "
            f"{qa['n_players']} players; {qa['n_microcycles']} microcycles"
        )
        print(f"Phase 01 ingestion/QA only. Outputs: {out_dir.resolve()}")
        if qa["negative_load_rows"] or qa["missing_load_cells"] or qa["unknown_status_rows"]:
            raise ValueError("Quality gate failed; inspect retained audit evidence")
        return
    qa = validate_sessions(sessions)
    if qa["missing_required_columns"] or qa["negative_load_rows"]:
        raise ValueError(f"Quality gate failed: {qa}")
    micro = make_microcycle_features(sessions)
    scores, pred = run_forecast(micro)
    micro.to_csv(out_dir / "microcycle_features.csv", index=False)
    pred.to_csv(out_dir / "holdout_predictions.csv", index=False)
    export_figures(sessions, micro, pred, out_dir / "figures", source)
    results = {
        "source": source,
        "dataset_quality": qa,
        "forecast": scores,
        "limitations": [
            "No individual injury outcomes are provided",
            "No linked event data for same players",
            "Training load is not equivalent to player development",
            "RATIO* full-season normalization is excluded from predictive features",
            "Observational data do not establish causality",
        ],
    }
    with (out_dir / "results.json").open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    (out_dir / "REPORT.md").write_text(
        f"# PathwayLab exploratory report\n\n**DATA SOURCE: {source}**\n\n"
        f"## Repeated-measures summary\n\nPlayers: {qa['n_players']} | "
        f"Microcycles: {qa['n_microcycles']} | Session rows: {qa['n_rows']}\n\n"
        f"## Chronological out-of-sample holdout\n\nRidge MAE: {scores['ridge_mae']:.1f} m | "
        f"Persistence MAE: {scores['persistence_mae']:.1f} m\n\n"
        "These values are descriptive, not independently validated and must "
        "not be used as player health or injury risk advice.\n"
        "A better model has LOWER MAE; if Ridge underperforms persistence, report it honestly.\n\n"
        "## Limitations\n\n- No injury labels, so no injury prediction.\n- No "
        "same-player event-data joins available.\n"
        "- No academy age or developmental outcomes, so don't claim player development effects.\n"
        "- Next OBSERVED microcycle may not be the next calendar week.\n"
        "- Excludes RATIO* features based on full-season maximal demand.\n"
        "- Synthetic results are not real athlete data or proof of operational impact.\n",
        encoding="utf-8",
    )
    print(
        f"[{mode}] {qa['n_rows']} sessions; {qa['n_players']} players; "
        f"Ridge MAE={scores['ridge_mae']:.1f}; Persistence MAE={scores['persistence_mae']:.1f}"
    )
    print(f"Outputs: {out_dir.resolve()}")


def main():
    ap = argparse.ArgumentParser(description="PathwayLab football load analytics research kit")
    ap.add_argument("--mode", choices=["demo", "zenodo", "eda", "forecast"], default="demo")
    ap.add_argument("--raw", type=Path, default=Path("data/raw/DataSetTMr.csv"))
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument(
        "--findings",
        type=Path,
        default=None,
        help="Findings Markdown path for eda or forecast mode",
    )
    args = ap.parse_args()
    out = args.out or Path("outputs") / args.mode
    findings = args.findings
    if findings is None and args.mode in {"eda", "forecast"}:
        name = "EDA_FINDINGS.md" if args.mode == "eda" else "FORECASTING_FINDINGS.md"
        findings = Path("research") / name
    run(args.mode, args.raw, out, findings)


if __name__ == "__main__":
    main()
