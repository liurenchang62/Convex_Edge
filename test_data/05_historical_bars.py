"""Download recent historical bars for a US stock."""

import argparse

from run_all import TestApp, connection_args, run_test, stock


class App(TestApp):
    def historicalData(self, reqId, bar):  # noqa: N802
        print(f"{bar.date} O={bar.open} H={bar.high} L={bar.low} C={bar.close} V={bar.volume}")
        self.rows.append(bar)

    def historicalDataEnd(self, reqId, start, end):  # noqa: N802
        print(f"PASS bars={len(self.rows)} range={start}..{end}")
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 105)
parser.add_argument("--symbol", default="AAPL")
parser.add_argument("--duration", default="2 D")
parser.add_argument("--bar-size", default="5 mins")
parser.add_argument("--what-to-show", default="TRADES")
parser.add_argument("--format-date", type=int, choices=[1, 2], default=1)
parser.add_argument("--use-rth", type=int, choices=[0, 1], default=1)
args = parser.parse_args()
app = App()


def request():
    app.reqHistoricalData(
        1,
        stock(args.symbol),
        "",
        args.duration,
        args.bar_size,
        args.what_to_show,
        args.use_rth,
        args.format_date,
        False,
        [],
    )


run_test(args, app, request, "historical bars")
