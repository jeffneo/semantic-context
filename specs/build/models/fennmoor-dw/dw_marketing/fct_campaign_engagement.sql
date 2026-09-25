SELECT
  e.campaign_id,
  e.dispatch_id,
  e.external_user_id AS cif_number,
  MIN(DATE(e.event_time, 'America/Chicago')) AS event_date,
  LOGICAL_OR(e.event_type = 'delivery') AS delivered,
  LOGICAL_OR(e.event_type = 'open') AS opened,
  LOGICAL_OR(e.event_type = 'click') AS clicked,
  LOGICAL_OR(e.event_type = 'unsubscribe') AS unsubscribed,
  LOGICAL_OR(e.event_type = 'bounce') AS bounced
FROM `fennmoor-dw.dw_staging.stg_braze__email_event` e
GROUP BY ALL
