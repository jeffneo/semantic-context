SELECT
  s.score_date,
  s.customer_key,
  s.churn_score,
  c.close_date,
  DATE_DIFF(c.close_date, s.score_date, DAY) AS days_to_close
FROM `fennmoor-dw.ml_scores.churn_score_v2` s
JOIN `fennmoor-dw.dw_core.fct_account_closures` c ON c.customer_key = s.customer_key
WHERE s.score_date BETWEEN '2026-01-01' AND '2026-03-31'
