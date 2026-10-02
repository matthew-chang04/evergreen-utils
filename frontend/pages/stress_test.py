import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from frontend.metric_utils import render_metric_grid
from frontend.percentile_projection import build_percentile_projection_figure
from frontend.session_state import ASSET_KEYS, add_scenario, ensure_app_state

ensure_app_state()

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
        .stDataFrame, .stPlotlyChart {
            margin-top: 0.25rem;
        }
        [data-testid="stExpander"] {
            margin-bottom: 0.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Stress Test")
st.caption("Create a custom return shock scenario and view the projected percentile path for the affected portfolio.")

ptf_name = st.selectbox("Portfolio Source", ["Test Portfolio", "Benchmark Portfolio"])
if st.session_state.get("test_weights") != st.session_state.get("benchmark_weights") and ptf_name == "Test Portfolio":
    ptf, alloc, liabilities = st.session_state.test_ptf
    weights = st.session_state.test_weights
    name = st.session_state.test_name
else:
    ptf, alloc, liabilities = st.session_state.benchmark_ptf
    weights = st.session_state.benchmark_weights
    name = st.session_state.benchmark_name

with st.expander("Create scenario", expanded=True):
    default_name = f"Stress {len([k for k in ptf.scenarios if k != 'base']) + 1}"
    scenario_name = st.text_input("Scenario name", value=default_name)

    scenario_df = pd.DataFrame({
        "Asset": [asset.replace("_", " ").title() for asset in ASSET_KEYS],
        "Return delta": [0.0 for _ in ASSET_KEYS],
    })
    edited_df = st.data_editor(
        scenario_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Asset": st.column_config.TextColumn("Asset", disabled=True),
            "Return delta": st.column_config.NumberColumn(
                "Return delta",
                min_value=-1.0,
                max_value=1.0,
                step=0.01,
                format="%.2f",
            ),
        },
    )

    if st.button("Create scenario"):
        cleaned_name = scenario_name.strip()
        if not cleaned_name:
            st.error("Please enter a scenario name.")
        else:
            deltas = {
                asset_key: float(row["Return delta"])
                for asset_key, row in zip(ASSET_KEYS, edited_df.to_dict("records"))
            }
            try:
                add_scenario(cleaned_name, {"returns": deltas})
                st.success(f"Created scenario '{cleaned_name}'.")
                st.session_state.last_stress_scenario = cleaned_name
            except ValueError as exc:
                st.error(str(exc))

scenario_names = [name for name in sorted(ptf.scenarios.keys()) if name != "base"]

if scenario_names:
    selected_scenario = st.selectbox("Scenario comparison", ["Base case", *scenario_names], index=0)
    if selected_scenario != "Base case":
        horizon = st.session_state.horizon
        downside_risk_metrics = {
            "Portfolio Vol",
            "VaR (95%, 1y)",
            "CVaR (95%, 1y)",
            "P(Underfunding)",
            "Funded Ratio Vol",
        }

        base_specs = {
            "Portfolio Return": ptf.get_expected_return() if hasattr(ptf, "get_expected_return") else alloc.get_expected_return(),
            "Portfolio Vol": ptf.portfolio_vol(scenario="base", horizon=horizon),
            "Sharpe Ratio": alloc.get_sharpe(),
            "VaR (95%, 1y)": ptf.get_var(ci=0.05, scenario="base", horizon=1),
            "CVaR (95%, 1y)": ptf.get_cvar(ci=0.05, scenario="base", horizon=1),
            "P(Underfunding)": ptf.underfunding_probability(scenario="base", horizon=horizon),
            "Avg funded ratio": ptf.funded_ratio_avg(scenario="base", horizon=horizon),
            "Funded Ratio Vol": ptf.funded_ratio_vol(scenario="base", horizon=horizon),
        }
        selected_specs = {
            "Portfolio Return": ptf.get_expected_return() if hasattr(ptf, "get_expected_return") else alloc.get_expected_return(),
            "Portfolio Vol": ptf.portfolio_vol(scenario=selected_scenario, horizon=horizon),
            "Sharpe Ratio": alloc.get_sharpe(),
            "VaR (95%, 1y)": ptf.get_var(ci=0.05, scenario=selected_scenario, horizon=1),
            "CVaR (95%, 1y)": ptf.get_cvar(ci=0.05, scenario=selected_scenario, horizon=1),
            "P(Underfunding)": ptf.underfunding_probability(scenario=selected_scenario, horizon=horizon),
            "Avg funded ratio": ptf.funded_ratio_avg(scenario=selected_scenario, horizon=horizon),
            "Funded Ratio Vol": ptf.funded_ratio_vol(scenario=selected_scenario, horizon=horizon),
        }

        metric_specs = [
            ("Portfolio Return", selected_specs["Portfolio Return"], base_specs["Portfolio Return"]),
            ("Portfolio Vol", selected_specs["Portfolio Vol"], base_specs["Portfolio Vol"]),
            ("Sharpe Ratio", selected_specs["Sharpe Ratio"], base_specs["Sharpe Ratio"]),
            ("VaR (95%, 1y)", selected_specs["VaR (95%, 1y)"], base_specs["VaR (95%, 1y)"]),
            ("CVaR (95%, 1y)", selected_specs["CVaR (95%, 1y)"], base_specs["CVaR (95%, 1y)"]),
            ("P(Underfunding)", selected_specs["P(Underfunding)"], base_specs["P(Underfunding)"]),
            ("Avg funded ratio", selected_specs["Avg funded ratio"], base_specs["Avg funded ratio"]),
            ("Funded Ratio Vol", selected_specs["Funded Ratio Vol"], base_specs["Funded Ratio Vol"]),
        ]

        render_metric_grid(metric_specs, columns=4, compact=True)
        st.markdown("---")

    chart_cols = st.columns(2)
    for idx, scenario_name in enumerate(scenario_names):
        scenario = ptf.scenarios[scenario_name]
        with chart_cols[idx % 2]:
            st.subheader(scenario_name)
            horizon = st.session_state.horizon
            mc_paths = st.session_state.mc_paths
            scenario.mc_paths = int(mc_paths)
            scenario_paths = scenario.get_paths(horizon=horizon)
            ptf_values = ptf._get_ptf_value(scenario_name, horizon=horizon)

            p10, p25, p50, p75, p90 = np.percentile(ptf_values, [10, 25, 50, 75, 90], axis=0)
            times = scenario_paths["times"]
            liability_values = [liabilities.get_closing_liabilities(t) for t in range(0, int(horizon) + 1)]
            liability_years = np.linspace(0, horizon, len(liability_values))

            fig = build_percentile_projection_figure(
                times=times,
                percentile_values={10: p10, 25: p25, 50: p50, 75: p75, 90: p90},
                liability_values=np.asarray(liability_values, dtype=float),
                liability_years=liability_years,
            )
            fig.update_layout(
                title=dict(text=f'{scenario_name} Percentile Projection', font=dict(color='#0f172a', size=12)),
                xaxis_title=dict(text='Years', font=dict(color='#0f172a')),
                yaxis_title=dict(text='Value', font=dict(color='#0f172a')),
                template='plotly_white',
                showlegend=False,
                margin=dict(l=12, r=12, t=24, b=12),
                height=240,
                paper_bgcolor='#f8fafc',
                plot_bgcolor='#f8fafc',
                font=dict(color='#0f172a'),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(100,116,139,0.18)',
                    tickfont=dict(color='#0f172a'),
                    title_font=dict(color='#0f172a'),
                    linecolor='#0f172a',
                    zerolinecolor='#0f172a',
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(100,116,139,0.18)',
                    tickfont=dict(color='#0f172a'),
                    title_font=dict(color='#0f172a'),
                    linecolor='#0f172a',
                    zerolinecolor='#0f172a',
                ),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
