CREATE OR REPLACE TABLE clean_pos AS
SELECT * EXCLUDE(rn)
FROM (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY txn_id, txn_line_no
    ORDER BY ingest_date DESC, source_file DESC
  ) AS rn
  FROM stg_pos
)
WHERE rn = 1;

CREATE OR REPLACE TABLE clean_telemetry AS
SELECT * EXCLUDE(reading_ts),
       CAST(reading_ts AS TIMESTAMP)
         - CASE WHEN firmware_version = '2.1.4' THEN INTERVAL 7 HOUR ELSE INTERVAL 0 HOUR END
         AS reading_ts,
       CASE
         WHEN UPPER(COALESCE(temp_unit, CASE WHEN telemetry_vendor='COLDEYE' THEN 'F' ELSE 'C' END)) = 'F'
           THEN (temp_value - 32.0) * 5.0 / 9.0
         ELSE temp_value
       END AS temperature_c
FROM stg_telemetry
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY device_id, reading_ts, route_code, gateway_id, temp_value
) = 1;

CREATE OR REPLACE TABLE current_outlets AS
SELECT * EXCLUDE(rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY outlet_code ORDER BY CAST(__op_ts AS TIMESTAMPTZ) DESC, __seq DESC) rn
  FROM stg_outlet_cdc
) WHERE rn=1 AND __op <> 'D';

CREATE OR REPLACE TABLE current_products AS
SELECT * EXCLUDE(rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY sku_code ORDER BY CAST(__op_ts AS TIMESTAMPTZ) DESC, __seq DESC) rn
  FROM stg_product_cdc
) WHERE rn=1 AND __op <> 'D';

CREATE OR REPLACE TABLE current_orders AS
SELECT * EXCLUDE(rn) FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY order_number ORDER BY CAST(__op_ts AS TIMESTAMPTZ) DESC, __seq DESC) rn
  FROM stg_order_cdc
) WHERE rn=1 AND __op <> 'D';

