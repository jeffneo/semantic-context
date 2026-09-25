SELECT
  CONCAT(CAST(e.amplitude_id AS STRING), '-', CAST(e.session_id AS STRING)) AS app_session_key,
  MIN(e.event_date) AS session_date,
  ANY_VALUE(e.user_id) AS olb_user_id,
  ANY_VALUE(u.cif_number) AS cif_number,
  COUNT(*) AS events,
  COUNT(DISTINCT e.screen_name) AS screens,
  ANY_VALUE(e.platform) AS platform,
  ANY_VALUE(e.version_name) AS app_version
FROM `fennmoor-dw.dw_staging.stg_amp__events` e
LEFT JOIN `fennmoor-dw.dw_staging.stg_olb__online_user` u ON u.olb_user_id = e.user_id
WHERE e.session_id > 0
GROUP BY ALL
