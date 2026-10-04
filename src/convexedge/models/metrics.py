"""Metrics for probabilistic returns and volatility forecasts."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss, mean_absolute_error, mean_squared_error


def quantile_loss(y_true, y_pred, quantile: float) -> float:
    if not 0 < quantile < 1:
        raise ValueError("quantile must be between zero and one")
    error = np.asarray(y_true) - np.asarray(y_pred)
    return float(np.mean(np.maximum(quantile * error, (quantile - 1) * error)))


def interval_coverage(y_true, lower, upper) -> float:
    y = np.asarray(y_true)
    lo, hi = np.asarray(lower), np.asarray(upper)
    if np.any(lo > hi):
        raise ValueError("lower prediction exceeds upper prediction")
    return float(np.mean((y >= lo) & (y <= hi)))


def probability_metrics(y_true, probability, *, n_bins: int = 5) -> dict[str, object]:
    y = np.asarray(y_true, dtype=int)
    probability = np.clip(np.asarray(probability, dtype=float), 0, 1)
    observed, predicted = calibration_curve(y, probability, n_bins=n_bins, strategy="quantile")
    return {
        "brier": float(brier_score_loss(y, probability)),
        "calibration": pd.DataFrame({"predicted": predicted, "observed": observed}),
    }


def volatility_metrics(y_true, y_pred) -> dict[str, float]:
    y = np.asarray(y_true, dtype=float)
    pred = np.maximum(np.asarray(y_pred, dtype=float), 1e-12)
    cutoff = np.quantile(y, 0.8)
    high = y >= cutoff
    return {
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(mean_squared_error(y, pred) ** 0.5),
        "qlike": float(np.mean(np.log(pred**2) + (y**2) / (pred**2))),
        "high_vol_mae": float(mean_absolute_error(y[high], pred[high])),
    }

