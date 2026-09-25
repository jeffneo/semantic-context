CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.workday` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.workday.compensation` (
  `worker_id` STRING NOT NULL,
  `effective_date` DATE,
  `base_pay_annual` NUMERIC,
  `bonus_target_pct` NUMERIC,
  `currency_code` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.workday.position` (
  `position_id` STRING NOT NULL,
  `worker_id` STRING,
  `job_profile` STRING,
  `effective_date` DATE,
  `fte` NUMERIC,
  `scheduled_hours` NUMERIC,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.workday.worker` (
  `worker_id` STRING NOT NULL,
  `legal_name` STRING,
  `preferred_name` STRING,
  `work_email` STRING,
  `hire_date` DATE,
  `termination_date` DATE,
  `job_profile` STRING,
  `job_family` STRING,
  `management_level` STRING,
  `cost_center_id` STRING,
  `location` STRING,
  `supervisor_worker_id` STRING,
  `worker_status` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);
