SELECT
  u.account_natural_key,
  u.account_family,
  u.primary_cif_number AS cif_number,
  u.product_code,
  u.close_date,
  u.close_reason,
  u.close_reason IN ('CUST_REQ', 'COMPETITOR', 'FEES', 'MOVED', 'CH', 'PC') AS is_voluntary
FROM `fennmoor-dw.dw_intermediate.int_accounts_unioned` u
WHERE u.close_date IS NOT NULL AND u.account_family IN ('DEPOSIT', 'CARD')
