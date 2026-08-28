SELECT * FROM mart_cold_chain_monthly
WHERE month BETWEEN $start_date AND $end_date
ORDER BY month, warehouse_code;

