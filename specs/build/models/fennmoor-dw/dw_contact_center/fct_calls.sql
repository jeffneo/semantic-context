SELECT
  c.conversation_id,
  c.conversation_date,
  c.conversation_start,
  c.media_type,
  c.direction,
  cu.customer_key,
  c.cif_number,
  c.queue_id,
  c.queue_name,
  c.queue_site_id,
  c.agent_user_id,
  ag.site_id AS agent_site_id,
  COALESCE(ag.site_id, c.queue_site_id) AS site_id,
  c.ivr_auth_result,
  c.ivr_intent,
  c.wrapup_code_name,
  c.is_account_closure_call,
  c.talk_sec,
  c.hold_sec,
  c.acw_sec,
  COALESCE(c.talk_sec, 0) + COALESCE(c.hold_sec, 0) + COALESCE(c.acw_sec, 0) AS handle_sec,
  c.was_transferred,
  c.is_abandoned,
  c.ivr_auth_result = 'AUTH_OK' AS is_authenticated
FROM `fennmoor-dw.dw_intermediate.int_calls_enriched` c
LEFT JOIN `fennmoor-dw.dw_core.dim_customer` cu ON cu.cif_number = c.cif_number
LEFT JOIN `fennmoor-dw.dw_contact_center.dim_agent` ag ON ag.agent_user_id = c.agent_user_id
