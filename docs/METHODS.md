# Methods and interpretation

PathwayLab has two independent research lanes and a separately generated public
demonstration. There is no shared athlete identity between the GPS and match-event
sources. Neither names nor apparent numeric-ID similarity creates a valid linkage.

## Physical load

The local research adapter verifies original Zenodo bytes, comma-decimal parsing,
Excel dates, coverage and quality flags. Descriptions distinguish observed rows,
players and dates. Repeated observations are not independent athletes. HSR and
other distance variables are reported in metres; acceleration/deceleration fields
are counts under source definitions. Missing duration prevents intensity claims.

Exploratory random-intercept models partition transformed load variation. ICCs
are scale/model dependent, not talent, readiness or physical development. Shared
team dates, serial dependence, heterogeneous residuals and small clusters restrict
inference even when optimization converges.

The real forecast target is the next observed training session's HSR. Features use
strictly earlier player observations. Full-season RATIO* fields, current outcomes
and unverified current status are excluded. Preprocessing fits within training
periods. All players share target-date boundaries; three expanding development
windows support selection before the final holdout. Earlier completed evaluation
observations may update later histories while model parameters remain frozen.

This is conditional retrospective forecasting: target weekday/gap assumes a known
target date. Historical schedule and processing-latency archives are unavailable.
It does not establish prospective scheduling, attendance prediction or coaching utility.

## Match involvement

The independent event lane pins StatsBomb source metadata and verifies file hashes.
It reconstructs estimated event-clock exposure from lineups, substitutions,
dismissals and period endpoints. Rates use 90 × summed counts / summed exposure.
Unused substitutes are not zero-performance appearances; temporary-off time and
missing official minutes limit the exposure estimates.

The original strict timeline policy and a separately labelled receipt-clock
sensitivity are preserved privately. The sensitivity ignores only invalid timing
on unused receipt annotations, without altering raw clocks or counted events.
Coverage and paired findings change under that policy. Neither version demonstrates
player development, maturation or causal improvement. No real result table or
individual record is bundled into the public application.

## Public synthetic demonstration

**SYNTHETIC DEMONSTRATION - NOT REAL PLAYER DATA.**
**SYNTHETIC - DEMONSTRATION ONLY.**

`demo_data.py` generates fictional load and event cohorts independently. Seeds 42
and 43 are fixed; parameters are illustrative and not fitted to professional-player
records. IDs beginning DEMO- and EVENT- belong to different fictional populations.

The load interface reuses the existing synthetic generator. The demo forecast is
the existing next-observed-microcycle benchmark: cumulative non-match HSR in the
next training block, with shared target-block holdout boundaries. Ridge uses fixed
alpha=10 and training-only preprocessing; persistence and training-median baselines
score the same targets. MAE/RMSE are calculated from generated predictions. This
block-level toy score is not the real study's session-level score.

Event counts and minutes are independently simulated. Per-90 values divide by
simulated exposure; historical rates use up to five prior appearances with at least
three required. Current appearances never enter their own historical window.
Peer plots describe distributions, not objective rankings.

## Proposed research and ethics

A possible future MSc study asks whether verified historical exposure and frozen
pre-session plans add predictive value beyond GPS history. It requires approved
matched identities, available-at timestamps, university/club governance and an
adequate archive. No access, supervision, affiliation or collaboration is agreed.
The public-data fallback remains independent and exploratory.

No injury, readiness, youth-potential, medical or causal label is available here.
Pseudonymization is not anonymity or redistribution permission. See
[data rights](../DATA_ACCESS_AND_LICENSE.md) before any external-data use.

## Original references

- Sierra-Casas, Castillo, Clemente and Rodríguez-Fernández (2026),
  [dataset descriptor](https://doi.org/10.3390/data11040084) and
  [Zenodo record](https://zenodo.org/records/18986229).
- [StatsBomb Open Data](https://github.com/hudl/open-data): provider specifications
  and terms; unrelated people to the GPS dataset.
- [PlayerData operational case study](https://playerdata.com/en-gb/blog/smoothing-the-jump-how-brondby-if-builds-players-through-the-academy-pathway)
  and [Keldmann's historical account](https://archive.trainingground.guru/articles/mikkel-keldmann-from-one-intern-to-automated-analysis-at-brondby)
  provide operational context, not independent evidence of predictive effectiveness
  or a current data-access commitment.
