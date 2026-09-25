CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_staging_restricted` OPTIONS (location = 'US');

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging_restricted.stg_aml__ctr_filing` AS
SELECT
  src.ctr_id,
  src.party_id,
  src.txn_date,
  src.cash_in_amount,
  src.cash_out_amount,
  src.filing_date,
  src.branch_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.ctr_filing` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging_restricted.stg_aml__kyc_review` AS
SELECT
  src.review_id,
  src.party_id,
  src.review_type,
  src.started_at,
  src.completed_at,
  src.outcome,
  src.reviewer_id,
  src.next_review_due,
  src.edd_required,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.kyc_review` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging_restricted.stg_aml__party` AS
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
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging_restricted.stg_aml__sar_filing` AS
SELECT
  src.sar_id,
  src.party_id,
  src.alert_ids,
  src.filing_date,
  src.activity_start,
  src.activity_end,
  src.amount_involved,
  src.narrative,
  src.bsa_id,
  src.status,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.sar_filing` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging_restricted.stg_aml__screening_hit` AS
SELECT
  src.hit_id,
  src.party_id,
  src.list_name,
  src.match_score,
  src.matched_name,
  src.status,
  src.reviewed_at,
  src.reviewer_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.screening_hit` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging_restricted.stg_aml__transaction_alert` AS
SELECT
  src.alert_id,
  src.party_id,
  src.scenario_code,
  src.alert_date,
  src.total_amount,
  src.status,
  src.assigned_to,
  src.closed_date,
  src.escalated_to_case,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.aml_kyc.transaction_alert` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging_restricted.stg_wd__compensation` AS
SELECT
  src.worker_id,
  src.effective_date,
  src.base_pay_annual,
  src.bonus_target_pct,
  src.currency_code,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.workday.compensation` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging_restricted.stg_wd__position` AS
SELECT
  src.position_id,
  src.worker_id,
  src.job_profile,
  src.effective_date,
  src.fte,
  src.scheduled_hours,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.workday.position` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging_restricted.stg_wd__worker` AS
SELECT
  src.worker_id,
  src.legal_name,
  src.preferred_name,
  src.work_email,
  src.hire_date,
  src.termination_date,
  src.job_profile,
  src.job_family,
  src.management_level,
  src.cost_center_id,
  src.location,
  src.supervisor_worker_id,
  src.worker_status,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.workday.worker` AS src
WHERE NOT src._fivetran_deleted;
