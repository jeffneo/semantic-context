SELECT
  c.agent_user_id,
  c.conversation_date,
  ANY_VALUE(c.agent_site_id) AS site_id,
  COUNT(*) AS contacts,
  SUM(c.handle_sec) AS handle_sec,
  AVG(c.handle_sec) AS avg_handle_sec,
  COUNTIF(c.is_account_closure_call) AS closure_calls,
  COUNTIF(c.was_transferred) AS transfers
FROM `fennmoor-dw.dw_contact_center.fct_calls` c
WHERE c.agent_user_id IS NOT NULL
GROUP BY ALL
