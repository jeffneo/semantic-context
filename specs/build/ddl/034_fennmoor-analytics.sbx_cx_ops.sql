CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.sbx_cx_ops` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_cx_ops.cc_closure_calls_apr_may` (
  `conversation_id` STRING,
  `conversation_date` DATE,
  `conversation_start` TIMESTAMP,
  `media_type` STRING,
  `direction` STRING,
  `customer_key` INT64,
  `cif_number` STRING,
  `queue_id` STRING,
  `queue_name` STRING,
  `queue_site_id` STRING,
  `agent_user_id` STRING,
  `agent_site_id` STRING,
  `site_id` STRING,
  `ivr_auth_result` STRING,
  `ivr_intent` STRING,
  `wrapup_code_name` STRING,
  `is_account_closure_call` BOOL,
  `talk_sec` INT64,
  `hold_sec` INT64,
  `acw_sec` INT64,
  `handle_sec` INT64,
  `was_transferred` BOOL,
  `is_abandoned` BOOL,
  `is_authenticated` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_cx_ops.cc_site_scorecard_2026` (
  `month_start` DATE,
  `site_name` STRING,
  `contacts` INT64,
  `closure_calls` INT64,
  `avg_handle_sec` FLOAT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_cx_ops.cdr_history_rollup` (
  `month_start` DATE,
  `site_id` STRING,
  `calls` INT64,
  `handled` INT64,
  `avg_talk_sec` FLOAT64
);
