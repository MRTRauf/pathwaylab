# Link validation

Relative Markdown/image links and heading anchors were checked against the public candidate.
No broken internal target was found. Results are rerun after publication.

| External target | Observed result |
|---|---|
| https://docs.pytest.org/en/stable/how-to/cache.html | 200 |
| https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app | 200 |
| https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies | 200 |
| https://doi.org/10.3390/data11040084 | HTTP Error 403: Forbidden |
| https://github.com/MRTRauf | 200 |
| https://github.com/MRTRauf/pathwaylab | 200 |
| https://github.com/MRTRauf/pathwaylab/actions | 200 |
| https://github.com/MRTRauf/pathwaylab/actions/runs/43160709722 | 200 |
| https://github.com/hudl/open-data | 200 |
| https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/README.md | 200 |
| https://mrtrauf.github.io/ | 200 |
| https://pathwaylab-rauf.streamlit.app/ | Actual embedded app verified in Chrome on all five before pages; urllib redirect handling failed |
| https://zenodo.org/records/18986229 | 200 |

The descriptor DOI returned HTTP 403 to this checker; the canonical reference
is retained without claiming successful retrieval. Important app/repository/portfolio
links are also checked in real browsers. HTTP success alone does not prove app rendering.
New GitHub documentation paths are verified after their release commit.
