CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.reverse_etl` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.reverse_etl.aud_card_upsell_q2_2026` (
  `customer_key` INT64,
  `offer_product_code` STRING,
  `propensity` FLOAT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.reverse_etl.aud_high_value_churn_risk` (
  `external_id` STRING,
  `churn_probability` FLOAT64,
  `segment` STRING,
  `total_deposit_balance` NUMERIC,
  `email` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.reverse_etl.braze_attr_sync` (
  `external_id` STRING,
  `segment` STRING,
  `is_digitally_enrolled` BOOL,
  `open_card_accounts` INT64,
  `next_best_offer` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.reverse_etl.sf_sync_customer_scores` (
  `sf_contact_id` STRING,
  `churn_probability__c` FLOAT64,
  `product_count__c` INT64,
  `total_deposit_balance__c` NUMERIC,
  `card_spend_90d__c` NUMERIC
);
