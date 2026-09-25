WITH agent_leg AS (
SELECT p.conversation_id,
       ARRAY_AGG(p.user_id IGNORE NULLS ORDER BY p.start_time LIMIT 1)[SAFE_OFFSET(0)] AS first_agent_user_id,
       ARRAY_AGG(p.queue_id IGNORE NULLS ORDER BY p.start_time LIMIT 1)[SAFE_OFFSET(0)] AS first_queue_id,
       COUNTIF(p.purpose = 'agent') AS agent_legs
FROM `fennmoor-dw.dw_staging.stg_genesys__participant` p
GROUP BY p.conversation_id
),
cust_leg AS (
SELECT p.conversation_id, ANY_VALUE(p.cif_number) AS cif_number,
       ANY_VALUE(p.ivr_auth_result) AS ivr_auth_result, ANY_VALUE(p.intent) AS ivr_intent
FROM `fennmoor-dw.dw_staging.stg_genesys__participant` p
WHERE p.purpose = 'customer'
GROUP BY p.conversation_id
),
segs AS (
SELECT s.conversation_id,
       SUM(IF(s.segment_type = 'interact', TIMESTAMP_DIFF(s.segment_end, s.segment_start, SECOND), 0)) AS talk_sec,
       SUM(IF(s.segment_type = 'hold', TIMESTAMP_DIFF(s.segment_end, s.segment_start, SECOND), 0)) AS hold_sec,
       SUM(IF(s.segment_type = 'wrapup', TIMESTAMP_DIFF(s.segment_end, s.segment_start, SECOND), 0)) AS acw_sec,
       ARRAY_AGG(s.wrap_up_code IGNORE NULLS ORDER BY s.segment_end DESC LIMIT 1)[SAFE_OFFSET(0)] AS final_wrapup_code_id,
       LOGICAL_OR(s.disconnect_type = 'transfer') AS was_transferred
FROM `fennmoor-dw.dw_staging.stg_genesys__segment` s
GROUP BY s.conversation_id
)
SELECT
  c.conversation_id,
  c.conversation_start,
  DATE(c.conversation_start, 'America/Chicago') AS conversation_date,
  c.media_type,
  c.originating_direction AS direction,
  cu.cif_number,
  cu.ivr_auth_result,
  cu.ivr_intent,
  a.first_queue_id AS queue_id,
  q.name AS queue_name,
  site.site_id AS queue_site_id,
  a.first_agent_user_id AS agent_user_id,
  a.agent_legs,
  sg.talk_sec,
  sg.hold_sec,
  sg.acw_sec,
  w.name AS wrapup_code_name,
  w.name = 'ACCT_CLOSE' OR (w.name = 'ACCT_MAINT' AND cu.ivr_intent = 'CLOSE_ACCOUNT') AS is_account_closure_call,
  sg.was_transferred,
  c.media_type = 'voice' AND COALESCE(a.agent_legs, 0) = 0 AS is_abandoned
FROM `fennmoor-dw.dw_staging.stg_genesys__conversation` c
LEFT JOIN agent_leg a ON a.conversation_id = c.conversation_id
LEFT JOIN cust_leg cu ON cu.conversation_id = c.conversation_id
LEFT JOIN segs sg ON sg.conversation_id = c.conversation_id
LEFT JOIN `fennmoor-dw.dw_staging.stg_genesys__queue` q ON q.queue_id = a.first_queue_id
LEFT JOIN `fennmoor-dw.dw_staging.stg_ref__contact_center_site` site ON STARTS_WITH(q.name, site.genesys_queue_prefix)
LEFT JOIN `fennmoor-dw.dw_staging.stg_genesys__wrapup_code` w ON w.wrapup_code_id = sg.final_wrapup_code_id
