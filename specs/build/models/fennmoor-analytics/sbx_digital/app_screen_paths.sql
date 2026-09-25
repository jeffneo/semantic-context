SELECT
  e.screen_name,
  e.platform,
  COUNT(*) AS events,
  COUNT(DISTINCT e.user_id) AS users
FROM `fennmoor-dw.dw_staging.stg_amp__events` e
WHERE e.screen_name IS NOT NULL
GROUP BY ALL
