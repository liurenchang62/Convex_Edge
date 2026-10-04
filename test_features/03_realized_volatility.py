"""Acceptance test for realized-volatility estimators."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.data.volatility import close_to_close_volatility, parkinson_volatility  # noqa: E402

returns = np.array([0.01, -0.02, 0.03])
close = pd.Series(100 * np.exp(np.r_[0.0, np.cumsum(returns)]))
assert np.isclose(
    close_to_close_volatility(close, 3).iloc[-1], returns.std(ddof=1) * np.sqrt(252)
)
high, low = pd.Series([110.0, 120.0]), pd.Series([100.0, 100.0])
expected = np.sqrt(np.mean(np.log(high / low) ** 2) / (4 * np.log(2)) * 252)
assert np.isclose(parkinson_volatility(high, low, 2).iloc[-1], expected)
print("PASS realized volatility")

