SELECT
  src.applicationId AS application_id,
  src.decisionSeq AS decision_seq,
  src.decidedBy AS decided_by,
  src.outcome,
  src.approvedAmount AS approved_amount,
  src.approvedApr AS approved_apr,
  src.conditions,
  src.decidedAt AS decided_at,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.decision` AS src
WHERE NOT src._fivetran_deleted
