"""Collect an immutable read-only IBKR daily stock snapshot."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "test_data"))

from convexedge.data.ibkr import normalize_daily_bars  # noqa: E402
from convexedge.data.storage import verify_snapshot, write_snapshot  # noqa: E402
from run_all import TestApp, connection_args, run_test, stock  # noqa: E402


class App(TestApp):
    def historicalData(self, reqId, bar):  # noqa: N802
        self.rows.append(bar)

    def historicalDataEnd(self, reqId, start, end):  # noqa: N802
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 701)
parser.add_argument("--symbol", default="AAPL")
parser.add_argument("--duration", default="1 Y")
parser.add_argument("--output-root", type=Path, default=ROOT / "data" / "raw")
args = parser.parse_args()
app = App()


def request() -> None:
    app.reqHistoricalData(
        1, stock(args.symbol), "", args.duration, "1 day", "ADJUSTED_LAST", 1, 1, False, []
    )


run_test(args, app, request, "daily adjusted stock history")
downloaded_at = datetime.now(UTC)
frame = normalize_daily_bars(app.rows, instrument_id=args.symbol, downloaded_at=downloaded_at)
if frame.empty:
    raise RuntimeError("IBKR returned no daily bars")
snapshot_id = f"{args.symbol}-{downloaded_at.strftime('%Y%m%dT%H%M%SZ')}"
path = write_snapshot(
    frame,
    args.output_root,
    dataset="ibkr-stock-adjusted-daily",
    snapshot_id=snapshot_id,
    metadata={
        "symbol": args.symbol,
        "duration": args.duration,
        "bar_size": "1 day",
        "what_to_show": "ADJUSTED_LAST",
        "use_rth": 1,
        "request_is_read_only": True,
    },
)
verify_snapshot(path)
print(f"PASS snapshot={path} rows={len(frame)} first={frame.session_date.min()} last={frame.session_date.max()}")

