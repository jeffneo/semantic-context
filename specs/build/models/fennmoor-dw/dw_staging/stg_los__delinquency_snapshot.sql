SELECT
  src.snapshotDate AS snapshot_date,
  src.loanNumber AS loan_number,
  src.dpd,
  src.bucket,
  src.pastDueAmount AS past_due_amount,
  src.collectorId AS collector_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.delinquency_snapshot` AS src
WHERE NOT src._fivetran_deleted
