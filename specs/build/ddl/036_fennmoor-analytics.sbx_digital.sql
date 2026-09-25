CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.sbx_digital` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_digital.app_screen_paths` (
  `screen_name` STRING,
  `platform` STRING,
  `events` INT64,
  `users` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_digital.ga4_sessions_flat_test` (
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
);
