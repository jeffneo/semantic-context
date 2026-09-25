SELECT
  src.review_id,
  src.party_id,
  src.review_type,
  src.started_at,
  src.completed_at,
  src.outcome,
  src.reviewer_id,
  src.next_review_due,
  src.edd_required,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.kyc_review` AS src
WHERE NOT src._fivetran_deleted
