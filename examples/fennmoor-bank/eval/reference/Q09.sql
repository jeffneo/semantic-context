-- Q09: loan delinquency rate (30+ days past due on the latest snapshot) by product and branch, over open
-- loans from dim_account, not only the delinquent ones.
WITH latest AS (SELECT MAX(snapshot_date) AS d FROM `fennmoor-dw.dw_risk.fct_delinquency_daily`),
delinquent AS (
  SELECT DISTINCT f.account_key
  FROM `fennmoor-dw.dw_risk.fct_delinquency_daily` f, latest
  WHERE f.snapshot_date = latest.d AND f.dpd >= 30
)
SELECT a.product_code, b.branch_name, COUNT(*) AS open_loans, COUNT(d.account_key) AS delinquent,
       ROUND(SAFE_DIVIDE(COUNT(d.account_key), COUNT(*)), 4) AS delinquency_rate
FROM `fennmoor-dw.dw_core.dim_account` a
LEFT JOIN delinquent d ON d.account_key = a.account_key
LEFT JOIN `fennmoor-dw.dw_core.dim_branch` b ON b.branch_id = a.branch_id
WHERE a.account_family = 'LOAN' AND a.is_open
GROUP BY 1, 2
ORDER BY open_loans DESC
