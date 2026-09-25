CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.genesys_cloud` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.genesys_cloud.conversation` (
  `conversation_id` STRING NOT NULL,
  `conversation_start` TIMESTAMP,
  `conversation_end` TIMESTAMP,
  `originating_direction` STRING,
  `media_type` STRING,
  `division_id` STRING,
  `ani_hash` STRING,
  `dnis` STRING,
  `external_tag` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(conversation_start);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.genesys_cloud.evaluation` (
  `evaluation_id` STRING NOT NULL,
  `conversation_id` STRING,
  `agent_id` STRING,
  `evaluator_id` STRING,
  `form_name` STRING,
  `total_score` NUMERIC,
  `critical_score` NUMERIC,
  `released_date` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.genesys_cloud.ivr_flow_outcome` (
  `conversation_id` STRING NOT NULL,
  `flow_id` STRING,
  `flow_name` STRING,
  `outcome_id` STRING,
  `outcome_name` STRING,
  `outcome_value` STRING,
  `outcome_start` TIMESTAMP,
  `outcome_end` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(outcome_start);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.genesys_cloud.participant` (
  `participant_id` STRING NOT NULL,
  `conversation_id` STRING NOT NULL,
  `purpose` STRING,
  `user_id` STRING,
  `queue_id` STRING,
  `participant_name` STRING,
  `start_time` TIMESTAMP,
  `end_time` TIMESTAMP,
  `attributes` JSON,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(start_time);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.genesys_cloud.queue` (
  `id` STRING NOT NULL,
  `name` STRING,
  `division_id` STRING,
  `description` STRING,
  `acw_timeout_ms` INT64,
  `skill_evaluation_method` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.genesys_cloud.segment` (
  `segment_id` STRING NOT NULL,
  `conversation_id` STRING NOT NULL,
  `participant_id` STRING,
  `segment_type` STRING,
  `segment_start` TIMESTAMP,
  `segment_end` TIMESTAMP,
  `queue_id` STRING,
  `wrap_up_code` STRING,
  `wrap_up_note` STRING,
  `disconnect_type` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(segment_start)
CLUSTER BY conversation_id;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.genesys_cloud.survey_response` (
  `survey_id` STRING NOT NULL,
  `conversation_id` STRING,
  `agent_user_id` STRING,
  `sent_at` TIMESTAMP,
  `completed_at` TIMESTAMP,
  `csat_score` INT64,
  `nps_score` INT64,
  `verbatim` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.genesys_cloud.user` (
  `id` STRING NOT NULL,
  `name` STRING,
  `email` STRING,
  `department` STRING,
  `title` STRING,
  `manager_id` STRING,
  `location_name` STRING,
  `employee_id` STRING,
  `state` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.genesys_cloud.wrapup_code` (
  `id` STRING NOT NULL,
  `name` STRING,
  `description` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);
