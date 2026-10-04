"""Forward-return labels with explicit forecast intervals."""

from __future__ import annotations

import numpy as np
import pandas as pd


def forward_log_returns(
    prices: pd.Series,
    horizon: int,
    *,
    timestamps: pd.Series | pd.Index | None = None,
) -> pd.DataFrame:
    """Create log-return labels from t to t+h without backfilling endpoints."""

    if horizon <= 0:
        raise ValueError("horizon must be positive")
    numeric = pd.to_numeric(prices, errors="coerce")
    if (numeric.dropna() <= 0).any():
        raise ValueError("prices must be positive")
    times = pd.Series(prices.index if timestamps is None else timestamps, index=prices.index)
    if len(times) != len(prices):
        raise ValueError("timestamps and prices must have equal length")
    start = pd.to_datetime(times, utc=True, errors="raise")
    end = start.shift(-horizon)
    label = np.log(numeric.shift(-horizon) / numeric)
    return pd.DataFrame(
        {
            "label_start_time": start,
            "label_end_time": end,
            f"forward_log_return_{horizon}": label,
        },
        index=prices.index,
    )

