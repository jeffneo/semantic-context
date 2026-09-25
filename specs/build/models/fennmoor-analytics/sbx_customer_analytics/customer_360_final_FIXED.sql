SELECT
  s.*
FROM `fennmoor-analytics.sbx_customer_analytics.customer_360_final` AS s
WHERE s.segment != 'employee'
