SELECT
  ca.account_id,
  ca.status AS card_status,
  ca.current_balance AS card_balance,
  a.account_status_code AS deposit_status,
  a.open_date AS deposit_open_date
FROM `fennmoor-dw.dw_staging.stg_cards__card_account` ca
JOIN `fennmoor-dw.dw_staging.stg_core__account` a ON a.account_id = ca.account_id
WHERE ca.delinquency_bucket IS NOT NULL
