# Navy redesign release report

Local redesign, documentation and safety verification: **PASS**.
Authorized existing-repository update: prepared for publication.
Live-after and hosted CI results are appended only after execution.

## Product and root cause

The previous light theme, explicit white CSS cards and white Plotly figures caused
the plain appearance. Root native config now uses dark navy, with matching
central tokens and figure backgrounds. Typography, numbered checked navigation,
public status, hero/module panels, KPIs, filter grouping/reset, dashed load lines,
selected-model encoding, semantic tables and methods panels form a coherent design.
All five pages and scientific qualifications remain.

The public title is PathwayLab - Football Data Science & Performance Analytics.
No named sporting organization, recruitment positioning, external crest or tool
branding appears in the current public Markdown/UI. MIT and source attribution remain.

## Executed engineering checks

- Original full suite: 64 passed in 70.27s.
- Offline suite: 54 passed, 10 integration checks deselected in 20.10s.
- Isolated public snapshot: 54 passed in 24.11s.
- Full Ruff lint/format: PASS, 42 workspace Python files.
- All 21 package modules imported; pip check and wheel build passed.
- Synthetic generation/CLI, original checksum verification and isolated Zenodo QA passed.
- Meaningful UI tests preserve reader spies, public guards, computed scores and chronology.
  Assertions were adapted to numbered display labels and removal of the public
  one-option dropdown; reset behavior was added. No scientific assertion was weakened.

All 233 protected files and scientific function ASTs in 15 modules are unchanged.
No expensive original experiments were rerun. One CLI sentence was made organization-neutral.

## Browser and documentation

Twenty actual live before cases and twenty local after cases, all five pages at
1440x900, 1280x800, 768x1024 and 390x844. Local forty interaction checks passed;
native dark canvas/card/chart computed styles were asserted. Additional stable
table captures and final live checks are recorded in the
[redesign review](docs/UI_REDESIGN_REVIEW.md). No page overflow/errors/title
overruns occurred in completed local checks. Representative genuine screenshots
were visually reviewed. This is bounded evidence, not full accessibility certification.

Canonical [workflow](docs/WORKFLOW.md) documents both real pipelines, actual modules,
commands, inputs, outputs, validation and limitations.
[Architecture](docs/ARCHITECTURE.md), [reproduction](REPRODUCIBILITY.md) and
[five-minute guide](docs/DASHBOARD_GUIDE.md) match the implemented system.
[Link audit](docs/LINK_VALIDATION.md) records internal paths, HTTP results and the
descriptor DOI's HTTP 403 limitation without inventing a successful retrieval.

## Public safety and delivery

The explicit manifest contains code, safe documents and genuine synthetic captures.
No raw datasets, real individual predictions, private artifacts, credentials or
personal machine paths are included. Independent generator cohorts remain separate.
Public entrypoint app/public_demo.py forces synthetic-only mode, including against
an accidentally enabled local flag. URL/widgets cannot grant research access.
Real numerical findings remain excluded; outside data retain their original terms.

[Repository](https://github.com/MRTRauf/pathwaylab) ·
[Live application](https://pathwaylab-rauf.streamlit.app/) ·
[Portfolio](https://mrtrauf.github.io/)

Community Cloud wraps the app in a frame; browser checks inspect the embedded app.
An initial outer-wrapper blank-body timeout was a harness issue and was corrected.
Final deployment is not inferred from a successful push or HTTP response.
