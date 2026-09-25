SELECT
  cv.conversion_id,
  cv.event_time AS conversion_at,
  cv.external_user_id AS cif_number,
  s.customer_key,
  cv.campaign_id,
  cv.conversion_behavior,
  s.message_send_id AS attributed_send_id,
  TIMESTAMP_DIFF(cv.event_time, s.sent_at, HOUR) AS hours_since_send
FROM `fennmoor-dw.dw_staging.stg_braze__conversion` cv
JOIN `fennmoor-dw.dw_marketing.fct_campaign_sends` s
  ON s.cif_number = cv.external_user_id AND s.campaign_id = cv.campaign_id AND s.sent_at <= cv.event_time
QUALIFY ROW_NUMBER() OVER (PARTITION BY cv.conversion_id ORDER BY s.sent_at DESC) = 1
