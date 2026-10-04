"""Read-only live smoke test: normalize real IBKR bars into the PIT schema."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "test_data"))

from convexedge.data.ibkr import normalize_historical_bars  # noqa: E402
from run_all import TestApp, connection_args, run_test, stock  # noqa: E402


class App(TestApp):
    def historicalData(self, reqId, bar):  # noqa: N802
        self.rows.append(bar)

    def historicalDataEnd(self, reqId, start, end):  # noqa: N802
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 601)
parser.add_argument("--symbol", default="AAPL")
args = parser.parse_args()
app = App()


def request() -> None:
    # formatDate=2 forces epoch seconds for intraday data, avoiding ambiguous
    # exchange/operator timezone strings.
    app.reqHistoricalData(1, stock(args.symbol), "", "1 D", "5 mins", "TRADES", 1, 2, False, [])


run_test(args, app, request, "UTC historical bars")
as_of = datetime.now(UTC)
frame = normalize_historical_bars(
    app.rows,
    instrument_id=args.symbol,
    bar_size=timedelta(minutes=5),
    as_of_time=as_of,
)
if frame.empty:
    raise RuntimeError("IBKR returned no historical bars")
print(
    "PASS PIT bars="
    f"{len(frame)} first={frame.event_time.min().isoformat()} "
    f"last_available={frame.available_time.max().isoformat()} as_of={as_of.isoformat()}"
)
