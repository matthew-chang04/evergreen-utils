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

st.title("Growth Model")
st.caption("Benchmark portfolio growth versus liability growth, based on the currently saved portfolio allocation.")


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

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=times,
        y=p90,
        line=dict(color='rgba(59,130,246,0)', width=0),
        fill='tonexty',
        fillcolor='rgba(96,165,250,0.12)',
        name='10th-90th percentile',
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=p10,
        line=dict(color='rgba(59,130,246,0)', width=0),
        showlegend=False,
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=p75,
        line=dict(color='rgba(59,130,246,0)', width=0),
        fill='tonexty',
        fillcolor='rgba(37,99,235,0.10)',
        name='25th-75th percentile',
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=times,
        y=p25,
        line=dict(color='rgba(59,130,246,0)', width=0),
        showlegend=False,
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(x=times, y=p50, mode='lines', line=dict(color='#1d4ed8', width=2.5), name='Median'))

    fig.add_trace(go.Scatter(
        x=liability_years,
        y=liability_values,
        mode='lines',
        line=dict(color='#dc2626', width=2.4),
        name='Liabilities',
    ))

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
        margin=dict(l=12, r=12, t=42, b=12),
        height=450,
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
col1, col2, col3 = st.columns(3)
with col1:
    var = ptf.get_var(ci=0.05, horizon=1)
    st.metric("VaR (95%, 1y)", f"${var:,.0f}")
with col2:
    cvar = ptf.get_cvar(ci=0.05, horizon=1)
    st.metric("CVaR (95%, 1y)", f"${cvar:,.0f}")
with col3:
    st.metric("Sharpe Ratio (ann.)", f"{alloc.get_sharpe():.2f}")

# st.header("Liability Growth")
# years = list(range(0, int(horizon) + 1))
# liability_values = [liabilities.get_closing_liabilities(t) for t in years]
# fig2 = go.Figure()
# fig2.add_trace(go.Scatter(x=years, y=liability_values, mode='lines+markers', name='Liabilities', line=dict(color='red')))
# fig2.update_layout(title='Projected Liabilities', xaxis_title='Years', yaxis_title='Liability Value')
# st.plotly_chart(fig2, use_container_width=True)

st.header("Funded Ratio Distribution")
final_vals = ptf_values[:, -1]
funded = np.array([ptf._get_funded_ratio(a, int(horizon)) for a in final_vals])
funded_df = pd.DataFrame({"final_portfolio": final_vals, "funded_ratio": funded})
st.write(funded_df["funded_ratio"].describe())

mean_funded = funded.mean()
std_funded = funded.std(ddof=1)
lo = max(0.0, mean_funded - 2.0 * std_funded)
hi = mean_funded + 2.0 * std_funded
centered_funded = funded[(funded >= lo) & (funded <= hi)]

hist, edges = np.histogram(centered_funded, bins=20, range=(lo, hi))
hist_df = pd.DataFrame({
    "bin_start": edges[:-1],
    "count": hist,
})
st.bar_chart(hist_df.set_index("bin_start")["count"])

st.markdown("---")

