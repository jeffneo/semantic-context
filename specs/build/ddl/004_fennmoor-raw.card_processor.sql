CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.card_processor` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.authorization` (
  `auth_id` STRING NOT NULL,
  `card_token` STRING,
  `account_id` INT64,
  `auth_ts` TIMESTAMP,
  `amount_cents` INT64,
  `currency_code` STRING,
  `merchant_id` STRING,
  `mcc` STRING,
  `pos_entry_mode` STRING,
  `channel` STRING,
  `response_code` STRING,
  `decline_reason` STRING,
  `vendor_fraud_score` INT64,
  `avs_result` STRING,
  `cvv_result` STRING,
  `is_recurring` BOOL,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
)
PARTITION BY DATE(auth_ts)
CLUSTER BY account_id, mcc;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.card` (
  `card_token` STRING NOT NULL,
  `account_id` INT64 NOT NULL,
  `card_role` STRING,
  `pan_last4` STRING,
  `expiry_yyyymm` STRING,
  `issue_date` DATE,
  `activation_date` DATE,
  `status` STRING,
  `replacement_reason` STRING,
  `embossed_name` STRING,
  `is_virtual` BOOL,
  `digital_wallet` STRING,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.card_account` (
  `account_id` INT64 NOT NULL,
  `bank_customer_ref` STRING NOT NULL,
  `product_code` STRING,
  `credit_limit_cents` INT64,
  `cash_limit_cents` INT64,
  `current_balance_cents` INT64,
  `statement_balance_cents` INT64,
  `min_payment_due_cents` INT64,
  `apr_purchase_bps` INT64,
  `apr_cash_bps` INT64,
  `open_date` DATE,
  `close_date` DATE,
  `status` STRING,
  `close_reason` STRING,
  `cycle_day` INT64,
  `autopay_flag` BOOL,
  `delinquency_bucket` STRING,
  `last_payment_date` DATE,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
)
CLUSTER BY account_id;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.card_account_hist_2019` (
  `account_id` INT64,
  `snapshot_month` DATE,
  `credit_limit_cents` INT64,
  `current_balance_cents` INT64,
  `status` STRING,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.card_status_change` (
  `card_token` STRING,
  `account_id` INT64,
  `change_ts` TIMESTAMP,
  `old_status` STRING,
  `new_status` STRING,
  `reason` STRING,
  `channel` STRING,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
)
PARTITION BY DATE(change_ts);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.dispute` (
  `dispute_id` STRING NOT NULL,
  `settlement_id` STRING,
  `account_id` INT64,
  `opened_date` DATE,
  `reason_code` STRING,
  `dispute_amount_cents` INT64,
  `status` STRING,
  `resolution` STRING,
  `resolved_date` DATE,
  `chargeback_flag` BOOL,
  `provisional_credit_cents` INT64,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
)
PARTITION BY opened_date;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.mcc_code` (
  `mcc` STRING NOT NULL,
  `description` STRING,
  `category_group` STRING,
  `irs_reportable` BOOL,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.merchant` (
  `merchant_id` STRING NOT NULL,
  `merchant_name` STRING,
  `dba_name` STRING,
  `mcc` STRING,
  `city` STRING,
  `state` STRING,
  `country` STRING,
  `postal_code` STRING,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.rewards_ledger` (
  `account_id` INT64,
  `activity_date` DATE,
  `points` INT64,
  `activity_type` STRING,
  `settlement_id` STRING,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
)
PARTITION BY activity_date;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.settlement` (
  `settlement_id` STRING NOT NULL,
  `auth_id` STRING,
  `card_token` STRING,
  `account_id` INT64 NOT NULL,
  `post_date` DATE NOT NULL,
  `txn_date` DATE,
  `amount_cents` INT64,
  `txn_type` STRING,
  `merchant_id` STRING,
  `mcc` STRING,
  `merchant_name_raw` STRING,
  `merchant_city` STRING,
  `merchant_state` STRING,
  `merchant_country` STRING,
  `network` STRING,
  `interchange_cents` INT64,
  `reward_points` INT64,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
)
PARTITION BY post_date
CLUSTER BY account_id, mcc;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.card_processor.statement` (
  `account_id` INT64 NOT NULL,
  `statement_date` DATE,
  `closing_balance_cents` INT64,
  `min_due_cents` INT64,
  `due_date` DATE,
  `interest_charged_cents` INT64,
  `fees_charged_cents` INT64,
  `purchases_cents` INT64,
  `payments_cents` INT64,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
)
PARTITION BY statement_date
CLUSTER BY account_id;
