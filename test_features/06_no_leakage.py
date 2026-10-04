"""Acceptance test proving that deliberately injected future data is rejected."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.data.pit import PointInTimeViolation, validate_point_in_time  # noqa: E402

frame = pd.DataFrame(
    {
        "event_time": ["2026-01-01T20:00:00Z"],
        "source_time": ["2026-01-01T20:01:00Z"],
        "available_time": ["2026-01-01T20:02:00Z"],
        "as_of_time": ["2026-01-01T20:01:30Z"],
    }
)
try:
    validate_point_in_time(frame)
except PointInTimeViolation:
    print("PASS deliberately injected future field was rejected")
else:
    raise AssertionError("future information was not rejected")

