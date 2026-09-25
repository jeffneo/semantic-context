SELECT
  src.login_event_id,
  src.olb_user_id,
  src.session_id,
  src.event_ts,
  src.channel,
  src.result,
  src.ip_address,
  src.device_id,
  src.geo_country,
  src.user_agent,
  src.risk_score,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.login_event` AS src
WHERE NOT src._fivetran_deleted
