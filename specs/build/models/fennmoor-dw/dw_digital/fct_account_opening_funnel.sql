SELECT
  s.session_date,
  s.traffic_medium,
  s.campaign_name,
  s.device_category,
  COUNT(*) AS sessions,
  COUNTIF(s.started_application) AS started,
  COUNTIF(s.submitted_application) AS submitted,
  SAFE_DIVIDE(COUNTIF(s.submitted_application), COUNTIF(s.started_application)) AS conversion_rate
FROM `fennmoor-dw.dw_digital.fct_web_sessions` s
GROUP BY ALL
