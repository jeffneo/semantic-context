SELECT
  src.loanNumber AS loan_number,
  src.applicationId AS application_id,
  src.borrowerCif AS borrower_cif,
  src.productCode AS product_code,
  src.originationDate AS origination_date,
  src.principalAmount AS principal_amount,
  src.currentPrincipal AS current_principal,
  src.interestRate AS interest_rate,
  src.termMonths AS term_months,
  src.maturityDate AS maturity_date,
  src.paymentAmount AS payment_amount,
  src.loanStatus AS loan_status,
  src.collateralType AS collateral_type,
  src.branchNumber AS branch_number,
  src.dpd,
  src.chargeOffDate AS charge_off_date,
  src.chargeOffAmount AS charge_off_amount,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.loan` AS src
WHERE NOT src._fivetran_deleted
