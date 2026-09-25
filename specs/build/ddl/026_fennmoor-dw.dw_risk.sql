CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_risk` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_risk.fct_bureau_monthly` (
  `archive_month` DATE,
  `customer_key` INT64,
  `fico_08` INT64,
  `vantage_4` INT64,
  `utilization_pct` NUMERIC,
  `total_revolving_balance` NUMERIC,
  `num_delinquent_30_24m` INT64,
  `estimated_income` NUMERIC
)
PARTITION BY archive_month;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_risk.fct_credit_applications` (
  `application_id` STRING,
  `submitted_date` DATE,
  `customer_key` INT64,
  `applicant_cif_number` STRING,
  `product_code` STRING,
  `channel` STRING,
  `requested_amount` NUMERIC,
  `final_outcome` STRING,
  `approved_amount` NUMERIC,
  `approved_apr` NUMERIC,
  `credit_score_at_app` INT64,
  `branch_id` INT64,
  `offer_code` STRING
)
PARTITION BY submitted_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_risk.fct_delinquency_daily` (
  `snapshot_date` DATE,
  `account_key` INT64,
  `customer_key` INT64,
  `loan_number` STRING,
  `product_code` STRING,
  `dpd` INT64,
  `bucket` STRING,
  `past_due_amount` NUMERIC
)
PARTITION BY snapshot_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_risk.fct_fraud_alerts` (
  `alert_id` STRING,
  `alert_date` DATE,
  `customer_key` INT64,
  `cif_number` STRING,
  `entity_type` STRING,
  `rule_id` STRING,
  `model_score` INT64,
  `channel` STRING,
  `amount` NUMERIC,
  `disposition` STRING,
  `case_id` STRING,
  `is_confirmed_fraud` BOOL,
  `fraud_type` STRING,
  `loss_amount` NUMERIC
)
PARTITION BY alert_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_risk.fct_loan_payments` (
  `payment_id` STRING,
  `payment_date` DATE,
  `account_key` INT64,
  `loan_number` STRING,
  `amount` NUMERIC,
  `principal` NUMERIC,
  `interest` NUMERIC,
  `fee` NUMERIC,
  `is_late` BOOL,
  `is_returned` BOOL
)
PARTITION BY payment_date;
