CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_marketing` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_marketing.dim_campaign` (
  `campaign_id` STRING,
  `campaign_name` STRING,
  `channels` ARRAY<STRING>,
  `tags` ARRAY<STRING>,
  `first_sent` TIMESTAMP,
  `last_sent` TIMESTAMP,
  `is_archived` BOOL,
  `sf_campaign_id` STRING,
  `budgeted_cost` NUMERIC,
  `actual_cost` NUMERIC
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_marketing.fct_campaign_attribution` (
  `conversion_id` STRING,
  `conversion_at` TIMESTAMP,
  `cif_number` STRING,
  `customer_key` INT64,
  `campaign_id` STRING,
  `conversion_behavior` STRING,
  `attributed_send_id` STRING,
  `hours_since_send` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_marketing.fct_campaign_engagement` (
  `campaign_id` STRING,
  `dispatch_id` STRING,
  `cif_number` STRING,
  `event_date` DATE,
  `delivered` BOOL,
  `opened` BOOL,
  `clicked` BOOL,
  `unsubscribed` BOOL,
  `bounced` BOOL
)
PARTITION BY event_date;

CREATE TABLE IF NOT EXISTS `fennmoor-dw.dw_marketing.fct_campaign_sends` (
  `message_send_id` STRING,
  `sent_date` DATE,
  `sent_at` TIMESTAMP,
  `cif_number` STRING,
  `customer_key` INT64,
  `campaign_id` STRING,
  `canvas_id` STRING,
  `channel` STRING,
  `dispatch_id` STRING
)
PARTITION BY sent_date
CLUSTER BY campaign_id, customer_key;
