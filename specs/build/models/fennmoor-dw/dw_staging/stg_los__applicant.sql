SELECT
  src.applicationId AS application_id,
  src.applicantRole AS applicant_role,
  src.cifNumber AS cif_number,
  src.firstName AS first_name,
  src.lastName AS last_name,
  src.dateOfBirth AS date_of_birth,
  src.ssnLast4 AS ssn_last4,
  src.email,
  src.phone,
  src.addressLine1 AS address_line1,
  src.city,
  src.state,
  src.zip,
  src.yearsAtAddress AS years_at_address,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.applicant` AS src
WHERE NOT src._fivetran_deleted
