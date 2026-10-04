"""Acceptance checks for holdout calibration and Brier score."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.models.calibration import SigmoidCalibrator  # noqa: E402
from convexedge.models.metrics import probability_metrics  # noqa: E402

rng = np.random.default_rng(42)
raw = np.linspace(0.05, 0.95, 200)
y = rng.binomial(1, np.sqrt(raw))
calibrator = SigmoidCalibrator(random_state=42).fit(raw[:100], y[:100])
prediction = calibrator.predict(raw[100:])
metrics = probability_metrics(y[100:], prediction, n_bins=5)
assert 0 <= metrics["brier"] <= 1
assert not metrics["calibration"].empty
print(f"PASS probability calibration brier={metrics['brier']:.6f}")

