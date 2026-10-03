"""Minimum-size US Treasury order: one USD 1,000-face-value bond unit."""
import argparse
from ibapi.contract import Contract
from run_all import add_connection_args, execute_test
p=argparse.ArgumentParser(description=__doc__); add_connection_args(p,203)
p.add_argument("--cusip",default="91282CQQ7"); p.add_argument("--limit",type=float,default=90.00); a=p.parse_args()
c=Contract(); c.symbol=a.cusip; c.secType="BOND"; c.exchange="SMART"; c.currency="USD"
execute_test(a,c,1,a.limit,"bond")
