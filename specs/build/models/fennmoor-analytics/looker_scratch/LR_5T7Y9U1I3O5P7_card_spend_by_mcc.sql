SELECT
  DATE_TRUNC(t.post_date, MONTH) AS month_start,
  t.mcc_category_group,
  SUM(t.amount) AS spend,
  COUNT(*) AS txn_count,
  COUNT(DISTINCT t.card_account_id) AS active_accounts
FROM `fennmoor-dw.dw_core.fct_card_transactions` t
WHERE t.is_purchase
GROUP BY ALL
