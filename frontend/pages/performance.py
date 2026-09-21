import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd
from portfolio import Asset, AssetAlloc, Portfolio
from pension import Liabilities
import cma


st.title("Portfolio Performance")

# settings
horizon = st.sidebar.slider("Horizon (years)", min_value=1, max_value=50, value=30)
mc_paths = st.sidebar.number_input("Monte Carlo paths", min_value=100, max_value=20000, value=5000, step=100)
sample_paths = st.sidebar.number_input("Sample paths to plot", min_value=10, max_value=500, value=50, step=10)

# same default allocation used in allocation page
DEFAULT_WEIGHTS = {
    "cash": 0.03,
    "fixed_income": 0.28,
    "can_equity": 0.09,
    "us_equity": 0.09,
    "id_equity": 0.04,
    "em_equity": 0.05,
    "real_estate": 0.16,
    "infrastructure": 0.13,
    "private_equity": 0.13,
}

assets = [(Asset(name=a), w) for a, w in DEFAULT_WEIGHTS.items()]
alloc = AssetAlloc(assets)
liab = Liabilities(
    retired_members=cma.RETIRED_MEMBERS,
    active_members=cma.ACTIVE_MEMBERS,
    average_salary=cma.AVG_SALARY,
    min_active_members=cma.MIN_ACTIVE_MEMBERS,
    active_members_decline=cma.ACTIVE_MEMBER_DECLINE,
    retired_members_growth=cma.RETIRED_MEMBERS_GROWTH,
    wage_growth_rate=cma.WAGE_GROWTH,
    starting_duration=cma.INITIAL_DURATION,
    actuarial_df=cma.ACTUARIAL_DF,
    service_cost=cma.SERVICE_COST_RATE,
    starting_liabilities=cma.LIABILITIES,
    starting_benefit=cma.STARTING_BENEFIT,
    benefit_growth_rate=cma.BENEFIT_GROWTH_RATE,
    liabilities_cache={},
)

ptf = Portfolio(alloc, liab)

st.header("Monte Carlo Portfolio Paths")

with st.spinner("Running Monte Carlo..."):
    s = ptf.run_scenario("base")
    s.mc_paths = int(mc_paths)
    paths = s.get_paths(horizon=horizon)

    ptf_values = ptf._get_ptf_value("base", horizon=horizon)

    # percentiles
    p10, p25, p50, p75, p90 = np.percentile(ptf_values, [10, 25, 50, 75, 90], axis=0)

    times = paths["times"]

    fig = go.Figure()
    # percentile ribbons
    fig.add_trace(go.Scatter(x=times, y=p90, line=dict(color='rgba(0,0,0,0)'), showlegend=False, name='p90'))
    fig.add_trace(go.Scatter(x=times, y=p10, fill='tonexty', fillcolor='rgba(200,200,255,0.2)', line=dict(color='rgba(0,0,0,0)'), showlegend=False, name='p10'))
    fig.add_trace(go.Scatter(x=times, y=p75, line=dict(color='rgba(0,0,0,0)'), showlegend=False, name='p75'))
    fig.add_trace(go.Scatter(x=times, y=p25, fill='tonexty', fillcolor='rgba(150,200,255,0.2)', line=dict(color='rgba(0,0,0,0)'), showlegend=False, name='p25'))
    # median
    fig.add_trace(go.Scatter(x=times, y=p50, mode='lines', line=dict(color='blue'), name='Median'))

    # sample random paths overlay
    rng = np.random.default_rng(123)
    idx = rng.choice(ptf_values.shape[0], size=min(int(sample_paths), ptf_values.shape[0]), replace=False)
    for i in idx:
        fig.add_trace(go.Scatter(x=times, y=ptf_values[i], mode='lines', line=dict(color='rgba(0,0,0,0.05)'), showlegend=False))

    fig.update_layout(title='Portfolio Value Distribution (AUM scale)', xaxis_title='Years', yaxis_title='Portfolio Value')
    st.plotly_chart(fig, use_container_width=True)

st.header("Liability Growth")
years = list(range(0, int(horizon) + 1))
liab_vals = [liab.get_closing_liabilities(t) for t in years]
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=years, y=liab_vals, mode='lines+markers', name='Liabilities', line=dict(color='red')))
fig2.update_layout(title='Projected Liabilities', xaxis_title='Years', yaxis_title='Liability Value')
st.plotly_chart(fig2, use_container_width=True)

st.header('Funded Ratio Distribution (Final Year)')
final_vals = ptf_values[:, -1]
funded = np.array([ptf._get_funded_ratio(a, int(horizon)) for a in final_vals])
df = pd.DataFrame({ 'final_portfolio': final_vals, 'funded_ratio': funded })
st.write(df['funded_ratio'].describe())
st.bar_chart(df['funded_ratio'].value_counts(bins=20).sort_index())
