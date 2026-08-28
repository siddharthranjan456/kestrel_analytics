SELECT business_date, channel, SUM(units_sold_eaches) AS units_sold_eaches
FROM mart_sales_daily
WHERE business_date BETWEEN $start_date AND $end_date
GROUP BY ALL ORDER BY business_date, channel;

