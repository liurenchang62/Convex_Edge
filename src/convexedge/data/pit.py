"""Point-in-time validation and alignment."""

from __future__ import annotations

import pandas as pd


REQUIRED_TIME_COLUMNS = ("event_time", "source_time", "available_time", "as_of_time")


class PointInTimeViolation(ValueError):
    """Raised when a feature was unavailable at its decision time."""


def _as_utc(series: pd.Series, name: str) -> pd.Series:
    try:
        converted = pd.to_datetime(series, utc=True, errors="raise")
    except (TypeError, ValueError) as exc:
        raise PointInTimeViolation(f"{name} contains invalid timestamps") from exc
    if converted.isna().any():
        raise PointInTimeViolation(f"{name} contains missing timestamps")
    return converted


def validate_point_in_time(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a UTC-normalized copy after enforcing availability constraints."""

    missing = [name for name in REQUIRED_TIME_COLUMNS if name not in frame.columns]
    if missing:
        raise PointInTimeViolation(f"missing required time columns: {missing}")
    result = frame.copy()
    for name in REQUIRED_TIME_COLUMNS:
        result[name] = _as_utc(result[name], name)
    future = result["available_time"] > result["as_of_time"]
    if future.any():
        rows = result.index[future].tolist()[:5]
        raise PointInTimeViolation(f"future information detected at rows {rows}")
    return result


def asof_join(
    decisions: pd.DataFrame,
    observations: pd.DataFrame,
    *,
    by: str = "instrument_id",
    decision_time: str = "as_of_time",
    availability_time: str = "available_time",
) -> pd.DataFrame:
    """Attach the latest actually available observation to each decision row."""

    for frame, names, label in (
        (decisions, (by, decision_time), "decisions"),
        (observations, (by, availability_time), "observations"),
    ):
        missing = [name for name in names if name not in frame.columns]
        if missing:
            raise PointInTimeViolation(f"{label} missing columns: {missing}")

    left = decisions.copy()
    right = observations.copy()
    left[decision_time] = _as_utc(left[decision_time], decision_time)
    right[availability_time] = _as_utc(right[availability_time], availability_time)
    left = left.sort_values([decision_time, by])
    right = right.sort_values([availability_time, by])
    joined = pd.merge_asof(
        left,
        right,
        left_on=decision_time,
        right_on=availability_time,
        by=by,
        direction="backward",
        allow_exact_matches=True,
    )
    leaked = joined[availability_time].notna() & (joined[availability_time] > joined[decision_time])
    if leaked.any():
        raise PointInTimeViolation("as-of join produced future information")
    return joined

