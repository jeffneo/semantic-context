SELECT
  t.settlement_id,
  t.post_date,
  t.card_account_id,
  a.account_key,
  a.customer_key,
  t.cif_number,
  t.card_token,
  t.amount,
  t.txn_type,
  t.is_purchase,
  t.merchant_id,
  t.merchant_name,
  t.mcc,
  t.mcc_category_group,
  t.is_foreign,
  t.interchange
FROM `fennmoor-dw.dw_intermediate.int_card_transactions_enriched` t
LEFT JOIN `fennmoor-dw.dw_core.dim_account` a ON a.card_account_id = t.card_account_id
