import numpy as np
import pandas as pd

from convexedge.features import build_daily_features, feature_columns


def sample_bars(rows: int = 70) -> pd.DataFrame:
    close = 100 * np.exp(np.arange(rows) * 0.01)
    return pd.DataFrame(
        {
            "instrument_id": "AAPL",
            "session_date": pd.bdate_range("2026-01-01", periods=rows),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1000,
        }
    )


def test_features_are_available_next_observed_session() -> None:
    result = build_daily_features(sample_bars())
    assert result.loc[0, "feature_available_session"] == result.loc[1, "session_date"]
    assert np.isclose(result.loc[0, "forward_log_return_5"], 0.05)


def test_label_columns_are_never_returned_as_features() -> None:
    result = build_daily_features(sample_bars())
    selected = feature_columns(result)
    assert "log_return_1" in selected
    assert not any(name.startswith(("forward_", "label_")) for name in selected)

