CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_customer` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_customer.customer_360` (
  `customer_key` INT64,
  `cif_number` STRING,
  `full_name` STRING,
  `primary_email` STRING,
  `segment` STRING,
  `tenure_months` INT64,
  `state_code` STRING,
  `is_digitally_enrolled` BOOL,
  `open_deposit_accounts` INT64,
  `open_card_accounts` INT64,
  `open_loans` INT64,
  `product_count` INT64,
  `first_account_open_date` DATE,
  `total_deposit_balance` NUMERIC,
  `card_spend_90d` NUMERIC,
  `card_txn_count_90d` INT64,
  `contacts_90d` INT64,
  `closure_calls_90d` INT64,
  `web_sessions_30d` INT64,
  `churn_probability` FLOAT64,
  `churn_risk_band` STRING
)
CLUSTER BY customer_key
OPTIONS (description = "Customer 360. Refreshed nightly. Churn from ml_scores.churn_score_v3.");

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_customer.customer_monthly_summary` (
  `month_start` DATE,
  `customer_key` INT64,
  `avg_daily_total_balance` NUMERIC,
  `max_daily_total_balance` NUMERIC,
  `accounts_with_balance` INT64
)
PARTITION BY month_start;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_customer.customer_product_holdings` (
  `customer_key` INT64,
  `product_code` STRING,
  `product_family` STRING,
  `product_line` STRING,
  `open_accounts` INT64,
  `first_open_date` DATE,
  `last_close_date` DATE
);
