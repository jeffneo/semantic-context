SELECT
  src.transfer_id,
  src.olb_user_id,
  src.from_account_id,
  src.direction,
  src.counterparty_token,
  src.counterparty_name,
  src.amount,
  src.initiated_at,
  src.status,
  src.fraud_hold,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.p2p_transfer` AS src
WHERE NOT src._fivetran_deleted
