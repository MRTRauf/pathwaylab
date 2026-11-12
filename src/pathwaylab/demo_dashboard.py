"""Public-safe five-section interface; every observation is independently synthetic."""

import pandas as pd
import plotly.express as px
import streamlit as st

from .demo_data import (
    EVENT_SOURCE,
    LABEL,
    LOAD_SOURCE,
    PUBLIC_LABEL,
    SEED,
    demo_forecast,
    event_cohort,
    load_cohort,
)
from .eda import NAMES, UNITS
from .presentation import (
    chart,
    footer,
    forecast_workflow,
    module_card,
    research_hero,
    section_intro,
)


@st.cache_data(show_spinner=False)
def demo_bundle() -> tuple:
    """Cache only deterministic generated fixtures and their calculated benchmark."""
    loads = load_cohort()
    scores, predictions, protocol = demo_forecast(loads)
    return loads, event_cohort(), scores, predictions, protocol


def navigate(section: str) -> None:
    st.session_state["research_section"] = section


def render_demo(page: str) -> None:
    st.warning(PUBLIC_LABEL + " · " + LABEL)
    loads, events, scores, predictions, protocol = demo_bundle()
    if page == "Research overview":
        overview(loads, events)
    elif page == "Training load explorer":
        explorer(loads)
    elif page == "Forecasting lab":
        forecasting(scores, predictions, protocol)
    elif page == "Player Performance Trajectories":
        trajectories(events)
    else:
        methods()
    footer()


def overview(loads: pd.DataFrame, events: pd.DataFrame) -> None:
    section_intro(
        "Research overview",
        "Explore physical load, evaluate temporal forecasts, and "
        "describe match involvement. Two independent analysis lanes, with context in view.",
    )
    research_hero()
    st.caption("The figures below describe generated fixtures, not professional football findings.")
    for col, label, value in zip(
        st.columns(4),
        [
            "Fictional load players",
            "Synthetic observations",
            "Simulated matches",
            "Event appearances",
        ],
        [loads.player_id.nunique(), len(loads), events.match_id.nunique(), len(events)],
    ):
        col.metric(label, f"{value:,}")
    st.caption("Independent generated cohorts · load seed 42 · event seed 43")
    st.subheader("Explore the research lanes")
    left, right = st.columns(2)
    with left:
        module_card(
            "01 / PHYSICAL LOAD",
            "Training Load Intelligence",
            "Explore repeated GPS-style observations, context and chronological baselines. "
            "Understand the sample before interpreting a model.",
        )
        st.button(
            "Open training load explorer",
            on_click=navigate,
            args=("Training load explorer",),
            width="stretch",
        )
    with right:
        module_card(
            "02 / MATCH INVOLVEMENT",
            "Player Performance Trajectories",
            "Inspect simulated appearances, exposure-weighted rates and historical windows. "
            "Changes describe involvement, not player development.",
        )
        st.button(
            "Open player trajectories",
            on_click=navigate,
            args=("Player Performance Trajectories",),
            width="stretch",
        )
    st.subheader("From independent inputs to interpretation")
    st.markdown(
        '<div class="pl-flow"><div class="pl-node"><b>01 · Independent inputs</b>'
        "<small>Load observations and event appearances stay in separate cohorts.</small></div>"
        '<div class="pl-node"><b>02 · Auditable methods</b>'
        "<small>Quality checks, explicit exposure, past-only features and "
        "temporal splits.</small></div>"
        '<div class="pl-node"><b>03 · Clear interpretation</b>'
        "<small>Baseline comparisons, coverage and limitations beside the "
        "output.</small></div></div>",
        unsafe_allow_html=True,
    )
    a, b = st.columns([2, 1])
    with a, st.container(border=True):
        profile = (
            loads.loc[loads.md_day.ne(0)].groupby("md_day").HSR.agg(["mean", "size"]).reset_index()
        )
        chart(
            px.bar(
                profile,
                x="md_day",
                y="mean",
                hover_data=["size"],
                labels={
                    "md_day": "Synthetic day offset",
                    "mean": "Mean HSR (m)",
                    "size": "Observations",
                },
                title="Synthetic training profile",
            ),
            LOAD_SOURCE,
        )
    with b:
        st.markdown("### What this demonstrates")
        st.write(
            "Data engineering, repeated-measures thinking, temporal evaluation and research "
            "communication in a reproducible Python project."
        )
        st.info(
            "The real research uses separate public GPS and event populations. Those files, "
            "individual results and real-data metrics are not bundled here."
        )


def reset_load_filters() -> None:
    """Restore the generated cohort's default observation window and selections."""
    for key in ("load_metric", "load_positions", "load_dates", "load_players"):
        st.session_state.pop(key, None)


def explorer(loads: pd.DataFrame) -> None:
    section_intro(
        "Training load explorer",
        "Follow fictional players through a simulated season. "
        "Use the filters to distinguish coverage from load variation.",
    )
    training = loads.loc[loads.md_day.ne(0)]
    with st.container(border=True, key="load_controls"):
        st.markdown("#### Observation controls")
        st.caption("Choose fictional players, a physical measure and an observation window.")
        controls = st.columns([1.2, 1.2, 2])
        with controls[0]:
            metric = st.selectbox(
                "Physical-load measure",
                list(NAMES),
                index=1,
                key="load_metric",
                format_func=lambda k: f"{NAMES[k]} ({UNITS[k]})",
            )
        with controls[1]:
            positions = st.multiselect(
                "Fictional positions",
                sorted(training.position.unique()),
                default=sorted(training.position.unique()),
                key="load_positions",
            )
        with controls[2]:
            dates = st.date_input(
                "Date range",
                (training.date.min().date(), training.date.max().date()),
                key="load_dates",
            )
        players = st.multiselect(
            "Fictional load players",
            sorted(training.player_id.unique()),
            default=sorted(training.player_id.unique())[:4],
            key="load_players",
        )
        st.button("Reset filters", on_click=reset_load_filters)
    if len(dates) != 2:
        st.info("Choose a start and end date to display the observation window.")
        return
    view = training.loc[
        training.player_id.isin(players)
        & training.position.isin(positions)
        & training.date.between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]))
    ]
    if view.empty:
        st.info(
            "No observations match these filters. Select a player, position and wider date range."
        )
        return
    a, b, c = st.columns(3)
    a.metric("Selected observations", f"{len(view):,}")
    b.metric("Fictional players", str(view.player_id.nunique()))
    c.metric(f"Mean {metric}", f"{view[metric].mean():,.1f} {UNITS[metric]}")
    st.caption(
        "Synthetic load fixture · non-match rows · repeated observations, not independent athletes"
    )
    labels = {
        "date": "Observation date",
        metric: f"{NAMES[metric]} ({UNITS[metric]})",
        "player_id": "Fictional player",
        "position": "Fictional position",
    }
    with st.container(border=True):
        chart(
            px.line(
                view,
                x="date",
                y=metric,
                color="player_id",
                markers=False,
                line_dash="player_id",
                hover_data=["position", "md_day"],
                labels=labels,
                title="Load over time",
            ),
            LOAD_SOURCE,
        )
    left, right = st.columns(2)
    with left, st.container(border=True):
        chart(
            px.box(
                view,
                x="player_id",
                y=metric,
                color="player_id",
                labels=labels,
                title="Within-player distribution",
            ),
            LOAD_SOURCE,
        )
    with right, st.container(border=True):
        day = view.groupby("md_day")[metric].agg(["mean", "count"]).reset_index()
        chart(
            px.bar(
                day,
                x="md_day",
                y="mean",
                hover_data=["count"],
                labels={"md_day": "Synthetic day offset", "mean": labels[metric]},
                title="Recorded-day context",
            ),
            LOAD_SOURCE,
        )
    st.caption(
        "Raw load is not duration-adjusted intensity. The generator defines these codes; "
        "the unrelated real dataset has additional coding and exposure uncertainty."
    )


def forecasting(scores: pd.DataFrame, predictions: pd.DataFrame, protocol: dict) -> None:
    section_intro(
        "Forecasting lab",
        "Compare calculated synthetic forecasts on identical temporal "
        "holdout targets. Lower error means closer predictions in this toy example.",
    )
    forecast_workflow()
    st.info(
        "Demo target: the next observed training block's cumulative HSR (synthetic microcycle). "
        "The separate real research targets one observed session; these metrics are not comparable."
    )
    st.caption("Synthetic block-level forecast · generated observations only")
    with st.container(border=True, key="model_controls"):
        chosen = st.selectbox("Demonstration model", list(scores.Model))
    row = scores.loc[scores.Model.eq(chosen)].iloc[0]
    a, b, c = st.columns(3)
    a.metric("Synthetic MAE", f"{row['MAE (m)']:.1f} m")
    b.metric("Synthetic RMSE", f"{row['RMSE (m)']:.1f} m")
    c.metric("Synthetic holdout targets", str(int(row.Targets)))
    st.caption(
        "MAE is mean absolute prediction error; RMSE gives larger errors more weight. "
        "Both use metres of cumulative synthetic training-block HSR."
    )
    left, right = st.columns(2)
    with left, st.container(border=True):
        chart(
            px.bar(
                scores,
                x="Model",
                y="MAE (m)",
                color="Model",
                color_discrete_map={
                    name: "#F4C542" if name == chosen else "#4A8AC4" for name in scores.Model
                },
                title="Synthetic model errors",
            ),
            LOAD_SOURCE,
        )
    with right:
        st.markdown("#### Temporal evaluation")
        st.write(
            f"Training targets: blocks {min(protocol['train_target_microcycles'])}–"
            f"{max(protocol['train_target_microcycles'])}. Holdout: blocks "
            f"{min(protocol['test_target_microcycles'])}–{max(protocol['test_target_microcycles'])}."
        )
        st.write(
            "All players share a target-block cutoff. Preprocessing fits training data only. "
            "Ridge uses fixed alpha=10; this demonstration does not tune on the holdout."
        )
        st.table(
            scores.set_index("Model").style.format(
                {"MAE (m)": "{:.1f}", "RMSE (m)": "{:.1f}", "Targets": "{:.0f}"}
            ),
        )
    view = predictions.loc[predictions.model.eq(chosen)]
    left, right = st.columns(2)
    with left, st.container(border=True):
        fig = px.scatter(
            view,
            x="next_train_hsr",
            y="prediction_m",
            color="position",
            hover_data=["player_id", "next_microcycle"],
            labels={
                "next_train_hsr": "Observed toy HSR (m)",
                "prediction_m": "Predicted toy HSR (m)",
                "position": "Position",
            },
            title="Observed and predicted",
        )
        limit = float(max(view.next_train_hsr.max(), view.prediction_m.max()))
        fig.add_shape(
            type="line", x0=0, y0=0, x1=limit, y1=limit, line={"color": "#8695A8", "dash": "dot"}
        )
        chart(fig, LOAD_SOURCE)
    with right, st.container(border=True):
        chart(
            px.histogram(
                view,
                x="error_m",
                nbins=22,
                labels={"error_m": "Prediction minus observation (m)"},
                title="Where the errors fall",
            ),
            LOAD_SOURCE,
        )
    st.caption(
        "A better toy score does not validate coaching utility. The audited real study is "
        "conditional retrospective forecasting with an assumed known target date, small "
        "dependent samples and unverified prospective processing latency."
    )


def trajectories(events: pd.DataFrame) -> None:
    section_intro(
        "Player Performance Trajectories",
        "Describe involvement across simulated "
        "appearances. Keep exposure and sample size beside each comparison.",
    )
    st.caption("Synthetic EVENT IDs · independent of the load-demo cohort")
    with st.container(border=True, key="event_controls"):
        st.markdown("#### Comparison controls")
        st.caption("Select a fictional player and seasons. Rates always retain simulated exposure.")
        columns = st.columns([1.2, 1.6, 1])
        with columns[0]:
            player = st.selectbox("Fictional event player", sorted(events.player_id.unique()))
        with columns[1]:
            seasons = st.multiselect(
                "Demo seasons",
                sorted(events.season.unique()),
                default=sorted(events.season.unique()),
            )
        with columns[2]:
            metric = st.selectbox(
                "Event measure", ["passes", "shots", "carries", "tackles", "interceptions"]
            )
    cohort = events.loc[events.season.isin(seasons)]
    view = cohort.loc[cohort.player_id.eq(player)]
    if view.empty:
        st.info("Select at least one demo season to display appearances.")
        return
    a, b, c = st.columns(3)
    a.metric("Simulated appearances", str(len(view)))
    b.metric("Simulated minutes", f"{view.minutes.sum():,.0f}")
    c.metric(f"{metric.title()} / 90", f"{90 * view[metric].sum() / view.minutes.sum():.1f}")
    st.caption(
        "Rate = 90 × total actions / total simulated minutes. No real event clocks or "
        "official minutes are used; exposure is independently simulated."
    )
    with st.container(border=True):
        chart(
            px.scatter(
                view,
                x="date",
                y=metric + "_per90",
                color="season",
                hover_data=["minutes", "position"],
                labels={
                    "date": "Simulated match date",
                    metric + "_per90": f"{metric.title()} / 90 simulated min",
                    "season": "Demo season",
                },
                title="Observed demo involvement",
            ),
            EVENT_SOURCE,
        )
    left, right = st.columns(2)
    with left, st.container(border=True):
        chart(
            px.line(
                view,
                x="date",
                y="prior_passes_per90",
                markers=True,
                labels={"date": "Simulated match date", "prior_passes_per90": "Prior passes / 90"},
                title="Prior passes / 90",
            ),
            EVENT_SOURCE,
        )
        st.caption(
            "Exposure-weighted up to five previous appearances; at least three required. "
            "The current appearance never contributes to its historical window."
        )
    with right, st.container(border=True):
        peers = cohort.loc[cohort.position.eq(view.position.iloc[0])]
        chart(
            px.box(
                peers,
                x="season",
                y=metric + "_per90",
                color="season",
                labels={"season": "Demo season", metric + "_per90": f"{metric.title()} / 90"},
                title=f"{view.position.iloc[0]} context",
            ),
            EVENT_SOURCE,
        )
        st.caption(
            f"{peers.player_id.nunique()} fictional peers, including the selected player. "
            "This is a distribution, not a quality ranking."
        )
    season = view.groupby("season").agg(
        appearances=("match_id", "nunique"), minutes=("minutes", "sum"), actions=(metric, "sum")
    )
    season["actions / 90"] = 90 * season.actions / season.minutes
    with st.expander("Season denominators and rates"):
        st.table(season.round(1))
    st.warning(
        "Variation in involvement is not proof of development. In the real study, season "
        "coverage and the timestamp inclusion rule change paired findings. Both real "
        "analyses remain private and are not loaded here."
    )


def methods() -> None:
    section_intro(
        "Methods and limitations",
        "A useful research interface makes its assumptions as visible as its charts.",
    )
    tabs = st.tabs(["Research design", "Data boundaries", "Reproduce"])
    with tabs[0], st.container(border=True):
        forecast_workflow()
        st.markdown(
            "[End-to-end workflow](https://github.com/MRTRauf/pathwaylab/blob/main/docs/WORKFLOW.md)"
        )
        with st.expander("Longitudinal statistics and event methodology"):
            st.write(
                "The separate local load pipeline uses repeated-measures models and diagnostics. "
                "The event pipeline validates lineups, reconstructs estimated playing exposure, "
                "builds player-match rates and compares inclusion sensitivities. "
                "Public event minutes are simulated; the two populations are never joined."
            )
        st.markdown("### Three questions")
        st.write(
            "How does physical load vary within players? Do historical features forecast "
            "later observed load beyond simple baselines? How do match-involvement rates "
            "change with exposure and coverage?"
        )
        st.markdown("### Principles carried through the project")
        st.markdown(
            "- Repeated observations are not independent athletes.\n"
            "- Preprocessing and selection belong inside development periods.\n"
            "- Future-normalized fields and current outcomes do not enter predictors.\n"
            "- Compare models on identical targets and retain negative findings.\n"
            "- No causal, injury, readiness or potential claims follow from these data."
        )
        st.info(
            "Future thesis proposal: test the incremental value of verified prior exposure "
            "and frozen pre-session plans. It requires approved matched data and governance; "
            "it has not been conducted."
        )
    with tabs[1], st.container(border=True):
        st.markdown("### Public demonstration")
        st.write(
            f"Independent deterministic generators, seeds {SEED} and {SEED + 1}. Load and "
            "event players are separate fictional populations. Values are not copied from "
            "professional players. Demo calculations are not research findings."
        )
        st.markdown("### Separate local research")
        st.markdown(
            "[Zenodo GPS record](https://zenodo.org/records/18986229) and "
            "[StatsBomb Open Data](https://github.com/hudl/open-data) provide the independent "
            "original research lanes. Their records, predictions and data-derived images "
            "are excluded from this public demo."
        )
        st.write(
            "The GPS study has ambiguous coding, limited exposure metadata and a small "
            "single-team sample. Forecasting assumes a known target date. Event exposure "
            "is estimated and the paired result is sensitive to inclusion policy. Neither "
            "dataset measures academy development or causal training effects."
        )
        st.caption(
            "Source methods: Sierra-Casas et al. (2026), doi:10.3390/data11040084; "
            "StatsBomb Open Data specifications. No club affiliation or endorsement."
        )
    with tabs[2], st.container(border=True):
        st.code(
            "python -m pip install -e '.[dev,app,research]'\n"
            "pytest -q -m 'not integration'\npython -m pathwaylab.cli --mode demo\n"
            "python -m streamlit run app/public_demo.py",
            language="bash",
        )
        st.write(
            "The public app reads no research files and requires no credentials. "
            "Research access is trusted local configuration, not a public control. "
            "Data rights, publication permissions and code licensing are separate."
        )
