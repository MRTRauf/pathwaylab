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
validated scientific modules remain unchanged. Hosted CI and actual desktop/mobile
live results are recorded after execution.
