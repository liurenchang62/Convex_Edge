from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from convexedge.data.ibkr import normalize_daily_bars, normalize_historical_bars, parse_ibkr_epoch
from convexedge.data.pit import PointInTimeViolation


@dataclass
class Bar:
    date: str
    open: float = 100
    high: float = 102
    low: float = 99
    close: float = 101
    volume: float = 1000
    average: float = 100.5
    barCount: int = 20


def test_epoch_is_always_utc() -> None:
    assert parse_ibkr_epoch("0") == datetime(1970, 1, 1, tzinfo=UTC)


def test_completed_bar_is_available_at_interval_end() -> None:
    bar = Bar(str(int(datetime(2026, 1, 2, 14, 30, tzinfo=UTC).timestamp())))
    frame = normalize_historical_bars(
        [bar],
        instrument_id="AAPL",
        bar_size=timedelta(minutes=5),
        as_of_time=datetime(2026, 1, 2, 14, 35, tzinfo=UTC),
    )
    assert frame.loc[0, "available_time"] == datetime(2026, 1, 2, 14, 35, tzinfo=UTC)


def test_incomplete_bar_cannot_enter_decision_frame() -> None:
    bar = Bar(str(int(datetime(2026, 1, 2, 14, 30, tzinfo=UTC).timestamp())))
    with pytest.raises(PointInTimeViolation, match="future information"):
        normalize_historical_bars(
            [bar],
            instrument_id="AAPL",
            bar_size=timedelta(minutes=5),
            as_of_time=datetime(2026, 1, 2, 14, 34, 59, tzinfo=UTC),
        )


def test_daily_bars_preserve_session_date_without_fake_close_time() -> None:
    bar = Bar("20260102")
    frame = normalize_daily_bars(
        [bar], instrument_id="AAPL", downloaded_at=datetime(2026, 1, 3, tzinfo=UTC)
    )
    assert str(frame.loc[0, "session_date"]) == "2026-01-02"
    assert "available_time" not in frame.columns

