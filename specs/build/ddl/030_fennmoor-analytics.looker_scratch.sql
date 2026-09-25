CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.looker_scratch` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.looker_scratch.LR_2K9WQXM1T7B8E_customer_facts` (
  `customer_key` INT64,
  `cif_number` STRING,
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
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.looker_scratch.LR_3M6N9B2V5C8X1_digital_funnel_daily` (
  `session_date` DATE,
  `traffic_medium` STRING,
  `campaign_name` STRING,
  `device_category` STRING,
  `sessions` INT64,
  `started` INT64,
  `submitted` INT64,
  `conversion_rate` FLOAT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.looker_scratch.LR_5T7Y9U1I3O5P7_card_spend_by_mcc` (
  `month_start` DATE,
  `mcc_category_group` STRING,
  `spend` NUMERIC,
  `txn_count` INT64,
  `active_accounts` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.looker_scratch.LR_6H0IZB3PQ4C6N_customer_facts` (
  `customer_key` INT64,
  `cif_number` STRING,
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
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.looker_scratch.LR_7F2G5H8J1K4L6_delinquency_trend` (
  `snapshot_date` DATE,
  `bucket` STRING,
  `loans` INT64,
  `past_due_amount` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.looker_scratch.LR_8B3N0C5D2X7Z1_churn_explore` (
  `score_date` DATE,
  `customer_key` INT64,
  `segment` STRING,
  `state_code` STRING,
  `churn_score` FLOAT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.looker_scratch.LR_9P2O5I8U1Y4T7_branch_scorecard` (
  `month_start` DATE,
  `branch_id` INT64,
  `branch_name` STRING,
  `region` STRING,
  `txn_count` INT64,
  `deposit_amount` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.looker_scratch.LR_Q1Z7T4V9N2M5A_site_monthly_kpis` (
  `month_start` DATE,
  `site_id` STRING,
  `site_name` STRING,
  `is_outsourced` BOOL,
  `contacts` INT64,
  `closure_calls` INT64,
  `total_expense` NUMERIC,
  `cost_per_contact` NUMERIC
);
