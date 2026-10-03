"""Request an option quote and model Greeks for one explicitly selected contract."""

import argparse

from ibapi.contract import Contract

from run_all import TestApp, clean, connection_args, run_test


class App(TestApp):
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        super().error(reqId, errorCode, errorString, advancedOrderRejectJson)
        # 10167 is informational here: TWS continues with delayed data.
        if reqId == 1 and errorCode in {321, 354, 10089, 10168}:
            print("UNAVAILABLE: option quote/Greeks permission or contract limitation")
            self.done.set()

    def tickPrice(self, reqId, tickType, price, attrib):  # noqa: N802
        print(f"price tick={tickType} value={clean(price)}")
        self.rows.append(("price", tickType, price))

    def tickOptionComputation(self, reqId, tickType, tickAttrib, impliedVol, delta, optPrice, pvDividend, gamma, vega, theta, undPrice):  # noqa: N802,E501
        print(f"greeks tick={tickType} iv={clean(impliedVol)} delta={clean(delta)} gamma={clean(gamma)} vega={clean(vega)} theta={clean(theta)} option={clean(optPrice)} underlying={clean(undPrice)}")
        self.rows.append(("greeks", tickType, impliedVol, delta, gamma, vega, theta))

    def tickSnapshotEnd(self, reqId):  # noqa: N802
        if not self.rows:
            self.fatal_error = "No option prices/Greeks received; option and underlying API market-data permissions are required"
        else:
            print(f"PASS option ticks={len(self.rows)}")
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 108)
parser.add_argument("--symbol", default="AAPL")
parser.add_argument("--expiry", required=True, help="YYYYMMDD; obtain from 06_option_chain.py")
parser.add_argument("--strike", required=True, type=float)
parser.add_argument("--right", choices=["C", "P"], default="C")
args = parser.parse_args()
app = App()


def request():
    c = Contract()
    c.symbol, c.secType, c.exchange, c.currency = args.symbol, "OPT", "SMART", "USD"
    c.lastTradeDateOrContractMonth, c.strike, c.right, c.multiplier = args.expiry, args.strike, args.right, "100"
    app.reqMarketDataType(3)  # live when entitled, otherwise delayed
    # Option price and model Greeks are standard option ticks; generic ticks are
    # invalid for snapshot requests and trigger error 321.
    app.reqMktData(1, c, "", True, False, [])


run_test(args, app, request, "option quote and Greeks")
