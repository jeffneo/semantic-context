CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.credit_bureau` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.credit_bureau.consumer_attributes_2019_archive` (
  `ARCHIVE_DT` DATE,
  `CIF` STRING,
  `FICO_08` INT64,
  `TOT_REV_BAL` NUMERIC,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.credit_bureau.consumer_attributes_monthly` (
  `ARCHIVE_DT` DATE NOT NULL,
  `CIF` STRING NOT NULL,
  `SSN_HASH` STRING,
  `FICO_08` INT64,
  `VANTAGE_4` INT64,
  `TOT_REV_BAL` NUMERIC,
  `TOT_REV_LMT` NUMERIC,
  `UTIL_PCT` NUMERIC,
  `NUM_TRD_OPEN` INT64,
  `NUM_INQ_6M` INT64,
  `NUM_DLQ_30_24M` INT64,
  `BK_FLG` STRING,
  `MOS_SINCE_DLQ` INT64,
  `EST_INCOME` NUMERIC,
  `_source_file` STRING,
  `_source_file_date` DATE,
  `_load_ts` TIMESTAMP
)
PARTITION BY ARCHIVE_DT
CLUSTER BY CIF;
