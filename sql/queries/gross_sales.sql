SELECT fiscal_year, fiscal_quarter, channel, SUM(gross_sales) AS gross_sales
FROM mart_sales_daily
WHERE business_date BETWEEN $start_date AND $end_date
GROUP BY ALL ORDER BY fiscal_year, fiscal_quarter, channel;

