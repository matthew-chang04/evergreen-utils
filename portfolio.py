from dataclasses import dataclass
import numpy as np
from cma import RETURNS, STD_DEV, COVARIANCE, BASE_SAA, INTEREST_RATE, ASSET_ORDER, SCENARIO_DELTAS
from pension import Liabilities
from monte_carlo import MonteCarloSim
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
    dc : int

    def __init__(self, scenario : str = "base", horizon : float = 30.0, dc : int = 252):
        self.horizon = horizon
        self.dc = dc
        self.paths = None
        scenario_deltas = SCENARIO_DELTAS.get(scenario)

        if scenario_deltas is None:
            raise ValueError(f"Scenario {scenario} not recognized")

        input_means = RETURNS.copy()
        for asset in input_means:
            input_means[asset] += scenario_deltas["returns"][asset]

        self.monte_carlo = MonteCarloSim(input_means, COVARIANCE, ASSET_ORDER)

    def get_paths(self, num_paths: int = 1000, horizon: float = 30.0):

        if self.paths is None:
            self.paths = self.monte_carlo.generate_paths(num_paths, horizon)

        return self.paths

    
class Portfolio:
    asset_alloc : AssetAlloc
    liabilities : Liabilities
    scenarios : dict[str, Scenario]

    def __init__(self, asset_alloc, liabilities):
        self.asset_alloc = asset_alloc
        self.liabilities = liabilities

    def run_scenario(self, scenario : str = "base") -> Scenario:
        if scenario in self.scenarios:
            return self.scenarios[scenario]
        else:
            self.scenarios[scenario] = Scenario(scenario)
            self.scenarios[scenario].get_paths()
            return self.scenarios[scenario]


    def get_var(self, ci : float = 0.95, scenario : str = "base"):
        s = self.scenarios[scenario]
        paths = s.get_paths(num_paths=10000, horizon=s.horizon)

        # asset weights in the same order as the scenario output
        asset_names = paths["asset_names"]
        weights = np.array([self.asset_alloc.weights[a] for a in asset_names], dtype=float)

        # final portfolio value relative to initial value
        initial_prices = paths["prices"][:, 0, :]
        final_prices = paths["prices"][:, -1, :]

        # assumes initial portfolio value = 1.0
        end_values = np.sum(weights * (final_prices / initial_prices), axis=1)
        losses = 1.0 - end_values  # positive means a loss

        return float(np.quantile(losses, ci))

    
    def _get_funded_ratio(self, assets : float, t : int):
        l = self.liabilities.get_closing_liabilities(t)
        return assets / l

    def underfunding_probability(self, scenario : str = "base"):
        s = self.scenarios[scenario]
        paths = s.get_paths()

        paths['prices'][:, -1, :]