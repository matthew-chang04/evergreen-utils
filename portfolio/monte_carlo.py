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
        self.paths = None

        if means is None:
            if RETURNS is None:
                raise ValueError("means must be provided if cma.RETURNS is unavailable")
            means = RETURNS
        if cov is None:
            if COVARIANCE is None:
                raise ValueError("cov must be provided if cma.COVARIANCE is unavailable")
            cov = COVARIANCE

        if asset_names is None:
            if isinstance(means, dict):
                self.asset_names = list(means.keys())
            else:
                raise ValueError("asset_names must be provided when means is not a dict")
        else:
            self.asset_names = list(asset_names)

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

        self._L = cholesky(self.cov, lower=True)
        self.num_vars = len(self.asset_names)

    @staticmethod
    def _as_weight_vector(weights, num_vars: int):
        w = np.asarray(weights, dtype=float).reshape(-1)
        if w.size != num_vars:
            raise ValueError(f"weights must contain exactly {num_vars} elements")
        return w

    def _resolve_weight_vector(self, weights: Sequence[float]):
        w = np.asarray(weights, dtype=float).reshape(-1)
        path_asset_names = self.paths.get("asset_names") if self.paths is not None else None
        if path_asset_names is not None:
            path_num_vars = len(path_asset_names)
            if w.size == path_num_vars:
                return w, path_num_vars
        if w.size == self.num_vars:
            return w, self.num_vars
        raise ValueError(f"weights must contain either {self.num_vars} elements or the path asset count ({len(path_asset_names) if path_asset_names is not None else 'unknown'})")

    def get_weighted_returns(self, weights: Sequence[float], step: Optional[int] = None):
        if self.paths is None:
            raise ValueError("Must run generate paths to obtain data")

        weights, num_vars = self._resolve_weight_vector(weights)
        prices = self.paths.get("prices")
        if prices is not None:
            price_array = np.asarray(prices, dtype=float)
            if price_array.ndim == 3 and price_array.shape[2] != num_vars:
                raise ValueError("weights do not align with the number of assets in the current paths")
            if step is None:
                step = price_array.shape[1] - 1
            start = price_array[:, 0, :]
            end = price_array[:, int(step), :]
            return np.sum(weights[None, :] * (end / start - 1.0), axis=1)

        simple_returns = np.asarray(self.paths.get("simple_returns"), dtype=float)
        if simple_returns.ndim != 3:
            raise ValueError("No weighted return distribution available in generated paths")
        if simple_returns.shape[2] != num_vars:
            raise ValueError("weights do not align with the number of assets in the current paths")
        if step is None:
            step = simple_returns.shape[1] - 1
        return np.sum(simple_returns[:, int(step), :] * weights[None, :], axis=1)

    def generate_paths(
        self,
        num_paths: int,
        horizon: float,
        points_per_year: int = 1,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate correlated asset-level return paths.

        Returns a dict with keys:
        - `log_returns`: shape (num_paths, num_steps, num_vars) incremental log-returns
        - `simple_returns`: shape (num_paths, num_steps, num_vars) = exp(log_returns)-1
        - `times`: array of time points in years (length num_steps+1)
        - `prices`: cumulative growth history with 1.0 at t=0
        - `growth_factor`: same as prices, alias retained for compatibility
        """
        num_paths = int(num_paths)
        points_per_year = int(points_per_year)
        num_steps = int(round(float(horizon) * points_per_year))
        dt = 1.0 / float(points_per_year)

        if seed is not None:
            np.random.seed(int(seed))

        z = np.random.standard_normal((num_paths, num_steps, self.num_vars))
        correlated = np.tensordot(z, self._L.T, axes=([2], [0]))

        variances = np.diag(self.cov)
        drift = (self.means - 0.5 * variances) * dt
        diffusion_scale = np.sqrt(dt)
        increments = drift[None, None, :] + correlated * diffusion_scale
        simple_returns = np.exp(increments) - 1.0

        cumulative = np.cumprod(1.0 + simple_returns, axis=1)
        growth_factor = np.concatenate(
            [np.ones((num_paths, 1, self.num_vars)), cumulative],
            axis=1,
        )

        asset_names = list(self.asset_names)
        path_result: Dict[str, Any] = {
            "log_returns": increments,
            "simple_returns": simple_returns,
            "times": np.arange(num_steps + 1) / float(points_per_year),
            "prices": growth_factor.copy(),
            "growth_factor": growth_factor.copy(),
            "asset_names": asset_names,
        }

        self.paths = path_result
        return self.paths

    def get_percentile(self, p: float, asset: Optional[str] = None, weights: Optional[Sequence[float]] = None, step: Optional[int] = None):
        if self.paths is None:
            raise ValueError("Must run generate paths to obtain data")
        if not 0.0 <= float(p) <= 1.0:
            raise ValueError("p must be between 0 and 1")

        if weights is not None:
            weighted_returns = self.get_weighted_returns(weights, step=step)
            return float(np.quantile(np.asarray(weighted_returns, dtype=float), p))

        if asset is not None:
            if asset not in self.asset_names:
                raise ValueError(f"Asset '{asset}' not found in asset_names")
            asset_idx = self.asset_names.index(asset)
            arr = np.asarray(self.paths.get("simple_returns"), dtype=float)
            if arr.ndim == 3:
                return float(np.quantile(arr[:, :, asset_idx].ravel(), p))
            return float(np.quantile(arr.ravel(), p))

        arr = np.asarray(self.paths.get("simple_returns"), dtype=float)
        if arr.ndim == 3:
            return float(np.quantile(arr.ravel(), p))
        return float(np.quantile(arr.ravel(), p))