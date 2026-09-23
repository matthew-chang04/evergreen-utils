from typing import Optional, Sequence, Dict, Any
import numpy as np
from scipy.linalg import cholesky
from assumptions.cma import RETURNS, COVARIANCE

    
    


class MonteCarloSim:
    """

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

    def _portfolio_metrics(self, weights: Optional[Sequence[float]] = None):
        if weights is None:
            weights = np.full(self.num_vars, 1.0 / self.num_vars, dtype=float)
        weights = np.asarray(weights, dtype=float)
        if weights.shape[0] != self.num_vars:
            raise ValueError("weights length must match number of assets")
        total_weight = float(np.sum(weights))
        if np.isclose(total_weight, 0.0):
            raise ValueError("weights must sum to a non-zero value")
        weights = weights / total_weight
        portfolio_mean = float(weights @ self.means)
        portfolio_variance = float(weights @ self.cov @ weights)
        return weights, portfolio_mean, portfolio_variance

    def generate_paths(
        self,
        num_paths: int,
        horizon: float,
        points_per_year: int = 1,
        initial_prices: Optional[Sequence[float]] = None,
        seed: Optional[int] = None,
        return_prices: bool = True,
        simple: bool = False,
        weights: Optional[Sequence[float]] = None,
    ) -> Dict[str, Any]:
        """Generate either full correlated asset paths or a simplified weighted-portfolio path.

        When `simple=True`, the simulation reduces to a single weighted portfolio return and
        variance projected across the requested horizon. It returns `simple_returns` as a
        2D array of shape (num_paths, num_steps), plus the aggregate portfolio mean/variance.
        """
        num_paths = int(num_paths)
        points_per_year = int(points_per_year)
        num_steps = int(round(float(horizon) * points_per_year))
        dt = 1.0 / float(points_per_year)

        if seed is not None:
            np.random.seed(int(seed))

        if simple:
            weight_vec, portfolio_mean, portfolio_variance = self._portfolio_metrics(weights)
            z = np.random.standard_normal((num_paths, num_steps))
            drift = portfolio_mean * dt
            diffusion = np.sqrt(max(portfolio_variance * dt, 0.0))
            simple_returns = drift + diffusion * z

            result: Dict[str, Any] = {
                "simple_returns": simple_returns,
                "portfolio_mean": float(portfolio_mean),
                "portfolio_variance": float(portfolio_variance),
                "portfolio_std_dev": float(np.sqrt(max(portfolio_variance, 0.0))),
                "times": np.arange(num_steps + 1) / float(points_per_year),
                "asset_names": list(self.asset_names),
                "weights": weight_vec,
            }

            if return_prices:
                path_values = np.cumprod(np.clip(1.0 + simple_returns, 1e-12, None), axis=1)
                prices = np.ones((num_paths, num_steps + 1), dtype=float)
                prices[:, 1:] = path_values
                result["prices"] = prices

            return result

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


        print(result["simple_returns"])
        return result

class SimpleMonteCarlo:

    def __init__(
        self,
        portfolio_mean : float,
        portfolio_var : float
    ):

        self.mean = float(portfolio_mean)
        self.variance = float(portfolio_var)

    def generate_paths(
        self,
        num_paths : int,
        horizon : int,
        points_per_year : int = 1,
    ):
        num_paths = int(num_paths)
        points_per_year = int(points_per_year)
        steps = int(round(float(horizon) * points_per_year))
        z = np.random.standard_normal((num_paths, steps))
        drift = self.mean / float(points_per_year)
        diffusion = np.sqrt(max(self.variance / float(points_per_year), 0.0))
        returns = drift + diffusion * z
        return returns
