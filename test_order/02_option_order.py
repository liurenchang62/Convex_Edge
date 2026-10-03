"""Minimum-size US equity option order: one contract."""
import argparse
from ibapi.contract import Contract
from run_all import add_connection_args, execute_test
p=argparse.ArgumentParser(description=__doc__); add_connection_args(p,202)
p.add_argument("--symbol",default="AAPL"); p.add_argument("--expiry",required=True); p.add_argument("--strike",required=True,type=float)
p.add_argument("--right",choices=["C","P"],required=True); p.add_argument("--limit",type=float,default=.01); a=p.parse_args()
c=Contract(); c.symbol=a.symbol; c.secType="OPT"; c.exchange="SMART"; c.currency="USD"
c.lastTradeDateOrContractMonth=a.expiry; c.strike=a.strike; c.right=a.right; c.multiplier="100"
execute_test(a,c,1,a.limit,"option")
