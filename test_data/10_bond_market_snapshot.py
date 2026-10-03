"""Request a one-shot bond price/yield market-data snapshot by CUSIP/ISIN."""

import argparse

from run_all import TestApp, bond, clean, connection_args, run_test


PRICE_NAMES = {1: "bid", 2: "ask", 4: "last", 6: "high", 7: "low", 9: "close", 14: "open", 37: "mark"}
GENERIC_NAMES = {50: "bid_yield", 51: "ask_yield", 52: "last_yield"}


class App(TestApp):
    def tickPrice(self, reqId, tickType, price, attrib):  # noqa: N802
        print(f"{PRICE_NAMES.get(tickType, 'price_'+str(tickType))}={clean(price)}")
        self.rows.append(("price", tickType, price))

    def tickSize(self, reqId, tickType, size):  # noqa: N802
        print(f"size_{tickType}={size}")

    def tickGeneric(self, reqId, tickType, value):  # noqa: N802
        print(f"{GENERIC_NAMES.get(tickType, 'generic_'+str(tickType))}={clean(value)}")
        self.rows.append(("generic", tickType, value))

    def tickSnapshotEnd(self, reqId):  # noqa: N802
        print(f"PASS bond ticks={len(self.rows)}")
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 110)
parser.add_argument("--id", required=True, help="CUSIP or ISIN copied from TWS")
parser.add_argument("--currency", default="USD")
parser.add_argument("--exchange", default="SMART")
args = parser.parse_args()
app = App()


def request():
    app.reqMarketDataType(1)
    app.reqMktData(1, bond(args.id, args.currency, args.exchange), "", True, False, [])


run_test(args, app, request, "bond market snapshot")
