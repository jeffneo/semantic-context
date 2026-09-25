CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.ml_features` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.ml_features.feat_card_velocity` (
  `card_account_id` INT64,
  `txn_count_1d` INT64,
  `txn_count_7d` INT64,
  `amount_7d` NUMERIC,
  `distinct_mcc_7d` INT64,
  `foreign_txn_7d` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.ml_features.feat_customer_daily` (
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
)
PARTITION BY as_of_date;
