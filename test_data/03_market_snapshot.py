"""Request one-shot stock, FX and index market-data snapshots."""

import argparse

from run_all import TestApp, clean, connection_args, forex, index, run_test, stock


TICK_NAMES = {1: "bid", 2: "ask", 4: "last", 6: "high", 7: "low", 9: "close", 14: "open", 37: "mark",
              66: "delayed_bid", 67: "delayed_ask", 68: "delayed_last", 72: "delayed_high",
              73: "delayed_low", 75: "delayed_close", 76: "delayed_open"}


class App(TestApp):
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        super().error(reqId, errorCode, errorString, advancedOrderRejectJson)
        if reqId in getattr(self, "pending", set()) and errorCode in {354, 10089, 10167, 10168, 10285}:
            print(f"UNAVAILABLE req={reqId}: permission/API-version limitation")
            self.pending.discard(reqId)
            if not self.pending:
                self.done.set()

    def tickPrice(self, reqId, tickType, price, attrib):  # noqa: N802
        print(f"req={reqId} {TICK_NAMES.get(tickType, 'price_'+str(tickType))}={clean(price)}")
        self.rows.append((reqId, tickType, price))

    def tickSize(self, reqId, tickType, size):  # noqa: N802
        print(f"req={reqId} size_{tickType}={size}")

    def tickSnapshotEnd(self, reqId):  # noqa: N802
        self.pending.discard(reqId)
        if not self.pending:
            if not self.rows:
                self.fatal_error = "No snapshot prices received; update ibapi and verify market-data permissions"
            else:
                print(f"PASS price ticks={len(self.rows)}")
            self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 103)
parser.add_argument("--stock", default="AAPL")
parser.add_argument("--fx", default="EURUSD")
parser.add_argument("--index", default="SPX")
args = parser.parse_args()
app = App()
app.pending = {1, 2, 3}


def request():
    app.reqMarketDataType(3)  # live when entitled, otherwise delayed
    for req_id, contract in [(1, stock(args.stock)), (2, forex(args.fx)), (3, index(args.index))]:
        app.reqMktData(req_id, contract, "", True, False, [])


run_test(args, app, request, "market snapshots")
