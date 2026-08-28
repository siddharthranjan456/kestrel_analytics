# Kestrel Analytics

A laptop-scale analytical foundation for Kestrel Provisions. It validates the
partitioned landing zone, standardises inconsistent feeds, builds documented
KPIs in DuckDB, reconciles trusted sales with the legacy Finance report, and
shows the results and SQL in Streamlit.

## Architecture

```text
Raw Parquet + reference CSVs
        -> manifest/readability checks
        -> staging views
        -> cleaned, deduplicated tables
        -> KPI marts + query library
        -> DuckDB + Streamlit
```

Raw data is never modified. The known corrupt telemetry part is reported and
excluded from metrics instead of causing the complete pipeline to fail.

## Cold start

Python 3.11+ is recommended.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python pipeline.py --generate --scale 1
streamlit run app.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python pipeline.py --generate --scale 1
streamlit run app.py
```

If the assignment data is already present under `data/`, omit `--generate`:

```bash
python pipeline.py --data-path data
```

The generator deletes and recreates its output directory, so do not use
`--generate` against a folder containing data you need to preserve.

## Outputs

- `output/kestrel.duckdb`: queryable analytical database
- `output/data_quality_report.csv`: partition and business-rule failures
- `output/pipeline_summary.csv`: raw-to-curated row summary
- `output/kpi_catalogue.yml`: copy of the governed KPI catalogue

## Implemented metrics

1. Gross and net sales using local business date and deduplicated POS lines.
2. Units sold in eaches with explicit unresolved-UOM reporting.
3. Weekly reconciliation against the legacy Finance report.
4. Cold-chain excursion rate using normalized temperatures.
5. Median RECEIVE-to-DISPATCH warehouse cycle time.
6. Partition completeness and Parquet readability.

Definitions, owners, filters, exclusions and limitations are centralized in
`config/metrics.yml`. Runnable analyst-facing SQL lives in `sql/queries/`.

## Tests

```bash
pytest -q
```

For an end-to-end development test, generate a small sample first:

```bash
python generate_dataset.py --scale 0.01 --out data_test
pytest -q -m integration
```

## Important modelling decisions

- POS timestamps are UTC and are converted to `Asia/Kolkata` before assigning a business date.
- POS schema drift is handled with name-based Parquet union and `qty`/`quantity_units` coalescing.
- POS lines are deduplicated on `(txn_id, txn_line_no)`.
- CDC current state is ordered by `(__op_ts, __seq)` and tombstones are excluded.
- Fahrenheit is converted to Celsius; missing units are inferred from the known vendor convention.
- Firmware `2.1.4` timestamps are corrected by seven hours.
- A cold-chain trip is a documented proxy: vehicle + route + calendar day.
- Carrier-level excursions are not claimed because the supplied feeds contain no carrier mapping.

## Repository policy

The assignment explicitly says not to commit the dataset. `data/`, generated
databases and reports are ignored. The fixed-seed generator remains committed
so evaluators can reproduce scale 1.

