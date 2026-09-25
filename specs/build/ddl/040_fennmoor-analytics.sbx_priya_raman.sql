CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.sbx_priya_raman` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_priya_raman.q2_board_deck_numbers` (
  `segment` STRING,
  `customers` INT64,
  `avg_balance` NUMERIC,
  `avg_churn` FLOAT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_priya_raman.tmp_priya_churn_feats` (
  `as_of_date` DATE,
  `customer_key` INT64,
  `tenure_months` INT64,
  `segment` STRING,
  `avg_balance_30d` NUMERIC,
  `logins_30d` INT64,
  `failed_logins_30d` INT64,
  `contacts_90d` INT64,
  `closure_calls_90d` INT64,
  `fee_count_90d` INT64,
  `waived_fee_count_90d` INT64
);
