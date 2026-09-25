SELECT
  l.olb_user_id,
  l.event_date,
  COUNTIF(NOT l.is_success) AS failed_logins,
  COUNT(DISTINCT l.device_id) AS distinct_devices,
  COUNT(DISTINCT l.geo_country) AS distinct_countries
FROM `fennmoor-dw.dw_digital.fct_digital_logins` l
GROUP BY ALL
