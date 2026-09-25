SELECT
  m.message_send_id,
  DATE(m.sent_at, 'America/Chicago') AS sent_date,
  m.sent_at,
  m.external_user_id AS cif_number,
  c.customer_key,
  m.campaign_id,
  m.canvas_id,
  m.channel,
  m.dispatch_id
FROM `fennmoor-dw.dw_staging.stg_braze__message_send` m
LEFT JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.cif_number = m.external_user_id
