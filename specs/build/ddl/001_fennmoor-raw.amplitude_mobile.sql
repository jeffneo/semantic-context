CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.amplitude_mobile` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.amplitude_mobile.EVENTS_318842` (
  `_insert_id` STRING,
  `amplitude_id` INT64,
  `user_id` STRING,
  `device_id` STRING,
  `event_type` STRING,
  `event_time` TIMESTAMP,
  `client_event_time` TIMESTAMP,
  `server_upload_time` TIMESTAMP,
  `session_id` INT64,
  `event_properties` STRING,
  `user_properties` STRING,
  `os_name` STRING,
  `os_version` STRING,
  `device_model` STRING,
  `platform` STRING,
  `version_name` STRING,
  `country` STRING,
  `region` STRING,
  `city` STRING,
  `ip_address` STRING,
  `language` STRING
)
PARTITION BY DATE(event_time)
CLUSTER BY event_type, user_id;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.amplitude_mobile.MERGE_IDS_318842` (
  `amplitude_id` INT64,
  `merged_amplitude_id` INT64,
  `merge_server_time` TIMESTAMP,
  `merge_event_time` TIMESTAMP
);
