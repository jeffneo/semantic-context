CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.sbx_fraud` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_fraud.ato_signals_login` (
  `olb_user_id` STRING,
  `event_date` DATE,
  `failed_logins` INT64,
  `distinct_devices` INT64,
  `distinct_countries` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_fraud.bust_out_candidates` (
  `account_id` INT64,
  `card_status` STRING,
  `card_balance` NUMERIC,
  `deposit_status` STRING,
  `deposit_open_date` DATE
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_fraud.p2p_scam_cases_2026` (
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
);
