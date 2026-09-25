SELECT
  r.account_id,
  r.cif_number,
  r.relationship_type_code,
  r.relationship_type_code = 'PRI' AS is_primary_holder,
  r.relationship_effective_date
FROM `fennmoor-dw.dw_staging.stg_core__account_customer_relationship` r
WHERE r.relationship_end_date IS NULL
