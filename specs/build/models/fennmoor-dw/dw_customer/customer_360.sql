WITH holdings AS (
SELECT a.customer_key,
       COUNTIF(a.account_family = 'DEPOSIT' AND a.is_open) AS open_deposit_accounts,
       COUNTIF(a.account_family = 'CARD' AND a.is_open) AS open_card_accounts,
       COUNTIF(a.account_family = 'LOAN' AND a.is_open) AS open_loans,
       MIN(a.open_date) AS first_account_open_date
FROM `fennmoor-dw.dw_core.dim_account` a
GROUP BY a.customer_key
),
bal AS (
SELECT b.customer_key, SUM(b.ledger_balance) AS total_deposit_balance
FROM `fennmoor-dw.dw_core.fct_daily_account_balances` b
WHERE b.balance_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY b.customer_key
),
spend AS (
SELECT t.customer_key, SUM(IF(t.is_purchase, t.amount, 0)) AS card_spend_90d,
       COUNT(*) AS card_txn_count_90d
FROM `fennmoor-dw.dw_core.fct_card_transactions` t
WHERE t.post_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY t.customer_key
),
contacts AS (
SELECT fc.customer_key, COUNT(*) AS contacts_90d,
       COUNTIF(fc.is_account_closure_call) AS closure_calls_90d
FROM `fennmoor-dw.dw_contact_center.fct_calls` fc
WHERE fc.conversation_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
GROUP BY fc.customer_key
),
web AS (
SELECT ws.customer_key, COUNT(*) AS web_sessions_30d
FROM `fennmoor-dw.dw_digital.fct_web_sessions` ws
WHERE ws.session_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY ws.customer_key
)
SELECT
  c.customer_key,
  c.cif_number,
  c.full_name,
  c.primary_email,
  c.segment,
  c.tenure_months,
  c.state_code,
  c.is_digitally_enrolled,
  COALESCE(h.open_deposit_accounts, 0) AS open_deposit_accounts,
  COALESCE(h.open_card_accounts, 0) AS open_card_accounts,
  COALESCE(h.open_loans, 0) AS open_loans,
  COALESCE(h.open_deposit_accounts, 0) + COALESCE(h.open_card_accounts, 0) + COALESCE(h.open_loans, 0) AS product_count,
  h.first_account_open_date,
  COALESCE(bal.total_deposit_balance, 0) AS total_deposit_balance,
  COALESCE(sp.card_spend_90d, 0) AS card_spend_90d,
  COALESCE(sp.card_txn_count_90d, 0) AS card_txn_count_90d,
  COALESCE(ct.contacts_90d, 0) AS contacts_90d,
  COALESCE(ct.closure_calls_90d, 0) AS closure_calls_90d,
  COALESCE(w.web_sessions_30d, 0) AS web_sessions_30d,
  ch.churn_probability,
  ch.risk_band AS churn_risk_band
FROM `fennmoor-dw.dw_core.dim_customer` c
LEFT JOIN holdings h ON h.customer_key = c.customer_key
LEFT JOIN bal ON bal.customer_key = c.customer_key
LEFT JOIN spend sp ON sp.customer_key = c.customer_key
LEFT JOIN contacts ct ON ct.customer_key = c.customer_key
LEFT JOIN web w ON w.customer_key = c.customer_key
LEFT JOIN `fennmoor-dw.ml_scores.churn_score_v3` ch ON ch.customer_key = c.customer_key AND ch.score_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
