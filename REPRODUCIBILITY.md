# Reproducibility

## A. Public synthetic quickstart

Use Python 3.10+; local validation uses Windows/Python 3.12, CI uses Ubuntu/Python
3.11. Streamlit 1.55+ is required by the presentation configuration. No original
dataset, credential or runtime downloader is needed.

PowerShell, from the repository root:

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e '.[dev,app,research]'
python -m pip check
python scripts/generate_demo.py
python -m pathwaylab.cli --mode demo
New-Item -ItemType Directory -Force outputs | Out-Null
pytest -q -m "not integration" --basetemp=outputs/pytest-review -o cache_dir=outputs/pytest-cache
python -m ruff check src app scripts tests
python -m ruff format --check src app scripts tests
python -m pip wheel . --no-deps -w dist
python -m streamlit run app/public_demo.py
~~~

On macOS/Linux use source .venv/bin/activate after creating the venv. The Python
commands are portable. Ordinary pytest -q also works where the system temporary
directory permits it; the explicit workspace basetemp avoids Windows ownership
problems. Use a fresh temporary directory for a new review.

Expected generated outputs:

| Command | Output and interpretation |
|---|---|
| scripts/generate_demo.py | data/synthetic/demo_training_sessions.csv, fake sessions, fixed seed 42 |
| CLI --mode demo | outputs/demo/REPORT.md, results.json, features, predictions and labelled figures |
| app/public_demo.py | Five pages; independent event fixture uses seed 43 in memory |
| pip wheel | Wheel under dist; datasets and private artifacts excluded |

DEMO load IDs and EVENT IDs are separate fictional cohorts. Demo errors measure
next-observed-block cumulative HSR; real research targets one observed session.
All displayed scores are calculated. **SYNTHETIC - DEMONSTRATION ONLY**.

The entrypoint forces PATHWAYLAB_PUBLIC_DEMO=1. Even an accidentally configured
PATHWAYLAB_ENABLE_LOCAL_RESEARCH=1 cannot grant research access through that
entrypoint. URL/widget changes cannot override the server branch. Public startup
does not read original files.

## B. Authorized real-data research

Review [data rights](DATA_ACCESS_AND_LICENSE.md), then follow the actual commands
and stage definitions in [WORKFLOW.md](docs/WORKFLOW.md). Originals, processed
records, individual predictions, fitted outputs and private reports remain ignored.
The public snapshot retains the algorithms; ten original-data integration checks
and real golden values stay in the original research workspace.

Verification and ingestion are safe read/QA checks on already acquired files:

~~~bash
python scripts/download_zenodo.py --verify-only --with-dictionary
python -m pathwaylab.cli --mode zenodo --out outputs/zenodo-review
~~~

Do not rerun expensive experiments merely for presentation. New research audits
must use separate output/report paths. Preserve strict and sensitivity event
versions separately. Never join independent sources by name or similar IDs.

For a private viewer only, start a new process with the trusted local flag,
authorized artifacts and loopback binding, as documented in the workflow.
That flag is not authentication and must not be used on public hosting.

## Evidence and deployment

Use app/public_demo.py, main, Python 3.12 and root requirements.txt (-e .[app]) on
Community Cloud. No application secret is required. The dark native theme lives
in root .streamlit/config.toml; presentation and Plotly share explicit navy tokens.
Inspect the actual HTTPS app after rebuild rather than infer success from CI.
[Review](docs/UI_REDESIGN_REVIEW.md) separates executed local, CI and live checks.
