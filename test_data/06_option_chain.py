"""Resolve a US stock and retrieve its option expirations and strikes."""

import argparse

from run_all import TestApp, connection_args, run_test, stock


class App(TestApp):
    def contractDetails(self, reqId, d):  # noqa: N802
        c = d.contract
        if c.primaryExchange:
            self.underlying = c

    def contractDetailsEnd(self, reqId):  # noqa: N802
        if not self.underlying:
            self.fatal_error = "No underlying contract found"
            self.done.set()
            return
        c = self.underlying
        print(f"underlying conId={c.conId} exchange={c.primaryExchange}")
        self.reqSecDefOptParams(2, c.symbol, "", c.secType, c.conId)

    def securityDefinitionOptionParameter(self, reqId, exchange, underlyingConId, tradingClass, multiplier, expirations, strikes):  # noqa: N802,E501
        print(f"exchange={exchange} class={tradingClass} multiplier={multiplier} expirations={len(expirations)} strikes={len(strikes)}")
        print("nearest expirations:", ", ".join(sorted(expirations)[:8]))
        self.rows.append((exchange, expirations, strikes))

    def securityDefinitionOptionParameterEnd(self, reqId):  # noqa: N802
        print(f"PASS option chains={len(self.rows)}")
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 106)
parser.add_argument("--symbol", default="AAPL")
args = parser.parse_args()
app = App()
app.underlying = None
run_test(args, app, lambda: app.reqContractDetails(1, stock(args.symbol)), "option chain")
