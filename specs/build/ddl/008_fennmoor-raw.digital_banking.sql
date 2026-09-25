CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.digital_banking` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.digital_banking.alert_subscription` (
  `olb_user_id` STRING NOT NULL,
  `alert_type` STRING,
  `channel` STRING,
  `threshold_amount` NUMERIC,
  `enabled` BOOL,
  `updated_at` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.digital_banking.bill_pay` (
  `payment_id` STRING NOT NULL,
  `olb_user_id` STRING,
  `from_account_id` INT64,
  `payee_id` STRING,
  `payee_name` STRING,
  `amount` NUMERIC,
  `scheduled_date` DATE,
  `sent_date` DATE,
  `status` STRING,
  `is_recurring` BOOL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY sent_date;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.digital_banking.device` (
  `device_id` STRING NOT NULL,
  `olb_user_id` STRING,
  `platform` STRING,
  `model` STRING,
  `os_version` STRING,
  `registered_at` TIMESTAMP,
  `last_seen_at` TIMESTAMP,
  `trusted` BOOL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.digital_banking.login_event` (
  `login_event_id` STRING NOT NULL,
  `olb_user_id` STRING,
  `session_id` STRING,
  `event_ts` TIMESTAMP,
  `channel` STRING,
  `result` STRING,
  `ip_address` STRING,
  `device_id` STRING,
  `geo_country` STRING,
  `user_agent` STRING,
  `risk_score` INT64,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(event_ts)
CLUSTER BY olb_user_id;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.digital_banking.mobile_deposit` (
  `deposit_id` STRING NOT NULL,
  `olb_user_id` STRING,
  `account_id` INT64,
  `amount` NUMERIC,
  `check_number` STRING,
  `submitted_at` TIMESTAMP,
  `status` STRING,
  `hold_until_date` DATE,
  `reject_reason` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(submitted_at);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.digital_banking.online_user` (
  `olb_user_id` STRING NOT NULL,
  `cif_number` STRING NOT NULL,
  `ga4_user_id` STRING,
  `username` STRING,
  `enrolled_at` TIMESTAMP,
  `enrollment_channel` STRING,
  `status` STRING,
  `mfa_method` STRING,
  `last_login_at` TIMESTAMP,
  `is_business` BOOL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.digital_banking.p2p_transfer` (
  `transfer_id` STRING NOT NULL,
  `olb_user_id` STRING,
  `from_account_id` INT64,
  `direction` STRING,
  `counterparty_token` STRING,
  `counterparty_name` STRING,
  `amount` NUMERIC,
  `initiated_at` TIMESTAMP,
  `status` STRING,
  `fraud_hold` BOOL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(initiated_at);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.digital_banking.secure_message` (
  `message_id` STRING,
  `olb_user_id` STRING,
  `thread_id` STRING,
  `direction` STRING,
  `subject` STRING,
  `body` STRING,
  `sent_at` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);
