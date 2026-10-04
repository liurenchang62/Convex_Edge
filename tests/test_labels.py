import numpy as np
import pandas as pd

from convexedge.data.labels import forward_log_returns


def test_forward_returns_and_intervals() -> None:
    times = pd.date_range("2026-01-01", periods=4, tz="UTC")
    prices = pd.Series([100.0, 110.0, 121.0, 133.1], index=times)
    result = forward_log_returns(prices, 2)
    assert np.isclose(result.iloc[0]["forward_log_return_2"], np.log(1.21))
    assert result.iloc[0]["label_end_time"] == times[2]
    assert result["forward_log_return_2"].iloc[-2:].isna().all()

