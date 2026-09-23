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
with st.container():
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

    if st.button("Set as benchmark portfolio"):
        st.session_state.benchmark_weights = normalized.copy()
        st.session_state.benchmark_name = "Custom benchmark"
        st.success("This portfolio is now the benchmark used in the Performance Metrics tab.")

    ptf, alloc, _ = build_portfolio(normalized)
    col1, col2, col3 = st.columns(3)
    with col1:
        var = ptf.get_var(ci=0.95, horizon=1)
        st.metric("VaR (95%, 1y)", f"${var:,.0f}")
    with col2:
        cvar = ptf.get_cvar(ci=0.95, horizon=1)
        st.metric("CVaR (95%, 1y)", f"${cvar:,.0f}")
    with col3:
        sharpe = alloc.get_sharpe()
        st.metric("Sharpe Ratio (ann.)", f"{sharpe:.2f}")

st.markdown("---")
st.info("Switch to Performance Metrics to review the portfolio currently saved as the benchmark.")
