SELECT
  s.*
FROM `fennmoor-dw.dw_contact_center.fct_calls` AS s
WHERE s.wrapup_code_name IN ('ACCT_MAINT', 'ACCT_CLOSE') AND s.conversation_date BETWEEN '2026-04-01' AND '2026-06-30'
