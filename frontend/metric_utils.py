import streamlit as st

PERCENT_METRICS = {
    "Portfolio Return",
    "Portfolio Vol",
    "P(Underfunding)",
    "Avg funded ratio",
    "Funded Ratio Vol",
}

MONEY_METRICS = {
    "VaR (95%, 1y)",
    "CVaR (95%, 1y)",
}

RISK_UP_IS_BAD = {
    "Portfolio Vol",
    "VaR (95%, 1y)",
    "CVaR (95%, 1y)",
    "P(Underfunding)",
    "Funded Ratio Vol",
}


def format_metric_value(label, value, money_decimals=2):
    if label in PERCENT_METRICS:
        return f"{value:.2%}"
    if label in MONEY_METRICS:
        return f"${value:,.{money_decimals}f}"
    return f"{value:.2f}"


def format_metric_delta(label, delta, money_decimals=2):
    if label in PERCENT_METRICS:
        return f"{delta:+.2%}"
    if label in MONEY_METRICS:
        return f"${delta:+,.{money_decimals}f}"
    return f"{delta:+.2f}"


def get_metric_delta_color(label, delta):
    if label in RISK_UP_IS_BAD:
        return "inverse"
    return "normal"


def apply_metric_grid_style(label_size="0.7rem", value_size="1.15rem", delta_size="0.7rem"):
    st.markdown(
        f"""
        <style>
            div[data-testid="stMetricLabel"] {{
                font-size: {label_size} !important;
                white-space: normal !important;
            }}
            div[data-testid="stMetricValue"] {{
                font-size: {value_size} !important;
                line-height: 1.25 !important;
            }}
            div[data-testid="stMetricDelta"] {{
                font-size: {delta_size} !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_grid(metric_specs, columns=4, money_decimals=2, compact=False):
    if compact:
        apply_metric_grid_style(label_size="0.62rem", value_size="1.0rem", delta_size="0.62rem")
    else:
        apply_metric_grid_style()

    cols = st.columns(columns, gap="small")
    for idx, spec in enumerate(metric_specs):
        with cols[idx % columns]:
            if len(spec) == 2:
                label, value = spec
                benchmark_value = None
            elif len(spec) == 3:
                label, value, benchmark_value = spec
            else:
                raise ValueError(f"Metric spec must have 2 or 3 items: {spec!r}")

            if benchmark_value is None:
                st.metric(label, format_metric_value(label, value, money_decimals=money_decimals))
                continue

            delta = value - benchmark_value
            delta_text = format_metric_delta(label, delta, money_decimals=money_decimals)
            delta_color = get_metric_delta_color(label, delta)
            st.metric(
                label,
                format_metric_value(label, value, money_decimals=money_decimals),
                delta=delta_text,
                delta_color=delta_color,
            )

        if idx % columns == columns - 1 and idx != len(metric_specs) - 1:
            st.markdown("<div style='height: 0.25rem'></div>", unsafe_allow_html=True)
