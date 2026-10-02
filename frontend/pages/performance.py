import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from frontend.metric_utils import render_metric_grid
from frontend.percentile_projection import build_percentile_projection_figure

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from frontend.session_state import ensure_app_state, build_portfolio

ensure_app_state()

st.title("Growth Model")
st.caption("Benchmark portfolio growth versus liability growth, based on the currently saved portfolio allocation.")

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

ptf_name = st.selectbox("Portfolio Source", ["Test Portfolio", "Benchmark Portfolio"])
if st.session_state.get("test_weights") != st.session_state.get("benchmark_weights") and ptf_name == "Test Portfolio":     
    ptf, alloc, liabilities = st.session_state.test_ptf
    weights = st.session_state.test_weights
    name = st.session_state.test_name

else:      
    ptf, alloc, liabilities = st.session_state.benchmark_ptf
    weights = st.session_state.benchmark_weights
    name = st.session_state.benchmark_name



st.subheader(name)

weights_df = pd.DataFrame({
    "asset": list(weights.keys()),
    "weight": list(weights.values()),
})
st.dataframe(weights_df.assign(weight=weights_df["weight"].map(lambda x: f"{x:.2%}")), use_container_width=True)

horizon = st.session_state.horizon
mc_paths = st.session_state.mc_paths
sample_paths = st.session_state.sample_paths

st.header("Portfolio growth distribution")
with st.spinner("Running Monte Carlo..."):
    scenario = ptf.run_scenario("base")
    scenario.mc_paths = int(mc_paths)
    paths = scenario.get_paths(horizon=horizon)
    ptf_values = ptf._get_ptf_value("base", horizon=horizon)

    p10, p25, p50, p75, p90 = np.percentile(ptf_values, [10, 25, 50, 75, 90], axis=0)
    times = paths["times"]
    liability_values = [liabilities.get_closing_liabilities(t) for t in range(0, int(horizon) + 1)]
    liability_years = np.linspace(0, horizon, len(liability_values))

    percentile_values = {10: p10, 25: p25, 50: p50, 75: p75, 90: p90}
    fig = build_percentile_projection_figure(
        times=times,
        percentile_values=percentile_values,
        liability_values=np.asarray(liability_values, dtype=float),
        liability_years=liability_years,
    )

    percentile_cap = max(np.quantile(ptf_values, 0.99), np.quantile(liability_values, 0.99))
    percentile_floor = min(np.quantile(ptf_values, 0.01), np.min(liability_values))
    y_min = percentile_floor * 0.9
    y_max = percentile_cap * 1.15
    fig.update_layout(
        title='Portfolio Growth vs. Liability Growth',
        xaxis_title='Years',
        yaxis_title='Value',
        template='plotly_white',
        legend=dict(
            orientation='h',
            yanchor='top',
            y=1.0,
            xanchor='left',
            x=0,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='rgba(148,163,184,0.4)',
            borderwidth=1,
            font=dict(color='#0f172a', size=11),
        ),
        margin=dict(l=12, r=12, t=30, b=12),
        height=330,
        paper_bgcolor='#f8fafc',
        plot_bgcolor='#f8fafc',
        xaxis=dict(
            rangemode='tozero',
            showgrid=True,
            gridcolor='rgba(100,116,139,0.22)',
            zerolinecolor='rgba(71,85,105,0.45)',
            tickfont=dict(color='#334155'),
            title=dict(text='Years', font=dict(color='#334155')),
        ),
        yaxis=dict(
            range=[y_min, y_max],
            rangemode='tozero',
            showgrid=True,
            gridcolor='rgba(100,116,139,0.22)',
            zerolinecolor='rgba(71,85,105,0.45)',
            tickfont=dict(color='#334155'),
            title=dict(text='Value', font=dict(color='#334155')),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

st.header("Key metrics")
final_vals = ptf_values[:, -1]
funded = np.array([ptf._get_funded_ratio(a, int(horizon)) for a in final_vals])

avg_funded_ratio = funded.mean()
prob_underfunded = np.mean(funded < 1.0)

metric_specs = [
    ("VaR (95%, 1y)", ptf.get_var(ci=0.05, horizon=1)),
    ("CVaR (95%, 1y)", ptf.get_cvar(ci=0.05, horizon=1)),
    ("Sharpe Ratio (ann.)", alloc.get_sharpe()),
    ("Avg funded ratio", avg_funded_ratio),
    ("P(Underfunding)", prob_underfunded),
]

render_metric_grid(metric_specs, columns=4)

st.markdown("---")

