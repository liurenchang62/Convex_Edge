"""Stream level-2 order-book updates for a US stock for several seconds."""

import argparse
import threading

from run_all import TestApp, connection_args, run_test, stock


class App(TestApp):
    def updateMktDepth(self, reqId, position, operation, side, price, size):  # noqa: N802
        print(f"L2 pos={position} op={operation} side={side} price={price} size={size}")
        self.rows.append((position, operation, side, price, size))

    def updateMktDepthL2(self, reqId, position, marketMaker, operation, side, price, size, isSmartDepth):  # noqa: N802,E501
        print(f"L2 venue={marketMaker} pos={position} op={operation} side={side} price={price} size={size}")
        self.rows.append((position, operation, side, price, size))


parser = argparse.ArgumentParser(description=__doc__)
connection_args(parser, 107)
parser.add_argument("--symbol", default="AAPL")
parser.add_argument("--seconds", type=float, default=10.0)
args = parser.parse_args()
app = App()


def request():
    app.reqMktDepth(1, stock(args.symbol), 5, True, [])
    def stop():
        app.cancelMktDepth(1, True)
        print(f"PASS depth updates={len(app.rows)}")
        app.done.set()
    threading.Timer(args.seconds, stop).start()


run_test(args, app, request, "market depth")
