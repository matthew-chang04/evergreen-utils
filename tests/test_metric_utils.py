from unittest.mock import MagicMock, patch

from frontend.metric_utils import get_metric_delta_color, render_metric_grid


def test_risk_metric_delta_uses_inverse_for_both_rises_and_falls():
    assert get_metric_delta_color("VaR (95%, 1y)", 2500.0) == "inverse"
    assert get_metric_delta_color("VaR (95%, 1y)", -2500.0) == "inverse"
    assert get_metric_delta_color("CVaR (95%, 1y)", 4000.0) == "inverse"
    assert get_metric_delta_color("CVaR (95%, 1y)", -4000.0) == "inverse"


def test_growth_metric_delta_uses_standard_positive_green_and_negative_red():
    assert get_metric_delta_color("Portfolio Return", 0.05) == "normal"
    assert get_metric_delta_color("Portfolio Return", -0.05) == "normal"


def test_metric_grid_uses_streamlit_metric_with_delta_and_delta_color():
    with patch("frontend.metric_utils.st.columns", return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()]), patch(
        "frontend.metric_utils.st.metric"
    ) as metric_mock:
        render_metric_grid(
            [
                ("Portfolio Return", 0.10, 0.08),
                ("VaR (95%, 1y)", 150000.0, 100000.0),
            ],
            columns=4,
        )

    assert metric_mock.call_count == 2
    metric_mock.assert_any_call("Portfolio Return", "10.00%", delta="+2.00%", delta_color="normal")
    metric_mock.assert_any_call("VaR (95%, 1y)", "$150,000.00", delta="$+50,000.00", delta_color="inverse")
