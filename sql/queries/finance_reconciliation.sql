SELECT * FROM mart_finance_reconciliation
WHERE week_ending BETWEEN $start_date AND $end_date
ORDER BY week_ending, channel;

