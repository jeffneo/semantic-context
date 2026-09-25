SELECT
  c.cif_number AS external_id,
  c.churn_probability,
  c.segment,
  c.total_deposit_balance,
  c.primary_email AS email
FROM `fennmoor-dw.dw_customer.customer_360` c
WHERE c.churn_probability >= 0.6 AND c.total_deposit_balance >= 50000
