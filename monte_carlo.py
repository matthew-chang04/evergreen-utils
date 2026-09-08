"""Monte Carlo return-path generator.

This module exposes `MonteCarloSim`, a small generator focused purely on
mathematical generation of correlated return paths (log-returns and
simple returns) and optional price paths. It does not perform portfolio
valuation or liability calculations — those belong in higher-level code
(e.g. the `Scenario`/`Portfolio` objects).

Usage:
    sim = MonteCarloSim(means=..., cov=..., asset_names=...)
    out = sim.generate_paths(num_paths=1000, horizon=30)

Returned dictionary contains `log_returns`, `simple_returns`, `prices`,
`times`, and `asset_names`.
"""

from typing import Optional, Sequence, Dict, Any, List
import numpy as np
from scipy.linalg import cholesky

try:
    # default inputs if user doesn't pass means/cov
    from cma import RETURNS, COVARIANCE
except Exception:  # pragma: no cover - cma optional
    RETURNS = None
    COVARIANCE = None


class MonteCarloSim:
    """Generate correlated return paths using geometric Brownian motion.

    Parameters
    - means: mapping name->annual expected return (if None, tries to use cma.RETURNS)
    - cov: annual covariance matrix (if None, tries to use cma.COVARIANCE)
    - asset_names: optional list specifying the order of assets corresponding to means/cov
    """

    def __init__(
        self,
        means: Optional[Dict[str, float]] = None,
        cov: Optional[Sequence[Sequence[float]]] = None,
        asset_names: Optional[Sequence[str]] = None,
    ):
        if means is None:
            if RETURNS is None:
                raise ValueError("means must be provided if cma.RETURNS is unavailable")
            means = RETURNS
        if cov is None:
            if COVARIANCE is None:
                raise ValueError("cov must be provided if cma.COVARIANCE is unavailable")
            cov = COVARIANCE

        # asset order
        if asset_names is None:
            if isinstance(means, dict):
                self.asset_names = list(means.keys())
            else:
                raise ValueError("asset_names must be provided when means is not a dict")
        else:
            self.asset_names = list(asset_names)

        # means vector in the order of asset_names
        if isinstance(means, dict):
            self.means = np.array([float(means[n]) for n in self.asset_names], dtype=float)
        else:
            self.means = np.array(means, dtype=float)

        cov_arr = np.array(cov, dtype=float)
        if cov_arr.shape[0] != cov_arr.shape[1]:
            raise ValueError("covariance must be square")
        if cov_arr.shape[0] != len(self.asset_names):
            raise ValueError("covariance dimension must match number of assets")
        self.cov = cov_arr

        # precompute cholesky lower-triangular for efficiency
        self._L = cholesky(self.cov, lower=True)
        self.num_vars = len(self.asset_names)

    def generate_paths(
        self,
        num_paths: int,
        horizon: float,
        points_per_year : int = 1,
        initial_prices: Optional[Sequence[float]] = None,
        seed: Optional[int] = None,
        return_prices: bool = True,
    ) -> Dict[str, Any]:
        """Generate correlated paths.

        Returns a dict with keys:
        - `log_returns`: shape (num_paths, num_steps, num_vars) incremental log-returns
        - `simple_returns`: shape (num_paths, num_steps, num_vars) = exp(log_returns)-1
        - `prices` (optional): shape (num_paths, num_steps+1, num_vars)
        - `times`: array of time points in years (length num_steps+1)
        - `asset_names`: list of asset names
        """
        num_paths = int(num_paths)
        points_per_year = int(points_per_year)
        num_steps = int(round(float(horizon) * points_per_year))
        dt = 1.0 / float(points_per_year)

        if seed is not None:
            np.random.seed(int(seed))

        if initial_prices is None:
            initial_prices = np.ones(self.num_vars, dtype=float)
        initial_prices = np.array(initial_prices, dtype=float)
        if initial_prices.shape[0] != self.num_vars:
            raise ValueError("initial_prices length must match number of assets")

        # generate iid normals and correlate them
        z = np.random.standard_normal((num_paths, num_steps, self.num_vars))
        correlated = np.tensordot(z, self._L.T, axes=([2], [0]))

        # GBM log-return increment: (mu - 0.5*sigma^2)*dt + sqrt(dt)*epsilon_correlated
        variances = np.diag(self.cov)
        drift = (self.means - 0.5 * variances) * dt
        diffusion_scale = np.sqrt(dt)

        # increments shape (num_paths, num_steps, num_vars)
        increments = drift[None, None, :] + correlated * diffusion_scale

        # log_returns are increments; cumulative log-return per path is cumsum
        # simple returns per step
        simple_returns = np.exp(increments) - 1.0

        result: Dict[str, Any] = {
            "log_returns": increments,
            "simple_returns": simple_returns,
            "times": np.arange(num_steps + 1) / float(points_per_year),
            "asset_names": list(self.asset_names),
        }

        if return_prices:
            prices = np.zeros((num_paths, num_steps + 1, self.num_vars), dtype=float)
            prices[:, 0, :] = initial_prices[None, :]
            # cumulative log returns for each step
            cum_log = np.cumsum(increments, axis=1)
            prices[:, 1:, :] = initial_prices[None, None, :] * np.exp(cum_log)
            result["prices"] = prices

        return result

class SimpleMonteCarlo:

    def __init__(
        self,
        portfolio_mean : float,
        portfolio_var : float
    ):

        self.mean = portfolio_mean
        self.variance = portfolio_var

    def generate_paths(
        self,
        num_paths : int,
        horizon : int,
        points_per_year : int = 1,
    ):
        z = np.random.standard_normal((num_paths, horizon * points_per_year))
        returns = (self.mean / points_per_year) + ((np.sqrt(points_per_year) * np.sqrt(self.variance)) * z)

        return returns         