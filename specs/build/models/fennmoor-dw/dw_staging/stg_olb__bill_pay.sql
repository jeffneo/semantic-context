SELECT
  src.payment_id,
  src.olb_user_id,
  src.from_account_id,
  src.payee_id,
  src.payee_name,
  src.amount,
  src.scheduled_date,
  src.sent_date,
  src.status,
  src.is_recurring,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.bill_pay` AS src
WHERE NOT src._fivetran_deleted
