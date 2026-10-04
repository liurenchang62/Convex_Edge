"""Acceptance test for forward-return labels and interval endpoints."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.data.labels import forward_log_returns  # noqa: E402

index = pd.date_range("2026-01-01", periods=4, tz="UTC")
result = forward_log_returns(pd.Series([100.0, 110.0, 121.0, 133.1], index=index), 2)
assert np.isclose(result.iloc[0]["forward_log_return_2"], np.log(1.21))
assert result.iloc[0]["label_end_time"] == index[2]
print("PASS forward-return labels")

