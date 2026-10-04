"""Acceptance test for stale, crossed, wide, and missing quotes."""

import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.data.quality import classify_quotes  # noqa: E402

as_of = pd.Timestamp("2026-01-01T15:00:00Z")
frame = pd.DataFrame(
    {
        "bid": [100, 102, 90, None, 99],
        "ask": [101, 101, 110, 101, 101],
        "quote_time": [as_of - pd.Timedelta(seconds=1)] * 4 + [as_of - pd.Timedelta(minutes=2)],
    }
)
actual = classify_quotes(
    frame, as_of_time=as_of, max_age=timedelta(seconds=30), max_relative_spread=0.05
)
assert actual.tolist() == ["valid", "crossed", "wide", "missing", "stale"]
print("PASS quote quality and missingness")

