"""Realized-volatility estimators."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _validate_window(window: int, periods_per_year: float) -> None:
    if window < 2:
        raise ValueError("window must be at least 2")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")


def close_to_close_volatility(
    close: pd.Series,
    window: int,
    *,
    periods_per_year: float = 252.0,
) -> pd.Series:
    """Annualized rolling standard deviation of close-to-close log returns."""

    _validate_window(window, periods_per_year)
    numeric = pd.to_numeric(close, errors="coerce")
    if (numeric.dropna() <= 0).any():
        raise ValueError("close prices must be positive")
    returns = np.log(numeric / numeric.shift(1))
    return returns.rolling(window=window, min_periods=window).std(ddof=1) * np.sqrt(periods_per_year)


def parkinson_volatility(
    high: pd.Series,
    low: pd.Series,
    window: int,
    *,
    periods_per_year: float = 252.0,
) -> pd.Series:
    """Annualized Parkinson range volatility over a rolling window."""

    _validate_window(window, periods_per_year)
    high_values = pd.to_numeric(high, errors="coerce")
    low_values = pd.to_numeric(low, errors="coerce")
    valid = high_values.notna() & low_values.notna()
    if ((high_values[valid] <= 0) | (low_values[valid] <= 0)).any():
        raise ValueError("high and low must be positive")
    if (high_values[valid] < low_values[valid]).any():
        raise ValueError("high cannot be below low")
    squared_range = np.log(high_values / low_values) ** 2
    variance = squared_range.rolling(window=window, min_periods=window).mean() / (4.0 * np.log(2.0))
    return np.sqrt(variance * periods_per_year)

