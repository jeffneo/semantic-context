CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.aml_kyc` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.aml_kyc.ctr_filing` (
  `ctr_id` STRING NOT NULL,
  `party_id` STRING,
  `txn_date` DATE,
  `cash_in_amount` NUMERIC,
  `cash_out_amount` NUMERIC,
  `filing_date` DATE,
  `branch_id` INT64,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.aml_kyc.kyc_review` (
  `review_id` STRING NOT NULL,
  `party_id` STRING,
  `review_type` STRING,
  `started_at` TIMESTAMP,
  `completed_at` TIMESTAMP,
  `outcome` STRING,
  `reviewer_id` STRING,
  `next_review_due` DATE,
  `edd_required` BOOL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.aml_kyc.party` (
  `party_id` STRING NOT NULL,
  `cif_number` STRING,
  `party_type` STRING,
  `full_name` STRING,
  `dob` DATE,
  `tax_id` STRING,
  `country_of_citizenship` STRING,
  `pep_flag` BOOL,
  `risk_rating` STRING,
  `risk_rating_date` DATE,
  `onboarding_date` DATE,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.aml_kyc.sar_filing` (
  `sar_id` STRING NOT NULL,
  `party_id` STRING,
  `alert_ids` ARRAY<STRING>,
  `filing_date` DATE,
  `activity_start` DATE,
  `activity_end` DATE,
  `amount_involved` NUMERIC,
  `narrative` STRING,
  `bsa_id` STRING,
  `status` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.aml_kyc.screening_hit` (
  `hit_id` STRING NOT NULL,
  `party_id` STRING,
  `list_name` STRING,
  `match_score` NUMERIC,
  `matched_name` STRING,
  `status` STRING,
  `reviewed_at` TIMESTAMP,
  `reviewer_id` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.aml_kyc.transaction_alert` (
  `alert_id` STRING NOT NULL,
  `party_id` STRING,
  `scenario_code` STRING,
  `alert_date` DATE,
  `total_amount` NUMERIC,
  `status` STRING,
  `assigned_to` STRING,
  `closed_date` DATE,
  `escalated_to_case` BOOL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY alert_date;
