SELECT
  src.hit_id,
  src.party_id,
  src.list_name,
  src.match_score,
  src.matched_name,
  src.status,
  src.reviewed_at,
  src.reviewer_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.screening_hit` AS src
WHERE NOT src._fivetran_deleted
