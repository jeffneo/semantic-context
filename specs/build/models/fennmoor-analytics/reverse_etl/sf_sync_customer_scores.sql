SELECT
  d.sf_contact_id,
  c.churn_probability AS churn_probability__c,
  c.product_count AS product_count__c,
  c.total_deposit_balance AS total_deposit_balance__c,
  c.card_spend_90d AS card_spend_90d__c
FROM `fennmoor-dw.dw_customer.customer_360` c
JOIN `fennmoor-dw.dw_core.dim_customer` d ON d.customer_key = c.customer_key
WHERE d.sf_contact_id IS NOT NULL
