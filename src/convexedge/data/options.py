"""Option-chain reference-data normalization."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd


def option_chain_frame(
    *,
    symbol: str,
    underlying_con_id: int,
    exchange: str,
    trading_class: str,
    multiplier: str,
    expirations: set[str],
    strikes: set[float],
    observed_at: datetime,
) -> pd.DataFrame:
    """Expand one IBKR securityDefinitionOptionParameter response."""

    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")
    try:
        multiplier_value = int(multiplier)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid option multiplier: {multiplier!r}") from exc
    if multiplier_value <= 0:
        raise ValueError("option multiplier must be positive")
    rows = []
    for expiry in sorted(expirations):
        expiry_time = pd.to_datetime(expiry, format="%Y%m%d", utc=True, errors="raise")
        for strike in sorted(strikes):
            if strike <= 0:
                raise ValueError("option strikes must be positive")
            rows.append(
                {
                    "symbol": symbol,
                    "underlying_con_id": underlying_con_id,
                    "exchange": exchange,
                    "trading_class": trading_class,
                    "multiplier": multiplier_value,
                    "expiration": expiry_time,
                    "strike": float(strike),
                    "observed_at": observed_at.astimezone(UTC),
                }
            )
    return pd.DataFrame(rows)


def validate_option_reference(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate option-chain reference rows before quote enrichment."""

    required = {
        "symbol", "underlying_con_id", "exchange", "trading_class", "multiplier",
        "expiration", "strike", "observed_at",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"missing option reference columns: {sorted(missing)}")
    result = frame.copy()
    result["expiration"] = pd.to_datetime(result["expiration"], utc=True, errors="raise")
    result["observed_at"] = pd.to_datetime(result["observed_at"], utc=True, errors="raise")
    if (pd.to_numeric(result["strike"], errors="raise") <= 0).any():
        raise ValueError("option strikes must be positive")
    if (pd.to_numeric(result["multiplier"], errors="raise") <= 0).any():
        raise ValueError("option multipliers must be positive")
    expired = result["expiration"].dt.date < result["observed_at"].dt.date
    if expired.any():
        raise ValueError("option reference contains already expired contracts")
    key = ["symbol", "exchange", "trading_class", "expiration", "strike"]
    if result.duplicated(key).any():
        raise ValueError("option reference contains duplicate contracts")
    return result

