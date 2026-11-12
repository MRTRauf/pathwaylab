"""Independent saved StatsBomb artifacts; no GPS loading or identity joins."""

import hashlib
import json
from pathlib import Path

import pandas as pd


def load_event_artifacts(directory: Path) -> tuple[pd.DataFrame, dict]:
    manifest = json.loads((directory / "manifest.json").read_text())
    for name, digest in manifest.items():
        path = (directory / name).resolve()
        if (
            not path.is_relative_to(directory.resolve())
            or hashlib.sha256(path.read_bytes()).hexdigest() != digest
        ):
            raise ValueError("Event artifact checksum mismatch")
    panel = pd.read_csv(directory / "player_match.csv", parse_dates=["match_date"])
    if not {"player_id", "match_id", "match_date", "minutes", "source", "season_name"}.issubset(
        panel
    ):
        raise ValueError("Invalid event panel schema")
    if not panel.source.str.startswith("StatsBomb Open Data").all():
        raise ValueError("Independent StatsBomb source label required")
    return panel, json.loads((directory / "summary.json").read_text())


def render_events(root: Path) -> None:
    import plotly.express as px
    import streamlit as st

    from .events import METRICS, SOURCE
    from .presentation import chart

    st.header("Player Performance Trajectories")
    st.info("StatsBomb Open Data · independent WSL population · no GPS linkage")
    st.warning(
        "Observed match involvement, not academy/physical development. "
        "Estimated event-clock minutes; incomplete selected-team coverage. "
        "Local research only."
    )
    try:
        panel, summary = load_event_artifacts(root / "outputs/events")
    except (OSError, ValueError) as exc:
        st.error(
            f"Event artifacts unavailable: {exc}. "
            "Run python scripts/run_events.py discover, download, analyze."
        )
        return
    for column, label, field in zip(
        st.columns(4),
        ["Retained matches", "Observed players", "Appearances", "Source exclusions"],
        ["valid_matches", "primary_players", "primary_appearances", "excluded_matches"],
    ):
        column.metric(label, str(summary[field]))
    with st.expander("Source and technical audit details"):
        st.write(summary)
    st.caption(
        "This viewer retains the strict Phase 06 exclusions. A separate Phase 09 "
        "receipt-clock sensitivity changes coverage and paired rates; it is not "
        "loaded here. Treat the original paired finding as sensitive to exclusions."
    )
    seasons = st.multiselect(
        "Observed seasons",
        sorted(panel.season_name.unique()),
        default=sorted(panel.season_name.unique()),
    )
    season_panel = panel.loc[panel.season_name.isin(seasons)]
    if season_panel.empty:
        st.info("Select at least one season.")
        return
    ids = sorted(season_panel.player_id.unique())
    names = season_panel.drop_duplicates("player_id").set_index("player_id").player_name.to_dict()
    player = st.selectbox("StatsBomb player ID", ids, format_func=lambda p: f"{names[p]} ({p})")
    metric = st.selectbox("Event metric per 90 estimated minutes", METRICS)
    view = season_panel.loc[season_panel.player_id.eq(player)].sort_values("match_date")
    st.caption(
        f"{len(view)} appearances, {view.minutes.sum():.1f} estimated minutes. "
        ">=30-minute observations only; zeros are observed actions, not non-appearances."
    )
    chart(
        px.scatter(
            view,
            x="match_date",
            y=metric + "_per90",
            color="season_name",
            labels={"match_date": "Match date", metric + "_per90": f"{metric} / 90 est. min"},
            title="Observed involvement",
        ),
        SOURCE,
    )
    chart(
        px.scatter(
            view,
            x="match_date",
            y="prior_passes_per90",
            color="season_name",
            labels={"match_date": "Match date", "prior_passes_per90": "Prior passes / 90"},
            title="Prior-appearance window",
        ),
        SOURCE,
    )
    position = st.selectbox(
        "Initial source position for context", sorted(season_panel.position.unique())
    )
    peer = season_panel.loc[season_panel.position.eq(position)]
    st.caption(
        f"Position context: {peer.player_id.nunique()} players, {len(peer)} appearances. "
        "Initial role can change; not objective quality rankings."
    )
    if peer.player_id.nunique() >= 4:
        chart(
            px.box(
                peer,
                x="season_name",
                y=metric + "_per90",
                labels={"season_name": "Observed season", metric + "_per90": f"{metric} / 90"},
                title="Initial-position context",
            ),
            SOURCE,
        )
    else:
        st.info("Too few peers for a benchmark (minimum four contributing players).")
    st.caption(
        SOURCE + ". Season/team/opponent effects, selection, survivorship and missing "
        "coverage confound apparent trends. No prospective deployment or "
        "causal interpretation."
    )
