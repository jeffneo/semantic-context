SELECT
  t.card_account_id,
  COUNTIF(t.post_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)) AS txn_count_1d,
  COUNT(*) AS txn_count_7d,
  SUM(t.amount) AS amount_7d,
  COUNT(DISTINCT t.mcc) AS distinct_mcc_7d,
  COUNTIF(t.is_foreign) AS foreign_txn_7d
FROM `fennmoor-dw.dw_core.fct_card_transactions` t
WHERE t.post_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY ALL
