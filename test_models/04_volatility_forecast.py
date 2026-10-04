"""Acceptance checks comparing EWMA, GARCH, and ML volatility outputs."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.models.baselines import ewma_variance, fit_garch11  # noqa: E402
from convexedge.models.metrics import volatility_metrics  # noqa: E402
from convexedge.models.volatility import VolatilityForecastModel  # noqa: E402

rng = np.random.default_rng(42)
X = rng.normal(size=(250, 4))
target = np.exp(-2 + 0.2 * X[:, 0] + rng.normal(scale=0.05, size=250))
ml = VolatilityForecastModel(random_state=42).fit(X[:200], target[:200]).predict(X[200:])
returns = rng.normal(scale=0.01, size=200)
ewma = np.full(50, np.sqrt(ewma_variance(returns)[-1] * 252))
garch = np.full(50, fit_garch11(returns).forecast(5))
for prediction in (ml, ewma, garch):
    metrics = volatility_metrics(target[200:], prediction)
    assert all(np.isfinite(list(metrics.values())))
print("PASS EWMA, GARCH, and ML volatility metrics")

