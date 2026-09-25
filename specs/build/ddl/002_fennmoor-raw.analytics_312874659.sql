CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.analytics_312874659` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251001` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251002` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251003` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251004` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251005` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251006` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251007` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251008` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251009` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251010` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251011` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251012` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251013` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251014` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251015` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251016` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251017` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251018` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251019` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251020` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251021` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251022` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251023` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251024` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251025` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251026` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251027` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251028` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251029` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251030` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251031` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251101` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251102` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251103` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251104` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251105` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251106` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251107` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251108` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251109` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251110` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251111` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251112` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251113` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251114` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251115` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251116` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251117` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251118` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251119` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251120` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251121` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251122` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251123` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251124` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251125` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251126` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251127` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251128` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251129` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251130` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251201` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251202` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251203` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251204` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251205` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251206` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251207` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251208` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251209` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251210` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251211` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251212` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251213` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251214` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251215` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251216` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251217` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251218` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251219` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251220` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251221` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251222` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251223` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251224` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251225` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251226` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251227` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251228` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251229` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251230` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20251231` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260101` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260102` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260103` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260104` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260105` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260106` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260107` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260108` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260109` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260110` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260111` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260112` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260113` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260114` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260115` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260116` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260117` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260118` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260119` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260120` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260121` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260122` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260123` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260124` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260125` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260126` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260127` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260128` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260129` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260130` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260131` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260201` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260202` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260203` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260204` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260205` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260206` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260207` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260208` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260209` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260210` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260211` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260212` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260213` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260214` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260215` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260216` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260217` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260218` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260219` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260220` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260221` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260222` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260223` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260224` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260225` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260226` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260227` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260228` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260301` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260302` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260303` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260304` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260305` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260306` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260307` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260308` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260309` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260310` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260311` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260312` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260313` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260314` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260315` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260316` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260317` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260318` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260319` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260320` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260321` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260322` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260323` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260324` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260325` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260326` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260327` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260328` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260329` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260330` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260331` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260401` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260402` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260403` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260404` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260405` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260406` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260407` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260408` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260409` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260410` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260411` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260412` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260413` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260414` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260415` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260416` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260417` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260418` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260419` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260420` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260421` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260422` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260423` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260424` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260425` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260426` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260427` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260428` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260429` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260430` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260501` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260502` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260503` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260504` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260505` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260506` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260507` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260508` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260509` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260510` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260511` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260512` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260513` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260514` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260515` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260516` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260517` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260518` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260519` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260520` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260521` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260522` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260523` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260524` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260525` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260526` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260527` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260528` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260529` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260530` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260531` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260601` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260602` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260603` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260604` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260605` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260606` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260607` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260608` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260609` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260610` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260611` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260612` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260613` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260614` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260615` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260616` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260617` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260618` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260619` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260620` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260621` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260622` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260623` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260624` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260625` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260626` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260627` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260628` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.events_20260629` (
  `event_date` STRING,
  `event_timestamp` INT64,
  `event_name` STRING,
  `event_params` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64>>>,
  `event_previous_timestamp` INT64,
  `event_value_in_usd` FLOAT64,
  `event_bundle_sequence_id` INT64,
  `event_server_timestamp_offset` INT64,
  `user_id` STRING,
  `user_pseudo_id` STRING,
  `privacy_info` STRUCT<analytics_storage STRING, ads_storage STRING, uses_transient_token STRING>,
  `user_properties` ARRAY<STRUCT<key STRING, value STRUCT<string_value STRING, int_value INT64, float_value FLOAT64, double_value FLOAT64, set_timestamp_micros INT64>>>,
  `user_first_touch_timestamp` INT64,
  `user_ltv` STRUCT<revenue FLOAT64, currency STRING>,
  `device` STRUCT<category STRING, mobile_brand_name STRING, mobile_model_name STRING, operating_system STRING, operating_system_version STRING, language STRING, is_limited_ad_tracking STRING, web_info STRUCT<browser STRING, browser_version STRING, hostname STRING>>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING, sub_continent STRING, metro STRING>,
  `traffic_source` STRUCT<name STRING, medium STRING, source STRING>,
  `collected_traffic_source` STRUCT<manual_campaign_id STRING, manual_campaign_name STRING, manual_source STRING, manual_medium STRING, manual_term STRING, manual_content STRING, gclid STRING>,
  `stream_id` STRING,
  `platform` STRING,
  `is_active_user` BOOL,
  `batch_event_index` INT64,
  `batch_page_id` INT64,
  `batch_ordering_id` INT64
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251001` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251002` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251003` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251004` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251005` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251006` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251007` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251008` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251009` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251010` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251011` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251012` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251013` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251014` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251015` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251016` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251017` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251018` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251019` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251020` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251021` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251022` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251023` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251024` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251025` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251026` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251027` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251028` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251029` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251030` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251031` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251101` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251102` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251103` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251104` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251105` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251106` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251107` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251108` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251109` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251110` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251111` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251112` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251113` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251114` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251115` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251116` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251117` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251118` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251119` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251120` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251121` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251122` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251123` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251124` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251125` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251126` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251127` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251128` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251129` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251130` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251201` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251202` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251203` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251204` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251205` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251206` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251207` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251208` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251209` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251210` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251211` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251212` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251213` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251214` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251215` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251216` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251217` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251218` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251219` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251220` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251221` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251222` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251223` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251224` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251225` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251226` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251227` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251228` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251229` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251230` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20251231` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260101` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260102` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260103` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260104` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260105` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260106` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260107` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260108` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260109` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260110` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260111` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260112` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260113` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260114` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260115` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260116` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260117` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260118` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260119` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260120` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260121` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260122` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260123` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260124` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260125` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260126` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260127` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260128` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260129` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260130` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260131` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260201` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260202` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260203` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260204` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260205` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260206` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260207` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260208` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260209` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260210` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260211` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260212` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260213` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260214` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260215` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260216` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260217` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260218` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260219` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260220` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260221` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260222` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260223` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260224` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260225` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260226` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260227` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260228` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260301` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260302` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260303` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260304` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260305` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260306` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260307` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260308` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260309` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260310` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260311` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260312` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260313` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260314` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260315` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260316` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260317` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260318` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260319` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260320` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260321` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260322` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260323` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260324` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260325` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260326` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260327` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260328` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260329` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260330` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260331` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260401` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260402` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260403` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260404` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260405` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260406` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260407` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260408` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260409` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260410` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260411` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260412` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260413` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260414` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260415` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260416` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260417` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260418` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260419` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260420` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260421` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260422` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260423` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260424` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260425` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260426` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260427` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260428` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260429` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260430` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260501` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260502` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260503` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260504` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260505` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260506` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260507` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260508` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260509` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260510` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260511` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260512` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260513` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260514` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260515` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260516` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260517` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260518` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260519` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260520` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260521` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260522` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260523` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260524` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260525` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260526` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260527` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260528` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260529` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260530` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260531` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260601` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260602` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260603` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260604` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260605` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260606` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260607` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260608` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260609` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260610` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260611` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260612` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260613` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260614` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260615` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260616` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260617` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260618` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260619` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260620` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260621` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260622` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260623` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260624` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260625` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260626` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260627` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260628` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.pseudonymous_users_20260629` (
  `pseudo_user_id` STRING,
  `stream_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `device` STRUCT<operating_system STRING, category STRING, mobile_brand_name STRING, mobile_model_name STRING, unified_screen_name STRING>,
  `geo` STRUCT<city STRING, country STRING, continent STRING, region STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `user_ltv` STRUCT<revenue_in_usd FLOAT64, sessions INT64, engagement_time_millis INT64, engaged_sessions INT64, session_duration_micros INT64>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251001` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251002` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251003` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251004` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251005` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251006` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251007` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251008` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251009` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251010` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251011` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251012` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251013` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251014` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251015` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251016` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251017` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251018` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251019` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251020` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251021` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251022` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251023` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251024` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251025` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251026` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251027` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251028` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251029` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251030` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251031` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251101` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251102` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251103` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251104` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251105` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251106` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251107` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251108` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251109` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251110` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251111` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251112` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251113` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251114` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251115` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251116` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251117` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251118` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251119` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251120` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251121` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251122` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251123` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251124` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251125` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251126` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251127` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251128` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251129` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251130` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251201` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251202` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251203` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251204` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251205` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251206` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251207` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251208` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251209` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251210` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251211` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251212` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251213` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251214` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251215` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251216` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251217` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251218` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251219` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251220` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251221` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251222` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251223` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251224` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251225` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251226` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251227` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251228` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251229` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251230` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20251231` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260101` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260102` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260103` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260104` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260105` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260106` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260107` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260108` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260109` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260110` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260111` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260112` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260113` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260114` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260115` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260116` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260117` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260118` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260119` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260120` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260121` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260122` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260123` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260124` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260125` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260126` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260127` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260128` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260129` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260130` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260131` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260201` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260202` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260203` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260204` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260205` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260206` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260207` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260208` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260209` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260210` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260211` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260212` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260213` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260214` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260215` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260216` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260217` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260218` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260219` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260220` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260221` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260222` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260223` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260224` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260225` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260226` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260227` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260228` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260301` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260302` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260303` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260304` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260305` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260306` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260307` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260308` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260309` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260310` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260311` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260312` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260313` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260314` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260315` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260316` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260317` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260318` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260319` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260320` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260321` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260322` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260323` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260324` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260325` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260326` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260327` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260328` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260329` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260330` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260331` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260401` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260402` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260403` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260404` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260405` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260406` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260407` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260408` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260409` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260410` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260411` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260412` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260413` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260414` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260415` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260416` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260417` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260418` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260419` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260420` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260421` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260422` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260423` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260424` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260425` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260426` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260427` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260428` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260429` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260430` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260501` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260502` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260503` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260504` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260505` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260506` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260507` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260508` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260509` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260510` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260511` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260512` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260513` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260514` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260515` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260516` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260517` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260518` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260519` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260520` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260521` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260522` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260523` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260524` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260525` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260526` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260527` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260528` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260529` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260530` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260531` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260601` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260602` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260603` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260604` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260605` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260606` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260607` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260608` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260609` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260610` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260611` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260612` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260613` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260614` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260615` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260616` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260617` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260618` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260619` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260620` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260621` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260622` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260623` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260624` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260625` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260626` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260627` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260628` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.analytics_312874659.users_20260629` (
  `user_id` STRING,
  `user_info` STRUCT<last_active_timestamp_micros INT64, user_first_touch_timestamp_micros INT64, first_purchase_date STRING>,
  `audiences` ARRAY<STRUCT<id INT64, name STRING, membership_start_timestamp_micros INT64, membership_expiry_timestamp_micros INT64, npa BOOL>>,
  `occurrence_date` STRING,
  `last_updated_date` STRING
);
