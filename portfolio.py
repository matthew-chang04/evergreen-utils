from dataclasses import dataclass
import numpy as np
from cma import RETURNS, STD_DEV, COVARIANCE, BASE_SAA, INTEREST_RATE, ASSET_ORDER, SCENARIO_DELTAS, AUM
from pension import Liabilities
from monte_carlo import MonteCarloSim, SimpleMonteCarlo
from math import sqrt

@dataclass
class Asset:
    name: str = "Asset"
    expected_return: float = 0.0
    variance: float = 0.0
    liquidity: float = 1.0
    asset_class: str = "Asset"

@dataclass
class Cash(Asset):
    name: str = "cash"
    expected_return: float = RETURNS["cash"]
    variance: float = COVARIANCE[0][0]
    liquidity: float = 1.0
    asset_class: str = "Cash"

@dataclass
class FixedIncome(Asset):
    name: str = "fixed_income"
    expected_return: float = RETURNS["fixed_income"]
    variance: float = COVARIANCE[1][1]
    liquidity: float = 1.0
    asset_class: str = "FixedIncome"

@dataclass
class CanEquity(Asset):
    name: str = "can_equity"
    expected_return: float = RETURNS["can_equity"]
    variance: float = COVARIANCE[2][2]
    liquidity: float = 1.0
    asset_class: str = "Equity"

@dataclass
class USEquity(Asset):
    name: str = "us_equity"
    expected_return: float = RETURNS["us_equity"]
    variance: float = COVARIANCE[3][3]
    liquidity: float = 1.0
    asset_class: str = "Equity"


@dataclass
class IDEquity(Asset):
    name: str = "id_equity"
    expected_return: float = RETURNS["id_equity"]
    variance: float = COVARIANCE[4][4]
    liquidity: float = 1.0
    asset_class: str = "Equity"

@dataclass
class EMEquity(Asset):
    name: str = "em_equity"
    expected_return: float = RETURNS["em_equity"]
    variance: float = COVARIANCE[5][5]
    liquidity: float = 1.0
    asset_class: str = "Equity"

@dataclass
class RealEstate(Asset):
    name: str = "real_estate"
    expected_return: float = RETURNS["real_estate"]
    variance: float = COVARIANCE[6][6]
    liquidity: float = 1.0
    asset_class: str = "RealAssets"

@dataclass
class Infrastructure(Asset):
    name: str = "infrastructure"
    expected_return: float = RETURNS["infrastructure"]
    variance: float = COVARIANCE[7][7]
    liquidity: float = 1.0
    asset_class: str = "RealAssets"

@dataclass
class PrivateEquity(Asset):
    name: str = "private_equity"
    expected_return: float = RETURNS["private_equity"]
    variance: float = COVARIANCE[8][8]
    liquidity: float = 1.0
    asset_class: str = "PrivateEquity"


class AssetAlloc:

    assets : dict[str, Asset]
    weights : dict[str, float]

    def __init__(self, assets : list[tuple[Asset, float]]):
        self.assets = { asset.name : asset for asset, _ in assets }
        self.weights = { asset.name : weight for asset, weight in assets }

        if sum(self.weights.values()) != 1.0:
            raise ValueError("Weights must sum to 100%")

    def _ordered_weight_vec(self):
        weight_vec = []
        for asset in ASSET_ORDER:
            weight_vec.append(self.weights[asset])
        return weight_vec

    def get_expected_return(self):

        weighted_returns_vec = []
        for asset in self.assets:
            weighted_returns_vec.append(self.assets[asset].expected_return * self.weights[asset]) 

        return sum(weighted_returns_vec)

    def get_variance(self):

        w = np.asarray(self._ordered_weight_vec(), dtype=float)

        return float(w @ COVARIANCE @ w.T)

    def get_std_dev(self):
        return sqrt(self.get_variance())


    def get_sharpe(self):
        e_x = self.get_expected_return()
        vol = self.get_std_dev()

        return (e_x - INTEREST_RATE) / vol

    def get_asset_drift(self):
        pass

class Scenario:
    monte_carlo : MonteCarloSim
    horizon : float
    comp : int

    def __init__(
            self, 
            scenario : str = "base", 
            horizon : float = 30.0, 
            dc : int = 1, 
            mc_paths: int = 10000, 
            scenario_deltas : dict | None = None
        ):

        self.horizon = horizon
        self.comp = dc
        self.paths = None
        self._paths_horizon = None
        self.mc_paths = mc_paths

        if scenario_deltas is None:
            if scenario in SCENARIO_DELTAS:
                scenario_deltas = SCENARIO_DELTAS.get(scenario)
            else: 
                raise ValueError(f"Scenario {scenario} not recognized")

        input_means = RETURNS.copy()
        for asset in input_means:
            input_means[asset] += scenario_deltas["returns"][asset]

        self.monte_carlo = MonteCarloSim(input_means, COVARIANCE, ASSET_ORDER)

    def get_paths(self, horizon: float | None = None):
        if horizon is None:
            horizon = self.horizon

        if self.paths is None or self._paths_horizon != horizon:
            self.paths = self.monte_carlo.generate_paths(self.mc_paths, horizon, points_per_year=self.comp)
            self._paths_horizon = horizon

        return self.paths

    
class Portfolio:
    asset_alloc : AssetAlloc
    liabilities : Liabilities
    scenarios : dict[str, Scenario]

    def __init__(self, asset_alloc, liabilities):
        self.asset_alloc = asset_alloc
        self.liabilities = liabilities
        self.scenarios = {}

        for s in SCENARIO_DELTAS:
            self.scenarios[s] = Scenario(s)
    def add_scenario(self, name : str, deltas : dict):
        if name in self.scenarios:
            raise ValueError(f"Cannot add scenario with name {name} as it is already present")
        self.scenarios[name] = Scenario(scenario=name, scenario_deltas=deltas)

    def run_scenario(self, scenario : str = "base") -> Scenario:
        if scenario in self.scenarios:
            return self.scenarios[scenario]
        else:
            self.scenarios[scenario] = Scenario(scenario)
            self.scenarios[scenario].get_paths()
            return self.scenarios[scenario]


    def get_var(self, ci : float = 0.95, scenario : str = "base", horizon : int = 1):
        s = self.run_scenario(scenario)
        paths = s.get_paths(horizon=horizon)

        asset_names = paths["asset_names"]
        weights = np.array([self.asset_alloc.weights.get(a, 0.0) for a in asset_names], dtype=float)

        initial_prices = paths["prices"][:, 0, :]
        final_idx = int(round(horizon * s.comp))
        final_prices = paths["prices"][:, final_idx, :]

        weighted_returns = np.sum(
            weights * (final_prices / initial_prices - 1.0),
            axis=1,
        )

        worst_return = float(np.quantile(weighted_returns, 1.0 - ci))
        return float(max(0.0, -worst_return) * AUM)

    def get_cvar(self, ci : float = 0.95, scenario : str = "base", horizon : int = 1):
        s = self.run_scenario(scenario)
        paths = s.get_paths(horizon=horizon)

        asset_names = paths["asset_names"]
        weights = np.array([self.asset_alloc.weights.get(a, 0.0) for a in asset_names], dtype=float)

        initial_prices = paths["prices"][:, 0, :]
        final_idx = int(round(horizon * s.comp))
        final_prices = paths["prices"][:, final_idx, :]

        weighted_returns = np.sum(
            weights * (final_prices / initial_prices - 1.0),
            axis=1,
        )

        var_return = float(np.quantile(weighted_returns, 1.0 - ci))
        tail = weighted_returns[weighted_returns <= var_return]
        if tail.size == 0:
            return float(max(0.0, -var_return) * AUM)
        return float(max(0.0, -np.mean(tail)) * AUM)

    def _get_ptf_value(self, scenario : str = "base", horizon : float | None = None):
        s = self.run_scenario(scenario)
        if horizon is None:
            horizon = s.horizon
        paths = s.get_paths(horizon=horizon)

        asset_names = paths["asset_names"]
        weights = np.array([self.asset_alloc.weights.get(a, 0.0) for a in asset_names], dtype=float)

        start_vals = AUM * weights

        growth = paths["prices"] / paths["prices"][:, 0, :][:, None, :]
        asset_vals = growth * start_vals[None, None, :]

        ptf_value = asset_vals.sum(axis=2)

        return ptf_value

     
    def _get_funded_ratio(self, assets : float, t : int):
        l = self.liabilities.get_closing_liabilities(t)
        return assets / l

    def underfunding_probability(self, scenario : str = "base", horizon : float = 30.0):
        s = self.run_scenario(scenario)
        ptf_values = self._get_ptf_value(scenario, horizon=horizon)
        final_idx = int(round(horizon * s.comp))

        l = self.liabilities.get_closing_liabilities(int(horizon))
        final_vals = ptf_values[:, final_idx]

        underfunded_cases = final_vals < l 
        return float(np.mean(underfunded_cases))

    
    def funded_ratio_avg(self, scenario : str = "base", horizon : float = 30.0):
        s = self.run_scenario(scenario)
        ptf_value = self._get_ptf_value(scenario, horizon=horizon)
        final_idx = int(round(horizon * s.comp))
        funded_ratios = np.array([self._get_funded_ratio(a, int(horizon)) for a in ptf_value[:, final_idx]])

        return np.mean(funded_ratios)
        
    def funded_ratio_vol(self, scenario : str = "base", horizon : float = 30.0):
        s = self.run_scenario(scenario)
        ptf_value = self._get_ptf_value(scenario, horizon=horizon)
        final_idx = int(round(horizon * s.comp))

        funded_ratios = np.array([self._get_funded_ratio(a, int(horizon)) for a in ptf_value[:, final_idx]])
        return np.std(funded_ratios, ddof=1)

    def portfolio_avg(self, scenario : str = "base", horizon : float | None = None):
        s = self.run_scenario(scenario)
        if horizon is None:
            horizon = s.horizon
        ptf_value = self._get_ptf_value(scenario, horizon=horizon)

        return np.mean(ptf_value)

    def portfolio_vol(self, scenario : str = "base", horizon : float | None = None):
        s = self.run_scenario(scenario)
        if horizon is None:
            horizon = s.horizon
        ptf_value = self._get_ptf_value(scenario, horizon=horizon)

        return np.std(ptf_value, ddof=1)