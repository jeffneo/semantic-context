SELECT
  DATE_TRUNC(DATE(c.CALL_START_DTTM), MONTH) AS month_start,
  c.SITE_CD AS site_id,
  COUNT(*) AS calls,
  COUNTIF(c.ABANDON_FLG = 'N') AS handled,
  AVG(c.TALK_SEC) AS avg_talk_sec
FROM `fennmoor-raw.contact_center_legacy.cdr_*` c
GROUP BY ALL
