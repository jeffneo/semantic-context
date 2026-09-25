CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_digital` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_digital.fct_account_opening_funnel` (
  `session_date` DATE,
  `traffic_medium` STRING,
  `campaign_name` STRING,
  `device_category` STRING,
  `sessions` INT64,
  `started` INT64,
  `submitted` INT64,
  `conversion_rate` FLOAT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_digital.fct_app_sessions` (
  `app_session_key` STRING,
  `session_date` DATE,
  `olb_user_id` STRING,
  `cif_number` STRING,
  `events` INT64,
  `screens` INT64,
  `platform` STRING,
  `app_version` STRING
)
PARTITION BY session_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_digital.fct_digital_logins` (
  `login_event_id` STRING,
  `event_date` DATE,
  `event_ts` TIMESTAMP,
  `olb_user_id` STRING,
  `cif_number` STRING,
  `channel` STRING,
  `result` STRING,
  `is_success` BOOL,
  `risk_score` INT64,
  `device_id` STRING,
  `geo_country` STRING
)
PARTITION BY event_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_digital.fct_p2p_transfers` (
  `transfer_id` STRING,
  `initiated_date` DATE,
  `olb_user_id` STRING,
  `cif_number` STRING,
  `core_account_id` INT64,
  `direction` STRING,
  `amount` NUMERIC,
  `status` STRING,
  `fraud_hold` BOOL
)
PARTITION BY initiated_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_digital.fct_web_sessions` (
  `session_key` STRING,
  `session_date` DATE,
  `session_start` TIMESTAMP,
  `user_pseudo_id` STRING,
  `ga4_user_id` STRING,
  `olb_user_id` STRING,
  `customer_key` INT64,
  `is_logged_in` BOOL,
  `page_views` INT64,
  `engaged_sec` FLOAT64,
  `landing_page` STRING,
  `traffic_medium` STRING,
  `campaign_name` STRING,
  `device_category` STRING,
  `started_application` BOOL,
  `submitted_application` BOOL,
  `visited_help` BOOL
)
PARTITION BY session_date
CLUSTER BY customer_key;
