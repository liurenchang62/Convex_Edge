"""Test live-TWS connectivity and read-only account summary."""

import argparse

from run_all import TestApp, connection_args, run_test


class App(TestApp):
    def accountSummary(self, reqId, account, tag, value, currency):  # noqa: N802
        print(f"{account:12} {tag:24} {value:>16} {currency}")
        self.rows.append((account, tag, value, currency))

    def accountSummaryEnd(self, reqId):  # noqa: N802
        print(f"PASS account fields={len(self.rows)}")
        self.done.set()


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 101)
args = parser.parse_args()
app = App()
run_test(args, app, lambda: app.reqAccountSummary(1, "All", "AccountType,NetLiquidation,TotalCashValue,BuyingPower,AvailableFunds,MaintMarginReq"), "account summary")
