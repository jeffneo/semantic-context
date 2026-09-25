SELECT
  r.review_id,
  r.party_id,
  r.review_type,
  DATE(r.completed_at) AS completed_date,
  r.outcome,
  r.edd_required,
  TIMESTAMP_DIFF(r.completed_at, r.started_at, DAY) AS days_to_complete,
  r.next_review_due < CURRENT_DATE() AS is_overdue
FROM `fennmoor-dw.dw_staging_restricted.stg_aml__kyc_review` r
