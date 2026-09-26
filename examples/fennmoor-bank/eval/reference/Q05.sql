-- Q05: month-end deposit balances by product line: each account's last balance date in each month.
WITH month_end AS (
  SELECT b.*, ROW_NUMBER() OVER (PARTITION BY b.account_key, DATE_TRUNC(b.balance_date, MONTH)
                                 ORDER BY b.balance_date DESC) AS latest
  FROM `fennmoor-dw.dw_core.fct_daily_account_balances` b
)
SELECT DATE_TRUNC(m.balance_date, MONTH) AS month, p.product_line, ROUND(SUM(m.ledger_balance), 2) AS month_end_balance
FROM month_end m
JOIN `fennmoor-dw.dw_core.dim_product` p ON p.product_code = m.product_code
WHERE m.latest = 1
GROUP BY 1, 2
ORDER BY 1, 2
