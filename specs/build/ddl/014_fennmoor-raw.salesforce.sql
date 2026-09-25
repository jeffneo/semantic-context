CREATE SCHEMA IF NOT EXISTS `fennmoor-raw.salesforce` OPTIONS (location = 'US');

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.account` (
  `id` STRING NOT NULL,
  `name` STRING,
  `type` STRING,
  `record_type_id` STRING,
  `owner_id` STRING,
  `primary_branch__c` STRING,
  `household_segment__c` STRING,
  `total_relationship_balance__c` NUMERIC,
  `billing_state` STRING,
  `billing_postal_code` STRING,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.campaign` (
  `id` STRING NOT NULL,
  `name` STRING,
  `type` STRING,
  `status` STRING,
  `start_date` DATE,
  `end_date` DATE,
  `braze_campaign_id__c` STRING,
  `budgeted_cost` NUMERIC,
  `actual_cost` NUMERIC,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.campaign_member` (
  `id` STRING NOT NULL,
  `campaign_id` STRING,
  `contact_id` STRING,
  `lead_id` STRING,
  `status` STRING,
  `has_responded` BOOL,
  `first_responded_date` DATE,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.case` (
  `id` STRING NOT NULL,
  `case_number` STRING,
  `contact_id` STRING,
  `account_id` STRING,
  `origin` STRING,
  `type` STRING,
  `reason` STRING,
  `sub_reason__c` STRING,
  `status` STRING,
  `priority` STRING,
  `subject` STRING,
  `description` STRING,
  `closed_date` TIMESTAMP,
  `is_closed` BOOL,
  `is_escalated` BOOL,
  `owner_id` STRING,
  `genesys_conversation_id__c` STRING,
  `related_account_number__c` STRING,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY DATE(created_date);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.case_history` (
  `id` STRING,
  `case_id` STRING,
  `field` STRING,
  `old_value` STRING,
  `new_value` STRING,
  `created_by_id` STRING,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.contact` (
  `id` STRING NOT NULL,
  `account_id` STRING,
  `cif_number__c` STRING,
  `first_name` STRING,
  `last_name` STRING,
  `email` STRING,
  `phone` STRING,
  `mobile_phone` STRING,
  `birthdate` DATE,
  `mailing_street` STRING,
  `mailing_city` STRING,
  `mailing_state` STRING,
  `mailing_postal_code` STRING,
  `do_not_call` BOOL,
  `has_opted_out_of_email` BOOL,
  `preferred_channel__c` STRING,
  `owner_id` STRING,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.financial_account__c` (
  `id` STRING NOT NULL,
  `name` STRING,
  `account_number__c` STRING,
  `core_account_id__c` STRING,
  `primary_owner__c` STRING,
  `product_code__c` STRING,
  `balance__c` NUMERIC,
  `open_date__c` DATE,
  `status__c` STRING,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.lead` (
  `id` STRING NOT NULL,
  `first_name` STRING,
  `last_name` STRING,
  `email` STRING,
  `phone` STRING,
  `status` STRING,
  `lead_source` STRING,
  `converted_contact_id` STRING,
  `is_converted` BOOL,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.opportunity` (
  `id` STRING NOT NULL,
  `account_id` STRING,
  `primary_contact__c` STRING,
  `name` STRING,
  `stage_name` STRING,
  `amount` NUMERIC,
  `close_date` DATE,
  `product_code__c` STRING,
  `lead_source` STRING,
  `campaign_id` STRING,
  `is_won` BOOL,
  `probability` NUMERIC,
  `owner_id` STRING,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.record_type` (
  `id` STRING NOT NULL,
  `name` STRING,
  `developer_name` STRING,
  `sobject_type` STRING,
  `is_active` BOOL,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.task` (
  `id` STRING NOT NULL,
  `who_id` STRING,
  `what_id` STRING,
  `subject` STRING,
  `type` STRING,
  `status` STRING,
  `activity_date` DATE,
  `call_duration_in_seconds` INT64,
  `call_disposition` STRING,
  `owner_id` STRING,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
)
PARTITION BY activity_date;

CREATE TABLE IF NOT EXISTS `fennmoor-raw.salesforce.user` (
  `id` STRING NOT NULL,
  `name` STRING,
  `email` STRING,
  `username` STRING,
  `profile_id` STRING,
  `user_role_id` STRING,
  `is_active` BOOL,
  `employee_number` STRING,
  `department` STRING,
  `division` STRING,
  `is_deleted` BOOL,
  `created_date` TIMESTAMP,
  `created_by_id` STRING,
  `last_modified_date` TIMESTAMP,
  `last_modified_by_id` STRING,
  `system_modstamp` TIMESTAMP,
  `_fivetran_synced` TIMESTAMP,
  `_fivetran_deleted` BOOL
);
