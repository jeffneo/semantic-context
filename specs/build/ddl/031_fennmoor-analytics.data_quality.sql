CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.data_quality` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.data_quality.dbt_run_results` (
  `invocation_id` STRING,
  `model_unique_id` STRING,
  `status` STRING,
  `execution_time_sec` FLOAT64,
  `rows_affected` INT64,
  `generated_at` TIMESTAMP
)
PARTITION BY DATE(generated_at);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.data_quality.elementary_test_results` (
  `test_result_id` STRING,
  `test_name` STRING,
  `model_fqn` STRING,
  `column_name` STRING,
  `status` STRING,
  `failures` INT64,
  `severity` STRING,
  `detected_at` TIMESTAMP
)
PARTITION BY DATE(detected_at);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.data_quality.freshness_checks` (
  `table_fqn` STRING,
  `max_loaded_at` TIMESTAMP,
  `checked_at` TIMESTAMP,
  `status` STRING,
  `lag_minutes` INT64
)
PARTITION BY DATE(checked_at);
