CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.loan_origination` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.loan_origination.applicant` (
  `applicationId` STRING NOT NULL,
  `applicantRole` STRING,
  `cifNumber` STRING,
  `firstName` STRING,
  `lastName` STRING,
  `dateOfBirth` DATE,
  `ssnLast4` STRING,
  `email` STRING,
  `phone` STRING,
  `addressLine1` STRING,
  `city` STRING,
  `state` STRING,
  `zip` STRING,
  `yearsAtAddress` INT64,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.loan_origination.application` (
  `applicationId` STRING NOT NULL,
  `applicantCifNumber` STRING,
  `coApplicantCifNumber` STRING,
  `productCode` STRING,
  `channel` STRING,
  `requestedAmount` NUMERIC,
  `submittedAt` TIMESTAMP,
  `decisionStatus` STRING,
  `decisionAt` TIMESTAMP,
  `decisionReasonCodes` ARRAY<STRING>,
  `statedIncome` NUMERIC,
  `employmentStatus` STRING,
  `housingStatus` STRING,
  `branchNumber` INT64,
  `loanOfficerId` STRING,
  `offerCode` STRING,
  `creditScoreAtApp` INT64,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(submittedAt);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.loan_origination.collateral` (
  `collateralId` STRING,
  `loanNumber` STRING,
  `collateralType` STRING,
  `vin` STRING,
  `appraisedValue` NUMERIC,
  `appraisalDate` DATE,
  `lienPosition` INT64,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.loan_origination.credit_pull` (
  `pullId` STRING,
  `applicationId` STRING,
  `bureau` STRING,
  `pulledAt` TIMESTAMP,
  `ficoScore` INT64,
  `totalDebt` NUMERIC,
  `dtiRatio` NUMERIC,
  `inquiriesLast6m` INT64,
  `tradelinesOpen` INT64,
  `derogatoryCount` INT64,
  `rawReportUri` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.loan_origination.decision` (
  `applicationId` STRING NOT NULL,
  `decisionSeq` INT64,
  `decidedBy` STRING,
  `outcome` STRING,
  `approvedAmount` NUMERIC,
  `approvedApr` NUMERIC,
  `conditions` ARRAY<STRING>,
  `decidedAt` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.loan_origination.delinquency_snapshot` (
  `snapshotDate` DATE NOT NULL,
  `loanNumber` STRING NOT NULL,
  `dpd` INT64,
  `bucket` STRING,
  `pastDueAmount` NUMERIC,
  `collectorId` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY snapshotDate;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.loan_origination.loan` (
  `loanNumber` STRING NOT NULL,
  `applicationId` STRING,
  `borrowerCif` STRING NOT NULL,
  `productCode` STRING,
  `originationDate` DATE,
  `principalAmount` NUMERIC,
  `currentPrincipal` NUMERIC,
  `interestRate` NUMERIC,
  `termMonths` INT64,
  `maturityDate` DATE,
  `paymentAmount` NUMERIC,
  `loanStatus` STRING,
  `collateralType` STRING,
  `branchNumber` INT64,
  `dpd` INT64,
  `chargeOffDate` DATE,
  `chargeOffAmount` NUMERIC,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
CLUSTER BY loanNumber;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.loan_origination.loan_payment` (
  `paymentId` STRING NOT NULL,
  `loanNumber` STRING NOT NULL,
  `paymentDate` DATE,
  `amount` NUMERIC,
  `principalPortion` NUMERIC,
  `interestPortion` NUMERIC,
  `feePortion` NUMERIC,
  `paymentMethod` STRING,
  `isLate` BOOL,
  `returnedFlag` BOOL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY paymentDate
CLUSTER BY loanNumber;
