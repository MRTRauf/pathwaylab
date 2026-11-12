"""Shared data-free presentation for the existing Streamlit research viewer."""

from html import escape

import plotly.graph_objects as go
import streamlit as st

NAVY = "#102B52"
BLUE = "#4A8AC4"
YELLOW = "#F4C542"
CANVAS = "#081B34"
SURFACE = "#102B4A"
ELEVATED = "#173656"
TEXT = "#F5F8FC"
MUTED = "#B9CBDE"
BORDER = "#2A4966"
SLATE = "#8FA9C4"


def apply_theme() -> None:
    """Use system fonts and restrained responsive styling, with no remote assets."""
    st.markdown(
        """<style>
    :root {color-scheme:dark;}
    .stApp,[data-testid="stMain"] {background:#081B34;color:#F5F8FC;}
    [data-testid="stHeader"] {background:#081B34;}
    [data-testid="stMainBlockContainer"] {max-width:1350px;padding:2rem 2rem 3rem;}
    h1,h2,h3,h4 {color:#F5F8FC;letter-spacing:-.02em;font-weight:650!important;}
    h1 {font-size:36px!important;padding-bottom:.3rem!important;}
    h2 {font-size:30px!important;} h3 {font-size:22px!important;}
    h4 {font-size:20px!important;}
    p,li {font-size:16px;line-height:1.6;}
    [data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p {
      color:#B9CBDE!important;font-size:13px!important;opacity:1!important;}
    [data-testid="stWidgetLabel"] p {font-size:14px!important;color:#F5F8FC;}
    [data-testid="stTable"] table {width:100%;table-layout:fixed;background:#102B4A;}
    [data-testid="stTable"] th,[data-testid="stTable"] td {
      color:#F5F8FC;border-color:#2A4966;padding:10px 8px;font-size:14px;
      overflow-wrap:anywhere;}
    [data-testid="stSidebar"] {background:#06162B;border-right:1px solid #2A4966;}
    [data-testid="stSidebar"] p,[data-testid="stSidebar"] label {color:#F5F8FC;}
    [data-testid="stSidebar"] [role="radiogroup"] label {
      padding:10px 9px;border-radius:8px;margin:3px 0;border-left:3px solid transparent;}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
      background:#214366;border-left-color:#F4C542;font-weight:700;}
    [data-testid="stSidebar"] a,a {color:#FFE28A;}
    [data-testid="stMetric"] {background:#173656;border:1px solid #2A4966;
      border-top:3px solid #F4C542;border-radius:12px;padding:18px;min-height:112px;}
    [data-testid="stMetricLabel"] p {font-size:14px;color:#B9CBDE;}
    [data-testid="stMetricValue"] {color:#F5F8FC;font-size:32px;font-weight:700;}
    [data-testid="stVerticalBlockBorderWrapper"] {background:#102B4A;border-radius:12px;}
    [data-testid="stVerticalBlockBorderWrapper"]>div {border-color:#2A4966;}
    .st-key-load_controls,.st-key-event_controls,.st-key-model_controls {
      background:#102B4A;border:1px solid #2A4966;border-radius:12px;padding:18px;
      margin:12px 0 20px;}
    [data-testid="stButton"] button {border:1px solid #4A8AC4;background:#214366;
      color:#F5F8FC;border-radius:8px;font-weight:600;min-height:42px;}
    [data-testid="stButton"] button:hover {border-color:#F4C542;color:#FFE28A;}
    [data-testid="stButton"] button[kind="primary"] {background:#F4C542;color:#081B34;}
    button:focus-visible,input:focus-visible {outline:2px solid #FFE28A!important;
      outline-offset:3px;}
    [data-testid="stAlert"] {background:#173656;border:1px solid #2A4966;
      border-left:3px solid #F4C542;border-radius:8px;}
    [data-testid="stAlert"] p {color:#F5F8FC;font-size:14px;line-height:1.5;}
    .pl-brand {display:flex;align-items:center;gap:12px;margin:8px 0 22px;}
    .pl-mark {background:#F4C542;color:#081B34;font-size:18px;font-weight:800;
      border-radius:8px;padding:10px;}
    .pl-brand strong {color:#F5F8FC;font-size:23px;}
    .pl-brand small {display:block;color:#B9CBDE;font-size:12px;}
    .pl-status {border:1px solid #2A4966;border-left:3px solid #F4C542;
      background:#102B4A;padding:12px 15px;border-radius:8px;margin:16px 0;}
    .pl-status b {color:#FFE28A;font-size:13px;}
    .pl-status span {display:block;color:#B9CBDE;font-size:14px;}
    .pl-hero {background:#102B4A;border:1px solid #2A4966;
      border-left:4px solid #F4C542;border-radius:14px;padding:24px 28px;margin:8px 0 16px;}
    .pl-kicker,.pl-eyebrow {color:#FFE28A;font-size:13px;font-weight:650;}
    .pl-hero h2 {font-size:36px!important;margin:8px 0;}
    .pl-hero h3 {font-size:22px;margin:8px 0;color:#B9CBDE;}
    .pl-hero p,.pl-card p,.pl-node small {color:#B9CBDE;font-size:15px;line-height:1.6;}
    .pl-principles {display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:16px 0;}
    .pl-principle {background:#173656;border:1px solid #2A4966;border-radius:8px;
      padding:12px;color:#F5F8FC;font-size:14px;}
    .pl-principle span {color:#FFE28A;margin-right:8px;}
    .pl-card {background:#173656;border:1px solid #2A4966;border-top:3px solid #4A8AC4;
      border-radius:12px;padding:22px;min-height:195px;}
    .pl-card h3 {font-size:23px;margin:10px 0;}
    .pl-card p {margin-bottom:0;}
    .pl-flow {display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0;}
    .pl-node {background:#102B4A;border:1px solid #2A4966;border-radius:10px;padding:16px;
      color:#F5F8FC;font-size:15px;}
    .pl-node small {display:block;font-size:14px;margin-top:6px;}
    .pl-footer {border-top:1px solid #2A4966;margin-top:28px;padding-top:16px;
      color:#B9CBDE;font-size:13px;line-height:1.8;}
    @media(max-width:768px) {
      [data-testid="stMainBlockContainer"] {padding:1.4rem 1rem;}
      .pl-flow {grid-template-columns:1fr;}
      .pl-principles {grid-template-columns:repeat(2,1fr);}
      .pl-hero {padding:20px;} .pl-hero h2 {font-size:30px!important;}
      .pl-card {min-height:0;margin-bottom:12px;padding:18px;}
      h1 {font-size:32px!important;} h2 {font-size:27px!important;}
      [data-testid="stMetric"] {padding:15px;min-height:100px;}
    }
    </style>""",
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    st.sidebar.markdown(
        '<div class="pl-brand"><span class="pl-mark">PL</span>'
        "<div><strong>PathwayLab</strong><small>DATA SCIENCE</small></div></div>",
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
        '<div class="pl-hero"><div class="pl-kicker">FOOTBALL PERFORMANCE RESEARCH</div>'
        "<h2>PathwayLab</h2><h3>Longitudinal Training Load &amp; Match Performance Analytics</h3>"
        "<p>Explore how physical load changes over time, "
        "compare historical forecasts and study match-performance trajectories. "
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
    palette = [BLUE, YELLOW, "#75CFD4", "#A5B8E8", "#E4B3C8"]
    groups: dict[str, str] = {}
    for trace in fig.data:
        color = groups.setdefault(str(trace.name), palette[len(groups) % len(palette)])
        if trace.type in {"scatter", "bar", "box", "histogram"}:
            if trace.marker.color is None or isinstance(trace.marker.color, str):
                trace.update(
                    marker_color=trace.marker.color
                    if fig.layout.title.text == "Synthetic model errors"
                    else color
                )
                if trace.type in {"scatter", "box"}:
                    trace.update(line_color=color)
    fig.update_layout(
        template="plotly_dark",
        font={"family": "Arial, sans-serif", "color": TEXT, "size": 14},
        title={"font": {"size": 18}, "x": 0, "xanchor": "left"},
        colorway=palette,
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        height=480,
        margin={"l": 14, "r": 18, "t": 65, "b": 105},
        legend={"orientation": "h", "y": -0.25, "x": 0, "title_text": ""},
        hoverlabel={"bgcolor": ELEVATED, "font_color": TEXT},
        meta={"source": source, "disclosure": "SYNTHETIC - DEMONSTRATION ONLY"},
    )
    fig.update_xaxes(showgrid=False, automargin=True, zeroline=False)
    fig.update_yaxes(gridcolor="#294664", automargin=True, zeroline=False)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displaylogo": False})
    st.caption(source.replace("SYNTHETIC - DEMONSTRATION ONLY", "Synthetic fixture"))


def footer() -> None:
    st.markdown(
        '<div class="pl-footer">Independent research by <strong>Muhammad Rauf</strong>'
        ' · <a href="https://mrtrauf.github.io/">Portfolio</a><br>'
        "Independent research. No injury, readiness or causal claims.</div>",
        unsafe_allow_html=True,
    )
