"""Conditional return distribution and direction probability models."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


class ReturnDistributionModel:
    def __init__(self, quantiles=(0.1, 0.5, 0.9), *, random_state: int = 42) -> None:
        self.quantiles = tuple(float(value) for value in quantiles)
        self.random_state = random_state
        self.quantile_models: dict[float, HistGradientBoostingRegressor] = {}
        self.direction_model = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(max_iter=1000, random_state=random_state),
        )

    def fit(self, X, y) -> "ReturnDistributionModel":
        target = np.asarray(y, dtype=float)
        for quantile in self.quantiles:
            model = HistGradientBoostingRegressor(
                loss="quantile",
                quantile=quantile,
                max_iter=100,
                max_leaf_nodes=15,
                min_samples_leaf=10,
                l2_regularization=1.0,
                random_state=self.random_state,
                early_stopping=False,
            )
            model.fit(X, target)
            self.quantile_models[quantile] = model
        self.direction_model.fit(X, target > 0)
        return self

    def predict(self, X) -> dict[str, np.ndarray]:
        quantile_predictions = np.column_stack(
            [self.quantile_models[q].predict(X) for q in self.quantiles]
        )
        quantile_predictions = np.maximum.accumulate(quantile_predictions, axis=1)
        result = {
            f"q{int(q * 100):02d}": quantile_predictions[:, index]
            for index, q in enumerate(self.quantiles)
        }
        result["prob_up"] = self.direction_model.predict_proba(X)[:, 1]
        return result

