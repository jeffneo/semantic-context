SELECT
  c.segment,
  DATE_TRUNC(s.post_date, MONTH) AS month_start,
  SUM(s.amount_cents) AS card_spend_usd,
  COUNT(DISTINCT ca.bank_customer_ref) AS cardholders
FROM `fennmoor-raw.card_processor.settlement` s
JOIN `fennmoor-raw.card_processor.card_account` ca ON ca.account_id = s.account_id
JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.cif_number = ca.bank_customer_ref
WHERE s.txn_type = 'PURCH'
GROUP BY ALL
