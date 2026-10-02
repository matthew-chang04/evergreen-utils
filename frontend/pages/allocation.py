import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from frontend.metric_utils import render_metric_grid
from frontend.session_state import ASSET_KEYS, ensure_app_state, build_portfolio

ensure_app_state()

st.title("Allocation Research")
st.caption("Build a target portfolio and keep it as the active benchmark for performance analytics.")

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1.5rem;
        }
        h1 {
            font-size: 1.6rem !important;
            margin-bottom: 0.2rem !important;
        }
        h2 {
            font-size: 1.15rem !important;
            margin-bottom: 0.2rem !important;
        }
        div[data-testid="stMetricLabel"] {
            font-size: 0.7rem !important;
            white-space: normal !important;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.15rem !important;
            line-height: 1.25 !important;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 0.7rem !important;
        }
        .stDataFrame, .stPlotlyChart {
            margin-top: 0.25rem;
        }
        div[data-testid="stExpander"] {
            margin-bottom: 0.5rem;
        }
        div[data-testid="stExpanderDetails"] {
            padding-top: 0.25rem;
        }
        div[data-testid="stSlider"] label {
            font-size: 0.62rem !important;
            margin-bottom: 0.05rem !important;
        }
        div[data-testid="stSlider"] [data-baseweb="slider"] {
            min-height: 0.8rem !important;
            margin-top: 0 !important;
        }
        div[data-testid="stSlider"] div {
            font-size: 0.68rem !important;
        }
        div[data-testid="stVerticalBlock"] > div {
            margin-bottom: 0.05rem !important;
        }
        div[data-testid="stVerticalBlock"] {
            gap: 0.1rem !important;
        }
        div[data-testid="stHorizontalBlock"] > div {
            gap: 0.08rem !important;
        }
        .stButton > button {
            min-width: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

weights = st.session_state.draft_weights.copy()

st.subheader("Portfolio worksheet")

with st.expander("Change Portfolio Allocation", expanded=False):
    slider_col, summary_col = st.columns([1.15, 1.85], gap="large")

    with slider_col:
        updated = {}
        for asset in ASSET_KEYS:
            updated[asset] = st.slider(
                asset.replace("_", " ").title(),
                min_value=0.0,
                max_value=1.0,
                value=float(weights.get(asset, 0.0)),
                step=0.01,
                key=f"draft_{asset}",
            )

    total = sum(updated.values())
    if total > 0:
        normalized = {key: value / total for key, value in updated.items()}
    else:
        normalized = {key: 0.0 for key in ASSET_KEYS}

    st.session_state.draft_weights = normalized

    with summary_col:
        st.caption(f"Current total: {total:.2%}")

        df = pd.DataFrame({"asset": list(normalized.keys()), "weight": list(normalized.values())})
        fig = px.pie(df, values="weight", names="asset", title="Portfolio Allocation")
        fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), font=dict(size=11), legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True, height=260)

        st.write("Weight summary")
        st.dataframe(df.assign(weight=df["weight"].map(lambda x: f"{x:.2%}")), use_container_width=True, hide_index=True)

        if not abs(total - 1.0) < 1e-6:
            st.warning("The raw mix must total 100% before the benchmark can be confirmed.")

        if st.button("Compare current alloc with model", disabled=not abs(total - 1.0) < 1e-6):
            st.session_state.test_weights = normalized.copy()
            st.success("Portfolio saved")


if st.session_state.benchmark_weights != normalized:
    st.session_state.test_ptf = build_portfolio(st.session_state.test_weights) 
    test_new = True
else: 
    test_new = False


bench_ptf, bench_alloc, _ = st.session_state.benchmark_ptf
ptf, alloc, _ = st.session_state.test_ptf

metric_specs = [
    ("Portfolio Return", alloc.get_expected_return(), bench_alloc.get_expected_return() if test_new else None),
    ("Portfolio Vol", alloc.get_std_dev(), bench_alloc.get_std_dev() if test_new else None),
    ("Sharpe Ratio", alloc.get_sharpe(), bench_alloc.get_sharpe() if test_new else None),
    ("VaR (95%, 1y)", ptf.get_var(ci=0.05, horizon=1), bench_ptf.get_var(ci=0.05, horizon=1) if test_new else None),
    ("CVaR (95%, 1y)", ptf.get_cvar(ci=0.05, horizon=1), bench_ptf.get_cvar(ci=0.05, horizon=1) if test_new else None),
    ("P(Underfunding)", ptf.underfunding_probability(), bench_ptf.underfunding_probability() if test_new else None),
    ("Funded Ratio Vol", ptf.funded_ratio_vol(), bench_ptf.funded_ratio_vol() if test_new else None),
]
render_metric_grid(metric_specs, columns=4)

st.markdown("---")
st.info("Switch to Growth Model to see portfolio movement over time.")
