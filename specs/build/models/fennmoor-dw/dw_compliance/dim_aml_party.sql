SELECT
  p.party_id,
  p.cif_number,
  c.customer_key,
  p.party_type,
  p.risk_rating,
  p.pep_flag,
  p.onboarding_date,
  p.tax_id_hash
FROM `fennmoor-dw.dw_staging_restricted.stg_aml__party` p
LEFT JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.cif_number = p.cif_number
