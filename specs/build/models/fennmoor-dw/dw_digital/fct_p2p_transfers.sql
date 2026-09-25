SELECT
  p.transfer_id,
  DATE(p.initiated_at, 'America/Chicago') AS initiated_date,
  p.olb_user_id,
  u.cif_number,
  p.from_account_id AS core_account_id,
  p.direction,
  p.amount,
  p.status,
  p.fraud_hold
FROM `fennmoor-dw.dw_staging.stg_olb__p2p_transfer` p
LEFT JOIN `fennmoor-dw.dw_staging.stg_olb__online_user` u ON u.olb_user_id = p.olb_user_id
