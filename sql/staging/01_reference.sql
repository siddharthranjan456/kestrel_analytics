CREATE OR REPLACE TABLE ref_fiscal_calendar AS
SELECT * FROM read_csv_auto('{{DATA_ROOT}}/reference/fiscal_calendar.csv', header=true);

CREATE OR REPLACE TABLE ref_uom_conversion AS
SELECT * FROM read_csv_auto('{{DATA_ROOT}}/reference/uom_conversion.csv', header=true);

CREATE OR REPLACE TABLE ref_warehouse AS
SELECT * FROM read_csv_auto('{{DATA_ROOT}}/reference/warehouse_master.csv', header=true);

CREATE OR REPLACE TABLE ref_carrier AS
SELECT * FROM read_csv_auto('{{DATA_ROOT}}/reference/carrier_master.csv', header=true);

CREATE OR REPLACE TABLE legacy_finance AS
SELECT * FROM read_csv_auto('{{DATA_ROOT}}/reference/legacy_finance_weekly_report.csv', header=true);

