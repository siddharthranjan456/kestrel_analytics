CREATE OR REPLACE TABLE mart_cold_chain_trip AS
SELECT vehicle_registration || '|' || route_code || '|' || CAST(CAST(reading_ts AS DATE) AS VARCHAR) AS trip_id,
       warehouse_code, DATE_TRUNC('month', reading_ts)::DATE AS month,
       MIN(reading_ts) trip_start, MAX(reading_ts) trip_end,
       COUNT(temperature_c) valid_readings, MAX(temperature_c) max_temperature_c,
       BOOL_OR(temperature_c > 8.0) breached
FROM clean_telemetry
WHERE temperature_c IS NOT NULL
GROUP BY ALL;

CREATE OR REPLACE TABLE mart_cold_chain_monthly AS
SELECT t.month, t.warehouse_code, w.warehouse_name,
       COUNT(*) observed_trips,
       COUNT(*) FILTER (WHERE breached) breached_trips,
       100.0*COUNT(*) FILTER (WHERE breached)/NULLIF(COUNT(*),0) excursion_rate_pct
FROM mart_cold_chain_trip t LEFT JOIN ref_warehouse w USING (warehouse_code)
GROUP BY ALL;

CREATE OR REPLACE TABLE mart_warehouse_order_cycle AS
WITH bounds AS (
 SELECT order_number, warehouse_code,
        MIN(CAST(event_ts AS TIMESTAMP)) FILTER (WHERE event_type='RECEIVE') receive_ts,
        MAX(CAST(event_ts AS TIMESTAMP)) FILTER (WHERE event_type='DISPATCH') dispatch_ts
 FROM stg_wms GROUP BY ALL
)
SELECT *, DATE_DIFF('minute', receive_ts, dispatch_ts) cycle_minutes
FROM bounds
WHERE receive_ts IS NOT NULL AND dispatch_ts IS NOT NULL AND dispatch_ts >= receive_ts;

CREATE OR REPLACE TABLE mart_warehouse_cycle_summary AS
SELECT c.warehouse_code, w.warehouse_name, COUNT(*) complete_orders,
       MEDIAN(cycle_minutes) median_cycle_minutes,
       AVG(cycle_minutes) average_cycle_minutes
FROM mart_warehouse_order_cycle c LEFT JOIN ref_warehouse w USING (warehouse_code)
GROUP BY ALL;

