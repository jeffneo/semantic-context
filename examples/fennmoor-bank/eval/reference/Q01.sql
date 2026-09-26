-- Q01: account-closure contacts by site in 2025 (both phone systems: Avaya to 2025-09-30, then Genesys),
-- and each site's 2025 GL expense on its cost center. Avaya codes closures CLSACCT/CLOSE (fct_contacts_all
-- maps them); the site is the one the contact was handled at.
WITH contacts AS (
  SELECT site_id, COUNTIF(is_account_closure_call) AS closure_contacts, COUNT(*) AS contacts
  FROM `fennmoor-dw.dw_contact_center.fct_contacts_all`
  WHERE conversation_date BETWEEN '2025-01-01' AND '2025-12-31'
  GROUP BY site_id
),
cost AS (
  SELECT site_id, SUM(total_expense) AS expense_2025
  FROM `fennmoor-dw.dw_contact_center.fct_cc_site_cost_monthly`
  WHERE month_start BETWEEN '2025-01-01' AND '2025-12-01'
  GROUP BY site_id
)
SELECT s.site_name, c.closure_contacts, c.contacts, ROUND(k.expense_2025, 2) AS expense_2025
FROM `fennmoor-dw.dw_contact_center.dim_cc_site` s
LEFT JOIN contacts c USING (site_id)
LEFT JOIN cost k USING (site_id)
ORDER BY c.closure_contacts DESC
