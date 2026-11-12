"""Shared data-free presentation for the existing Streamlit research viewer."""

from html import escape

import plotly.graph_objects as go
import streamlit as st

NAVY = "#102B52"
BLUE = "#2B65A0"
YELLOW = "#F4C542"
CANVAS = "#F7F8FA"
SLATE = "#526173"


def apply_theme() -> None:
    """Use system fonts and restrained responsive styling, with no remote assets."""
    st.markdown(
        """<style>
    .stApp {background:#F7F8FA;}
    [data-testid="stMain"] {background:#F7F8FA;}
    [data-testid="stButton"] button {border-radius:8px;font-weight:600;}
    [data-testid="stButton"] button:hover {border-color:#2B65A0;color:#102B52;}
    .st-key-load_controls,.st-key-event_controls {
      background:#EDF2F8!important;border-top:3px solid #2B65A0!important;
      border-radius:12px;padding:20px!important;margin:12px 0 22px;}
    .pl-hero {background:#102B52;border-left:5px solid #F4C542;border-radius:12px;
      padding:28px 30px;margin:12px 0 24px;color:#F7F8FA;}
    .pl-hero .pl-kicker {color:#F4C542;font-size:11px;font-weight:700;
      letter-spacing:1.5px;text-transform:uppercase;}
    .pl-hero h2 {color:#F7F8FA!important;font-size:30px;margin:12px 0;line-height:1.25;}
    .pl-hero p {color:#D8E3F0;max-width:760px;line-height:1.7;margin:0;}
    .pl-principles {display:grid;grid-template-columns:repeat(4,1fr);gap:10px;
      margin:20px 0 28px;}
    .pl-principle {background:#E9EFF6;border:1px solid #D8E2EE;border-radius:8px;
      padding:13px 15px;color:#102B52;font-size:13px;font-weight:600;}
    .pl-principle span {color:#2B65A0;margin-right:8px;}
    [data-testid="stMainBlockContainer"] {padding-top:2.4rem;max-width:1440px;}
    h1,h2,h3 {color:#102B52;letter-spacing:-.025em;}
    h1 {font-weight:750!important;} h2 {font-weight:680!important;}
    [data-testid="stSidebar"] {background:#102B52;}
    [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,[data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {color:#F7F8FA;}
    [data-testid="stSidebar"] [data-baseweb="select"] * {color:#102B52;}
    [data-testid="stSidebar"] [data-baseweb="select"] input {
      -webkit-text-fill-color:#102B52;opacity:1;}
    [data-testid="stSidebar"] [data-testid="stSelectbox"] input {
      color:#102B52!important;-webkit-text-fill-color:#102B52!important;}
    [data-testid="stSidebar"] a {color:#F4C542;}
    [data-testid="stMetric"] {background:white;border:1px solid #E0E5EC;
      border-top:3px solid #F4C542;box-shadow:0 3px 12px #102B5208;
      border-radius:10px;padding:18px 20px;min-height:110px;}
    [data-testid="stMetricLabel"] {color:#526173;font-size:.85rem;}
    [data-testid="stMetricValue"] {color:#102B52;font-weight:680;}
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {color:#526173!important;}
    [data-testid="stCaptionContainer"] {opacity:1!important;}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
      color:#C7D4E6!important;}
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {color:#102B52;}
    [data-testid="stVerticalBlockBorderWrapper"] {background:white;border-radius:12px;}
    .pl-brand {display:flex;align-items:center;gap:12px;margin:10px 0 28px;}
    .pl-mark {background:#F4C542;color:#102B52;font-size:17px;font-weight:800;
      border-radius:7px;padding:10px 9px;letter-spacing:-1px;}
    .pl-brand strong {color:white;font-size:21px;letter-spacing:-.5px;}
    .pl-brand small {display:block;color:#C7D4E6;font-size:10px;letter-spacing:1.7px;}
    .pl-card {padding:22px 24px;border:1px solid #E0E5EC;border-radius:12px;
      background:white;min-height:168px;border-top:3px solid #2B65A0;
      box-shadow:0 3px 12px #102B5208;}
    .pl-card h3 {margin:6px 0 10px;font-size:21px;}
    .pl-card p {color:#526173;line-height:1.65;margin:0;}
    .pl-eyebrow {color:#526173;font-size:10px;letter-spacing:1.7px;font-weight:700;}
    .pl-flow {display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin:16px 0;}
    .pl-node {border:1px solid #E0E5EC;border-radius:9px;padding:18px;
      background:white;color:#102B52;line-height:1.6;}
    .pl-node small {display:block;color:#526173;margin-top:6px;}
    .pl-footer {border-top:1px solid #E0E5EC;margin-top:36px;padding-top:18px;
      color:#526173;font-size:12px;line-height:1.8;}
    .pl-footer a {color:#2B65A0;}
    @media(max-width:768px) {
      [data-testid="stMainBlockContainer"] {padding:1.6rem 1rem;}
      .pl-flow {grid-template-columns:1fr;}
      .pl-principles {grid-template-columns:repeat(2,1fr);}
      .pl-hero {padding:22px 20px;}
      .pl-hero h2 {font-size:25px!important;}
      .pl-card {padding:18px;min-height:0;margin-bottom:12px;}
      [data-testid="stMetric"] {padding:14px 16px;min-height:94px;}
      h1 {font-size:2.2rem!important;} h2 {font-size:1.65rem!important;}
    }
    </style>""",
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    st.sidebar.markdown(
        '<div class="pl-brand"><span class="pl-mark">PL</span>'
        "<div><strong>PathwayLab</strong><small>FOOTBALL RESEARCH</small></div></div>",
        unsafe_allow_html=True,
    )


def section_intro(title: str, subtitle: str) -> None:
    st.header(title)
    st.markdown(subtitle)


def module_card(number: str, title: str, description: str) -> None:
    st.markdown(
        f'<div class="pl-card"><div class="pl-eyebrow">{escape(number)}</div>'
        f"<h3>{escape(title)}</h3><p>{escape(description)}</p></div>",
        unsafe_allow_html=True,
    )


def research_hero() -> None:
    """Frame the two independent modules without suggesting a linked population."""
    st.markdown(
        '<div class="pl-hero"><div class="pl-kicker">Independent football research</div>'
        "<h2>Physical load. Match involvement.<br>Evidence in context.</h2>"
        "<p>Two independent research lanes for exploring longitudinal observations, "
        "testing historical forecasts and understanding playing exposure. "
        "Public views use fictional players throughout.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="pl-principles">'
        + "".join(
            f'<div class="pl-principle"><span>{index:02d}</span>{label}</div>'
            for index, label in enumerate(
                [
                    "Reproducibility",
                    "Temporal validation",
                    "Synthetic public demo",
                    "Scientific limitations",
                ],
                1,
            )
        )
        + "</div>",
        unsafe_allow_html=True,
    )


def forecast_workflow() -> None:
    """Present the existing evaluation protocol as a compact sequence."""
    st.markdown(
        '<div class="pl-flow">'
        '<div class="pl-node"><b>01 · Historical inputs</b>'
        "<small>Only earlier observed blocks enter features.</small></div>"
        '<div class="pl-node"><b>02 · Shared cutoff</b>'
        "<small>All fictional players share target-block boundaries.</small></div>"
        '<div class="pl-node"><b>03 · Fair comparison</b>'
        "<small>Score each model on the same held-out synthetic targets.</small></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def chart(fig: go.Figure, source: str) -> None:
    """Apply consistent appearance while keeping source beside each chart."""
    palette = [BLUE, NAVY, "#B68B16", "#648AB4", "#8695A8"]
    groups: dict[str, str] = {}
    for trace in fig.data:
        color = groups.setdefault(str(trace.name), palette[len(groups) % len(palette)])
        if trace.type in {"scatter", "bar", "box", "histogram"}:
            if trace.marker.color is None or isinstance(trace.marker.color, str):
                trace.update(marker_color=color)
                if trace.type in {"scatter", "box"}:
                    trace.update(line_color=color)
    fig.update_layout(
        template="plotly_white",
        font={"family": "Arial, sans-serif", "color": NAVY, "size": 12},
        title={"font": {"size": 15}, "x": 0, "xanchor": "left"},
        colorway=palette,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin={"l": 10, "r": 14, "t": 60, "b": 90},
        legend={"orientation": "h", "y": -0.25, "x": 0, "title_text": ""},
        hoverlabel={"bgcolor": "white", "font_color": NAVY},
    )
    fig.update_xaxes(showgrid=False, automargin=True, zeroline=False)
    fig.update_yaxes(gridcolor="#E8EDF3", automargin=True, zeroline=False)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displaylogo": False})
    st.caption(source)


def footer() -> None:
    st.markdown(
        '<div class="pl-footer">Independent research by <strong>Muhammad Rauf</strong>'
        ' · <a href="https://mrtrauf.github.io/">Portfolio</a><br>'
        "No club affiliation or endorsement. No injury, readiness or causal claims.</div>",
        unsafe_allow_html=True,
    )
