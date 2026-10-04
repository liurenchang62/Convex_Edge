"""Run deterministic feature-layer acceptance scripts."""

from __future__ import annotations

import subprocess
import sys
import argparse
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--include-live", action="store_true", help="also run the read-only IBKR smoke test")
args = parser.parse_args()
scripts = sorted(root.glob("[0-9][0-9]_*.py"))
if not args.include_live:
    scripts = [script for script in scripts if not script.name.startswith("00_")]
failures = []
for script in scripts:
    print(f"===== {script.name} =====", flush=True)
    result = subprocess.run([sys.executable, str(script)], cwd=root, check=False)
    if result.returncode:
        failures.append(script.name)
print(f"SUMMARY executed={len(scripts)} passed={len(scripts)-len(failures)} failed={len(failures)}")
for failure in failures:
    print(f"FAIL {failure}")
raise SystemExit(1 if failures else 0)
