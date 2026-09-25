SELECT
  l.login_event_id,
  DATE(l.event_ts, 'America/Chicago') AS event_date,
  l.event_ts,
  l.olb_user_id,
  u.cif_number,
  l.channel,
  l.result,
  l.result = 'SUCCESS' AS is_success,
  l.risk_score,
  l.device_id,
  l.geo_country
FROM `fennmoor-dw.dw_staging.stg_olb__login_event` l
LEFT JOIN `fennmoor-dw.dw_staging.stg_olb__online_user` u ON u.olb_user_id = l.olb_user_id
