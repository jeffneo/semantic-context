CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_intermediate` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_intermediate.int_account_closures` (
  `account_natural_key` STRING,
  `account_family` STRING,
  `cif_number` STRING,
  `product_code` STRING,
  `close_date` DATE,
  `close_reason` STRING,
  `is_voluntary` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_intermediate.int_account_holders` (
  `account_id` INT64,
  `cif_number` STRING,
  `relationship_type_code` STRING,
  `is_primary_holder` BOOL,
  `relationship_effective_date` DATE
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_intermediate.int_accounts_unioned` (
  `account_natural_key` STRING,
  `account_family` STRING,
  `core_account_id` INT64,
  `card_account_id` INT64,
  `loan_number` STRING,
  `primary_cif_number` STRING,
  `product_code` STRING,
  `branch_id` INT64,
  `open_date` DATE,
  `close_date` DATE,
  `close_reason` STRING,
  `status_code` STRING,
  `open_channel` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_intermediate.int_calls_enriched` (
  `conversation_id` STRING,
  `conversation_start` TIMESTAMP,
  `conversation_date` DATE,
  `media_type` STRING,
  `direction` STRING,
  `cif_number` STRING,
  `ivr_auth_result` STRING,
  `ivr_intent` STRING,
  `queue_id` STRING,
  `queue_name` STRING,
  `queue_site_id` STRING,
  `agent_user_id` STRING,
  `agent_legs` INT64,
  `talk_sec` INT64,
  `hold_sec` INT64,
  `acw_sec` INT64,
  `wrapup_code_name` STRING,
  `is_account_closure_call` BOOL,
  `was_transferred` BOOL,
  `is_abandoned` BOOL
)
PARTITION BY conversation_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_intermediate.int_calls_legacy_cdr` (
  `legacy_call_id` STRING,
  `conversation_start` TIMESTAMP,
  `conversation_date` DATE,
  `site_id` STRING,
  `cif_number` STRING,
  `agent_login_id` STRING,
  `talk_sec` INT64,
  `hold_sec` INT64,
  `acw_sec` INT64,
  `disposition_code` STRING,
  `is_abandoned` BOOL,
  `was_transferred` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_intermediate.int_card_transactions_enriched` (
  `settlement_id` STRING,
  `post_date` DATE,
  `card_account_id` INT64,
  `cif_number` STRING,
  `card_token` STRING,
  `amount` NUMERIC,
  `txn_type` STRING,
  `is_purchase` BOOL,
  `merchant_id` STRING,
  `merchant_name` STRING,
  `mcc` STRING,
  `mcc_category_group` STRING,
  `merchant_state` STRING,
  `is_foreign` BOOL,
  `interchange` NUMERIC
)
PARTITION BY post_date
CLUSTER BY card_account_id, mcc;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_intermediate.int_customer_contact_points` (
  `cif_number` STRING,
  `primary_email` STRING,
  `primary_mobile` STRING,
  `has_verified_email` BOOL,
  `email_opt_in` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_intermediate.int_customer_identity` (
  `cif_number` STRING,
  `customer_key` INT64,
  `sf_contact_id` STRING,
  `sf_household_id` STRING,
  `sf_contact_count` INT64,
  `olb_user_ids` ARRAY<STRING>,
  `ga4_user_ids` ARRAY<STRING>,
  `first_enrolled_at` TIMESTAMP,
  `braze_id` STRING,
  `is_digitally_enrolled` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_intermediate.int_digital_sessions` (
  `session_key` STRING,
  `user_pseudo_id` STRING,
  `ga4_user_id` STRING,
  `session_date` DATE,
  `session_start` TIMESTAMP,
  `session_end` TIMESTAMP,
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
PARTITION BY session_date;
