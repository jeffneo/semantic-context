SELECT
  src.ARCHIVE_DT AS archive_date,
  src.CIF AS cif_number,
  src.SSN_HASH AS ssn_hash,
  src.FICO_08 AS fico_08,
  src.VANTAGE_4 AS vantage_4,
  src.TOT_REV_BAL AS total_revolving_balance,
  src.TOT_REV_LMT AS total_revolving_limit,
  src.UTIL_PCT AS utilization_pct,
  src.NUM_TRD_OPEN AS num_trades_open,
  src.NUM_INQ_6M AS num_inquiries_6m,
  src.NUM_DLQ_30_24M AS num_delinquent_30_24m,
  src.BK_FLG = 'Y' AS is_bankruptcy,
  src.MOS_SINCE_DLQ AS months_since_delinquent,
  src.EST_INCOME AS estimated_income,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.credit_bureau.consumer_attributes_monthly` AS src
