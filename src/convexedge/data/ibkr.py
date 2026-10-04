"""Normalization helpers for read-only IBKR historical bar responses."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Iterable, Protocol

import pandas as pd

from .pit import validate_point_in_time


class IbkrBar(Protocol):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    average: float
    barCount: int


def parse_ibkr_epoch(value: str | int) -> datetime:
    """Parse an IBKR formatDate=2 intraday timestamp as UTC."""

    try:
        seconds = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"expected IBKR epoch seconds, received {value!r}") from exc
    return datetime.fromtimestamp(seconds, tz=UTC)


def normalize_historical_bars(
    bars: Iterable[IbkrBar],
    *,
    instrument_id: str,
    bar_size: timedelta,
    as_of_time: datetime,
    source: str = "ibkr_tws",
) -> pd.DataFrame:
    """Convert IBKR bars to the canonical PIT schema.

    IBKR intraday bar timestamps denote interval starts. A completed bar becomes
    usable at its interval end. The caller's as_of_time is the decision timestamp,
    not the local download time hidden inside the function.
    """

    if bar_size <= timedelta(0):
        raise ValueError("bar_size must be positive")
    if as_of_time.tzinfo is None or as_of_time.utcoffset() is None:
        raise ValueError("as_of_time must be timezone-aware")
    as_of_utc = as_of_time.astimezone(UTC)
    rows: list[dict[str, object]] = []
    for bar in bars:
        event_time = parse_ibkr_epoch(bar.date)
        available_time = event_time + bar_size
        rows.append(
            {
                "instrument_id": instrument_id,
                "event_time": event_time,
                "source_time": event_time,
                "available_time": available_time,
                "as_of_time": as_of_utc,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
                "average": float(bar.average),
                "bar_count": int(bar.barCount),
                "source": source,
            }
        )
    columns = [
        "instrument_id", "event_time", "source_time", "available_time", "as_of_time",
        "open", "high", "low", "close", "volume", "average", "bar_count", "source",
    ]
    frame = pd.DataFrame(rows, columns=columns)
    if frame.empty:
        return frame
    return validate_point_in_time(frame)


def normalize_daily_bars(
    bars: Iterable[IbkrBar],
    *,
    instrument_id: str,
    downloaded_at: datetime,
    source: str = "ibkr_tws",
) -> pd.DataFrame:
    """Normalize IBKR daily bars without inventing an intraday availability time."""

    if downloaded_at.tzinfo is None or downloaded_at.utcoffset() is None:
        raise ValueError("downloaded_at must be timezone-aware")
    rows: list[dict[str, object]] = []
    for bar in bars:
        session_date = pd.to_datetime(bar.date, format="%Y%m%d", errors="raise").date()
        rows.append(
            {
                "instrument_id": instrument_id,
                "session_date": session_date,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
                "average": float(bar.average),
                "bar_count": int(bar.barCount),
                "downloaded_at": downloaded_at.astimezone(UTC),
                "source": source,
            }
        )
    return pd.DataFrame(rows)

