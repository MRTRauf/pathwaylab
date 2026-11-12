"""Local read-only research viewer. No model fitting or synthetic substitution."""

import os
from pathlib import Path

import plotly.express as px
import streamlit as st

from pathwaylab.dashboard_data import (
    CAUTION,
    ROOT,
    SOURCE,
    filter_training,
    load_research,
    revision,
)
from pathwaylab.eda import NAMES, UNITS
from pathwaylab.presentation import apply_theme, sidebar_brand
from pathwaylab.presentation import chart as styled_chart

st.set_page_config(
    page_title="PathwayLab - Football Data Science & Performance Analytics", layout="wide"
)
apply_theme()
sidebar_brand()
st.title("PathwayLab")
st.caption("Football Data Science & Performance Analytics")
data_modes = ["Synthetic demonstration"]
local_research_enabled = (
    os.environ.get("PATHWAYLAB_ENABLE_LOCAL_RESEARCH") == "1"
    and os.environ.get("PATHWAYLAB_PUBLIC_DEMO") != "1"
)
if local_research_enabled:
    data_modes.append("Verified local research")
if local_research_enabled:
    mode = st.sidebar.selectbox("Data mode", data_modes)
else:
    mode = "Synthetic demonstration"
    st.sidebar.markdown(
        '<div class="pl-status"><b>DEMO DATA</b><span>Synthetic only</span></div>',
        unsafe_allow_html=True,
    )
page = st.sidebar.radio(
    "Research sections",
    [
        "Research overview",
        "Training load explorer",
        "Forecasting lab",
        "Player Performance Trajectories",
        "Methods and limitations",
    ],
    key="research_section",
    format_func=lambda value: {
        "Research overview": "01 Research overview",
        "Training load explorer": "02 Training load explorer",
        "Forecasting lab": "03 Forecasting lab",
        "Player Performance Trajectories": "04 Player Performance Trajectories",
        "Methods and limitations": "05 Methods and limitations",
    }[value],
)
st.sidebar.caption(
    "Independent synthetic demonstration. No real player records loaded."
    if not local_research_enabled
    else "Private research viewer. No automatic research fitting or uploads."
)
st.sidebar.markdown(
    "[GitHub](https://github.com/MRTRauf/pathwaylab) · "
    "[Documentation](https://github.com/MRTRauf/pathwaylab/blob/main/docs/WORKFLOW.md) · "
    "[Portfolio](https://mrtrauf.github.io/)"
)
if not local_research_enabled or mode != "Verified local research":
    from pathwaylab.demo_dashboard import render_demo

    render_demo(page)
    st.stop()
if page == "Player Performance Trajectories":
    from pathwaylab.event_dashboard import render_events

    render_events(ROOT)
    st.stop()
st.info(SOURCE)
st.warning(CAUTION)


@st.cache_data(show_spinner=False)
def cached(root: str, version: tuple):
    return load_research(Path(root))


try:
    b = cached(str(ROOT), revision(ROOT))
except ValueError as exc:
    st.error(str(exc))
    st.stop()
d, meta = b["data"], b["metadata"]
test = b["predictions"].loc[lambda x: x.fold.eq("test")]
final = b["scores"].loc[lambda x: x.fold.eq("test")]
chosen = meta["chosen_ml"]


def chart(fig):
    styled_chart(fig, SOURCE)


if page == "Research overview":
    st.header("Research overview")
    for col, label, value in zip(
        st.columns(5),
        [
            "Source observations",
            "Players",
            "Training observations",
            "Forecast targets",
            "Final test observations",
        ],
        [
            len(d),
            d.player_id.nunique(),
            int(d.md_day.ne(0).sum()),
            meta["primary_rows"],
            len(test.loc[test.model.eq(chosen)]),
        ],
    ):
        col.metric(label, str(value))
    st.subheader("Can past training loads forecast the next observed session’s HSR?")
    st.write(
        "Single-team, single-season observational study. Strictly historical "
        "features, global target-date cutoffs and three expanding validation "
        "windows."
    )
    row = final.loc[final.model.eq(chosen)].iloc[0]
    base = (
        final.loc[final.model.isin(["global_median", "last_hsr", "rolling_mean"])]
        .sort_values("mae_m")
        .iloc[0]
    )
    st.metric(f"Validation-selected {chosen} · holdout MAE", f"{row.mae_m:.6f} m")
    st.write(
        "MAE means average absolute prediction error in metres. MAE is "
        f"{100 * (base.mae_m - row.mae_m) / base.mae_m:.2f}% lower than the strongest "
        f"evaluated holdout baseline ({base.model}) in this period."
    )
    chart(
        px.bar(
            final,
            x="model",
            y="mae_m",
            labels={"mae_m": "Holdout MAE (m)"},
            title="Historical baselines and ML · same holdout observations",
        )
    )
    st.caption(
        "Selected using validation data. Final holdout was not used for "
        "selection. Not prospective deployment evidence."
    )
    st.markdown(
        "[Zenodo v1 · DOI "
        "10.5281/zenodo.18986229](https://doi.org/10.5281/zenodo.18986229). "
        "Creator: Alejandro Rodríguez-Fernández. Source and saved artifact "
        "checksums verified."
    )
elif page == "Training load explorer":
    st.header("Training load explorer")
    st.caption(
        "DIA 0 excluded. Original day/position codes retained; meanings incompletely documented."
    )
    metric = st.selectbox("Physical-load measure", list(NAMES), index=1)
    players = st.multiselect(
        "Anonymous players", sorted(d.player_id.unique()), default=sorted(d.player_id.unique())
    )
    positions = st.multiselect(
        "Original position codes", sorted(d.position.unique()), default=sorted(d.position.unique())
    )
    dates = st.date_input("Date range", value=(d.date.min().date(), d.date.max().date()))
    day_values = sorted(d.loc[d.md_day.ne(0), "md_day"].unique())
    days = st.multiselect("Recorded day codes", day_values, default=day_values)
    if len(dates) != 2:
        st.info("Select both endpoints.")
        st.stop()
    view = filter_training(d, players, positions, *dates, days)
    st.write(
        f"{len(view)} observations · {view.player_id.nunique()} players · "
        f"{view[metric].isna().sum()} missing values · unit: {UNITS[metric]}"
    )
    st.caption(
        "Repeated measurements; unequal exposure/coverage. Filters only change "
        "this explorer, never holdout claims. Raw load is not intensity, "
        "fatigue or readiness."
    )
    if view.empty:
        st.info("No observations match these filters. Widen the selection.")
    else:
        labels = {metric: f"{NAMES[metric]} ({UNITS[metric]})"}
        chart(
            px.scatter(
                view,
                x="date",
                y=metric,
                color="player_id",
                labels=labels,
                title="Individual observations in calendar time",
            )
        )
        chart(
            px.box(
                view,
                x="player_id",
                y=metric,
                labels=labels,
                title="Observed distributions across players",
            )
        )
        day = view.groupby("md_day")[metric].agg(["mean", "count"]).reset_index()
        chart(
            px.bar(
                day,
                x="md_day",
                y="mean",
                text="count",
                labels={"mean": labels[metric]},
                title="Recorded-day profile · valid row counts",
            )
        )
        sd = view.groupby("player_id")[metric].agg(["std", "count"]).reset_index()
        chart(
            px.bar(
                sd,
                x="player_id",
                y="std",
                text="count",
                labels={"std": f"Sample SD ({UNITS[metric]})"},
                title="Within-player variability · selected day mixture",
            )
        )
        chart(
            px.box(
                view,
                x="position",
                y=metric,
                labels=labels,
                title="Original position codes · unadjusted distributions",
            )
        )
elif page == "Forecasting lab":
    st.header("Forecasting lab")
    period = b["splits"].loc[lambda x: x.fold.eq("test") & x.role.eq("evaluation")].iloc[0]
    st.write(
        f"Final test: {period.start}–{period.end} · {period.n} targets · "
        f"{period.players} players · {period.dates} dates."
    )
    st.caption(
        f"{chosen}: selected using validation data. Final holdout was not used for selection. "
        "Frozen models; earlier completed sessions may update later histories."
    )
    st.dataframe(final[["model", "n", "mae_m", "rmse_m", "median_ae_m", "bias_m"]], hide_index=True)
    names = sorted(test.model.unique())
    model = st.selectbox("Saved model predictions", names, index=names.index(chosen))
    view = test.loc[test.model.eq(model)].copy()
    row = final.loc[final.model.eq(model)].iloc[0]
    a, c = st.columns(2)
    a.metric(f"{model} · holdout MAE", f"{row.mae_m:.6f} m")
    c.metric(f"{model} · holdout RMSE", f"{row.rmse_m:.6f} m")
    chart(
        px.scatter(
            view,
            x="target_hsr",
            y="prediction_m",
            labels={"target_hsr": "Observed HSR (m)", "prediction_m": "Predicted HSR (m)"},
            title=f"{model} · saved final-test predictions",
        )
    )
    view["error_m"] = view.prediction_m - view.target_hsr
    chart(
        px.histogram(
            view,
            x="error_m",
            labels={"error_m": "Prediction minus observation (m)"},
            title="Signed prediction errors",
        )
    )
    daily = view.groupby("date").error_m.apply(lambda s: s.abs().mean()).reset_index(name="MAE (m)")
    chart(px.line(daily, x="date", y="MAE (m)", title="Time-ordered date-level errors"))
    groups = (
        view.groupby("player_id")
        .error_m.agg(n="size", mae_m=lambda s: s.abs().mean())
        .reset_index()
    )
    chart(
        px.bar(
            groups,
            x="player_id",
            y="mae_m",
            text="n",
            labels={"mae_m": "MAE (m)"},
            title="Player errors · observation counts",
        )
    )
    with st.expander("Development validation performance · used for selection"):
        st.dataframe(b["scores"].loc[lambda x: ~x.fold.eq("test")], hide_index=True)
    st.caption(
        "No predictive intervals. Unequal repeated observations; subgroup "
        "errors are not new generalization claims. Validation-only sensitivity "
        "tables are in the research report."
    )
else:
    st.header("Methods and limitations")
    st.success(
        "Original CSV/dictionary MD5 and EDA/inference/forecast artifact SHA-256 checks passed."
    )
    st.write(
        "DIA 0 is source-consistent with match rows, not independently "
        "verified. T/S meanings remain unknown. There are 31 observed cycle "
        "IDs versus 30 published. No session duration or playing minutes; raw "
        "loads are not intensity."
    )
    st.write(
        "Training-only preprocessing; shifted histories; global date cutoffs "
        "and reserved final test. Baselines: training median, last HSR and "
        "rolling mean, with training-median fallback. Ridge and constrained "
        "histogram gradient boosting; no fitting in this app."
    )
    st.dataframe(b["availability"], hide_index=True)
    st.subheader("Longitudinal random-intercept models")
    st.dataframe(
        b["models"].loc[
            lambda x: x.model.str.startswith("M"), ["model", "n", "players", "icc", "converged"]
        ],
        hide_index=True,
    )
    st.write(
        "ICC is model/scale dependent, not an inherent player trait. Heavy "
        "tails, heteroscedasticity, shared team dates, temporal dependence and "
        "only 20 players limit inference. One team/season does not establish "
        "generalization or coaching utility."
    )
    st.write(
        "Publication: Sierra-Casas, Castillo, Clemente and Rodríguez-Fernández "
        "(2026), Data 11(4), 84, DOI 10.3390/data11040084. Original access: "
        "2026-11-12. Paper states dataset CC BY 4.0; record Rights text was "
        "blank. Anonymization alone does not grant redistribution rights. Raw "
        "and individual/prediction artifacts stay local and gitignored pending "
        "review. No uploads/download exports. Unlinked public datasets must "
        "not be joined by player identity."
    )
    reports = [
        "REAL_DATA_AUDIT.md",
        "EDA_FINDINGS.md",
        "STATISTICAL_ANALYSIS_PLAN.md",
        "LONGITUDINAL_FINDINGS.md",
        "FORECASTING_PROTOCOL.md",
        "FORECASTING_FINDINGS.md",
    ]
    report = st.selectbox("Local research document", reports, index=4)
    with st.expander(f"Read research/{report}"):
        path = ROOT / "research" / report
        if path.exists():
            st.code(path.read_text(encoding="utf-8"), language="markdown")
        else:
            st.info("Document unavailable in this checkout.")
    st.code(
        "python -m pip install -e '.[app,dev,research]'\npython "
        "scripts/download_zenodo.py --with-dictionary\npython -m pathwaylab.cli "
        "--mode eda\npython scripts/run_inference.py\npython -m pathwaylab.cli "
        "--mode forecast\npython -m streamlit run app/streamlit_app.py "
        "--server.address 127.0.0.1"
    )
