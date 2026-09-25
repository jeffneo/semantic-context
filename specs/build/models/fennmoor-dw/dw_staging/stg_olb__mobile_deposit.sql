SELECT
  src.deposit_id,
  src.olb_user_id,
  src.account_id,
  src.amount,
  src.check_number,
  src.submitted_at,
  src.status,
  src.hold_until_date,
  src.reject_reason,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.mobile_deposit` AS src
WHERE NOT src._fivetran_deleted
