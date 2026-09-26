-- Q14: account closures by reason, deposits versus cards. The card processor has its own codes: mapped to
-- core banking's (CH cardholder request -> CUST_REQ, FR -> FRAUD, IN inactive -> DORMANT); PC and CO
-- have no core-banking equivalent and keep their own names.
SELECT account_family,
       CASE close_reason WHEN 'CH' THEN 'CUST_REQ' WHEN 'FR' THEN 'FRAUD' WHEN 'IN' THEN 'DORMANT'
                         WHEN 'PC' THEN 'PRODUCT_CHANGE' WHEN 'CO' THEN 'CHARGE_OFF' ELSE close_reason END AS reason,
       COUNT(*) AS closures
FROM `fennmoor-dw.dw_core.fct_account_closures`
GROUP BY 1, 2
ORDER BY 1, 3 DESC
