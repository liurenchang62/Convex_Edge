"""Shared TWS live-order test harness and all-tests runner."""
from __future__ import annotations
import argparse, subprocess, sys, threading, time
from pathlib import Path
from ibapi.client import EClient
from ibapi.order import Order
from ibapi.wrapper import EWrapper

LIVE_PORT = 7496
CONFIRM_TEXT = "I_UNDERSTAND_LIVE_ORDER"

def add_connection_args(p, client_id):
    p.add_argument("--host", default="127.0.0.1"); p.add_argument("--port", type=int, default=LIVE_PORT)
    p.add_argument("--client-id", type=int, default=client_id); p.add_argument("--timeout", type=float, default=20)
    p.add_argument("--cancel-after", type=float, default=10)
    p.add_argument("--confirm-live", metavar="TEXT", help=f"Transmit only when TEXT is {CONFIRM_TEXT}")

def make_order(qty, price, live):
    o = Order(); o.action="BUY"; o.orderType="LMT"; o.totalQuantity=qty; o.lmtPrice=price
    o.tif="DAY"; o.outsideRth=False; o.transmit=True; o.whatIf=not live
    # Recent TWS versions reject these legacy attributes, while some ibapi
    # releases still default both of them to True (errors 10268/10269).
    o.eTradeOnly=False; o.firmQuoteOnly=False
    o.orderRef="ConvexEdge-minimum-order-test"
    return o

class App(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self); self.ready=threading.Event(); self.done=threading.Event()
        self.next_id=None; self.order_id=None; self.accounts_received=False; self.whatif_timer=None
        self.live=False; self.cancel_after=10; self.cancel_started=False; self.failure=None
    def _set_ready_if_complete(self):
        if self.next_id is not None and self.accounts_received: self.ready.set()
    def nextValidId(self, orderId):
        self.next_id=orderId; print(f"CONNECTED serverVersion={self.serverVersion()} nextOrderId={orderId}")
        self.reqManagedAccts(); self._set_ready_if_complete()
    def managedAccounts(self, value):
        accounts=[x for x in value.split(',') if x]; masked=(accounts[0][:3]+"***"+accounts[0][-2:]) if accounts else "NONE"
        print(f"ACCOUNT count={len(accounts)} id={masked}"); self.accounts_received=True; self._set_ready_if_complete()
    def error(self, reqId, code, message, advancedOrderRejectJson=""):
        if code in {2104,2106,2107,2108,2158}: print(f"INFO code={code}: {message}"); return
        print(f"ERROR reqId={reqId} code={code}: {message}")
        if advancedOrderRejectJson: print(f"ADVANCED_REJECT {advancedOrderRejectJson}")
        if code in {200,201,202,321,502,503,504,1100,1300,10268,10269,10270}:
            if code != 202: self.failure=f"{code}: {message}"
            if code in {502,503,504,1100,1300}: self.ready.set()
            self.done.set()
    def openOrder(self, orderId, contract, order, state):
        print(f"OPEN orderId={orderId} BUY {order.totalQuantity} {contract.symbol or contract.localSymbol} LMT @{order.lmtPrice} status={state.status} whatIf={order.whatIf}")
        print(f"WHATIF commission={state.commission} {state.commissionCurrency} initMarginChange={state.initMarginChange} maintMarginChange={state.maintMarginChange}")
        if order.whatIf:
            # A final reject can arrive just after the WHAT-IF openOrder.  Use a
            # short quiet period so it is reported instead of printing PASS first.
            if self.whatif_timer: self.whatif_timer.cancel()
            self.whatif_timer=threading.Timer(1.0,self.done.set); self.whatif_timer.daemon=True; self.whatif_timer.start()
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"STATUS orderId={orderId} status={status} filled={filled} remaining={remaining} avgFill={avgFillPrice}")
        if status=="Filled": self.done.set()
        elif status in {"Cancelled","ApiCancelled","Inactive"}:
            if status=="Inactive": self.failure="Order became Inactive"
            self.done.set()
        elif self.live and status in {"Submitted","PreSubmitted"} and not self.cancel_started:
            self.cancel_started=True; threading.Timer(self.cancel_after, self.cancel).start()
    def execDetails(self, reqId, contract, execution): print(f"FILL shares={execution.shares} price={execution.price} execId={execution.execId}")
    def commissionReport(self, r): print(f"COMMISSION amount={r.commission} {r.currency}")
    def cancel(self):
        if self.order_id is not None and self.isConnected() and not self.done.is_set():
            print(f"AUTO_CANCEL orderId={self.order_id}"); self.cancelOrder(self.order_id)

def execute_test(args, contract, qty, price, label):
    live=args.confirm_live==CONFIRM_TEXT
    if args.confirm_live and not live: raise ValueError(f"Confirmation must equal {CONFIRM_TEXT}")
    if args.port != LIVE_PORT: raise ValueError(f"Live tests require TWS port {LIVE_PORT}")
    print(f"MODE={'LIVE TRANSMIT' if live else 'WHAT-IF ONLY'} asset={label} quantity={qty} limit={price}")
    app=App(); app.live=live; app.cancel_after=args.cancel_after
    try:
        app.connect(args.host,args.port,args.client_id); threading.Thread(target=app.run,daemon=True).start()
        if not app.ready.wait(args.timeout): raise TimeoutError("TWS/account handshake timed out")
        if app.failure: raise RuntimeError(app.failure)
        app.order_id=app.next_id; app.placeOrder(app.order_id,contract,make_order(qty,price,live))
        if not app.done.wait(args.timeout+args.cancel_after):
            if live: app.cancel()
            raise TimeoutError(f"Timed out waiting for {label} order result")
        if app.failure: raise RuntimeError(app.failure)
        print(f"PASS {label}")
    finally:
        if live and not app.done.is_set(): app.cancel(); time.sleep(1)
        app.disconnect()

def main():
    p=argparse.ArgumentParser(); p.add_argument("--confirm-live"); p.add_argument("--option-expiry",default="20261016")
    p.add_argument("--option-strike",type=float,default=400); p.add_argument("--option-right",choices=["C","P"],default="C"); a=p.parse_args()
    root=Path(__file__).resolve().parent
    cmds=[[sys.executable,str(root/"01_stock_order.py")],
          [sys.executable,str(root/"02_option_order.py"),"--expiry",a.option_expiry,"--strike",str(a.option_strike),"--right",a.option_right],
          [sys.executable,str(root/"03_bond_order.py")]]
    if a.confirm_live: cmds=[x+["--confirm-live",a.confirm_live] for x in cmds]
    failed=[]
    for cmd in cmds:
        print(f"\n===== {Path(cmd[1]).name} =====",flush=True); result=subprocess.run(cmd,cwd=root,check=False)
        if result.returncode: failed.append(Path(cmd[1]).name)
    print(f"\nSUMMARY passed={len(cmds)-len(failed)} failed={len(failed)}"); return 1 if failed else 0

if __name__=="__main__": raise SystemExit(main())
