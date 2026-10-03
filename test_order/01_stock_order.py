"""Minimum-size stock order: one whole share."""
import argparse
from ibapi.contract import Contract
from run_all import add_connection_args, execute_test
p=argparse.ArgumentParser(description=__doc__); add_connection_args(p,201)
p.add_argument("--symbol",default="F"); p.add_argument("--limit",type=float,default=1.00); a=p.parse_args()
c=Contract(); c.symbol=a.symbol; c.secType="STK"; c.exchange="SMART"; c.currency="USD"
execute_test(a,c,1,a.limit,"stock")
