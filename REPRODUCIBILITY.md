# Reproducibility

The public application and fixture tests need no original research datasets,
credentials or runtime data downloads. Use Python 3.10+; the local release checks
use Python 3.12.10 on Windows. Hosted Linux verification is reported only after an
actual Actions run.

## Install and run

```bash
python -m venv .venv
# PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e '.[dev,app,research]'
python -m pip check
python -m ruff check src app scripts tests
python -m ruff format --check src app scripts tests
pytest -q -m "not integration"
python -m pathwaylab.cli --mode demo
python -m streamlit run app/public_demo.py
```

`app/public_demo.py` is the public deployment entry point. It sets the synthetic-only
guard before executing the existing viewer. Even an accidentally present local
research flag cannot expose research through that entry point. The synthetic
generators use seeds 42 and 43; outputs are calculated rather than hardcoded.

The CLI toy experiment predicts next-observed-training-block cumulative HSR;
the independent real study predicts a session. Synthetic metrics are labelled
**SYNTHETIC - DEMONSTRATION ONLY** and must not be quoted as football findings.

## Public versus local tests

The original research workspace retains the complete suite, including ten
integration checks that need authorized external files or private saved outputs.
The curated public snapshot includes the fixture-only tests; private-data
integration assertions and their real benchmark constants remain local. No original
test assertion was weakened or removed from that research workspace. Public CI
does not download records or rely on unshared research artifacts.

Exact observed counts, versions, durations, browser cases and CI status are recorded
in FINAL_RELEASE_REPORT.md after execution. Do not substitute a previous phase's
test count for the current run. On Windows, if pytest temporary-directory ownership
fails, use a fresh workspace-local base, for example:

```powershell
New-Item -ItemType Directory -Force outputs | Out-Null
pytest -q -m "not integration" --basetemp=outputs/pytest-review -o cache_dir=outputs/pytest-cache
```

## Explicit authorized research reproduction

Read [data access/rights](DATA_ACCESS_AND_LICENSE.md) before acquiring external
data. The public application never invokes these commands:

```bash
python scripts/download_zenodo.py --with-dictionary
python scripts/download_zenodo.py --verify-only --with-dictionary
python -m pathwaylab.cli --mode zenodo
python -m pathwaylab.cli --mode eda
python scripts/run_inference.py
python -m pathwaylab.cli --mode forecast
python scripts/run_events.py discover
python scripts/run_events.py download
python scripts/run_events.py analyze
```

These assume project-root execution and appropriate permissions. Real data and
outputs stay ignored. Different output/report paths should be used for an audit
rerun; no validated result should be silently overwritten. `run_events` writes
additional narratives only when `report_dir` is explicit. Strict event chronology
remains the default; the optional receipt-clock sensitivity must be separately
labelled and stored. It does not repair source timestamps.

See [methods](docs/METHODS.md) for target-date chronology, training-only preprocessing,
unverified prospective availability and independent source boundaries. Code,
data/derivative rights and deployment authorization are separate gates.
