CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.braze` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.braze.campaign` (
  `id` STRING NOT NULL,
  `name` STRING,
  `created_at` TIMESTAMP,
  `channels` ARRAY<STRING>,
  `tags` ARRAY<STRING>,
  `archived` BOOL,
  `first_sent` TIMESTAMP,
  `last_sent` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.braze.canvas` (
  `id` STRING NOT NULL,
  `name` STRING,
  `created_at` TIMESTAMP,
  `tags` ARRAY<STRING>,
  `archived` BOOL,
  `enabled` BOOL,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.braze.conversion` (
  `id` STRING NOT NULL,
  `external_user_id` STRING,
  `campaign_id` STRING,
  `canvas_id` STRING,
  `conversion_behavior` STRING,
  `event_time` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(event_time);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.braze.email_event` (
  `id` STRING NOT NULL,
  `event_type` STRING,
  `external_user_id` STRING,
  `campaign_id` STRING,
  `canvas_id` STRING,
  `dispatch_id` STRING,
  `email_address` STRING,
  `url` STRING,
  `event_time` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(event_time);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.braze.message_send` (
  `id` STRING NOT NULL,
  `user_id` STRING,
  `external_user_id` STRING,
  `campaign_id` STRING,
  `canvas_id` STRING,
  `canvas_step_id` STRING,
  `channel` STRING,
  `sent_at` TIMESTAMP,
  `message_variation_id` STRING,
  `dispatch_id` STRING,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(sent_at)
CLUSTER BY external_user_id;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.braze.push_event` (
  `id` STRING NOT NULL,
  `event_type` STRING,
  `external_user_id` STRING,
  `campaign_id` STRING,
  `canvas_id` STRING,
  `platform` STRING,
  `event_time` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(event_time);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.braze.user_profile` (
  `external_id` STRING NOT NULL,
  `braze_id` STRING,
  `email` STRING,
  `phone` STRING,
  `first_name` STRING,
  `email_subscribe` STRING,
  `push_subscribe` STRING,
  `custom_attributes` JSON,
  `updated_at` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);
