SELECT
  s.* EXCEPT (full_name, primary_email)
FROM `fennmoor-dw.dw_customer.customer_360` AS s
