SELECT
  DATE_TRUNC(c.conversation_date, MONTH) AS month_start,
  c.site_id,
  COUNT(*) AS contacts,
  COUNTIF(c.is_account_closure_call) AS closure_calls,
  COUNT(DISTINCT c.customer_key) AS unique_callers,
  AVG(c.handle_sec) AS avg_handle_sec
FROM `fennmoor-dw.dw_contact_center.fct_calls` c
GROUP BY ALL
