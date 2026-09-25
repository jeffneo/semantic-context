SELECT
  src.collateralId AS collateral_id,
  src.loanNumber AS loan_number,
  src.collateralType AS collateral_type,
  src.vin,
  src.appraisedValue AS appraised_value,
  src.appraisalDate AS appraisal_date,
  src.lienPosition AS lien_position,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.collateral` AS src
WHERE NOT src._fivetran_deleted
