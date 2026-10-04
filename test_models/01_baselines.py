"""Acceptance checks for historical, EWMA, and GARCH baselines."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.models.baselines import (  # noqa: E402
    ewma_variance,
    fit_garch11,
    historical_distribution,
    historical_up_probability,
    linear_baseline,
)

rng = np.random.default_rng(42)
returns = rng.normal(0.0005, 0.01, 400)
distribution = historical_distribution(returns)
assert distribution[0.1] <= distribution[0.5] <= distribution[0.9]
assert 0 <= historical_up_probability(returns) <= 1
assert np.all(ewma_variance(returns) > 0)
garch = fit_garch11(returns)
assert garch.omega > 0 and garch.alpha >= 0 and garch.beta >= 0
assert garch.alpha + garch.beta < 1 and garch.forecast(5) > 0
X = rng.normal(size=(400, 3))
linear = linear_baseline().fit(X[:300], returns[:300]).predict(X[300:])
assert np.all(np.isfinite(linear))
print("PASS historical, EWMA, GARCH, and linear baselines")

