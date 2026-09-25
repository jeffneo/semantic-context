SELECT
  cc.cif_number,
  MAX(IF(cc.contact_type_code = 'EML' AND cc.is_primary, cc.contact_value, NULL)) AS primary_email,
  MAX(IF(cc.contact_type_code = 'MPH' AND cc.is_primary, cc.contact_value, NULL)) AS primary_mobile,
  LOGICAL_OR(cc.contact_type_code = 'EML' AND cc.is_verified) AS has_verified_email,
  LOGICAL_OR(cc.contact_type_code = 'EML' AND cc.is_opted_in) AS email_opt_in
FROM `fennmoor-dw.dw_staging.stg_core__customer_contact` cc
GROUP BY ALL
