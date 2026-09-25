WITH bal AS (
SELECT b.customer_key, AVG(b.ledger_balance) AS avg_balance_30d
FROM `fennmoor-dw.dw_core.fct_daily_account_balances` b
WHERE b.balance_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY b.customer_key
),
lg AS (
SELECT fl.cif_number, COUNTIF(fl.is_success) AS logins_30d, COUNTIF(NOT fl.is_success) AS failed_logins_30d
FROM `fennmoor-dw.dw_digital.fct_digital_logins` fl
WHERE fl.event_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY fl.cif_number
),
cl AS (
SELECT fc.customer_key, COUNT(*) AS contacts_90d, COUNTIF(fc.is_account_closure_call) AS closure_calls_90d
FROM `fennmoor-dw.dw_contact_center.fct_calls` fc
WHERE fc.conversation_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY fc.customer_key
),
fe AS (
SELECT f.customer_key, COUNT(*) AS fee_count_90d, COUNTIF(f.is_waived) AS waived_fee_count_90d
FROM `fennmoor-dw.dw_core.fct_fees` f
WHERE f.assessed_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY f.customer_key
)
SELECT
  CURRENT_DATE() AS as_of_date,
  c.customer_key,
  c.tenure_months,
  c.segment,
  COALESCE(bal.avg_balance_30d, 0) AS avg_balance_30d,
  COALESCE(lg.logins_30d, 0) AS logins_30d,
  COALESCE(lg.failed_logins_30d, 0) AS failed_logins_30d,
  COALESCE(cl.contacts_90d, 0) AS contacts_90d,
  COALESCE(cl.closure_calls_90d, 0) AS closure_calls_90d,
  COALESCE(fe.fee_count_90d, 0) AS fee_count_90d,
  COALESCE(fe.waived_fee_count_90d, 0) AS waived_fee_count_90d
FROM `fennmoor-dw.dw_core.dim_customer` c
LEFT JOIN bal ON bal.customer_key = c.customer_key
LEFT JOIN lg ON lg.cif_number = c.cif_number
LEFT JOIN cl ON cl.customer_key = c.customer_key
LEFT JOIN fe ON fe.customer_key = c.customer_key
