SELECT
  src.sar_id,
  src.party_id,
  src.alert_ids,
  src.filing_date,
  src.activity_start,
  src.activity_end,
  src.amount_involved,
  src.narrative,
  src.bsa_id,
  src.status,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.sar_filing` AS src
WHERE NOT src._fivetran_deleted
