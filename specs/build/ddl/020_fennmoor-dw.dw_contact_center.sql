CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_contact_center` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_contact_center.agg_site_monthly` (
  `month_start` DATE,
  `site_id` STRING,
  `contacts` INT64,
  `closure_calls` INT64,
  `unique_callers` INT64,
  `avg_handle_sec` FLOAT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_contact_center.dim_agent` (
  `agent_user_id` STRING,
  `agent_name` STRING,
  `employee_id` STRING,
  `location_name` STRING,
  `site_id` STRING,
  `is_bpo` BOOL,
  `hire_date` DATE,
  `tenure_months` INT64,
  `job_profile` STRING,
  `manager_user_id` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_contact_center.dim_cc_site` (
  `site_id` STRING,
  `site_name` STRING,
  `city` STRING,
  `state` STRING,
  `operator` STRING,
  `is_outsourced` BOOL,
  `cost_center_id` STRING,
  `cost_center_name` STRING,
  `seat_count` INT64,
  `go_live_date` DATE,
  `queue_prefix` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_contact_center.dim_queue` (
  `queue_id` STRING,
  `queue_name` STRING,
  `site_id` STRING,
  `line_of_business` STRING,
  `division_id` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_contact_center.fct_agent_daily` (
  `agent_user_id` STRING,
  `conversation_date` DATE,
  `site_id` STRING,
  `contacts` INT64,
  `handle_sec` INT64,
  `avg_handle_sec` FLOAT64,
  `closure_calls` INT64,
  `transfers` INT64
)
PARTITION BY conversation_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_contact_center.fct_calls` (
  `conversation_id` STRING,
  `conversation_date` DATE,
  `conversation_start` TIMESTAMP,
  `media_type` STRING,
  `direction` STRING,
  `customer_key` INT64,
  `cif_number` STRING,
  `queue_id` STRING,
  `queue_name` STRING,
  `queue_site_id` STRING,
  `agent_user_id` STRING,
  `agent_site_id` STRING,
  `site_id` STRING,
  `ivr_auth_result` STRING,
  `ivr_intent` STRING,
  `wrapup_code_name` STRING,
  `is_account_closure_call` BOOL,
  `talk_sec` INT64,
  `hold_sec` INT64,
  `acw_sec` INT64,
  `handle_sec` INT64,
  `was_transferred` BOOL,
  `is_abandoned` BOOL,
  `is_authenticated` BOOL
)
PARTITION BY conversation_date
CLUSTER BY site_id, customer_key
OPTIONS (description = "Contacts (voice, chat, email). site_id = agent's site.");

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_contact_center.fct_cc_site_cost_monthly` (
  `site_id` STRING,
  `month_start` DATE,
  `cost_center_id` STRING,
  `total_expense` NUMERIC,
  `payroll_expense` NUMERIC,
  `vendor_expense` NUMERIC,
  `other_expense` NUMERIC
);

CREATE OR REPLACE VIEW `fennmoor-dw.dw_contact_center.fct_contacts_all` AS
WITH g AS (
SELECT fc.conversation_id AS contact_id, 'GENESYS' AS source_system,
       fc.conversation_date, fc.site_id, fc.cif_number, fc.handle_sec,
       fc.is_account_closure_call, fc.is_abandoned
FROM `fennmoor-dw.dw_contact_center.fct_calls` fc
),
l AS (
SELECT lc.legacy_call_id, 'AVAYA', lc.conversation_date, lc.site_id, lc.cif_number,
       lc.talk_sec + lc.hold_sec + lc.acw_sec,
       lc.disposition_code IN ('CLSACCT', 'CLOSE'), lc.is_abandoned
FROM `fennmoor-dw.dw_intermediate.int_calls_legacy_cdr` lc
),
u AS (
SELECT * FROM g UNION ALL SELECT * FROM l
)
SELECT
  u.contact_id,
  u.source_system,
  u.conversation_date,
  u.site_id,
  u.cif_number,
  u.handle_sec,
  u.is_account_closure_call,
  u.is_abandoned
FROM u;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_contact_center.fct_csat` (
  `survey_id` STRING,
  `conversation_id` STRING,
  `conversation_date` DATE,
  `site_id` STRING,
  `agent_user_id` STRING,
  `customer_key` INT64,
  `csat_score` INT64,
  `nps_score` INT64,
  `is_promoter` BOOL,
  `is_detractor` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_contact_center.rpt_site_cost_per_contact` (
  `month_start` DATE,
  `site_id` STRING,
  `site_name` STRING,
  `is_outsourced` BOOL,
  `contacts` INT64,
  `closure_calls` INT64,
  `total_expense` NUMERIC,
  `cost_per_contact` NUMERIC
);
