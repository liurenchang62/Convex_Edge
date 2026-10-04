"""Leakage-aware daily stock feature construction."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from .data.volatility import close_to_close_volatility, parkinson_volatility


def build_daily_features(
    bars: pd.DataFrame,
    *,
    return_horizons: Sequence[int] = (1, 5, 21),
    volatility_windows: Sequence[int] = (21, 63),
) -> pd.DataFrame:
    """Build trailing features and forward labels on observed trading sessions.

    Features for session t become usable on the next observed session. Forward
    labels are retained for supervised learning but must never be selected as
    model inputs.
    """

    required = {"instrument_id", "session_date", "open", "high", "low", "close", "volume"}
    missing = required.difference(bars.columns)
    if missing:
        raise ValueError(f"missing daily bar columns: {sorted(missing)}")
    if any(horizon <= 0 for horizon in return_horizons):
        raise ValueError("return horizons must be positive")
    if any(window < 2 for window in volatility_windows):
        raise ValueError("volatility windows must be at least 2")

    result_frames = []
    for instrument_id, group in bars.groupby("instrument_id", sort=False):
        group = group.copy()
        group["session_date"] = pd.to_datetime(group["session_date"], errors="raise")
        group = group.sort_values("session_date").reset_index(drop=True)
        if group["session_date"].duplicated().any():
            raise ValueError(f"duplicate sessions for {instrument_id}")
        close = pd.to_numeric(group["close"], errors="raise")
        group["feature_available_session"] = group["session_date"].shift(-1)
        group["log_return_1"] = np.log(close / close.shift(1))
        for window in volatility_windows:
            group[f"rv_close_{window}"] = close_to_close_volatility(close, window)
            group[f"rv_parkinson_{window}"] = parkinson_volatility(
                group["high"], group["low"], window
            )
        for horizon in return_horizons:
            group[f"label_end_session_{horizon}"] = group["session_date"].shift(-horizon)
            group[f"forward_log_return_{horizon}"] = np.log(close.shift(-horizon) / close)
            # At row t, use returns from t+1 through t+h. Rolling at t+h
            # contains exactly that interval, then shifting by -h aligns it to t.
            future_squared = group["log_return_1"].pow(2).rolling(horizon).sum().shift(-horizon)
            group[f"forward_realized_vol_{horizon}"] = np.sqrt(
                future_squared * (252.0 / horizon)
            )
        result_frames.append(group)
    if not result_frames:
        return bars.copy()
    return pd.concat(result_frames, ignore_index=True)


def feature_columns(frame: pd.DataFrame) -> list[str]:
    """Return columns eligible as predictors, excluding labels and raw metadata."""

    forbidden_prefixes = ("forward_", "label_")
    metadata = {
        "instrument_id", "session_date", "feature_available_session", "downloaded_at", "source"
    }
    return [
        column
        for column in frame.columns
        if column not in metadata and not column.startswith(forbidden_prefixes)
    ]

