CREATE OR REPLACE TABLE mart_sales_lines AS
SELECT p.*, CAST(p.event_ts_local AS DATE) AS business_date,
       c.fiscal_year, c.fiscal_quarter, c.fiscal_month_no, c.iso_week,
       p.quantity * p.unit_price AS gross_sales,
       p.quantity * p.unit_price - COALESCE(p.discount_amount,0) AS net_sales,
       CASE WHEN p.uom='EA' THEN p.quantity
            WHEN p.uom='CS' THEN p.quantity * u.eaches_per_case END AS eaches,
       CASE WHEN p.uom='CS' AND u.eaches_per_case IS NULL THEN 1 ELSE 0 END AS unresolved_uom
FROM clean_pos p
LEFT JOIN ref_fiscal_calendar c ON CAST(p.event_ts_local AS DATE)=CAST(c.calendar_date AS DATE)
LEFT JOIN ref_uom_conversion u USING (sku_code)
WHERE p.quantity > 0 AND p.unit_price >= 0 AND p.event_ts_local IS NOT NULL;

CREATE OR REPLACE TABLE mart_sales_daily AS
SELECT business_date, fiscal_year, fiscal_quarter, fiscal_month_no, iso_week, channel,
       SUM(gross_sales) gross_sales, SUM(net_sales) net_sales,
       SUM(eaches) units_sold_eaches, COUNT(DISTINCT basket_id) basket_count,
       SUM(unresolved_uom) unresolved_uom_lines
FROM mart_sales_lines
GROUP BY ALL;

CREATE OR REPLACE TABLE mart_finance_reconciliation AS
WITH trusted AS (
 SELECT f.week_ending, s.channel,
        SUM(s.gross_sales) AS trusted_gross_sales,
        SUM(s.units_sold_eaches) AS trusted_units_sold,
        SUM(s.basket_count) AS trusted_basket_count
 FROM legacy_finance f
 JOIN mart_sales_daily s
   ON s.business_date BETWEEN CAST(f.week_ending AS DATE)-INTERVAL 6 DAY AND CAST(f.week_ending AS DATE)
  AND s.channel=f.channel
 GROUP BY f.week_ending, s.channel
)
SELECT f.week_ending, f.channel, t.trusted_gross_sales,
       f.gross_sales_inr AS finance_gross_sales,
       t.trusted_gross_sales-f.gross_sales_inr AS variance_inr,
       100.0*(t.trusted_gross_sales-f.gross_sales_inr)/NULLIF(f.gross_sales_inr,0) AS variance_pct,
       t.trusted_units_sold, f.units_sold AS finance_units_sold,
       t.trusted_basket_count, f.basket_count AS finance_basket_count
FROM legacy_finance f LEFT JOIN trusted t USING (week_ending, channel);

