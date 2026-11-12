# Presentation update

The five-section Streamlit app now uses a navy overview banner with a yellow edge,
a four-part research-principles row, shaded load/event control panels, metric cards
with restrained yellow accents, a compact forecast workflow and bordered methods
tabs. Off-white canvas, white plot cards, subtle borders/shadows and system fonts
provide structure. Charts use royal blue, navy, darker gold and neutral supporting
colors. Gold is darker in charts for contrast; yellow remains the identity accent.
No club logo or endorsement is implied.

Implementation changes are limited to presentation.py and demo_dashboard.py.
Calculations, generated observations, temporal splits and the public entrypoint's
synthetic-only guard are unchanged. Both synthetic disclaimers remain visible.

## Actual local verification

- Original workspace: 64 tests passed in 88.39s.
- Updated public fixture suite: 54 tests passed in 17.04s.
- Full Ruff lint and format passed (42 workspace Python files).
- Synthetic CLI, original source checksum verification and isolated ingestion QA passed.
- Google Chrome 157.0.8103.39 / Streamlit 1.67.0: all five pages at 1440, 1280,
  768 and 390 pixels; 20 page cases, 40 interaction checks, 36 genuine captures.
- Tested dropdowns, date windows, model changes, hover tooltips, empty selections,
  methods tabs, tables and mobile navigation. No page errors, page overflow or
  recorded chart-title overruns. Representative desktop/tablet/mobile captures
  were visually inspected. Owned test server stopped.
- Existing safety regressions passed, including public-mode overrides and forbidden
  research-reader spies. Protected research files and scientific functions unchanged.

Selected screenshots under assets/screenshots are genuine synthetic captures of
this update. Detailed logs and all captures remain local. This bounded Chrome
review is not a screen-reader, physical-device or cross-browser certification.

## Delivery

The update is prepared in the separate data-free release repository. It requires
a new push to the hosting branch and the normal Streamlit rebuild/redeploy before
it appears publicly. This update does not claim a live deployment or live-browser
verification. No deployed URL was available in the current task context. No major
UI defect remained in the tested local cases.
