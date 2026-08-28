from __future__ import annotations

from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq


def readable_parquet_files(root: Path) -> tuple[list[Path], list[dict]]:
    readable, issues = [], []
    for path in sorted(root.rglob("*.parquet")):
        try:
            pq.ParquetFile(path).metadata
            readable.append(path)
        except Exception as exc:
            issues.append({"check_name": "parquet_readable", "feed": root.name,
                           "partition": path.parent.name, "status": "FAIL",
                           "expected": None, "actual": None,
                           "details": f"{path.name}: {type(exc).__name__}"})
    return readable, issues


def manifest_checks(data_root: Path) -> tuple[pd.DataFrame, dict[str, list[Path]]]:
    manifest_path = data_root / "_manifest" / "expected_partitions.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")
    manifest = pd.read_csv(manifest_path)
    rows: list[dict] = []
    readable_by_feed: dict[str, list[Path]] = {}

    for feed in manifest["feed"].unique():
        root = data_root / "raw" / feed
        readable, read_issues = readable_parquet_files(root)
        readable_by_feed[feed] = readable
        rows.extend(read_issues)
        readable_set = set(readable)
        for item in manifest.loc[manifest.feed == feed].itertuples(index=False):
            part_dir = root / item.partition
            actual_files = sorted(part_dir.glob("*.parquet")) if part_dir.exists() else []
            valid_files = [p for p in actual_files if p in readable_set]
            actual_rows = sum(pq.ParquetFile(p).metadata.num_rows for p in valid_files)
            file_ok = len(actual_files) == int(item.file_count)
            read_ok = len(valid_files) == len(actual_files)
            row_ok = actual_rows == int(item.row_count)
            status = "PASS" if file_ok and read_ok and row_ok else "FAIL"
            rows.append({"check_name": "manifest_reconciliation", "feed": feed,
                         "partition": item.partition, "status": status,
                         "expected": int(item.row_count), "actual": actual_rows,
                         "details": (f"files expected={int(item.file_count)}, found={len(actual_files)}, "
                                     f"readable={len(valid_files)}")})
    return pd.DataFrame(rows), readable_by_feed

