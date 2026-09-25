SELECT
  src.rate_date,
  src.from_ccy,
  src.to_ccy,
  src.rate,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.fx_rate_daily` AS src
