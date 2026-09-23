import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from frontend.session_state import ensure_app_state, build_portfolio

ensure_app_state()

st.title("Performance Metrics")
st.caption("Analytics are produced for the saved benchmark portfolio, regardless of the worksheet draft.")

benchmark_weights = st.session_state.get("benchmark_weights", {})
benchmark_name = st.session_state.get("benchmark_name", "Benchmark Portfolio")

ptf, alloc, liabilities = build_portfolio(benchmark_weights)

st.subheader(benchmark_name)

weights_df = pd.DataFrame({
    "asset": list(benchmark_weights.keys()),
    "weight": list(benchmark_weights.values()),
})
st.dataframe(weights_df.assign(weight=weights_df["weight"].map(lambda x: f"{x:.2%}")), use_container_width=True)

horizon = st.session_state.horizon
mc_paths = st.session_state.mc_paths
sample_paths = st.session_state.sample_paths

st.header("Monte Carlo benchmark paths")
with st.spinner("Running Monte Carlo..."):
    scenario = ptf.run_scenario("base")
    scenario.mc_paths = int(mc_paths)
    paths = scenario.get_paths(horizon=horizon)
    ptf_values = ptf._get_ptf_value("base", horizon=horizon)

    p10, p25, p50, p75, p90 = np.percentile(ptf_values, [10, 25, 50, 75, 90], axis=0)
    times = paths["times"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=p90, line=dict(color='rgba(0,0,0,0)'), showlegend=False, name='p90'))
    fig.add_trace(go.Scatter(x=times, y=p10, fill='tonexty', fillcolor='rgba(200,200,255,0.2)', line=dict(color='rgba(0,0,0,0)'), showlegend=False, name='p10'))
    fig.add_trace(go.Scatter(x=times, y=p75, line=dict(color='rgba(0,0,0,0)'), showlegend=False, name='p75'))
    fig.add_trace(go.Scatter(x=times, y=p25, fill='tonexty', fillcolor='rgba(150,200,255,0.2)', line=dict(color='rgba(0,0,0,0)'), showlegend=False, name='p25'))
    fig.add_trace(go.Scatter(x=times, y=p50, mode='lines', line=dict(color='blue'), name='Median'))

    rng = np.random.default_rng(123)
    idx = rng.choice(ptf_values.shape[0], size=min(int(sample_paths), ptf_values.shape[0]), replace=False)
    for i in idx:
        fig.add_trace(go.Scatter(x=times, y=ptf_values[i], mode='lines', line=dict(color='rgba(0,0,0,0.05)'), showlegend=False))

    fig.update_layout(title='Portfolio Value Distribution (AUM scale)', xaxis_title='Years', yaxis_title='Portfolio Value')
    st.plotly_chart(fig, use_container_width=True)

st.header("Key metrics")
col1, col2, col3 = st.columns(3)
with col1:
    var = ptf.get_var(ci=0.95, horizon=1)
    st.metric("VaR (95%, 1y)", f"${var:,.0f}")
with col2:
    cvar = ptf.get_cvar(ci=0.95, horizon=1)
    st.metric("CVaR (95%, 1y)", f"${cvar:,.0f}")
with col3:
    st.metric("Sharpe Ratio (ann.)", f"{alloc.get_sharpe():.2f}")

st.header("Liability Growth")
years = list(range(0, int(horizon) + 1))
liability_values = [liabilities.get_closing_liabilities(t) for t in years]
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=years, y=liability_values, mode='lines+markers', name='Liabilities', line=dict(color='red')))
fig2.update_layout(title='Projected Liabilities', xaxis_title='Years', yaxis_title='Liability Value')
st.plotly_chart(fig2, use_container_width=True)

st.header("Funded Ratio Distribution")
final_vals = ptf_values[:, -1]
funded = np.array([ptf._get_funded_ratio(a, int(horizon)) for a in final_vals])
funded_df = pd.DataFrame({"final_portfolio": final_vals, "funded_ratio": funded})
st.write(funded_df["funded_ratio"].describe())
st.bar_chart(funded_df["funded_ratio"].value_counts(bins=20).sort_index())

st.markdown("---")
st.info("Use the Allocation Research page to edit the draft worksheet; the Performance Metrics page evaluates the saved benchmark portfolio.")
