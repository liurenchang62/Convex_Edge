"""Machine-learning forecast for future realized volatility."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor


class VolatilityForecastModel:
    def __init__(self, *, random_state: int = 42) -> None:
        self.model = HistGradientBoostingRegressor(
            loss="squared_error",
            max_iter=100,
            max_leaf_nodes=15,
            min_samples_leaf=10,
            l2_regularization=1.0,
            random_state=random_state,
            early_stopping=False,
        )

    def fit(self, X, y) -> "VolatilityForecastModel":
        target = np.asarray(y, dtype=float)
        if np.any(target <= 0):
            raise ValueError("volatility targets must be positive")
        self.model.fit(X, np.log(target))
        return self

    def predict(self, X) -> np.ndarray:
        return np.exp(self.model.predict(X))
