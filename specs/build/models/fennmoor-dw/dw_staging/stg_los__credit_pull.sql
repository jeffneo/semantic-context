SELECT
  src.pullId AS pull_id,
  src.applicationId AS application_id,
  src.bureau,
  src.pulledAt AS pulled_at,
  src.ficoScore AS fico_score,
  src.totalDebt AS total_debt,
  src.dtiRatio AS dti_ratio,
  src.inquiriesLast6m AS inquiries_last6m,
  src.tradelinesOpen AS tradelines_open,
  src.derogatoryCount AS derogatory_count,
  src.rawReportUri AS raw_report_uri,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.credit_pull` AS src
WHERE NOT src._fivetran_deleted
