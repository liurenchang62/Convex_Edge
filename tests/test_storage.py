import json

import pandas as pd
import pytest

from convexedge.data.storage import verify_snapshot, write_snapshot


def test_snapshot_is_immutable_and_verifiable(tmp_path) -> None:
    frame = pd.DataFrame({"instrument_id": ["AAPL"], "close": [100.0]})
    path = write_snapshot(frame, tmp_path, dataset="stock-bars", snapshot_id="sample")
    manifest = verify_snapshot(path)
    assert manifest["rows"] == 1
    with pytest.raises(FileExistsError):
        write_snapshot(frame, tmp_path, dataset="stock-bars", snapshot_id="sample")


def test_snapshot_detects_tampered_manifest(tmp_path) -> None:
    frame = pd.DataFrame({"x": [1]})
    path = write_snapshot(frame, tmp_path, dataset="test", snapshot_id="sample")
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["rows"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="schema mismatch"):
        verify_snapshot(path)

