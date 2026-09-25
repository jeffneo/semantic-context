CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.gl_erp` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.gl_erp.CC_EXPENSE_SUMMARY` (
  `PERIOD_NAME` STRING,
  `CC_ID` STRING NOT NULL,
  `GL_ACCT` STRING,
  `ACTUAL_AMT` NUMERIC,
  `BUDGET_AMT` NUMERIC,
  `VARIANCE_AMT` NUMERIC,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.gl_erp.cost_center` (
  `cost_center_id` STRING NOT NULL,
  `cost_center_name` STRING,
  `department_code` STRING,
  `owner_worker_id` STRING,
  `region` STRING,
  `is_active` BOOL,
  `effective_date` DATE,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.gl_erp.gl_account` (
  `gl_account_code` STRING NOT NULL,
  `account_name` STRING,
  `account_type` STRING,
  `parent_code` STRING,
  `is_active` BOOL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.gl_erp.journal_line` (
  `journal_id` STRING NOT NULL,
  `line_number` INT64,
  `period_name` STRING,
  `accounting_date` DATE,
  `gl_account_code` STRING,
  `cost_center_id` STRING,
  `entered_dr` NUMERIC,
  `entered_cr` NUMERIC,
  `line_description` STRING,
  `source` STRING,
  `currency_code` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY accounting_date
CLUSTER BY cost_center_id, gl_account_code;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.gl_erp.vendor_invoice` (
  `invoice_id` STRING NOT NULL,
  `vendor_name` STRING,
  `cost_center_id` STRING,
  `gl_account_code` STRING,
  `invoice_date` DATE,
  `amount` NUMERIC,
  `po_number` STRING,
  `line_description` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY invoice_date;
