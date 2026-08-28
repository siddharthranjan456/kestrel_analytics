from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import pandas as pd

from src.database import connect, sql_list
from src.validation import manifest_checks


ROOT = Path(__file__).resolve().parent


def generate_if_requested(data_root: Path, generate: bool, scale: float) -> None:
    if (data_root / "raw").exists():
        return
    if not generate:
        raise FileNotFoundError(
            f"Raw data not found at {data_root / 'raw'}. "
            "Copy the supplied data folder or rerun with --generate."
        )
    generator = ROOT / "generate_dataset.py"
    if not generator.exists():
        raise FileNotFoundError(f"Missing generator: {generator}")
    subprocess.run(
        [sys.executable, str(generator), "--scale", str(scale), "--out", str(data_root)],
        check=True,
    )


def execute_folder(con, folder: Path, replacements: dict[str, str]) -> None:
    for path in sorted(folder.glob("*.sql")):
        sql = path.read_text(encoding="utf-8")
        for key, value in replacements.items():
            sql = sql.replace("{{" + key + "}}", value)
        print(f"Running {path.relative_to(ROOT)}")
        con.execute(sql)


def add_business_quality_checks(con, quality: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("duplicate_pos_business_keys", "pos_transactions",
         "SELECT COUNT(*)-COUNT(DISTINCT txn_id || '|' || txn_line_no) FROM stg_pos",
         "WARNING", "Duplicate rows are removed in clean_pos"),
        ("unresolved_uom_lines", "pos_transactions",
         "SELECT COALESCE(SUM(unresolved_uom),0) FROM mart_sales_lines",
         "WARNING", "Case rows without reference conversion are excluded from eaches"),
        ("null_temperature_readings", "reefer_telemetry",
         "SELECT COUNT(*) FROM clean_telemetry WHERE temperature_c IS NULL",
         "WARNING", "Null sensor readings are excluded from excursion calculations"),
        ("incomplete_wms_orders", "wms_scan_events",
         "WITH x AS (SELECT order_number, BOOL_OR(event_type='RECEIVE') r, BOOL_OR(event_type='DISPATCH') d FROM stg_wms GROUP BY 1) SELECT COUNT(*) FROM x WHERE NOT r OR NOT d",
         "WARNING", "Incomplete event sequences are excluded from cycle time"),
    ]
    extra = []
    for name, feed, query, status, details in checks:
        value = int(con.execute(query).fetchone()[0])
        extra.append({"check_name": name, "feed": feed, "partition": "ALL",
                      "status": "PASS" if value == 0 else status,
                      "expected": 0, "actual": value, "details": details})
    return pd.concat([quality, pd.DataFrame(extra)], ignore_index=True)


def run(data_root: Path, output_root: Path, generate: bool = False, scale: float = 1.0) -> Path:
    data_root, output_root = data_root.resolve(), output_root.resolve()
    generate_if_requested(data_root, generate, scale)
    output_root.mkdir(parents=True, exist_ok=True)

    print("Validating partitions and Parquet readability")
    quality, readable = manifest_checks(data_root)
    required = ["pos_transactions", "reefer_telemetry", "wms_scan_events"]
    for feed in required:
        if not readable.get(feed):
            raise RuntimeError(f"No readable Parquet files found for {feed}")

    db_path = output_root / "kestrel.duckdb"
    if db_path.exists():
        db_path.unlink()
    con = connect(db_path)
    replacements = {
        "DATA_ROOT": str(data_root).replace("\\", "/").replace("'", "''"),
        "POS_FILES": sql_list(readable["pos_transactions"]),
        "TELEMETRY_FILES": sql_list(readable["reefer_telemetry"]),
        "WMS_FILES": sql_list(readable["wms_scan_events"]),
    }
    try:
        for name in ["staging", "clean", "marts"]:
            execute_folder(con, ROOT / "sql" / name, replacements)
        quality = add_business_quality_checks(con, quality)
        con.register("quality_df", quality)
        con.execute("CREATE OR REPLACE TABLE data_quality AS SELECT * FROM quality_df")
        con.unregister("quality_df")
        summary = con.execute("""
            SELECT
              (SELECT COUNT(*) FROM stg_pos) raw_pos_rows,
              (SELECT COUNT(*) FROM clean_pos) clean_pos_rows,
              (SELECT COUNT(*) FROM mart_sales_lines) valid_sales_lines,
              (SELECT COUNT(*) FROM mart_cold_chain_trip) observed_cold_chain_trips,
              (SELECT COUNT(*) FROM mart_warehouse_order_cycle) complete_wms_orders
        """).df()
    finally:
        con.close()

    quality.to_csv(output_root / "data_quality_report.csv", index=False)
    summary.to_csv(output_root / "pipeline_summary.csv", index=False)
    shutil.copy2(ROOT / "config" / "metrics.yml", output_root / "kpi_catalogue.yml")
    print(f"Pipeline complete: {db_path}")
    return db_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Kestrel's trusted analytical layer")
    parser.add_argument("--data-path", type=Path, default=ROOT / "data")
    parser.add_argument("--output-path", type=Path, default=ROOT / "output")
    parser.add_argument("--generate", action="store_true", help="Generate fixed-seed data when raw data is absent")
    parser.add_argument("--scale", type=float, default=1.0)
    args = parser.parse_args()
    run(args.data_path, args.output_path, args.generate, args.scale)


if __name__ == "__main__":
    main()
