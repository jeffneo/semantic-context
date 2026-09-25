CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.sbx_finance` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_finance.cc_cost_per_call_fy25` (
  `fiscal_period` STRING,
  `cc_id` STRING,
  `expense` NUMERIC,
  `calls` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_finance.eom_bal_by_product_tableau` (
  `snap_month` DATE,
  `reporting_category` STRING,
  `eom_balance` NUMERIC
);
