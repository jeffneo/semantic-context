SELECT
  src.ctr_id,
  src.party_id,
  src.txn_date,
  src.cash_in_amount,
  src.cash_out_amount,
  src.filing_date,
  src.branch_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.ctr_filing` AS src
WHERE NOT src._fivetran_deleted
