CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_finance` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_finance.dim_cost_center` (
  `cost_center_id` STRING,
  `cost_center_name` STRING,
  `department_code` STRING,
  `region` STRING,
  `is_active` BOOL,
  `owner_worker_id` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_finance.fct_customer_profitability_monthly` (
  `customer_key` INT64,
  `month_start` DATE,
  `avg_balance` NUMERIC,
  `fee_revenue` NUMERIC,
  `interchange_revenue` NUMERIC,
  `deposit_margin` NUMERIC,
  `total_revenue` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_finance.fct_fee_income_monthly` (
  `month_start` DATE,
  `product_code` STRING,
  `fee_type` STRING,
  `gross_fees` NUMERIC,
  `waived_fees` NUMERIC,
  `net_fees` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_finance.fct_gl_monthly` (
  `month_start` DATE,
  `period_name` STRING,
  `gl_account_code` STRING,
  `account_type` STRING,
  `cost_center_id` STRING,
  `net_amount` NUMERIC
)
PARTITION BY month_start;
