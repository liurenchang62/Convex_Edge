"""Acceptance check for deterministic model predictions."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.models.distribution import ReturnDistributionModel  # noqa: E402

rng = np.random.default_rng(42)
X = rng.normal(size=(180, 4))
y = rng.normal(size=180)
first = ReturnDistributionModel(random_state=77).fit(X[:140], y[:140]).predict(X[140:])
second = ReturnDistributionModel(random_state=77).fit(X[:140], y[:140]).predict(X[140:])
for key in first:
    assert np.array_equal(first[key], second[key])
print("PASS fixed-seed model predictions are reproducible")

