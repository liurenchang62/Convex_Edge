"""Resolve stock, FX and index contracts and print identifiers/trading rules."""

import argparse

from run_all import TestApp, connection_args, forex, index, run_test, stock


class App(TestApp):
    def contractDetails(self, reqId, d):  # noqa: N802
        c = d.contract
        print(f"req={reqId} conId={c.conId} {c.symbol} {c.secType} exchange={c.exchange} primary={c.primaryExchange} currency={c.currency} minTick={d.minTick}")
        self.rows.append(c)

    def contractDetailsEnd(self, reqId):  # noqa: N802
        self.pending.discard(reqId)
        if not self.pending:
            print(f"PASS contracts={len(self.rows)}")
            self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 102)
parser.add_argument("--stock", default="AAPL")
parser.add_argument("--fx", default="EURUSD")
parser.add_argument("--index", default="SPX")
args = parser.parse_args()
app = App()
app.pending = {1, 2, 3}


def request():
    app.reqContractDetails(1, stock(args.stock))
    app.reqContractDetails(2, forex(args.fx))
    app.reqContractDetails(3, index(args.index))


run_test(args, app, request, "contract details")
