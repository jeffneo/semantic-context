SELECT
  s.sar_id,
  s.party_id,
  s.filing_date,
  s.amount_involved,
  s.status,
  ARRAY_LENGTH(s.alert_ids) AS alert_count
FROM `fennmoor-dw.dw_staging_restricted.stg_aml__sar_filing` s
