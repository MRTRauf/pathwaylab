> Release authorization: the owner explicitly approved MIT for eligible original code,
> the reviewed public GitHub release and synthetic-only Community Cloud deployment.
> Third-party data, assets and dependencies retain their original terms.

# PathwayLab maintenance and deployment handoff

## Application

Public entry point: **app/public_demo.py**. It forces `PATHWAYLAB_PUBLIC_DEMO=1`
before executing the existing five-section viewer. Private local research uses
app/streamlit_app.py, explicitly trusted `PATHWAYLAB_ENABLE_LOCAL_RESEARCH=1` and
loopback access. Neither URL parameters nor widget values grant research access.
The public guard overrides an accidentally configured private flag.

Synthetic generation/calculation is in demo_data.py; interface rendering in
demo_dashboard.py; shared style in presentation.py and .streamlit/config.toml.
Scientific adapters, inference and forecasting retain their audited logic.

## Local maintenance

```bash
python -m pip install -e '.[dev,app,research]'
python -m pip check
python -m ruff check src app scripts tests
python -m ruff format --check src app scripts tests
pytest -q -m "not integration"
python -m pathwaylab.cli --mode demo
python -m streamlit run app/public_demo.py
```

The original local workspace retains full authorized-data integration checks. The
curated public repository contains fixture-only checks; it has no private golden
results or external records. Do not replace the original research repository with
the public snapshot, or push its historical commits: a legacy test fixture had
copied a real record and has been replaced with invented values.

Never overwrite saved research merely for a UI change. Check protected hashes,
temporal/source invariants and meaningful tests after analytical edits. Keep the
strict and receipt-clock-sensitive event analyses separate. Real numerical claims
and figures remain withheld pending their own rights review.

## Releasing changes

Maintain the explicit RELEASE_MANIFEST.json in the public candidate. Review every
file and Git history, generated assets, links and dependency changes. Never stage
all files indiscriminately from the local research workspace. Exclude raw data,
processed/individual/prediction records, research weights, private audit reports,
logs, screenshots of real data, development prompts and credentials.

All public images must be genuine captures of the independently generated demo.
Retain both synthetic disclaimer strings. Do not add club logos, personal records,
injury/readiness gauges or misleading cross-source identities. Recheck mobile
titles, legends, filters, empty states and source captions after layout changes.

## Streamlit Community Cloud

After approval and verified GitHub publication, deploy the reviewed public branch
using **app/public_demo.py**, Python 3.12 and root requirements.txt (`.[app]`).
The project config disables telemetry/static serving and uses the navy/light theme.
No dataset, API credential or application secret is required. Do not enable private
research on the hosted app; the public wrapper must remain in use.

Use the supported Community Cloud interface and owner account authorization.
Official documentation:
[deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)
and [dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
Do not invent a successful app URL or bypass account security.

After a deployment, open the actual HTTPS URL in an independent browser session.
Verify public visibility without login, all five sections, computed demo forecasts,
interactive/empty states, mobile rendering and isolation from research data. Observe
an actual hosted CI run and test a clean clone before publishing success claims.
Update README/outreach links only after verification. No outreach message is sent
automatically by releasing software.

## Decisions and interpretation

The owner must approve the original-code license and concrete public contents before
irreversible publication. External data keep their own terms. See DATA_ACCESS_AND_LICENSE.md
and FINAL_RELEASE_REPORT.md for current decisions/status. Original research is
exploratory and conditional retrospective forecasting, with small dependent samples,
unverified prospective timing and event inclusion sensitivity. Proposed connected
club research has not occurred; no Brøndby affiliation or endorsement exists.
