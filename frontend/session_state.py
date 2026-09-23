import streamlit as st

from portfolio.liabilities import Liabilities
from portfolio.portfolio import Asset, AssetAlloc, Portfolio
import assumptions.cma as cma

ASSET_KEYS = [
    "cash",
    "fixed_income",
    "can_equity",
    "us_equity",
    "id_equity",
    "em_equity",
    "real_estate",
    "infrastructure",
    "private_equity",
]

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


def ensure_app_state():
    if "horizon" not in st.session_state:
        st.session_state.horizon = 30
    if "mc_paths" not in st.session_state:
        st.session_state.mc_paths = 5000
    if "sample_paths" not in st.session_state:
        st.session_state.sample_paths = 5000
    if "draft_weights" not in st.session_state:
        st.session_state.draft_weights = DEFAULT_WEIGHTS.copy()
    if "benchmark_weights" not in st.session_state:
        st.session_state.benchmark_weights = DEFAULT_WEIGHTS.copy()
    if "benchmark_name" not in st.session_state:
        st.session_state.benchmark_name = "Benchmark Portfolio"


def normalize_weights(weights):
    if not weights:
        return DEFAULT_WEIGHTS.copy()

    cleaned = {key: float(weights.get(key, 0.0)) for key in ASSET_KEYS}
    total = sum(cleaned.values())
    if total <= 0:
        return DEFAULT_WEIGHTS.copy()
    return {key: cleaned[key] / total for key in ASSET_KEYS}


def build_portfolio(weights):
    normalized = normalize_weights(weights)
    assets = [(Asset(name=name), float(weight)) for name, weight in normalized.items()]
    alloc = AssetAlloc(assets)
    liabilities = Liabilities(
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
    portfolio = Portfolio(alloc, liabilities)
    return portfolio, alloc, liabilities
