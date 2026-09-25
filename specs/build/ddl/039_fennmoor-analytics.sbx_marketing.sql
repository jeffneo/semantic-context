CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.sbx_marketing` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_marketing.attrition_propensity_2025` (
  `cif_number` STRING,
  `model_run_date` DATE,
  `attrition_propensity` FLOAT64,
  `decile` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_marketing.campain_results_2025` (
  `campaign_id` STRING,
  `campaign_name` STRING,
  `delivered` INT64,
  `opens` INT64,
  `clicks` INT64,
  `unsubscribes` INT64,
  `open_rate` FLOAT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_marketing.card_spend_by_segment` (
  `segment` STRING,
  `month_start` DATE,
  `card_spend_usd` INT64,
  `cardholders` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_marketing.email_list_affluent_apr26` (
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
  `churn_probability` FLOAT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_marketing.web_to_branch_journeys` (
  `event_date` DATE,
  `segment` STRING,
  `sessions` INT64
);
