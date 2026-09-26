-- Q11: customers using the mobile app each week, counted by CIF (joint users have several logins).
SELECT DATE_TRUNC(session_date, WEEK) AS week, COUNT(DISTINCT cif_number) AS customers
FROM `fennmoor-dw.dw_digital.fct_app_sessions`
WHERE cif_number IS NOT NULL
GROUP BY week
ORDER BY week
