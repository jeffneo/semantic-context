WITH d AS (
SELECT x.application_id, x.outcome, x.approved_amount, x.approved_apr
FROM `fennmoor-dw.dw_staging.stg_los__decision` x
QUALIFY ROW_NUMBER() OVER (PARTITION BY x.application_id ORDER BY x.decision_seq DESC) = 1
)
SELECT
  a.application_id,
  DATE(a.submitted_at, 'America/Chicago') AS submitted_date,
  c.customer_key,
  a.applicant_cif_number,
  a.product_code,
  a.channel,
  a.requested_amount,
  d.outcome AS final_outcome,
  d.approved_amount,
  d.approved_apr,
  a.credit_score_at_app,
  a.branch_number AS branch_id,
  a.offer_code
FROM `fennmoor-dw.dw_staging.stg_los__application` a
LEFT JOIN d ON d.application_id = a.application_id
LEFT JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.cif_number = a.applicant_cif_number
