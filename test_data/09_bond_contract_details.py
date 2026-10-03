"""Resolve a bond by CUSIP/ISIN and print its contract and bond terms."""

import argparse

from run_all import TestApp, bond, connection_args, run_test


class App(TestApp):
    def bondContractDetails(self, reqId, d):  # noqa: N802
        c = d.contract
        fields = {
            "conId": c.conId,
            "symbol": c.symbol,
            "localSymbol": c.localSymbol,
            "exchange": c.exchange,
            "currency": c.currency,
            "cusip": getattr(d, "cusip", ""),
            "maturity": getattr(d, "maturity", ""),
            "coupon": getattr(d, "coupon", ""),
            "bondType": getattr(d, "bondType", ""),
            "callable": getattr(d, "callable", ""),
            "putable": getattr(d, "putable", ""),
            "convertible": getattr(d, "convertible", ""),
            "minTick": getattr(d, "minTick", ""),
        }
        print(" ".join(f"{k}={v}" for k, v in fields.items()))
        self.rows.append(d)

    def contractDetailsEnd(self, reqId):  # noqa: N802
        print(f"PASS bond contracts={len(self.rows)}")
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 109)
parser.add_argument("--id", required=True, help="CUSIP or ISIN copied from TWS")
parser.add_argument("--currency", default="USD")
parser.add_argument("--exchange", default="SMART")
args = parser.parse_args()
app = App()
run_test(args, app, lambda: app.reqContractDetails(1, bond(args.id, args.currency, args.exchange)), "bond contract details")
