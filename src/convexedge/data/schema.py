"""Canonical data contracts used across research, backtests, and execution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class DataQuality(StrEnum):
    VALID = "valid"
    STALE = "stale"
    CROSSED = "crossed"
    WIDE = "wide"
    MISSING = "missing"
    UNTRADABLE = "untradable"


@dataclass(frozen=True, slots=True)
class ObservationTime:
    """Time semantics for one observation.

    event_time is when the economic event occurred. source_time is the timestamp
    reported by the provider. available_time is the earliest instant the strategy
    could have observed it. as_of_time is the decision timestamp.
    """

    event_time: datetime
    source_time: datetime
    available_time: datetime
    as_of_time: datetime

    def __post_init__(self) -> None:
        values = (self.event_time, self.source_time, self.available_time, self.as_of_time)
        if any(value.tzinfo is None or value.utcoffset() is None for value in values):
            raise ValueError("all timestamps must be timezone-aware")
        if self.available_time > self.as_of_time:
            raise ValueError("observation was not available at the decision time")


@dataclass(frozen=True, slots=True)
class MarketBar:
    instrument_id: str
    observation: ObservationTime
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    source: str
    quality: DataQuality = DataQuality.VALID

    def __post_init__(self) -> None:
        if not self.instrument_id or not self.source:
            raise ValueError("instrument_id and source are required")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.high < max(self.open, self.low, self.close):
            raise ValueError("high is below another OHLC value")
        if self.low > min(self.open, self.high, self.close):
            raise ValueError("low is above another OHLC value")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume cannot be negative")

