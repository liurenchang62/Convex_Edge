"""Acceptance checks for train/validation/test time isolation."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from convexedge.models.split import walk_forward_date_splits, walk_forward_splits  # noqa: E402

folds = list(
    walk_forward_splits(
        300, min_train_size=126, validation_size=42, test_size=21, gap=5, max_train_size=180
    )
)
assert len(folds) >= 4
for fold in folds:
    assert fold.train.max() + 5 < fold.validation.min()
    assert fold.validation.max() + 5 < fold.test.min()
    assert len(fold.train) <= 180
panel_dates = pd.Series(pd.date_range("2026-01-01", periods=300).repeat(3))
panel_fold = next(
    walk_forward_date_splits(
        panel_dates,
        min_train_sessions=126,
        validation_sessions=42,
        test_sessions=21,
        gap_sessions=5,
    )
)
assert set(panel_dates.iloc[panel_fold.train]).isdisjoint(set(panel_dates.iloc[panel_fold.test]))
print(f"PASS walk-forward folds={len(folds)} and panel-session isolation")

