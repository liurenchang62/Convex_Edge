import pandas as pd
import pytest

from convexedge.data.pit import PointInTimeViolation, asof_join, validate_point_in_time


def test_future_field_is_rejected() -> None:
    frame = pd.DataFrame(
        {
            "event_time": ["2026-01-01T20:00:00Z"],
            "source_time": ["2026-01-01T20:01:00Z"],
            "available_time": ["2026-01-01T20:02:00Z"],
            "as_of_time": ["2026-01-01T20:01:30Z"],
        }
    )
    with pytest.raises(PointInTimeViolation, match="future information"):
        validate_point_in_time(frame)


def test_asof_join_uses_latest_available_not_latest_event() -> None:
    decisions = pd.DataFrame(
        {"instrument_id": ["AAPL"], "as_of_time": ["2026-01-02T15:00:00Z"]}
    )
    observations = pd.DataFrame(
        {
            "instrument_id": ["AAPL", "AAPL"],
            "event_time": ["2026-01-02T14:00:00Z", "2026-01-01T20:00:00Z"],
            "available_time": ["2026-01-02T16:00:00Z", "2026-01-01T20:01:00Z"],
            "value": [999.0, 100.0],
        }
    )
    result = asof_join(decisions, observations)
    assert result.loc[0, "value"] == 100.0

