SELECT
  m.merchant_id,
  m.merchant_name,
  m.dba_name,
  m.mcc,
  c.description AS mcc_description,
  c.category_group,
  m.city,
  m.state,
  m.country
FROM `fennmoor-dw.dw_staging.stg_cards__merchant` m
LEFT JOIN `fennmoor-dw.dw_staging.stg_cards__mcc_code` c ON c.mcc = m.mcc
