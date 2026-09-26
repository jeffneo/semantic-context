-- Q10: CSAT by agent tenure. BPO agents have no hire date: a band of their own, not "new".
SELECT CASE WHEN a.hire_date IS NULL THEN 'BPO (no hire date)'
            WHEN a.tenure_months < 12 THEN 'under 1 year'
            WHEN a.tenure_months < 36 THEN '1 to 3 years'
            ELSE '3 years or more' END AS tenure,
       COUNT(*) AS surveys, ROUND(AVG(s.csat_score), 2) AS avg_csat
FROM `fennmoor-dw.dw_contact_center.fct_csat` s
JOIN `fennmoor-dw.dw_contact_center.dim_agent` a ON a.agent_user_id = s.agent_user_id
GROUP BY 1
ORDER BY 1
