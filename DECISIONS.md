# Decisions

## Built

I built a reproducible DuckDB metric layer rather than a dashboard-first
solution: source/manifest validation, staging views, POS deduplication and
schema-drift handling, timezone and telemetry normalization, CDC current-state
models, five governed KPI models, Finance reconciliation, a SQL library,
automated rule tests, and a small Streamlit interface that exposes definitions
and SQL.

## Deliberately not built

I did not add cloud infrastructure, orchestration, authentication, streaming,
or unrestricted text-to-SQL. They do not improve trust in the eight-hour core.
I also do not report cold-chain performance by carrier: no supplied key maps a
telemetry reading/route/vehicle to `carrier_id`, so such a result would be
invented.

## Assumptions

`(txn_id, txn_line_no)` is the POS business key. Business date is the UTC sale
timestamp converted to Asia/Kolkata, not ingest date. CDC latest state is the
greatest `(__op_ts, __seq)` and a latest `D` is absent current state. Missing
temperature unit follows the observed vendor convention. A trip is proxied by
vehicle, route and corrected reading date. Excursion means at least one valid
reading above 8°C; this intentionally errs toward sensitivity and is labelled
as vulnerable to sensor spikes. Warehouse cycle is first RECEIVE to last
DISPATCH; incomplete sequences are excluded and counted.

## With two more weeks

I would validate metric definitions with Finance and Operations, build
point-in-time outlet/product dimensions, replace the trip proxy with dispatch
assignments, add consecutive-reading/duration excursion rules, introduce dbt
tests and lineage, add incremental partition processing, and evaluate a
read-only semantic text-to-SQL layer restricted to approved views.

## What breaks first

At roughly 100× volume, full refreshes and global window sorts for deduplication
and CDC become the first bottlenecks, followed by a single local database and
interactive scans. I would retain the SQL contracts but process only new/changed
partitions on object storage with Spark/Trino/dbt, compact small files, cluster
by business keys and dates, and serve pre-aggregated marts through a governed
warehouse. The supplied corrupt Parquet part already demonstrates why file-level
quarantine and observability are required before scale becomes the problem.

