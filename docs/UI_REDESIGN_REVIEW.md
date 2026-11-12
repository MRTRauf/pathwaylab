# Navy redesign review

## Before: verified live application

The native config selected a light base/off-white canvas. CSS set cards to white
and Plotly explicitly used white paper/plot colors. Theme files were present;
the design was not being defeated by a missing config. The previous light-polish
commit was local. A sidebar-only change could not recolor those explicit surfaces.

Community Cloud embeds the app in a frame. The first browser attempt targeted
the hosting wrapper and found a blank body; it was corrected to inspect the
actual app frame. All five live before pages were then captured at all four sizes:
20 cases and 36 genuine captures. Computed metric background was rgb(255,255,255),
sidebar rgb(16,43,82). No successful inspection is inferred from HTTP status alone.

## After: implemented and tested locally

Central tokens: canvas #081B34, sidebar #06162B, surface #102B4A, elevated #173656,
border #2A4966, text #F5F8FC, muted #B9CBDE, analytics blue #4A8AC4 and yellow #F4C542.
Native theme settings were checked against installed Streamlit 1.55 and the fresh
1.67 environment. Scoped CSS controls hierarchy; Plotly is explicitly dark.

All five pages retain calculations/controls. Numbered checked navigation replaces
the one-option public dropdown with a compact status. Overview has a research
hero, computed KPIs and independent lanes. Load controls have reset and dashed
lines without dense markers. Forecasts highlight the selected model. Semantic
tables expose small model/season comparisons as readable text. Event history is
explicitly Prior passes / 90. Methods combine workflow, tabs and technical details.
One persistent disclosure replaces repeated large notices; charts retain source
captions and full synthetic provenance metadata.

Computed after styles: canvas rgb(8,27,52), sidebar rgb(6,22,43), metrics
rgb(23,54,86), title 36px, inputs 16px. Plot paper AND plot backgrounds were
#102B4A in every recorded chart. Body is 16px, metadata 13px, chart labels 14px,
titles 18px, page headings 30px and KPI values 32px.

## Browser evidence

Local Chrome 157 / Streamlit 1.67 on Windows/Python 3.12.10: all five pages at
1440x900, 1280x800, 768x1024 and 390x844. Twenty after cases, forty original
interaction checks and 36 genuine captures. No page errors, document overflow or
recorded chart-title overruns. Both light and dark browser preferences were tested.
Dropdowns, dates, model changes, hover tooltips, empty selections, tables, tabs
and mobile navigation passed. Owned local servers stopped.

Representative desktop, tablet and mobile images were visually inspected.
An early table capture showed a loading placeholder; final captures wait for
actual model labels. Small tables use semantic text rather than a canvas grid.
Additional final live checks include reset and season denominators.
Harness failures (hidden native radio input, chart animation waits and missing
axis offsets for hover) were corrected and repeated; they are not counted as
passing cases. Detailed logs and all captures remain local.

| View | Before | After |
|---|---|---|
| Desktop overview | [Genuine live before](../assets/screenshots/before-overview.png) | [Redesigned overview](../assets/screenshots/overview.png) |
| Mobile overview | [Genuine live before](../assets/screenshots/before-mobile.png) | [Redesigned mobile](../assets/screenshots/mobile.png) |

## Accessibility

Token-pair normal-text contrast checks exceed AA's 4.5:1 target:

| Foreground / background | Contrast |
|---|---|
| #F5F8FC / #081B34 | 16.20:1 |
| #F5F8FC / #173656 | 11.61:1 |
| #B9CBDE / #173656 | 7.45:1 |
| #F5F8FC / #214366 | 9.57:1 |
| #FFE28A / #102B4A | 11.25:1 |

Native checked states/numbers supplement navigation color; dashed load lines and
labels supplement series color. Focus outlines and keyboard control interaction
were checked. Semantic comparison tables improve reading order. This is bounded
Chrome/contrast evidence, not a comprehensive WCAG certification, screen-reader,
Safari/Firefox or physical-device audit.

## Research and delivery boundary

All 233 protected research files and function ASTs in 15 scientific modules remain
unchanged. Public-only access overrides, forbidden-reader spies, calculation and
chronology assertions passed. No real numerical findings are released. The only
CLI reporting change removes obsolete named-organization wording.

README and canonical workflow, architecture, reproduction and dashboard guide were
rewritten against actual paths/interfaces. See [link review](LINK_VALIDATION.md).
Release and anonymous live-after results are appended only after execution.
