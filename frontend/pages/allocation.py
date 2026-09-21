import streamlit as st
import plotly.express as px
import pandas as pd
from portfolio import Asset, AssetAlloc, Portfolio
from pension import Liabilities
import cma


st.title("Strategic Asset Allocation")

# default allocation (sums to 1.0)
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

st.sidebar.header("Settings")
horizon = st.sidebar.slider("Horizon (years)", min_value=1, max_value=50, value=30)
mc_paths = st.sidebar.number_input("Monte Carlo paths", min_value=100, max_value=20000, value=5000, step=100)

st.header("Portfolio Composition")
weights = DEFAULT_WEIGHTS.copy()

df = pd.DataFrame({"asset": list(weights.keys()), "weight": list(weights.values())})
fig = px.pie(df, values="weight", names="asset", title="Portfolio Allocation")
st.plotly_chart(fig, use_container_width=True)

st.header("Key Metrics")

# build simple AssetAlloc and Portfolio
assets = [(Asset(name=a), w) for a, w in weights.items()]
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
st.info("Use the 'Performance' page to view Monte Carlo paths and liabilities over the selected horizon.")
