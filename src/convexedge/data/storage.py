"""Immutable Parquet snapshots with auditable manifests."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd


SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")


def _safe_name(value: str, label: str) -> str:
    if not value or not SAFE_NAME.fullmatch(value):
        raise ValueError(f"unsafe {label}: {value!r}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_snapshot(
    frame: pd.DataFrame,
    root: str | Path,
    *,
    dataset: str,
    snapshot_id: str,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Atomically write one immutable Parquet snapshot and JSON manifest."""

    dataset = _safe_name(dataset, "dataset")
    snapshot_id = _safe_name(snapshot_id, "snapshot_id")
    target = Path(root).resolve() / dataset / snapshot_id
    if target.exists():
        raise FileExistsError(f"snapshot already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix=f".{snapshot_id}-", dir=target.parent))
    try:
        data_path = temp / "data.parquet"
        frame.to_parquet(data_path, index=False)
        manifest = {
            "dataset": dataset,
            "snapshot_id": snapshot_id,
            "created_at": datetime.now(UTC).isoformat(),
            "rows": len(frame),
            "columns": list(frame.columns),
            "data_file": data_path.name,
            "sha256": sha256_file(data_path),
            "metadata": metadata or {},
        }
        (temp / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        os.replace(temp, target)
    except Exception:
        for child in temp.iterdir():
            child.unlink()
        temp.rmdir()
        raise
    return target


def verify_snapshot(path: str | Path) -> dict[str, Any]:
    snapshot = Path(path)
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    data_path = snapshot / manifest["data_file"]
    if sha256_file(data_path) != manifest["sha256"]:
        raise ValueError(f"snapshot checksum mismatch: {snapshot}")
    frame = pd.read_parquet(data_path)
    if len(frame) != manifest["rows"] or list(frame.columns) != manifest["columns"]:
        raise ValueError(f"snapshot schema mismatch: {snapshot}")
    return manifest

