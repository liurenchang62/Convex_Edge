from datetime import timedelta

import pandas as pd

from convexedge.data.quality import classify_quotes


def test_quote_quality_precedence() -> None:
    as_of = pd.Timestamp("2026-01-01T15:00:00Z")
    frame = pd.DataFrame(
        {
            "bid": [100, 102, 90, None, 99],
            "ask": [101, 101, 110, 101, 101],
            "quote_time": [
                as_of - pd.Timedelta(seconds=1),
                as_of - pd.Timedelta(seconds=1),
                as_of - pd.Timedelta(seconds=1),
                as_of - pd.Timedelta(seconds=1),
                as_of - pd.Timedelta(minutes=2),
            ],
        }
    )
    actual = classify_quotes(
        frame,
        as_of_time=as_of,
        max_age=timedelta(seconds=30),
        max_relative_spread=0.05,
    )
    assert actual.tolist() == ["valid", "crossed", "wide", "missing", "stale"]

