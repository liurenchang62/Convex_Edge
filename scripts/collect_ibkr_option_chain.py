"""Collect an immutable read-only IBKR option-chain reference snapshot."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "test_data"))

from convexedge.data.options import option_chain_frame, validate_option_reference  # noqa: E402
from convexedge.data.storage import verify_snapshot, write_snapshot  # noqa: E402
from run_all import TestApp, connection_args, run_test, stock  # noqa: E402


class App(TestApp):
    def __init__(self) -> None:
        super().__init__()
        self.underlying_con_id: int | None = None

    def contractDetails(self, reqId, details):  # noqa: N802
        self.underlying_con_id = details.contract.conId

    def contractDetailsEnd(self, reqId):  # noqa: N802
        if self.underlying_con_id is None:
            self.fatal_error = "underlying contract did not resolve"
            self.done.set()
            return
        self.reqSecDefOptParams(2, args.symbol, "", "STK", self.underlying_con_id)

    def securityDefinitionOptionParameter(  # noqa: N802
        self, reqId, exchange, underlyingConId, tradingClass, multiplier, expirations, strikes
    ):
        self.rows.append((exchange, underlyingConId, tradingClass, multiplier, expirations, strikes))

    def securityDefinitionOptionParameterEnd(self, reqId):  # noqa: N802
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 702)
parser.add_argument("--symbol", default="AAPL")
parser.add_argument("--exchange", default="SMART")
parser.add_argument("--output-root", type=Path, default=ROOT / "data" / "raw")
args = parser.parse_args()
app = App()


run_test(args, app, lambda: app.reqContractDetails(1, stock(args.symbol)), "option chain")
observed_at = datetime.now(UTC)
frames = [
    option_chain_frame(
        symbol=args.symbol,
        underlying_con_id=underlying_id,
        exchange=exchange,
        trading_class=trading_class,
        multiplier=multiplier,
        expirations=expirations,
        strikes=strikes,
        observed_at=observed_at,
    )
    for exchange, underlying_id, trading_class, multiplier, expirations, strikes in app.rows
    if exchange == args.exchange
]
if not frames:
    raise RuntimeError(f"IBKR returned no {args.exchange} option chain")
frame = validate_option_reference(pd.concat(frames, ignore_index=True).drop_duplicates())
snapshot_id = f"{args.symbol}-{observed_at.strftime('%Y%m%dT%H%M%SZ')}"
path = write_snapshot(
    frame,
    args.output_root,
    dataset="ibkr-option-chain-reference",
    snapshot_id=snapshot_id,
    metadata={
        "symbol": args.symbol,
        "exchange": args.exchange,
        "quotes_included": False,
        "request_is_read_only": True,
    },
)
verify_snapshot(path)
print(
    f"PASS snapshot={path} rows={len(frame)} "
    f"expirations={frame.expiration.nunique()} strikes={frame.strike.nunique()}"
)
