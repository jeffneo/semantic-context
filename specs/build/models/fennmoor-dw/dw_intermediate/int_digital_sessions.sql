SELECT
  CONCAT(e.user_pseudo_id, '-', CAST(e.ga_session_id AS STRING)) AS session_key,
  e.user_pseudo_id,
  MAX(e.user_id) AS ga4_user_id,
  MIN(e.event_date) AS session_date,
  MIN(e.event_ts) AS session_start,
  MAX(e.event_ts) AS session_end,
  COUNTIF(e.event_name = 'page_view') AS page_views,
  SUM(e.engagement_time_msec) / 1000 AS engaged_sec,
  ARRAY_AGG(e.page_location IGNORE NULLS ORDER BY e.event_ts LIMIT 1)[SAFE_OFFSET(0)] AS landing_page,
  ANY_VALUE(e.traffic_medium) AS traffic_medium,
  ANY_VALUE(e.campaign_name) AS campaign_name,
  ANY_VALUE(e.device_category) AS device_category,
  LOGICAL_OR(e.application_step = 'start') AS started_application,
  LOGICAL_OR(e.application_step = 'submit') AS submitted_application,
  LOGICAL_OR(STRPOS(e.page_location, '/help') > 0 OR STRPOS(e.page_location, '/contact') > 0) AS visited_help
FROM `fennmoor-dw.dw_staging.stg_ga4__events` e
WHERE e.ga_session_id IS NOT NULL
GROUP BY ALL
