SELECT
  c.cif_number,
  c.segment,
  c.tenure_months,
  c.total_deposit_balance,
  c.contacts_90d,
  x.account_key IS NOT NULL AS label_attrited
FROM `fennmoor-dw.dw_customer.customer_360` c
LEFT JOIN `fennmoor-dw.dw_core.fct_account_closures` x ON x.customer_key = c.customer_key AND x.is_voluntary
