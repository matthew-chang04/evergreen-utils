import numpy as np
import pytest

from assumptions.cma import AUM
from portfolio.liabilities import Liabilities
from portfolio.monte_carlo import MonteCarloSim
from portfolio.portfolio import AssetAlloc, Cash, FixedIncome, Portfolio


@pytest.fixture
def portfolio():
    alloc = AssetAlloc([
        (Cash(), 0.5),
        (FixedIncome(), 0.5),
    ])

    liabilities = Liabilities(
        retired_members=100,
        active_members=200,
        average_salary=50000,
        min_active_members=50,
        active_members_decline=2,
        retired_members_growth=1,
        wage_growth_rate=0.03,
        starting_duration=15,
        actuarial_df=0.05,
        service_cost=0.02,
        starting_liabilities=1000000,
        starting_benefit=10000,
        benefit_growth_rate=0.02,
        liabilities_cache={},
    )
    return Portfolio(alloc, liabilities)


def test_get_var_uses_lower_tail_of_weighted_returns(portfolio, monkeypatch):
    prices = np.array([
        [[1.0, 1.0], [1.10, 1.02]],
        [[1.0, 1.0], [0.95, 0.97]],
        [[1.0, 1.0], [1.05, 0.90]],
        [[1.0, 1.0], [0.80, 1.10]],
        [[1.0, 1.0], [1.00, 1.00]],
    ], dtype=float)
    paths = {
        "prices": prices,
        "asset_names": ["cash", "fixed_income"],
    }
    monkeypatch.setattr(portfolio.scenarios["base"], "get_paths", lambda num_paths=10000, horizon=30.0: paths)

    weights = np.array([portfolio.asset_alloc.weights[a] for a in ["cash", "fixed_income"]], dtype=float)
    weighted_returns = np.sum(
        weights * (paths["prices"][:, -1, :] / paths["prices"][:, 0, :] - 1.0),
        axis=1,
    )

    worst_5pct_return = float(np.quantile(weighted_returns, 0.05))
    expected = float(max(0.0, -worst_5pct_return) * AUM)
    assert portfolio.get_var(ci=0.95, scenario="base") == pytest.approx(expected)


def test_funded_ratio_uses_requested_horizon_for_simulation(portfolio, monkeypatch):
    seen = {}

    def fake_get_paths(self, horizon=30.0):
        seen["horizon"] = horizon
        n_steps = int(round(horizon)) + 1
        prices = np.ones((2, n_steps, 2), dtype=float)
        prices[:, :, :] = 1.0
        return {"prices": prices, "asset_names": ["cash", "fixed_income"]}

    monkeypatch.setattr(portfolio.scenarios["base"], "get_paths", fake_get_paths.__get__(portfolio.scenarios["base"], type(portfolio.scenarios["base"])))

    result = portfolio.funded_ratio_avg(scenario="base", horizon=10.0)

    assert seen["horizon"] == 10.0
    assert np.isfinite(result)


def test_generate_paths_supports_simple_weighted_return_mode():
    sim = MonteCarloSim(
        means={"cash": 0.02, "fixed_income": 0.04},
        cov=[[0.01, 0.0], [0.0, 0.04]],
        asset_names=["cash", "fixed_income"],
    )

    paths = sim.generate_paths(
        num_paths=250,
        horizon=2,
        points_per_year=1,
        seed=42,
        simple=True,
        weights=[0.5, 0.5],
    )

    assert paths["simple_returns"].shape == (250, 2)
    assert paths["portfolio_mean"] == pytest.approx(0.03)
    assert paths["portfolio_variance"] == pytest.approx(0.0125)
