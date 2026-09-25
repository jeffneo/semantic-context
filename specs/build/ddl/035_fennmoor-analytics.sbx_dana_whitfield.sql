CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.sbx_dana_whitfield` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_dana_whitfield.dana_attrition_training_set` (
  `cif_number` STRING,
  `segment` STRING,
  `tenure_months` INT64,
  `total_deposit_balance` NUMERIC,
  `contacts_90d` INT64,
  `label_attrited` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_dana_whitfield.zzz_old_campaign_pull` (
  `message_send_id` STRING,
  `sent_date` DATE,
  `sent_at` TIMESTAMP,
  `cif_number` STRING,
  `customer_key` INT64,
  `campaign_id` STRING,
  `canvas_id` STRING,
  `channel` STRING,
  `dispatch_id` STRING
);
