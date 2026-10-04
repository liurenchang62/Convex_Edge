from datetime import UTC, datetime, timedelta

import pytest

from convexedge.data.schema import MarketBar, ObservationTime


NOW = datetime(2026, 10, 2, 20, 0, tzinfo=UTC)


def test_observation_rejects_unavailable_information() -> None:
    with pytest.raises(ValueError, match="not available"):
        ObservationTime(NOW, NOW, NOW + timedelta(seconds=1), NOW)


def test_market_bar_checks_ohlc_invariants() -> None:
    observation = ObservationTime(NOW, NOW, NOW, NOW)
    with pytest.raises(ValueError, match="high"):
        MarketBar("AAPL", observation, 100, 99, 98, 100, 10, "fixture")

