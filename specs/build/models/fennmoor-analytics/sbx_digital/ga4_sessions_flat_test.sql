SELECT
  s.*
FROM `fennmoor-dw.dw_digital.fct_web_sessions` AS s
WHERE s.session_date >= '2026-02-01'
