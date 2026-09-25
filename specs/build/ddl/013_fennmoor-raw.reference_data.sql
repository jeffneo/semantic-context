CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.reference_data` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.reference_data.contact_center_site` (
  `site_id` STRING NOT NULL,
  `site_name` STRING,
  `city` STRING,
  `state` STRING,
  `country` STRING,
  `operator` STRING,
  `is_outsourced` BOOL,
  `cost_center_id` STRING,
  `seat_count` INT64,
  `go_live_date` DATE,
  `genesys_queue_prefix` STRING,
  `_uploaded_at` TIMESTAMP,
  `_uploaded_by` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.reference_data.fx_rate_daily` (
  `rate_date` DATE NOT NULL,
  `from_ccy` STRING,
  `to_ccy` STRING,
  `rate` NUMERIC,
  `_uploaded_at` TIMESTAMP,
  `_uploaded_by` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.reference_data.holiday_calendar` (
  `holiday_date` DATE NOT NULL,
  `holiday_name` STRING,
  `is_bank_holiday` BOOL,
  `fed_closed` BOOL,
  `_uploaded_at` TIMESTAMP,
  `_uploaded_by` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.reference_data.product_hierarchy_FINAL_v3` (
  `prod_cd` STRING NOT NULL,
  `product_line` STRING,
  `product_group` STRING,
  `reporting_category` STRING,
  `fee_bearing` STRING,
  `_uploaded_at` TIMESTAMP,
  `_uploaded_by` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.reference_data.zip_region_map` (
  `zip` STRING NOT NULL,
  `state` STRING,
  `msa_name` STRING,
  `fennmoor_region` STRING,
  `market_cd` STRING,
  `_uploaded_at` TIMESTAMP,
  `_uploaded_by` STRING
);
