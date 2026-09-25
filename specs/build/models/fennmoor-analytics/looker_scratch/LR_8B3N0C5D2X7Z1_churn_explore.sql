SELECT
  s.score_date,
  s.customer_key,
  c.segment,
  c.state_code,
  s.churn_score
FROM `fennmoor-dw.ml_scores.churn_score_v2` s
JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.customer_key = s.customer_key
