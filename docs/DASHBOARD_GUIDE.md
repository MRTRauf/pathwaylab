# Five-minute dashboard guide

The public app is **SYNTHETIC DEMONSTRATION - NOT REAL PLAYER DATA**. All values
come from independent generated cohorts. One persistent disclosure applies to every
page; chart provenance remains available.

## Research Overview — first minute

Read the two research lanes. Cards count fictional load players, generated load
observations, simulated matches and event appearances, computed from fixtures.
Use either module button. The workflow/principles explain reproducibility,
temporal validation and interpretation limits. DEMO and EVENT people are unrelated.

## Training Load Explorer — second minute

Choose a distance/count measure, positions, players and dates in the control panel.
Reset filters restores defaults. Empty selections produce a useful message.
Cards show filtered rows, distinct fictional players and row mean in the selected unit.
The line chart shows observations over time; select fewer players or shorter dates
to inspect detail. Dash styles supplement series colors. Distribution/day-context
plots summarize the same selected rows. Distances are metres; accelerations and
decelerations are counts. Volume is not duration-adjusted intensity; repeated rows
are not independent athletes.

## Forecasting Lab — third minute

Choose Ridge, Last block or Training median. MAE is mean absolute error; RMSE
weights larger errors. Both are metres of cumulative next-observed-block HSR.
Holdout observations counts evaluated synthetic targets. The selected model is
yellow, alternatives blue and labelled. Observed/predicted points, an equality
line, error histogram and table show identical targets. All players share the
target-block cutoff; preprocessing fits training only. Fixed Ridge alpha is not
tuned on holdout. This toy task is distinct from real next-session research and
does not establish prospective utility.

## Player Performance Trajectories — fourth minute

Select EVENT player, seasons and measure. Cards show appearances, simulated minutes
and 90 × total actions / total simulated minutes. The main chart separates seasons;
peer distributions condition on fictional position, not quality rankings.
The **Prior passes / 90** chart always describes passes even when the event selector
shows shots. It uses up to five previous appearances with at least three required,
weighted by exposure. Current observations do not enter their own history.
The season expander exposes denominators/rates. Simulated minutes are not official
minutes; small samples, coverage and roles prevent development/causal claims.

## Methods and Limitations — fifth minute

Research design explains questions, temporal workflow and independent statistical/
event methods. Expand technical context. Data boundaries explains generators,
original sources and exclusions. Reproduce provides executable public commands.
For detail, read [workflow](WORKFLOW.md), [methods](METHODS.md),
[architecture](ARCHITECTURE.md) and [reproduction](../REPRODUCIBILITY.md).
Keyboard focus, numbered navigation and native checked states accompany color
accents. No public control grants local research access.
