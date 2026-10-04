import numpy as np
import pandas as pd

from convexedge.data.volatility import close_to_close_volatility, parkinson_volatility


def test_close_to_close_matches_manual_sample_std() -> None:
    returns = np.array([0.01, -0.02, 0.03])
    prices = pd.Series(100 * np.exp(np.r_[0.0, np.cumsum(returns)]))
    actual = close_to_close_volatility(prices, 3, periods_per_year=252).iloc[-1]
    expected = returns.std(ddof=1) * np.sqrt(252)
    assert np.isclose(actual, expected)


def test_parkinson_matches_formula() -> None:
    high = pd.Series([110.0, 120.0])
    low = pd.Series([100.0, 100.0])
    actual = parkinson_volatility(high, low, 2, periods_per_year=252).iloc[-1]
    expected = np.sqrt(np.mean(np.log(high / low) ** 2) / (4 * np.log(2)) * 252)
    assert np.isclose(actual, expected)

