import pandas as pd
import numpy as np
from scipy.linalg import cholesky
from cma import RETURNS, COVARIANCE
from typing import Optional, Sequence, Dict, Any


class MonteCarloSim:
    """Monte Carlo simulator for multiple correlated asset classes.

    The class simulates geometric Brownian motion asset prices using annual
    expected returns and an annual covariance matrix. It can value a
    portfolio given allocations and compute funded ratios vs liabilities.
    """

    def __init__(
        self,
        num_paths: int,
        horizon: int,
        days_per_year: int = 252,
        means: Optional[Dict[str, float]] = None,
        cov: Optional[Sequence[Sequence[float]]] = None,
    ):
        self.num_paths = int(num_paths)
        self.horizon = int(horizon)
        self.days_per_year = int(days_per_year)

        # Load asset names / means from cma.py by default
        if means is None:
            means = RETURNS
        self.asset_names = list(means.keys())

        self.means = np.array([means[k] for k in self.asset_names], dtype=float)

        # covariance matrix
        if cov is None:
            cov = COVARIANCE
        cov_arr = np.array(cov, dtype=float)
        if cov_arr.shape[0] != cov_arr.shape[1]:
            raise ValueError("Covariance must be a square matrix")
        if cov_arr.shape[0] != len(self.asset_names):
            raise ValueError("Covariance dimension must match number of assets")
        self.cov = cov_arr

        # derived
        self.num_vars = len(self.asset_names)

    def simulate_paths(self, allocation : dict[str, float], seed: Optional[int] = None) -> np.ndarray:

        if seed is not None:
            np.random.seed(int(seed))

        num_steps = int(self.horizon * self.days_per_year)
        dt = 1.0 / float(self.days_per_year)

        # initial prices from allocation
        if initial_prices is None:
            initial_prices = np.ones(self.num_vars, dtype=float)
        initial_prices = np.array(initial_prices, dtype=float)
        if initial_prices.shape[0] != self.num_vars:
            raise ValueError("initial_prices length must match number of assets")

        # generate standard normals: shape (num_paths, num_steps, num_vars)
        z = np.random.standard_normal((self.num_paths, num_steps, self.num_vars))

        # correlate the normals using Cholesky of the covariance matrix
        L = cholesky(self.cov, lower=True)
        # correlated normals: broadcast matmul
        correlated = np.matmul(z, L.T)

        # drift and diffusion
        variance = np.diag(self.cov)
        drift = (self.means - 0.5 * variance) * dt
        diffusion_scale = np.sqrt(dt)

        # prepare price array
        prices = np.zeros((self.num_paths, num_steps + 1, self.num_vars), dtype=float)
        prices[:, 0, :] = initial_prices[None, :]

        # iterate steps vectorized
        # increments shape (num_paths, num_steps, num_vars)
        increments = drift[None, None, :] + correlated * diffusion_scale
        log_returns = np.cumsum(increments, axis=1)
        # prices for t>0: initial * exp(log_returns)
        prices[:, 1:, :] = initial_prices[None, None, :] * np.exp(log_returns)

        return prices

    def portfolio_values(self, prices: np.ndarray, allocations: Dict[str, float], total_initial_assets: float) -> np.ndarray:
        """Compute portfolio total value across time for each path.

        - `prices` shape: (num_paths, time_points+1, num_vars)
        - `allocations`: mapping asset_name -> weight (sums to 1)
        - `total_initial_assets`: scalar starting portfolio size
        Returns array shape (num_paths, time_points+1)
        """
        # build weight vector consistent with asset_names
        weights = np.array([allocations.get(n, 0.0) for n in self.asset_names], dtype=float)
        if not np.isclose(weights.sum(), 1.0):
            # normalize if user provided non-normalized weights
            weights = weights / weights.sum()

        # compute initial holdings (number of units) from initial assets
        init_prices = prices[:, 0, :].mean(axis=0)
        holdings = (weights * float(total_initial_assets)) / init_prices

        # portfolio value over time: sum holdings * price_t
        # prices: (num_paths, time, num_vars); holdings: (num_vars,)
        portfolio_vals = np.einsum('ptv,v->pt', prices, holdings)
        return portfolio_vals

    def simulate_funded_ratio(
        self,
        total_initial_assets: float,
        allocations: Dict[str, float],
        liabilities: Optional[Any] = None,
        liability_growth: float = 0.0,
        initial_prices: Optional[Sequence[float]] = None,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Run simulation and compute funded ratio = assets / liabilities.

        `liabilities` can be:
        - None: treated as constant 1.0 (user should supply real liabilities via cma.py)
        - scalar: initial liability amount (will be grown by `liability_growth` annually)
        - array-like of length time_points+1: explicit liability path

        Returns a dict containing `prices`, `portfolio_values`, `liabilities`, and `funded_ratio`.
        """
        prices = self.simulate_paths(initial_prices=initial_prices, seed=seed)
        portfolio_vals = self.portfolio_values(prices, allocations, total_initial_assets)

        num_steps = int(self.horizon * self.days_per_year)
        times = np.arange(num_steps + 1) / float(self.days_per_year)

        # build liabilities path
        if liabilities is None:
            # try to import LIABILITY or LIABILITIES from cma.py if present
            try:
                from cma import LIABILITY  # type: ignore

                liabilities0 = float(LIABILITY)
            except Exception:
                liabilities0 = 1.0
            liab_path = liabilities0 * (1.0 + liability_growth) ** times
        elif np.isscalar(liabilities):
            liabilities0 = float(liabilities)
            liab_path = liabilities0 * (1.0 + liability_growth) ** times
        else:
            arr = np.array(liabilities, dtype=float)
            if arr.shape[0] != num_steps + 1:
                raise ValueError("liabilities array must match simulation time points (horizon * days_per_year + 1)")
            liab_path = arr

        # funded ratio per path & time
        # portfolio_vals shape (num_paths, time)
        funded = portfolio_vals / liab_path[None, :]

        # summary at horizon
        horizon_idx = -1
        horizon_vals = funded[:, horizon_idx]
        summary = {
            'median': float(np.median(horizon_vals)),
            'p10': float(np.percentile(horizon_vals, 10)),
            'p90': float(np.percentile(horizon_vals, 90)),
        }

        return {
            'prices': prices,
            'portfolio_values': portfolio_vals,
            'liabilities': liab_path,
            'funded_ratio': funded,
            'summary': summary,
            'asset_names': self.asset_names,
            'times': times,
        }
