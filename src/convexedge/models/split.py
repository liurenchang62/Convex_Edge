"""Leakage-resistant walk-forward splits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    fold: int
    train: np.ndarray
    validation: np.ndarray
    test: np.ndarray


def walk_forward_splits(
    n_samples: int,
    *,
    min_train_size: int,
    validation_size: int,
    test_size: int,
    gap: int,
    step: int | None = None,
    max_train_size: int | None = None,
) -> Iterator[WalkForwardFold]:
    """Yield expanding or rolling train/validation/test index blocks."""

    values = (n_samples, min_train_size, validation_size, test_size)
    if any(value <= 0 for value in values) or gap < 0:
        raise ValueError("sizes must be positive and gap non-negative")
    if max_train_size is not None and max_train_size < min_train_size:
        raise ValueError("max_train_size cannot be below min_train_size")
    step = test_size if step is None else step
    if step <= 0:
        raise ValueError("step must be positive")

    fold = 0
    test_start = min_train_size + gap + validation_size + gap
    while test_start + test_size <= n_samples:
        validation_end = test_start - gap
        validation_start = validation_end - validation_size
        train_end = validation_start - gap
        train_start = 0 if max_train_size is None else max(0, train_end - max_train_size)
        train = np.arange(train_start, train_end)
        validation = np.arange(validation_start, validation_end)
        test = np.arange(test_start, test_start + test_size)
        if len(train) < min_train_size:
            break
        yield WalkForwardFold(fold, train, validation, test)
        fold += 1
        test_start += step


def walk_forward_date_splits(
    dates,
    *,
    min_train_sessions: int,
    validation_sessions: int,
    test_sessions: int,
    gap_sessions: int,
    step_sessions: int | None = None,
    max_train_sessions: int | None = None,
) -> Iterator[WalkForwardFold]:
    """Split panel data by complete sessions so a date never crosses partitions."""

    normalized = pd.to_datetime(pd.Series(dates), errors="raise").dt.normalize()
    sessions = np.sort(normalized.unique())
    session_folds = walk_forward_splits(
        len(sessions),
        min_train_size=min_train_sessions,
        validation_size=validation_sessions,
        test_size=test_sessions,
        gap=gap_sessions,
        step=step_sessions,
        max_train_size=max_train_sessions,
    )
    values = normalized.to_numpy()
    for fold in session_folds:
        yield WalkForwardFold(
            fold.fold,
            np.flatnonzero(np.isin(values, sessions[fold.train])),
            np.flatnonzero(np.isin(values, sessions[fold.validation])),
            np.flatnonzero(np.isin(values, sessions[fold.test])),
        )

