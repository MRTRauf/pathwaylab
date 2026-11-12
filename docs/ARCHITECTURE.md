# Architecture

The existing Python package is retained. Presentation does not reimplement the
validated research algorithms or create shared identities across independent sources.

~~~mermaid
flowchart TD
    subgraph Local authorized research
      A[audit.py and data.py] --> B[eda.py and inference.py]
      A --> C[forecasting.py]
      D[event_source.py] --> E[events.py]
      B --> F[Saved local artifacts]
      C --> F
      E --> F
      F --> G[Private research viewers]
    end
    subgraph Public demonstration
      H[synthetic.py and demo_data.py] --> I[demo_dashboard.py]
      J[app/public_demo.py forces synthetic guard] --> K[app/streamlit_app.py]
      K --> I
      L[presentation.py and config.toml] --> I
    end
~~~

| Layer | Responsibility |
|---|---|
| data.py, audit.py | Original schema, checksum verification, retained QA |
| quality.py, eda.py | Validation, synthetic block features, real descriptions |
| inference.py, inference_output.py | Repeated-measures models, diagnostics and reports |
| forecasting.py, forecast_output.py | Real session features, target-date folds, selection/evaluation |
| event_source.py | Independent pinned discovery/acquisition |
| events.py, event_output.py | Timeline validation, exposure, rates, historical windows and sensitivity |
| synthetic.py, model.py | Deterministic load generator and original synthetic block benchmark |
| demo_data.py | Independent fictional cohorts and calculated public comparisons |
| presentation.py | Central navy tokens, reusable panels and Plotly rendering policy |
| demo_dashboard.py | Five public pages, filters and calculated displays |
| app/public_demo.py | Forces PATHWAYLAB_PUBLIC_DEMO=1 before invoking the viewer |
| app/streamlit_app.py | Navigation and guarded server-side public/private branch |
| tests/ | Safe fixtures, chronology, metrics, access guards and AppTest; private checks stay local |
| .github/workflows/ci.yml | Ubuntu/Python 3.11 install, Ruff/format, dependency/import checks, offline tests, demo and wheel |

## Access and deployment

Public startup uses installed dependencies and generated fixtures. It never needs
data/raw or private outputs, and never invokes downloaders. The public guard
overrides an accidental local-research flag. Query parameters/widget manipulation
cannot grant research access. The trusted local flag is not authentication.

Root .streamlit/config.toml selects the native dark theme. Scoped CSS handles
hierarchy and spacing; Plotly backgrounds, labels and hover appearance are explicit.
System fonts and project-native text/CSS avoid external assets.

Community Cloud uses main, app/public_demo.py and root requirements.txt (.[app]).
Python 3.12 is the local deployment target; package metadata permits Python 3.10+.
No secret is required. A successful push/build is distinct from live-browser validation.

The public repository has a separately curated history. Original research history,
source caches, private audits and individual records were never pushed.
RELEASE_MANIFEST.json records reviewed public bytes. External terms remain separate
from the [MIT code license](../LICENSE). See [workflow](WORKFLOW.md) and
[rights](../DATA_ACCESS_AND_LICENSE.md).
