CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_compliance` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_compliance.dim_aml_party` (
  `party_id` STRING,
  `cif_number` STRING,
  `customer_key` INT64,
  `party_type` STRING,
  `risk_rating` STRING,
  `pep_flag` BOOL,
  `onboarding_date` DATE,
  `tax_id_hash` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_compliance.fct_aml_alerts` (
  `alert_id` STRING,
  `alert_date` DATE,
  `party_id` STRING,
  `customer_key` INT64,
  `scenario_code` STRING,
  `total_amount` NUMERIC,
  `status` STRING,
  `escalated_to_case` BOOL
)
PARTITION BY alert_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_compliance.fct_kyc_reviews` (
  `review_id` STRING,
  `party_id` STRING,
  `review_type` STRING,
  `completed_date` DATE,
  `outcome` STRING,
  `edd_required` BOOL,
  `days_to_complete` INT64,
  `is_overdue` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_compliance.fct_sar_filings` (
  `sar_id` STRING,
  `party_id` STRING,
  `filing_date` DATE,
  `amount_involved` NUMERIC,
  `status` STRING,
  `alert_count` INT64
);
