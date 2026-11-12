# PathwayLab — Football Data Science & Performance Analytics

Independent research software for longitudinal physical load, historical forecasting
and exposure-aware match-performance analysis.

**[Live application](https://pathwaylab-rauf.streamlit.app/) ·
[GitHub](https://github.com/MRTRauf/pathwaylab) ·
[Author portfolio](https://mrtrauf.github.io/)**

![PathwayLab navy synthetic research workspace](assets/screenshots/overview.png)

**SYNTHETIC DEMONSTRATION - NOT REAL PLAYER DATA**  
**SYNTHETIC - DEMONSTRATION ONLY**

The public app generates fictional observations independently. It does not bundle
external player records, individual research predictions or private analytical outputs.

## Research objectives

- Describe within-player physical-load variation without treating repeated rows as independent athletes.
- Compare historical forecasting approaches using shared chronological target boundaries.
- Describe match involvement while keeping playing exposure, coverage and uncertainty visible.

## Two independent modules

**Training Load Intelligence** covers verified ingestion, descriptions,
repeated-measures modelling and chronological next-session forecasting.

**Player Performance Trajectories** covers event validation, estimated exposure,
per-90 metrics, prior-only windows and sensitivity to observation inclusion.

The original GPS and event sources contain **unlinked people**. No player-level
join exists. The two public generators also use separate DEMO and EVENT identities.

## Dashboard walkthrough

| Section | Controls and output |
|---|---|
| Research Overview | Computed cohort counts, independent research lanes and workflow |
| Training Load Explorer | Player/position/date/metric controls, reset, load histories and distributions |
| Forecasting Lab | Three calculated synthetic baselines, MAE/RMSE, observed/predicted plots and errors |
| Player Performance Trajectories | Simulated exposure, season comparison, historical passes and peer distributions |
| Methods and Limitations | Questions, source boundaries, assumptions and reproduction |

The navy canvas, integrated controls, readable charts and numbered navigation form
one research workspace. [Five-minute guide](docs/DASHBOARD_GUIDE.md).

## Workflow and architecture

~~~mermaid
flowchart LR
    A[Verified GPS source] --> B[QA and repeated-measures analysis]
    A --> C[Historical features and temporal forecasts]
    D[Independent event source] --> E[Exposure and trajectory analysis]
    B --> F[Private research artifacts]
    C --> F
    E --> F
    G[Independent synthetic generators] --> H[Public demonstration]
~~~

[Complete stage-by-stage workflow](docs/WORKFLOW.md) ·
[Actual module architecture](docs/ARCHITECTURE.md) · [Methods](docs/METHODS.md)

## Methodology and findings

Real research targets next observed session HSR using earlier observations and
training-only preprocessing. All players share target-date boundaries. Full-season
RATIO fields are excluded. Repeated-measures diagnostics and event inclusion
sensitivities constrain interpretation.

The public forecast instead predicts next observed block cumulative HSR. Ridge,
persistence and training median score the same synthetic targets; metrics are
calculated, not copied from real experiments. Event minutes/counts are simulated.
Original numerical findings remain withheld pending separate publication clearance.

## Repository structure

~~~text
app/                  public entrypoint and guarded local viewer
src/pathwaylab/       ingestion, research algorithms, generators and presentation
tests/                safe fixtures, chronology and public-access regressions
docs/                 workflow, architecture, methods and dashboard guide
assets/screenshots/   genuine synthetic browser captures
.streamlit/           native dark-theme configuration
.github/workflows/    data-independent CI
~~~

## Install and run

Python 3.10+; locally verified on Python 3.12. From the project root:

~~~bash
python -m venv .venv
# PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e '.[dev,app,research]'
python scripts/generate_demo.py
python -m pathwaylab.cli --mode demo
pytest -q -m "not integration"
python -m streamlit run app/public_demo.py
~~~

No originals or credentials are needed. [Tested reproduction and outputs](REPRODUCIBILITY.md).

## Testing and CI

Tests cover chronology, calculated scores, exposure, missing artifacts, widget
interactions and public guards. CI runs full Ruff/format checks, imports,
dependencies, offline tests, synthetic CLI and wheel packaging.
[Actual Actions runs](https://github.com/MRTRauf/pathwaylab/actions).
Local and live checks are distinguished in [redesign review](docs/UI_REDESIGN_REVIEW.md).

## Data, license and attribution

Eligible original code uses the [MIT License](LICENSE). Third-party data/packages
retain their terms. References: [Zenodo GPS record](https://zenodo.org/records/18986229),
[dataset descriptor](https://doi.org/10.3390/data11040084) and
[StatsBomb Open Data](https://github.com/hudl/open-data).
[Rights boundary](DATA_ACCESS_AND_LICENSE.md) · [Acknowledgements](ACKNOWLEDGEMENTS.md).

## Scientific limitations and future research

Original samples are small and dependent; exposure/coding metadata are incomplete.
Forecasts are conditional retrospective estimates assuming a known target date,
not prospective operational validation. Event interpretation depends on estimated
minutes and inclusion. No injury, readiness, causal effect or player-development
claim follows.

A future matched-data study would require approved identities, available-at
timestamps, governance and an adequate archive. No such study or external
collaboration is claimed.

## Author

Muhammad Rauf — independent football data science research.
[Portfolio](https://mrtrauf.github.io/) · [GitHub profile](https://github.com/MRTRauf)
