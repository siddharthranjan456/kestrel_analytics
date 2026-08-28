CREATE OR REPLACE VIEW stg_pos AS
SELECT txn_id, txn_line_no, basket_id, outlet_code, channel, sku_code,
       CAST(event_ts AS TIMESTAMPTZ) AS event_ts_utc,
       CAST(event_ts AS TIMESTAMPTZ) AT TIME ZONE 'Asia/Kolkata' AS event_ts_local,
       COALESCE(TRY_CAST(qty AS DOUBLE), TRY_CAST(quantity_units AS DOUBLE)) AS quantity,
       COALESCE(uom, 'EA') AS uom, TRY_CAST(unit_price AS DOUBLE) AS unit_price,
       TRY_CAST(discount_amount AS DOUBLE) AS discount_amount,
       TRY_CAST(tax_amount AS DOUBLE) AS tax_amount, source_file,
       CAST(ingest_date AS DATE) AS ingest_date
FROM read_parquet({{POS_FILES}}, union_by_name=true, hive_partitioning=true);

CREATE OR REPLACE VIEW stg_telemetry AS
SELECT *, CAST(dt AS DATE) AS partition_date
FROM read_parquet({{TELEMETRY_FILES}}, union_by_name=true, hive_partitioning=true);

CREATE OR REPLACE VIEW stg_wms AS
SELECT *, CAST(dt AS DATE) AS partition_date
FROM read_parquet({{WMS_FILES}}, union_by_name=true, hive_partitioning=true);

CREATE OR REPLACE VIEW stg_outlet_cdc AS
SELECT * FROM read_parquet('{{DATA_ROOT}}/raw/erp_cdc/outlet_master/*/*.parquet', union_by_name=true, hive_partitioning=true);

CREATE OR REPLACE VIEW stg_product_cdc AS
SELECT * FROM read_parquet('{{DATA_ROOT}}/raw/erp_cdc/product_master/*/*.parquet', union_by_name=true, hive_partitioning=true);

CREATE OR REPLACE VIEW stg_order_cdc AS
SELECT * FROM read_parquet('{{DATA_ROOT}}/raw/erp_cdc/sales_order_header/*/*.parquet', union_by_name=true, hive_partitioning=true);

