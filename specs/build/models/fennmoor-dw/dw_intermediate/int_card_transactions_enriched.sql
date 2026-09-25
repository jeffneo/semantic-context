SELECT
  s.settlement_id,
  s.post_date,
  s.account_id AS card_account_id,
  ca.bank_customer_ref AS cif_number,
  s.card_token,
  s.amount,
  s.txn_type,
  s.txn_type = 'PURCH' AS is_purchase,
  s.merchant_id,
  COALESCE(mer.merchant_name, s.merchant_name_raw) AS merchant_name,
  s.mcc,
  m.category_group AS mcc_category_group,
  s.merchant_state,
  s.merchant_country != 'USA' AS is_foreign,
  s.interchange
FROM `fennmoor-dw.dw_staging.stg_cards__settlement` s
JOIN `fennmoor-dw.dw_staging.stg_cards__card_account` ca ON ca.account_id = s.account_id
LEFT JOIN `fennmoor-dw.dw_staging.stg_cards__mcc_code` m ON m.mcc = s.mcc
LEFT JOIN `fennmoor-dw.dw_staging.stg_cards__merchant` mer ON mer.merchant_id = s.merchant_id
