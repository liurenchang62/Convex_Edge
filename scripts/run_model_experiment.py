"""Run and store a reproducible walk-forward forecasting experiment."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.data.storage import verify_snapshot, write_snapshot  # noqa: E402
from convexedge.models.experiment import run_walk_forward_experiment  # noqa: E402


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("feature_snapshot", type=Path)
parser.add_argument("--horizon", type=int, default=5)
parser.add_argument("--min-train-size", type=int, default=252)
parser.add_argument("--validation-size", type=int, default=63)
parser.add_argument("--test-size", type=int, default=21)
parser.add_argument("--random-state", type=int, default=42)
parser.add_argument("--output-root", type=Path, default=ROOT / "data" / "processed")
args = parser.parse_args()

input_manifest = verify_snapshot(args.feature_snapshot)
frame = pd.read_parquet(args.feature_snapshot / input_manifest["data_file"])
result = run_walk_forward_experiment(
    frame,
    horizon=args.horizon,
    min_train_size=args.min_train_size,
    validation_size=args.validation_size,
    test_size=args.test_size,
    random_state=args.random_state,
)
created_at = datetime.now(UTC)
snapshot_id = f"h{args.horizon}-{created_at.strftime('%Y%m%dT%H%M%SZ')}"
path = write_snapshot(
    result.predictions,
    args.output_root,
    dataset="walk-forward-model-results",
    snapshot_id=snapshot_id,
    metadata={
        "input_snapshot": str(args.feature_snapshot.resolve()),
        "input_sha256": input_manifest["sha256"],
        "horizon": args.horizon,
        "min_train_size": args.min_train_size,
        "validation_size": args.validation_size,
        "test_size": args.test_size,
        "gap": args.horizon,
        "random_state": args.random_state,
        "experiment_schema_version": 1,
        "feature_names": result.feature_names,
        "metrics": result.metrics,
    },
)
verify_snapshot(path)
print(f"PASS snapshot={path} predictions={len(result.predictions)}")
for name, value in sorted(result.metrics.items()):
    print(f"{name}={value:.8f}")

