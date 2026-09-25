CREATE SCHEMA IF NOT EXISTS `fennmoor-analytics.sbx_risk` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_risk.acct_bal_legacy_recon` (
  `balance_date` DATE,
  `core_account_id` INT64,
  `legacy_balance` NUMERIC,
  `dw_balance` NUMERIC,
  `diff` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_risk.bureau_fico_migration` (
  `archive_month` DATE,
  `fico_band` STRING,
  `customers` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_risk.dlq_roll_rates_2026` (
  `month_start` DATE,
  `bucket` STRING,
  `loans` INT64,
  `past_due_amount` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-analytics.sbx_risk.kyc_review_extract` (
  `party_id` STRING NOT NULL,
  `cif_number` STRING,
  `party_type` STRING,
  `full_name` STRING,
  `tax_id` STRING,
  `country_of_citizenship` STRING,
  `pep_flag` BOOL,
  `risk_rating` STRING,
  `risk_rating_date` DATE,
  `onboarding_date` DATE,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);
