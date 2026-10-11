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
    if delta == 0:
        return "off"

    if label in RISK_UP_IS_BAD:
        return "inverse"

    return "normal"



def render_metric_grid(metric_specs, columns=4, money_decimals=2, compact=False):
    del compact

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

            value_text = format_metric_value(label, value, money_decimals=money_decimals)
            if benchmark_value is None:
                st.metric(label, value_text)
                continue

            delta = value - benchmark_value
            delta_text = format_metric_delta(label, delta, money_decimals=money_decimals)
            delta_color = get_metric_delta_color(label, delta)
            st.metric(label, value_text, delta=delta_text, delta_color=delta_color)
