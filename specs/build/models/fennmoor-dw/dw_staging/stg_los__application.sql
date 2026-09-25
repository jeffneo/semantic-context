SELECT
  src.applicationId AS application_id,
  src.applicantCifNumber AS applicant_cif_number,
  src.coApplicantCifNumber AS co_applicant_cif_number,
  src.productCode AS product_code,
  src.channel,
  src.requestedAmount AS requested_amount,
  src.submittedAt AS submitted_at,
  src.decisionStatus AS decision_status,
  src.decisionAt AS decision_at,
  src.decisionReasonCodes AS decision_reason_codes,
  src.statedIncome AS stated_income,
  src.employmentStatus AS employment_status,
  src.housingStatus AS housing_status,
  src.branchNumber AS branch_number,
  src.loanOfficerId AS loan_officer_id,
  src.offerCode AS offer_code,
  src.creditScoreAtApp AS credit_score_at_app,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.application` AS src
WHERE NOT src._fivetran_deleted
