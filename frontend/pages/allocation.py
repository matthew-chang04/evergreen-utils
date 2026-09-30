import os
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from frontend.session_state import ASSET_KEYS, ensure_app_state, build_portfolio

ensure_app_state()

st.title("Allocation Research")
st.caption("Build a target portfolio and keep it as the active benchmark for performance analytics.")

weights = st.session_state.draft_weights.copy()

st.subheader("Portfolio worksheet")


with st.expander("Change Portfolio Allocation"):
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

    st.write("Current target mix")
    df = pd.DataFrame({"asset": list(normalized.keys()), "weight": list(normalized.values())})
    fig = px.pie(df, values="weight", names="asset", title="Portfolio Allocation")
    st.plotly_chart(fig, use_container_width=True)

    st.write("Weight summary")
    st.dataframe(df.assign(weight=df["weight"].map(lambda x: f"{x:.2%}")), use_container_width=True)

    if sum(normalized.values()) != 1.0:
        st.warning("The worksheet weights are being normalized to sum to 100% before evaluation.")

    if st.button("Compare current alloc with model"):
        st.session_state.test_weights = normalized.copy() 
        st.success = "Portfolio saved"


portfolio_metrics_col, monte_carlo_stats, monte_carlo_vis = st.columns(3)

with portfolio_metrics_col:
    ptf, alloc, _ = build_portfolio(normalized) 
    if st.session_state.benchmark_weights != normalized:
        bench_ptf, bench_alloc, _= build_portfolio(st.session_state.benchmark_weights)
        test_new = True
    else:
        test_new = False
 

col1, col2, col3, col4, col5, col6, col7  = st.columns(7, border=True, wrap=False)
with col1:
    ex = alloc.get_expected_return()
    st.metric("Portfolio Return", f"{ex:.2f}")

    if test_new:
        ex_bench = bench_alloc.get_expected_return()
        st.metric("Benchmark Ptf Return", f"{ex_bench:.2f}")
        st.metric("Change", f"{ex - ex_bench:.2f}")
        
with col2:
    variance = alloc.get_variance()
    st.metric("Portfolio Variance", f"{ex:.2f}")   

    if test_new:
        variance_bench = bench_alloc.get_variance()
        st.metric("Benchmark Ptf Return", f"{variance_bench:.2f}")
        st.metric("Change", f"{variance - variance_bench:.2f}")

with col3:
    sharpe = alloc.get_sharpe()
    st.metric("Sharpe Ratio", f"{sharpe:.2f}")

    if test_new:
        sharpe_bench = bench_alloc.get_sharpe()
        st.metric("Benchmark Sharpe", f"{sharpe_bench:.2f}")
        st.metric("Change", f"{sharpe - sharpe_bench:.2f}")

with col4: 
    var = ptf.get_var(ci=0.05, horizon=1)
    st.metric("VaR (95%, 1y)", f"${var:,.2f}")

    if test_new:
        var_bench = bench_ptf.get_var(ci=0.05, horizon=1)
        st.metric("Benchmark Ptf Return", f"{var_bench:.2f}")
        st.metric("Change", f"{var - var_bench:.2f}")

with col5:
    cvar = ptf.get_cvar(ci=0.05, horizon=1)
    st.metric("CVaR (95%, 1y)", f"${cvar:,.2f}") 

    if test_new:
        cvar_bench = ptf.get_cvar(ci=0.05, horizon=1)
        st.metric("Benchmark CVaR", f"{cvar_bench:.2f}")
        st.metric("Change", f"{cvar - cvar_bench:.2f}")

with col6:
    p_underfunding = ptf.underfunding_probability()
    st.metric("P(Underfunding)", f"{p_underfunding:.2f}")

    if test_new:
        p_u_bench = bench_ptf.underfunding_probability()
        st.metric("Benchmark P(Underfunding)", f"{p_u_bench:.2f}")
        st.metric("Change", f"{p_underfunding - p_u_bench:.2f}")

with col7:
    fr_vol = ptf.funded_ratio_vol()
    st.metric("Funded Ratio Vol", f"{fr_vol:.2f}")

    if test_new:
        fr_vol_bench = bench_ptf.funded_ratio_vol()
        st.metric("Benchmark Funded Ratio Vol", f"{fr_vol_bench:.2f}")
        st.metric("Change", f"{fr_vol - fr_vol_bench:.2f}")

        




st.markdown("---")
st.info("Switch to Performance Metrics to review the portfolio currently saved as the benchmark.")
