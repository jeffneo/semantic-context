CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_core` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.dim_account` (
  `account_key` INT64,
  `account_natural_key` STRING,
  `account_family` STRING,
  `core_account_id` INT64,
  `card_account_id` INT64,
  `loan_number` STRING,
  `customer_key` INT64,
  `primary_cif_number` STRING,
  `product_code` STRING,
  `product_name` STRING,
  `product_family` STRING,
  `branch_id` INT64,
  `open_date` DATE,
  `close_date` DATE,
  `close_reason` STRING,
  `status_code` STRING,
  `open_channel` STRING,
  `is_open` BOOL
)
CLUSTER BY account_key
OPTIONS (description = "All accounts. account_family = DEPOSIT, CARD or LOAN.");

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.dim_branch` (
  `branch_id` INT64,
  `branch_name` STRING,
  `branch_type` STRING,
  `city` STRING,
  `state_code` STRING,
  `zip_code` STRING,
  `region` STRING,
  `market_code` STRING,
  `msa_name` STRING,
  `cost_center_id` STRING,
  `manager_employee_id` STRING,
  `open_date` DATE,
  `close_date` DATE,
  `is_open` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.dim_card` (
  `card_token` STRING,
  `card_account_id` INT64,
  `cif_number` STRING,
  `card_role` STRING,
  `pan_last4` STRING,
  `issue_date` DATE,
  `activation_date` DATE,
  `status` STRING,
  `is_virtual` BOOL,
  `digital_wallet` STRING,
  `embossed_name` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.dim_customer` (
  `customer_key` INT64,
  `cif_number` STRING,
  `customer_type` STRING,
  `full_name` STRING,
  `birth_date` DATE,
  `tax_id_hash` STRING,
  `customer_since_date` DATE,
  `tenure_months` INT64,
  `customer_status` STRING,
  `segment` STRING,
  `preferred_branch_id` INT64,
  `preferred_language` STRING,
  `is_employee` BOOL,
  `aml_risk_rating` STRING,
  `primary_email` STRING,
  `primary_mobile` STRING,
  `email_opt_in` BOOL,
  `state_code` STRING,
  `zip_code` STRING,
  `sf_contact_id` STRING,
  `sf_household_id` STRING,
  `is_digitally_enrolled` BOOL,
  `is_deceased` BOOL
)
CLUSTER BY cif_number
OPTIONS (description = "One row per customer (CIF). See int_customer_identity for cross-system ids.");

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.dim_date` (
  `date_day` DATE,
  `month_start` DATE,
  `week_start` DATE,
  `quarter` INT64,
  `year` INT64,
  `day_of_week` STRING,
  `is_weekend` BOOL,
  `is_bank_holiday` BOOL,
  `is_business_day` BOOL,
  `fiscal_period_name` STRING
)
OPTIONS (description = "Standard date dimension.");

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.dim_merchant` (
  `merchant_id` STRING,
  `merchant_name` STRING,
  `dba_name` STRING,
  `mcc` STRING,
  `mcc_description` STRING,
  `category_group` STRING,
  `city` STRING,
  `state` STRING,
  `country` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.dim_product` (
  `product_code` STRING,
  `product_name` STRING,
  `product_family` STRING,
  `product_type` STRING,
  `monthly_fee_amount` NUMERIC,
  `interest_rate` NUMERIC,
  `term_months` INT64,
  `is_active` BOOL,
  `product_line` STRING,
  `product_group` STRING,
  `reporting_category` STRING,
  `is_fee_bearing` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.fct_account_closures` (
  `account_key` INT64,
  `customer_key` INT64,
  `cif_number` STRING,
  `account_family` STRING,
  `product_code` STRING,
  `close_date` DATE,
  `close_reason` STRING,
  `is_voluntary` BOOL,
  `tenure_days` INT64
)
PARTITION BY close_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.fct_card_transactions` (
  `settlement_id` STRING,
  `post_date` DATE,
  `card_account_id` INT64,
  `account_key` INT64,
  `customer_key` INT64,
  `cif_number` STRING,
  `card_token` STRING,
  `amount` NUMERIC,
  `txn_type` STRING,
  `is_purchase` BOOL,
  `merchant_id` STRING,
  `merchant_name` STRING,
  `mcc` STRING,
  `mcc_category_group` STRING,
  `is_foreign` BOOL,
  `interchange` NUMERIC
)
PARTITION BY post_date
CLUSTER BY customer_key, mcc
OPTIONS (description = "Settled card transactions, USD. Partitioned by post_date.");

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.fct_daily_account_balances` (
  `balance_date` DATE,
  `account_key` INT64,
  `core_account_id` INT64,
  `customer_key` INT64,
  `product_code` STRING,
  `ledger_balance` NUMERIC,
  `available_balance` NUMERIC,
  `accrued_interest` NUMERIC
)
PARTITION BY balance_date
CLUSTER BY account_key;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.fct_deposit_transactions` (
  `transaction_id` INT64,
  `posted_date` DATE,
  `core_account_id` INT64,
  `account_key` INT64,
  `customer_key` INT64,
  `transaction_type` STRING,
  `amount` NUMERIC,
  `signed_amount` NUMERIC,
  `channel` STRING,
  `branch_id` INT64,
  `is_reversal` BOOL
)
PARTITION BY posted_date
CLUSTER BY customer_key, transaction_type;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_core.fct_fees` (
  `fee_id` INT64,
  `assessed_date` DATE,
  `account_key` INT64,
  `customer_key` INT64,
  `product_code` STRING,
  `fee_type` STRING,
  `fee_amount` NUMERIC,
  `is_waived` BOOL,
  `is_reversed` BOOL,
  `net_fee` NUMERIC
)
PARTITION BY assessed_date;
