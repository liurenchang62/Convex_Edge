import numpy as np
import pandas as pd

from convexedge.models.baselines import ewma_variance, fit_garch11
from convexedge.models.calibration import SigmoidCalibrator
from convexedge.models.distribution import ReturnDistributionModel
from convexedge.models.experiment import run_walk_forward_experiment
from convexedge.models.metrics import interval_coverage, quantile_loss
from convexedge.models.split import walk_forward_date_splits, walk_forward_splits
from convexedge.models.volatility import VolatilityForecastModel


def test_walk_forward_has_gap_and_strict_order() -> None:
    folds = list(
        walk_forward_splits(
            100, min_train_size=40, validation_size=10, test_size=10, gap=5
        )
    )
    assert folds
    for fold in folds:
        assert fold.train.max() + 5 < fold.validation.min()
        assert fold.validation.max() + 5 < fold.test.min()


def test_panel_split_never_divides_one_session() -> None:
    dates = np.repeat(pd.date_range("2026-01-01", periods=80), 3)
    folds = list(
        walk_forward_date_splits(
            dates,
            min_train_sessions=30,
            validation_sessions=10,
            test_sessions=10,
            gap_sessions=2,
        )
    )
    for fold in folds:
        train_dates = set(dates[fold.train])
        validation_dates = set(dates[fold.validation])
        test_dates = set(dates[fold.test])
        assert train_dates.isdisjoint(validation_dates | test_dates)
        assert validation_dates.isdisjoint(test_dates)


def test_baseline_volatility_models_are_positive() -> None:
    rng = np.random.default_rng(42)
    returns = rng.normal(0, 0.01, 300)
    assert np.all(ewma_variance(returns) > 0)
    fitted = fit_garch11(returns)
    assert fitted.alpha + fitted.beta < 1
    assert fitted.forecast(5) > 0


def test_distribution_outputs_ordered_quantiles_and_probabilities() -> None:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(160, 4))
    y = 0.01 * X[:, 0] + rng.normal(scale=0.02, size=160)
    model = ReturnDistributionModel(random_state=7).fit(X[:120], y[:120])
    prediction = model.predict(X[120:])
    assert np.all(prediction["q10"] <= prediction["q50"])
    assert np.all(prediction["q50"] <= prediction["q90"])
    assert np.all((prediction["prob_up"] >= 0) & (prediction["prob_up"] <= 1))


def test_volatility_model_is_positive_and_reproducible() -> None:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(150, 3))
    y = np.exp(-4 + 0.2 * X[:, 0])
    first = VolatilityForecastModel(random_state=9).fit(X[:100], y[:100]).predict(X[100:])
    second = VolatilityForecastModel(random_state=9).fit(X[:100], y[:100]).predict(X[100:])
    assert np.all(first > 0)
    assert np.array_equal(first, second)


def test_metrics_and_calibrator() -> None:
    y = np.array([0, 0, 1, 1])
    probability = np.array([0.1, 0.4, 0.6, 0.9])
    calibrated = SigmoidCalibrator().fit(probability, y).predict(probability)
    assert np.all((calibrated >= 0) & (calibrated <= 1))
    assert quantile_loss([0, 1], [0, 0], 0.5) == 0.25
    assert interval_coverage([0, 1], [-1, 0], [0, 2]) == 1.0


def test_end_to_end_experiment_produces_only_out_of_sample_rows() -> None:
    from convexedge.features import build_daily_features

    rng = np.random.default_rng(5)
    rows = 260
    returns = rng.normal(0.0003, 0.01, rows)
    close = 100 * np.exp(np.cumsum(returns))
    bars = pd.DataFrame(
        {
            "instrument_id": "TEST",
            "session_date": pd.bdate_range("2025-01-01", periods=rows),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": rng.integers(1000, 5000, rows),
        }
    )
    features = build_daily_features(bars)
    result = run_walk_forward_experiment(
        features,
        horizon=5,
        min_train_size=100,
        validation_size=30,
        test_size=30,
        random_state=11,
    )
    assert not result.predictions.empty
    assert result.predictions["session_date"].is_monotonic_increasing
    assert "baseline_brier" in result.metrics
    assert "vol_ewma_high_vol_mae" in result.metrics
