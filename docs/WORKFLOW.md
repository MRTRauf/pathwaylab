# Research workflow

Two independent research pipelines and a separately generated public demonstration.
GPS and event people are never joined. Commands run from the repository root.
Review [rights](../DATA_ACCESS_AND_LICENSE.md) before acquisition; all original
records and analytical outputs stay local. Do not overwrite validated experiments
for a UI change. The command identifiers in the tables refer to commands below.

## A. Physical load

~~~mermaid
flowchart TD
    A[Official source files] --> B[Checksum verification]
    B --> C[Parsing and schema validation]
    C --> D[Quality checks]
    D --> E[Exploratory analysis]
    E --> F[Repeated-measures models]
    D --> G[Historical feature engineering]
    G --> H[Chronological forecasting]
    H --> I[Model evaluation]
    F --> J[Local reports and private viewer]
    I --> J
~~~

| Stage / purpose | Input and processing | Output | Actual module | Command | Validation and limitation |
|---|---|---|---|---|---|
| Acquisition: preserve originals | Official CSV/dictionary; public download | data/raw originals | scripts/download_zenodo.py | A1 | Provider checksums; access is not redistribution permission |
| Verification: establish provenance | Bytes compared to expected MD5 | Verification result | audit.py; download script | A2 | Mismatches rejected; a hash does not prove scientific validity |
| Parsing: standardize fields | Semicolon/comma-decimal CSV, Excel dates, IDs/categories | Canonical session frame | data.py | A3 | Required fields/malformed values checked; dictionary coding incomplete |
| QA: retain coverage/anomalies | Parsed rows; missingness, duplicates, signs, codes and zeros | QA JSON/report/tables | audit.py; quality.py | A3 | Retain anomalies; zero running distance is not automatically missing |
| EDA: describe variation | Sessions; day/status/position summaries, within-player variation | EDA tables/plots/report | eda.py | A4 | Explicit denominators; repeated rows are dependent |
| Longitudinal modelling | Provisional training rows; transformed random-intercept models | Coefficients/residual diagnostics/model summaries | inference.py; inference_output.py | A5 | Convergence/sensitivity recorded; small clusters/shared dates limit inference |
| Historical features | Ordered sessions; shifted histories, target date/gap | Forecast feature panel | forecasting.py | A6 | No full-season RATIO fields; target-date knowledge assumed |
| Temporal evaluation | Shared target-date development folds, frozen selection, final holdout | Baseline/model predictions and scores | forecasting.py; forecast_output.py | A6 | Training-only preprocessing; no row-random split/final-period tuning |
| Reporting | QA, diagnostics, scores, provenance | Versioned local reports/manifests | audit.py; inference_output.py; forecast_output.py | A3/A5/A6 | No health, causal or prospective operational claim |
| Dashboard | Verified source/saved artifact hashes and schemas | Local interactive research views | dashboard_data.py; app/streamlit_app.py | A7 | No fitting in real viewer; trusted flag is not authentication |

~~~bash
# A1/A2, only after source access and rights review
python scripts/download_zenodo.py --with-dictionary
python scripts/download_zenodo.py --verify-only --with-dictionary
# A3
python -m pathwaylab.cli --mode zenodo --out outputs/zenodo
# A4
python -m pathwaylab.cli --mode eda --out outputs/eda --findings research/EDA_FINDINGS.md
# A5
python scripts/run_inference.py --out outputs/inference --report research/LONGITUDINAL_FINDINGS.md
# A6
python -m pathwaylab.cli --mode forecast --out outputs/forecast --findings research/FORECASTING_FINDINGS.md
~~~

A7: in a private new process with authorized files, set
PATHWAYLAB_ENABLE_LOCAL_RESEARCH=1, leave PATHWAYLAB_PUBLIC_DEMO unset and run
python -m streamlit run app/streamlit_app.py --server.address 127.0.0.1.
Never enable this flag on public hosting. New audit runs need separate output and
report paths. The real target is next observed session HSR, conditional on a known
target date; observed sessions may skip dates. The public toy task instead predicts
cumulative next observed block HSR, so scores are not comparable.

## B. Match performance

~~~mermaid
flowchart TD
    A[Competition discovery] --> B[Pinned event and lineup acquisition]
    B --> C[Schema and timeline validation]
    C --> D[Estimated playing exposure]
    D --> E[Counts and rates]
    E --> F[Player-match panel]
    F --> G[Prior-only windows and season descriptions]
    G --> H[Separate inclusion sensitivity]
    H --> I[Local reporting and private viewer]
~~~

| Stage / purpose | Input and processing | Output | Actual module | Command | Validation and limitation |
|---|---|---|---|---|---|
| Discovery: define coverage | Pinned competitions/matches metadata | Selected coverage manifest | event_source.py | B1 | Available seasons constrain longitudinal questions |
| Acquisition: provenance | Events/lineups at pinned revision | Local JSON/source hashes | event_source.py | B2 | Provider terms apply; no downloads during public startup |
| Validation | IDs, period clocks, lineups, completeness | Retention/exclusion audit | events.py | B3 | Strict timeline policy; missing matches are not invented |
| Exposure reconstruction | Lineups, substitutions, dismissals, period endpoints | Estimated stints/minutes | events.py:player_match | B3 | Event-clock estimates are not official minutes |
| Metric engineering | Counts and estimated exposure | Counts/per-90 rates | events.py:player_match | B3 | 90 × summed counts / summed minutes; no unweighted average of row rates |
| Player-match panel | Retained observed appearances | Analysis panel | events.py | B3 | Unused substitutes are not zero-performance appearances |
| Longitudinal analysis | Ordered appearances/prior windows | History/season summaries | events.py:historical_panel; event_output.py | B3 | Current appearance excluded; coverage and roles confound changes |
| Sensitivity analysis | Same originals, optional unused receipt-clock handling | Separately labelled output directory | events.py:run_events | B4 | Never replaces strict results or repairs raw clocks |
| Reporting | Panel/audit/source manifest | Local reports/figures/hashes | event_output.py | B3/B4 | No development/causal interpretation |
| Dashboard | Saved event artifacts | Private trajectory views | event_dashboard.py | A7 | Independent people, no GPS join |

~~~bash
# B1 / B2
python scripts/run_events.py discover
python scripts/run_events.py download
# B3: also writes local research reports
python scripts/run_events.py analyze
~~~

For isolated report-free reruns, use the existing API rather than nonexistent CLI flags:

~~~python
from pathlib import Path
from pathwaylab.events import run_events

run_events(dest=Path("outputs/events_strict_review"), report_dir=None)
# B4: preserve strict results and raw source bytes
run_events(
    dest=Path("outputs/events_receipt_sensitivity"),
    report_dir=None,
    allow_invalid_receipt_time=True,
)
~~~

## Public demonstration

~~~mermaid
flowchart LR
    A[Load generator seed 42] --> B[Fictional DEMO cohort]
    B --> C[Explorer and block forecast]
    D[Independent event generator seed 43] --> E[Fictional EVENT cohort]
    E --> F[Simulated exposure and trajectories]
    C --> G[Synthetic-only public app]
    F --> G
~~~

synthetic.py and demo_data.py generate observations. model.py and quality.py retain
the original synthetic block benchmark; demo_dashboard.py renders computed results.
No original records/private scores are copied. See [reproduction](../REPRODUCIBILITY.md),
[methods](METHODS.md), [architecture](ARCHITECTURE.md) and [guide](DASHBOARD_GUIDE.md).
