SELECT
  src.party_id,
  src.cif_number,
  src.party_type,
  src.full_name,
  src.dob,
  TO_HEX(SHA256(src.tax_id)) AS tax_id_hash,
  src.country_of_citizenship,
  src.pep_flag,
  src.risk_rating,
  src.risk_rating_date,
  src.onboarding_date,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.party` AS src
WHERE NOT src._fivetran_deleted
