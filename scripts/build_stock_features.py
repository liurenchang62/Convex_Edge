"""Build and store daily stock features from an immutable raw snapshot."""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from convexedge.data.storage import verify_snapshot, write_snapshot  # noqa: E402
from convexedge.features import build_daily_features, feature_columns  # noqa: E402


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("raw_snapshot", type=Path)
parser.add_argument("--output-root", type=Path, default=ROOT / "data" / "processed")
args = parser.parse_args()

manifest = verify_snapshot(args.raw_snapshot)
bars = pd.read_parquet(args.raw_snapshot / manifest["data_file"])
features = build_daily_features(bars)
created_at = datetime.now(UTC)
instrument = str(features["instrument_id"].iloc[0])
snapshot_id = f"{instrument}-{created_at.strftime('%Y%m%dT%H%M%SZ')}"
path = write_snapshot(
    features,
    args.output_root,
    dataset="stock-daily-features",
    snapshot_id=snapshot_id,
    metadata={
        "input_snapshot": str(args.raw_snapshot.resolve()),
        "input_sha256": manifest["sha256"],
        "feature_columns": feature_columns(features),
        "feature_schema_version": 2,
        "return_horizons": [1, 5, 21],
        "volatility_windows": [21, 63],
    },
)
verify_snapshot(path)
print(f"PASS snapshot={path} rows={len(features)} predictors={len(feature_columns(features))}")

