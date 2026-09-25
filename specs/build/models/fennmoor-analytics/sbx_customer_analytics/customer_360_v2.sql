SELECT
  s.*,
  s.total_deposit_balance * 0.02 + s.card_spend_90d * 0.015 AS ltv_estimate
FROM `fennmoor-dw.dw_customer.customer_360` AS s
