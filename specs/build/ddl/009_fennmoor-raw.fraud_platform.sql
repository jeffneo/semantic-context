CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.fraud_platform` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.fraud_platform.alert` (
  `alert_id` STRING NOT NULL,
  `alert_ts` TIMESTAMP,
  `entity_type` STRING,
  `entity_ref` STRING,
  `cif_number` STRING,
  `rule_id` STRING,
  `model_score` INT64,
  `alert_status` STRING,
  `priority` STRING,
  `channel` STRING,
  `amount` NUMERIC,
  `disposition` STRING,
  `dispositioned_at` TIMESTAMP,
  `analyst_id` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(alert_ts);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.fraud_platform.case_alert_link` (
  `case_id` STRING NOT NULL,
  `alert_id` STRING NOT NULL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.fraud_platform.fraud_case` (
  `case_id` STRING NOT NULL,
  `opened_at` TIMESTAMP,
  `closed_at` TIMESTAMP,
  `case_type` STRING,
  `status` STRING,
  `cif_number` STRING,
  `total_loss_amount` NUMERIC,
  `recovered_amount` NUMERIC,
  `confirmed_fraud` BOOL,
  `fraud_type` STRING,
  `assigned_analyst` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(opened_at);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.fraud_platform.model_score_realtime` (
  `score_id` STRING NOT NULL,
  `scored_at` TIMESTAMP,
  `entity_type` STRING,
  `entity_ref` STRING,
  `model_name` STRING,
  `model_version` STRING,
  `score` INT64,
  `reason_codes` ARRAY<STRING>,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(scored_at)
CLUSTER BY entity_type, model_name;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.fraud_platform.rule` (
  `rule_id` STRING NOT NULL,
  `rule_version` INT64,
  `rule_name` STRING,
  `channel` STRING,
  `active` BOOL,
  `threshold` NUMERIC,
  `created_at` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);
