SELECT
  e.event_date,
  c.segment,
  COUNT(DISTINCT e.ga_session_id) AS sessions
FROM `fennmoor-dw.dw_staging.stg_ga4__events` e
JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.cif_number = e.user_id
GROUP BY ALL
