"""Transparent mean and volatility baselines."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def historical_distribution(y, quantiles=(0.1, 0.5, 0.9)) -> dict[float, float]:
    values = np.asarray(y, dtype=float)
    values = values[np.isfinite(values)]
    if not len(values):
        raise ValueError("at least one finite observation is required")
    return {float(q): float(np.quantile(values, q)) for q in quantiles}


def historical_up_probability(y, *, smoothing: float = 1.0) -> float:
    values = np.asarray(y, dtype=float)
    values = values[np.isfinite(values)]
    return float(((values > 0).sum() + smoothing) / (len(values) + 2 * smoothing))


def ewma_variance(returns, decay: float = 0.94) -> np.ndarray:
    if not 0 < decay < 1:
        raise ValueError("decay must lie between zero and one")
    values = np.asarray(returns, dtype=float)
    if len(values) < 2:
        raise ValueError("at least two returns are required")
    variance = np.empty_like(values)
    variance[0] = np.nanvar(values, ddof=1)
    for index in range(1, len(values)):
        variance[index] = decay * variance[index - 1] + (1 - decay) * values[index - 1] ** 2
    return variance


def linear_baseline(*, alpha: float = 1.0):
    """Median-imputed, standardized ridge baseline."""

    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=alpha))


@dataclass(frozen=True, slots=True)
class Garch11:
    omega: float
    alpha: float
    beta: float
    last_variance: float
    last_squared_return: float

    def forecast(self, horizon: int = 1, *, annualization: float = 252.0) -> float:
        if horizon <= 0:
            raise ValueError("horizon must be positive")
        variance = self.omega + self.alpha * self.last_squared_return + self.beta * self.last_variance
        forecasts = []
        persistence = self.alpha + self.beta
        for _ in range(horizon):
            forecasts.append(variance)
            variance = self.omega + persistence * variance
        return float(np.sqrt(np.mean(forecasts) * annualization))


def fit_garch11(returns) -> Garch11:
    values = np.asarray(returns, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 30:
        raise ValueError("GARCH requires at least 30 finite returns")
    centered = values - values.mean()
    sample_variance = max(float(np.var(centered)), 1e-10)

    def unpack(raw):
        alpha = 0.30 / (1.0 + np.exp(-raw[0]))
        beta = (0.999 - alpha) / (1.0 + np.exp(-raw[1]))
        omega = np.exp(raw[2])
        return omega, alpha, beta

    def likelihood(raw):
        omega, alpha, beta = unpack(raw)
        variance = np.empty_like(centered)
        variance[0] = sample_variance
        for index in range(1, len(centered)):
            variance[index] = omega + alpha * centered[index - 1] ** 2 + beta * variance[index - 1]
        variance = np.maximum(variance, 1e-12)
        return 0.5 * np.sum(np.log(variance) + centered**2 / variance)

    initial = np.array([-1.5, 3.0, np.log(sample_variance * 0.05)])
    result = minimize(likelihood, initial, method="L-BFGS-B")
    if not result.success:
        raise RuntimeError(f"GARCH optimization failed: {result.message}")
    omega, alpha, beta = unpack(result.x)
    variance_path = np.empty_like(centered)
    variance_path[0] = sample_variance
    for index in range(1, len(centered)):
        variance_path[index] = (
            omega + alpha * centered[index - 1] ** 2 + beta * variance_path[index - 1]
        )
    return Garch11(omega, alpha, beta, float(variance_path[-1]), float(centered[-1] ** 2))

