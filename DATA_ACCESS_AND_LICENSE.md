> Release authorization: the owner explicitly approved MIT for eligible original code,
> the reviewed public GitHub release and synthetic-only Community Cloud deployment.
> Third-party data, assets and dependencies retain their original terms.

# Data access, licensing and publication boundary

The public PathwayLab application is **SYNTHETIC DEMONSTRATION - NOT REAL PLAYER
DATA** and **SYNTHETIC - DEMONSTRATION ONLY**. Its load/event cohorts are generated
independently, with fixed seeds and fictional identities. It does not ship raw
football datasets, individual real predictions, fitted research models or real
data-derived images.

## Original code and external packages

Eligible original PathwayLab code is licensed under the owner-approved MIT License.
No missing-license default is assumed. Third-party packages retain their own
licenses and are not relicensed by PathwayLab. No external dataset is placed under
the original-code license. See [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md).

## Separate original research references

| Source | Provenance | Current public-package handling |
|---|---|---|
| GPS training/load data | [Zenodo v1](https://zenodo.org/records/18986229), creator Alejandro Rodríguez-Fernández; [Sierra-Casas et al. (2026)](https://doi.org/10.3390/data11040084) | Originals, processed records, individual predictions and real figures omitted |
| Match events | [StatsBomb Open Data](https://github.com/hudl/open-data), original analysis pinned to commit `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb` | Raw caches, real panels, findings and real screenshots omitted |

These contain unrelated people. Do not join by names, teams or similar numeric IDs.
The public event fixture is independently simulated, not a redistributed or
anonymized copy of either source.

## Rights status

Reviewed 2026-11-12. Zenodo's record license field was blank while the descriptor
explicitly states a dataset CC BY 4.0 license. This is incomplete/conflicting release
evidence, not a conclusion that no license exists. Clarify rights before further
redistribution of those files or source-derived records.

The [pinned StatsBomb README](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/README.md)
and original Public Data User Agreement were reviewed. Applicable attribution,
official-logo, registration and commercial-use conditions need review before
publishing affected real-data analysis. The official media-pack route redirected
to an inaccessible service during audit. No substitute logo or permission was
invented. Those affected real-data insights/assets are excluded from this release.

Copyright, database reuse, attribution, privacy and software licensing are separate.
Public downloadability and pseudonymization do not independently confer permission.
This data-free publication scope does not clear or distribute the external data.

## Authorized local research only

Obtain original files through their official sources, review their terms and retain
source records, access dates and methods. Original Zenodo MD5 values:

- CSV: `864bfbc3f78a736f60bba764de8d4f4d`.
- Dictionary: `10959d59ba0ad221a0b783d618d27d53`.

Raw files belong under ignored data/raw; analytical outputs under ignored outputs.
Research commands are explicit local actions, not public-app startup behavior.
Only a private viewer may use trusted `PATHWAYLAB_ENABLE_LOCAL_RESEARCH=1` with
app/streamlit_app.py on a loopback server. This flag is not authentication.
app/public_demo.py forces the synthetic guard and cannot enable research via URL
or widget manipulation, including when the local research flag is present.

Future club data require separate approved access, privacy/ethics decisions and
verified identities/timestamps. There is no current club affiliation or agreement.
