"""Stream stock quotes for a fixed number of seconds; sends no orders."""

import argparse
import threading

from run_all import TestApp, clean, connection_args, run_test, stock


class App(TestApp):
    def tickPrice(self, reqId, tickType, price, attrib):  # noqa: N802
        print(f"price tick={tickType} value={clean(price)}")
        self.rows.append((tickType, price))

    def tickSize(self, reqId, tickType, size):  # noqa: N802
        print(f"size  tick={tickType} value={size}")


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 104)
parser.add_argument("--symbol", default="AAPL")
parser.add_argument("--seconds", type=float, default=10.0)
args = parser.parse_args()
app = App()


def request():
    app.reqMarketDataType(3)  # live when entitled, otherwise delayed
    # Generic tick 233 is not available when TWS falls back to delayed data.
    app.reqMktData(1, stock(args.symbol), "", False, False, [])
    def stop():
        app.cancelMktData(1)
        if not app.rows:
            app.fatal_error = "No streaming prices received; verify US stock API market-data permissions"
        else:
            print(f"PASS price ticks={len(app.rows)}")
        app.done.set()
    threading.Timer(args.seconds, stop).start()


run_test(args, app, request, "streaming quotes")
