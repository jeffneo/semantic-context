SELECT
  DATE_TRUNC(c.conversation_date, MONTH) AS month_start,
  s.site_name,
  COUNT(*) AS contacts,
  COUNTIF(c.is_account_closure_call) AS closure_calls,
  AVG(c.handle_sec) AS avg_handle_sec
FROM `fennmoor-dw.dw_contact_center.fct_calls` c
JOIN `fennmoor-dw.dw_contact_center.dim_cc_site` s ON s.site_id = c.site_id
WHERE c.conversation_date >= '2026-01-01'
GROUP BY ALL
