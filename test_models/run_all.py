"""Run all model-layer acceptance tests."""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
scripts = sorted(root.glob("[0-9][0-9]_*.py"))
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
