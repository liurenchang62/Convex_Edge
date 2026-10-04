from datetime import UTC, datetime

import pytest

from convexedge.data.options import option_chain_frame, validate_option_reference


def test_option_chain_expands_reference_grid() -> None:
    frame = option_chain_frame(
        symbol="AAPL",
        underlying_con_id=265598,
        exchange="SMART",
        trading_class="AAPL",
        multiplier="100",
        expirations={"20261120", "20261030"},
        strikes={330.0, 335.0},
        observed_at=datetime(2026, 10, 4, tzinfo=UTC),
    )
    assert len(frame) == 4
    assert set(frame["multiplier"]) == {100}
    assert frame["expiration"].dt.tz is not None


def test_expired_reference_is_rejected() -> None:
    frame = option_chain_frame(
        symbol="AAPL",
        underlying_con_id=265598,
        exchange="SMART",
        trading_class="AAPL",
        multiplier="100",
        expirations={"20260101"},
        strikes={100.0},
        observed_at=datetime(2026, 10, 4, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="expired"):
        validate_option_reference(frame)
