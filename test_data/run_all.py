"""Run every numbered TWS API test in this folder, in order."""

from __future__ import annotations

import argparse
import math
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper


HOST = "127.0.0.1"
LIVE_PORT = 7496


def connection_args(parser: argparse.ArgumentParser, client_id: int) -> None:
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=LIVE_PORT)
    parser.add_argument("--client-id", type=int, default=client_id)
    parser.add_argument("--timeout", type=float, default=15.0)


def stock(symbol: str = "AAPL") -> Contract:
    c = Contract()
    c.symbol, c.secType, c.exchange, c.currency = symbol, "STK", "SMART", "USD"
    return c


def forex(pair: str = "EURUSD") -> Contract:
    c = Contract()
    c.symbol, c.secType, c.exchange, c.currency = pair[:3], "CASH", "IDEALPRO", pair[3:]
    return c


def index(symbol: str = "SPX") -> Contract:
    c = Contract()
    c.symbol, c.secType, c.exchange, c.currency = symbol, "IND", "CBOE", "USD"
    return c


def bond(identifier: str, currency: str = "USD", exchange: str = "SMART") -> Contract:
    c = Contract()
    c.symbol, c.secType, c.exchange, c.currency = identifier, "BOND", exchange, currency
    return c


class TestApp(EWrapper, EClient):
    def __init__(self) -> None:
        EClient.__init__(self, self)
        self.ready = threading.Event()
        self.done = threading.Event()
        self.rows: list[object] = []
        self.fatal_error: str | None = None

    def nextValidId(self, orderId: int) -> None:  # noqa: N802
        print(f"CONNECTED nextValidOrderId={orderId}")
        self.ready.set()

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson="") -> None:
        level = "INFO" if errorCode in {2104, 2106, 2107, 2108, 2158} else "ERROR"
        print(f"{level} reqId={reqId} code={errorCode}: {errorString}")
        if errorCode in {502, 503, 504, 1100, 1300}:
            self.fatal_error = f"{errorCode}: {errorString}"
            self.done.set()

    def connect_and_start(self, host: str, port: int, client_id: int, timeout: float) -> None:
        # ibapi.EClient.connect() returns None even when the socket is opened.
        # Connection success is confirmed asynchronously by nextValidId().
        self.connect(host, port, client_id)
        threading.Thread(target=self.run, daemon=True).start()
        if not self.ready.wait(timeout):
            self.disconnect()
            raise TimeoutError(f"TWS connection timed out: {host}:{port}, clientId={client_id}")

    def wait(self, timeout: float, label: str) -> None:
        if not self.done.wait(timeout):
            raise TimeoutError(f"Timed out waiting for {label}")
        if self.fatal_error:
            raise RuntimeError(self.fatal_error)


def run_test(args, app: TestApp, request: Callable[[], None], label: str) -> None:
    try:
        app.connect_and_start(args.host, args.port, args.client_id, args.timeout)
        request()
        app.wait(args.timeout, label)
    finally:
        app.disconnect()
        time.sleep(0.2)


def clean(value) -> object:
    return None if isinstance(value, float) and (math.isnan(value) or abs(value) > 1e307) else value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bond-id", default="91282CQQ7", help="CUSIP/ISIN (default: active 10-year US Treasury 91282CQQ7)")
    parser.add_argument("--option-expiry", default="20260918", help="YYYYMMDD (default: currently valid AAPL expiry 20260918)")
    parser.add_argument("--option-strike", type=float, default=330.0, help="Strike (default: 330, near current AAPL price)")
    parser.add_argument("--option-right", choices=["C", "P"], default="C")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    scripts = sorted(root.glob("[0-9][0-9]_*.py"))
    failures, skipped = [], []
    for script in scripts:
        command = [sys.executable, str(script)]
        if script.name.startswith(("09_", "10_", "11_")):
            if not args.bond_id:
                skipped.append(f"{script.name} (missing --bond-id)")
                continue
            command += ["--id", args.bond_id]
        if script.name.startswith("08_"):
            if not (args.option_expiry and args.option_strike is not None):
                skipped.append(f"{script.name} (missing --option-expiry/--option-strike)")
                continue
            command += ["--expiry", args.option_expiry, "--strike", str(args.option_strike), "--right", args.option_right]
        print(f"\n===== {script.name} =====", flush=True)
        result = subprocess.run(command, cwd=root, check=False)
        if result.returncode:
            failures.append(f"{script.name} (exit={result.returncode})")
    print("\n===== SUMMARY =====")
    print(f"executed={len(scripts)-len(skipped)} passed={len(scripts)-len(skipped)-len(failures)} failed={len(failures)} skipped={len(skipped)}")
    for item in skipped:
        print(f"SKIP {item}")
    for item in failures:
        print(f"FAIL {item}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
