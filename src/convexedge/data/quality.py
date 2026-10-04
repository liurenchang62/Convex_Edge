"""Deterministic market-data quality classification."""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from .schema import DataQuality


def classify_quotes(
    frame: pd.DataFrame,
    *,
    as_of_time: pd.Timestamp,
    max_age: timedelta,
    max_relative_spread: float,
) -> pd.Series:
    """Classify quotes conservatively; invalid states take precedence."""

    required = {"bid", "ask", "quote_time"}
    missing_columns = required.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"missing quote columns: {sorted(missing_columns)}")
    if max_age <= timedelta(0) or max_relative_spread <= 0:
        raise ValueError("quality thresholds must be positive")
    as_of = pd.Timestamp(as_of_time)
    if as_of.tzinfo is None:
        raise ValueError("as_of_time must be timezone-aware")
    quote_time = pd.to_datetime(frame["quote_time"], utc=True, errors="coerce")
    bid = pd.to_numeric(frame["bid"], errors="coerce")
    ask = pd.to_numeric(frame["ask"], errors="coerce")
    quality = pd.Series(DataQuality.VALID.value, index=frame.index, dtype="string")

    missing = quote_time.isna() | bid.isna() | ask.isna() | (bid <= 0) | (ask <= 0)
    crossed = ~missing & (bid > ask)
    stale = ~missing & ~crossed & ((as_of.tz_convert("UTC") - quote_time) > max_age)
    midpoint = (bid + ask) / 2.0
    relative_spread = (ask - bid) / midpoint.replace(0, np.nan)
    wide = ~missing & ~crossed & ~stale & (relative_spread > max_relative_spread)

    quality.loc[wide] = DataQuality.WIDE.value
    quality.loc[stale] = DataQuality.STALE.value
    quality.loc[crossed] = DataQuality.CROSSED.value
    quality.loc[missing] = DataQuality.MISSING.value
    return quality

