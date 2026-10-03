"""Download historical bond price or yield bars by CUSIP/ISIN."""

import argparse

from run_all import TestApp, bond, connection_args, run_test


class App(TestApp):
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        super().error(reqId, errorCode, errorString, advancedOrderRejectJson)
        if reqId == 1 and errorCode == 162:
            print("UNAVAILABLE: IBKR returned no historical bars for this bond/data type")
            self.done.set()

    def historicalData(self, reqId, bar):  # noqa: N802
        print(f"{bar.date} O={bar.open} H={bar.high} L={bar.low} C={bar.close} V={bar.volume}")
        self.rows.append(bar)

    def historicalDataEnd(self, reqId, start, end):  # noqa: N802
        print(f"PASS bond bars={len(self.rows)} range={start}..{end}")
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 111)
parser.add_argument("--id", required=True, help="CUSIP or ISIN copied from TWS")
parser.add_argument("--currency", default="USD")
parser.add_argument("--exchange", default="SMART")
parser.add_argument("--duration", default="1 M")
parser.add_argument("--bar-size", default="1 day")
parser.add_argument(
    "--what-to-show",
    choices=["TRADES", "MIDPOINT", "BID", "ASK", "BID_ASK", "YIELD_BID", "YIELD_ASK", "YIELD_BID_ASK", "YIELD_LAST"],
    default="BID_ASK",
    help="YIELD_* history is available only for corporate bonds",
)
args = parser.parse_args()
app = App()


def request():
    app.reqHistoricalData(1, bond(args.id, args.currency, args.exchange), "", args.duration, args.bar_size, args.what_to_show, 0, 1, False, [])


run_test(args, app, request, "bond historical bars")
