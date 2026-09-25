SELECT
  x.customer_key,
  c.cif_number,
  CASE c.customer_type_code WHEN 'I' THEN 'INDIVIDUAL' WHEN 'B' THEN 'BUSINESS' END AS customer_type,
  COALESCE(c.business_name, CONCAT(c.first_name, ' ', c.last_name)) AS full_name,
  c.birth_date,
  c.tax_id_hash,
  c.customer_since_date,
  DATE_DIFF(CURRENT_DATE(), c.customer_since_date, MONTH) AS tenure_months,
  c.customer_status_code AS customer_status,
  c.segment_code AS segment,
  c.preferred_branch_id,
  c.preferred_language_code AS preferred_language,
  c.is_employee,
  c.risk_rating_code AS aml_risk_rating,
  cp.primary_email,
  cp.primary_mobile,
  cp.email_opt_in,
  ad.state_code,
  ad.zip_code,
  x.sf_contact_id,
  x.sf_household_id,
  x.is_digitally_enrolled,
  c.deceased_date IS NOT NULL AS is_deceased
FROM `fennmoor-dw.dw_staging.stg_core__customer` c
JOIN `fennmoor-dw.dw_intermediate.int_customer_identity` x ON x.cif_number = c.cif_number
LEFT JOIN `fennmoor-dw.dw_intermediate.int_customer_contact_points` cp ON cp.cif_number = c.cif_number
LEFT JOIN `fennmoor-dw.dw_staging.stg_core__customer_address` ad
  ON ad.cif_number = c.cif_number AND ad.is_primary AND ad.end_date IS NULL
