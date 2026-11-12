# Repository-source deployment fix

The redesign was present in GitHub and CI passed, but live computed styles combined
the new native theme with legacy white cards, old sidebar styling and older title
sizes. Config and imported presentation code were therefore inconsistent.

Root requirements.txt installed the local package as a regular wheel using .[app].
In a controlled installed-package experiment, isolated Python resolved presentation
from the environment's site-packages copy. Installing the same project editably
resolved it from src/pathwaylab/presentation.py instead, including outside the
repository working directory.

The minimal correction is **-e .[app]** in requirements.txt. This makes repository
source the installed runtime source and changes the dependency file so Community
Cloud rebuilds the environment. No sys.path insertion, PYTHONPATH override,
scientific change, CSS redesign or manual cache deletion is introduced.
The prior live symptom and installation experiment support stale installed
package code as the cause; the private Cloud interpreter was not introspected.

The regression test runs app/public_demo.py in isolated Python from another
directory, with no pytest/PYTHONPATH source assistance. It checks the resolved
presentation path, navy token and synthetic-only public status. It must run in a
complete installed development environment; a global environment whose dependencies
exist only in user-site is insufficient for Python's isolated mode.

The complete installed development environment passed 11 relevant regressions
and all 65 full tests. Offline testing passed 55 tests with ten private integration
checks deselected. Full Ruff lint and formatting passed. The public entrypoint and
validated scientific modules remain unchanged. Hosted [CI passed](https://github.com/MRTRauf/pathwaylab/actions/runs/43169158005):
55 offline tests, full style checks, dependency/import checks, demo and wheel build.

## Actual live verification

Runtime correction 11809fa was pushed to the existing main branch. Fresh anonymous
Chrome sessions inspected the actual embedded app at
https://pathwaylab-rauf.streamlit.app/ on 1440x900 desktop and 390x844 mobile.
All five pages passed in both sizes: 10 completed page cases, 23 interaction checks
and 18 genuine captures. No page errors, document overflow or recorded title clipping.
Desktop pointer hover, navigation, filters, dates, reset, model results, tables,
empty states and methods tabs were checked; mobile checked the applicable controls.

Computed main background was rgb(8,27,52), sidebar rgb(6,22,43), KPI cards
rgb(23,54,86), and every recorded plot/paper background was #102B4A. Typography,
yellow accents and synthetic-only status matched the completed design. Genuine
desktop/mobile images were visually compared with the prior white-card deployment.
No stale white presentation panels remained.

Earlier local browser helpers supplied PYTHONPATH, which masked installed-wheel
resolution. The new isolated regression and installed-app smoke remove that help.
The corrected live rendering after the packaging change confirms the operational
fix; no redesign or scientific recalculation was needed.
