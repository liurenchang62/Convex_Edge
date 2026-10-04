"""Acceptance test for availability-time alignment."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.data.pit import asof_join  # noqa: E402

decisions = pd.DataFrame({"instrument_id": ["AAPL"], "as_of_time": ["2026-01-02T15:00:00Z"]})
observations = pd.DataFrame(
    {
        "instrument_id": ["AAPL", "AAPL"],
        "available_time": ["2026-01-01T20:01:00Z", "2026-01-02T16:00:00Z"],
        "value": [100.0, 999.0],
    }
)
result = asof_join(decisions, observations)
assert result.loc[0, "value"] == 100.0
print("PASS point-in-time alignment")

