from frontend.metric_utils import get_metric_delta_color


def test_risk_metric_delta_is_red_for_positive_increase_and_green_for_negative_drop():
    assert get_metric_delta_color("VaR (95%, 1y)", 2500.0) == "bad"
    assert get_metric_delta_color("VaR (95%, 1y)", -2500.0) == "good"
    assert get_metric_delta_color("CVaR (95%, 1y)", 4000.0) == "bad"
    assert get_metric_delta_color("CVaR (95%, 1y)", -4000.0) == "good"


def test_growth_metric_delta_stays_positive_green_and_negative_red():
    assert get_metric_delta_color("Portfolio Return", 0.05) == "good"
    assert get_metric_delta_color("Portfolio Return", -0.05) == "bad"
