"""Holdout probability calibration."""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression


def _logit(probability):
    clipped = np.clip(np.asarray(probability, dtype=float), 1e-6, 1 - 1e-6)
    return np.log(clipped / (1 - clipped)).reshape(-1, 1)


class SigmoidCalibrator:
    def __init__(self, *, random_state: int = 42) -> None:
        self.model = LogisticRegression(random_state=random_state)
        self.constant: float | None = None

    def fit(self, probability, y) -> "SigmoidCalibrator":
        target = np.asarray(y, dtype=int)
        if np.unique(target).size < 2:
            self.constant = float(target.mean())
        else:
            self.model.fit(_logit(probability), target)
        return self

    def predict(self, probability) -> np.ndarray:
        if self.constant is not None:
            return np.full(len(probability), self.constant)
        return self.model.predict_proba(_logit(probability))[:, 1]

