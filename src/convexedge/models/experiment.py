"""End-to-end walk-forward stock forecasting experiment."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from convexedge.features import feature_columns

from .baselines import fit_garch11, historical_distribution, historical_up_probability, linear_baseline
from .calibration import SigmoidCalibrator
from .distribution import ReturnDistributionModel
from .metrics import interval_coverage, probability_metrics, quantile_loss, volatility_metrics
from .split import walk_forward_date_splits
from .volatility import VolatilityForecastModel


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    predictions: pd.DataFrame
    metrics: dict[str, float]
    feature_names: tuple[str, ...]


def run_walk_forward_experiment(
    frame: pd.DataFrame,
    *,
    horizon: int = 5,
    min_train_size: int = 126,
    validation_size: int = 42,
    test_size: int = 21,
    random_state: int = 42,
) -> ExperimentResult:
    return_target = f"forward_log_return_{horizon}"
    volatility_target = f"forward_realized_vol_{horizon}"
    required = {"session_date", "log_return_1", return_target, volatility_target}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"experiment missing columns: {sorted(missing)}")
    ordered = frame.copy()
    ordered["session_date"] = pd.to_datetime(ordered["session_date"], errors="raise")
    ordered = ordered.sort_values(["session_date", "instrument_id"]).reset_index(drop=True)
    predictors = [
        name for name in feature_columns(ordered)
        if pd.api.types.is_numeric_dtype(ordered[name]) and name not in {"open", "high", "low", "close"}
    ]
    usable = ordered.dropna(subset=[return_target, volatility_target]).reset_index(drop=True)
    X = usable[predictors]
    y_return = usable[return_target].to_numpy(float)
    y_volatility = usable[volatility_target].to_numpy(float)
    rows: list[pd.DataFrame] = []

    folds = list(
        walk_forward_date_splits(
            usable["session_date"],
            min_train_sessions=min_train_size,
            validation_sessions=validation_size,
            test_sessions=test_size,
            gap_sessions=horizon,
        )
    )
    if not folds:
        raise ValueError("not enough observations for one walk-forward fold")

    for fold in folds:
        train, validation, test = fold.train, fold.validation, fold.test
        distribution = ReturnDistributionModel(random_state=random_state).fit(X.iloc[train], y_return[train])
        validation_prediction = distribution.predict(X.iloc[validation])
        calibrator = SigmoidCalibrator(random_state=random_state).fit(
            validation_prediction["prob_up"], y_return[validation] > 0
        )
        prediction = distribution.predict(X.iloc[test])
        probability = calibrator.predict(prediction["prob_up"])

        volatility_model = VolatilityForecastModel(random_state=random_state).fit(
            X.iloc[train], y_volatility[train]
        )
        ml_volatility = volatility_model.predict(X.iloc[test])
        garch = fit_garch11(usable.iloc[train]["log_return_1"])
        garch_volatility = np.full(len(test), garch.forecast(horizon))
        ewma_volatility = usable.iloc[test]["rv_close_21"].to_numpy(float)
        linear_return_model = linear_baseline().fit(X.iloc[train], y_return[train])
        linear_return = linear_return_model.predict(X.iloc[test])
        linear_volatility_model = linear_baseline().fit(X.iloc[train], np.log(y_volatility[train]))
        linear_volatility = np.exp(linear_volatility_model.predict(X.iloc[test]))

        baseline_quantiles = historical_distribution(y_return[train])
        baseline_probability = historical_up_probability(y_return[train])
        rows.append(
            pd.DataFrame(
                {
                    "fold": fold.fold,
                    "session_date": usable.iloc[test]["session_date"].to_numpy(),
                    "y_return": y_return[test],
                    "y_volatility": y_volatility[test],
                    "q10": prediction["q10"],
                    "q50": prediction["q50"],
                    "q90": prediction["q90"],
                    "prob_up": probability,
                    "baseline_q10": baseline_quantiles[0.1],
                    "baseline_q50": baseline_quantiles[0.5],
                    "baseline_q90": baseline_quantiles[0.9],
                    "baseline_prob_up": baseline_probability,
                    "linear_return": linear_return,
                    "vol_ml": ml_volatility,
                    "vol_ewma": ewma_volatility,
                    "vol_garch": garch_volatility,
                    "vol_linear": linear_volatility,
                }
            )
        )
    predictions = pd.concat(rows, ignore_index=True)
    metrics: dict[str, float] = {}
    for prefix in ("", "baseline_"):
        metrics[f"{prefix}pinball_q10"] = quantile_loss(
            predictions["y_return"], predictions[f"{prefix}q10"], 0.1
        )
        metrics[f"{prefix}pinball_q50"] = quantile_loss(
            predictions["y_return"], predictions[f"{prefix}q50"], 0.5
        )
        metrics[f"{prefix}pinball_q90"] = quantile_loss(
            predictions["y_return"], predictions[f"{prefix}q90"], 0.9
        )
        metrics[f"{prefix}coverage_80"] = interval_coverage(
            predictions["y_return"], predictions[f"{prefix}q10"], predictions[f"{prefix}q90"]
        )
        probability_name = f"{prefix}prob_up"
        metrics[f"{prefix}brier"] = probability_metrics(
            predictions["y_return"] > 0, predictions[probability_name]
        )["brier"]
    linear_error = predictions["y_return"] - predictions["linear_return"]
    metrics["baseline_return_mae"] = float(
        np.mean(np.abs(predictions["y_return"] - predictions["baseline_q50"]))
    )
    metrics["ml_median_return_mae"] = float(
        np.mean(np.abs(predictions["y_return"] - predictions["q50"]))
    )
    metrics["linear_return_mae"] = float(np.mean(np.abs(linear_error)))
    metrics["linear_return_rmse"] = float(np.sqrt(np.mean(linear_error**2)))
    for name in ("ml", "ewma", "garch", "linear"):
        for metric, value in volatility_metrics(
            predictions["y_volatility"], predictions[f"vol_{name}"]
        ).items():
            metrics[f"vol_{name}_{metric}"] = value
    return ExperimentResult(predictions, metrics, tuple(predictors))

