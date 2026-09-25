CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.sbx_customer_analytics` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_customer_analytics.churn_cohort_analysis_2026q1` (
  `score_date` DATE,
  `customer_key` INT64,
  `churn_score` FLOAT64,
  `close_date` DATE,
  `days_to_close` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_customer_analytics.customer_360_final` (
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
  `churn_risk` FLOAT64,
  `churn_risk_band` STRING,
  `ltv_estimate` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_customer_analytics.customer_360_final_FIXED` (
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
  `churn_risk` FLOAT64,
  `churn_risk_band` STRING,
  `ltv_estimate` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_customer_analytics.customer_360_v2` (
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
  `churn_risk_band` STRING,
  `ltv_estimate` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_customer_analytics.hh_rollup_test` (
  `sf_household_id` STRING,
  `members` INT64,
  `segment` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_customer_analytics.tmp_cust_bal_check` (
  `balance_date` DATE,
  `account_key` INT64,
  `core_account_id` INT64,
  `customer_key` INT64,
  `product_code` STRING,
  `ledger_balance` NUMERIC,
  `available_balance` NUMERIC,
  `accrued_interest` NUMERIC
);
