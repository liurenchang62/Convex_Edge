"""Acceptance checks for conditional return distribution outputs."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.models.distribution import ReturnDistributionModel  # noqa: E402
from convexedge.models.metrics import interval_coverage, quantile_loss  # noqa: E402

rng = np.random.default_rng(42)
X = rng.normal(size=(240, 5))
y = 0.01 * X[:, 0] - 0.005 * X[:, 1] + rng.normal(scale=0.02, size=240)
prediction = ReturnDistributionModel(random_state=42).fit(X[:180], y[:180]).predict(X[180:])
assert np.all(prediction["q10"] <= prediction["q50"])
assert np.all(prediction["q50"] <= prediction["q90"])
assert np.all((prediction["prob_up"] >= 0) & (prediction["prob_up"] <= 1))
assert quantile_loss(y[180:], prediction["q50"], 0.5) >= 0
assert 0 <= interval_coverage(y[180:], prediction["q10"], prediction["q90"]) <= 1
print("PASS return quantiles, probability, pinball loss, and coverage")

