WITH sf AS (
SELECT ct.cif_number, ANY_VALUE(ct.contact_id) AS sf_contact_id,
       ANY_VALUE(ct.account_id) AS sf_household_id, COUNT(*) AS sf_contact_count
FROM `fennmoor-dw.dw_staging.stg_sf__contact` ct
WHERE ct.cif_number IS NOT NULL
GROUP BY ct.cif_number
),
olb AS (
SELECT ou.cif_number, ARRAY_AGG(ou.olb_user_id) AS olb_user_ids,
       ARRAY_AGG(ou.ga4_user_id IGNORE NULLS) AS ga4_user_ids,
       MIN(ou.enrolled_at) AS first_enrolled_at
FROM `fennmoor-dw.dw_staging.stg_olb__online_user` ou
GROUP BY ou.cif_number
)
SELECT
  c.cif_number,
  FARM_FINGERPRINT(c.cif_number) AS customer_key,
  sf.sf_contact_id,
  sf.sf_household_id,
  COALESCE(sf.sf_contact_count, 0) AS sf_contact_count,
  olb.olb_user_ids,
  olb.ga4_user_ids,
  olb.first_enrolled_at,
  b.braze_id,
  olb.cif_number IS NOT NULL AS is_digitally_enrolled
FROM `fennmoor-dw.dw_staging.stg_core__customer` c
LEFT JOIN sf ON sf.cif_number = c.cif_number
LEFT JOIN olb ON olb.cif_number = c.cif_number
LEFT JOIN `fennmoor-dw.dw_staging.stg_braze__user_profile` b ON b.external_id = c.cif_number
