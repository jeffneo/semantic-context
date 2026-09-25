SELECT
  src.paymentId AS payment_id,
  src.loanNumber AS loan_number,
  src.paymentDate AS payment_date,
  src.amount,
  src.principalPortion AS principal_portion,
  src.interestPortion AS interest_portion,
  src.feePortion AS fee_portion,
  src.paymentMethod AS payment_method,
  src.isLate AS is_late,
  src.returnedFlag AS returned_flag,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.loan_payment` AS src
WHERE NOT src._fivetran_deleted
