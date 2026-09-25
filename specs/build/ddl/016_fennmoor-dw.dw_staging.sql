CREATE SCHEMA IF NOT EXISTS `fennmoor-dw.dw_staging` OPTIONS (location = 'US');

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_amp__events` AS
SELECT
  src._insert_id,
  src.amplitude_id,
  src.user_id,
  src.device_id,
  src.event_type,
  src.event_time,
  src.client_event_time,
  src.server_upload_time,
  src.session_id,
  src.event_properties,
  src.user_properties,
  src.os_name,
  src.os_version,
  src.device_model,
  src.platform,
  src.version_name,
  src.country,
  src.region,
  src.city,
  src.ip_address,
  src.language,
  DATE(src.event_time, 'America/Chicago') AS event_date,
  JSON_VALUE(src.event_properties, '$.screen_name') AS screen_name,
  JSON_VALUE(src.event_properties, '$.product_code') AS product_code,
  JSON_VALUE(src.user_properties, '$.app_build') AS app_build
FROM `fennmoor-raw.amplitude_mobile.EVENTS_318842` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_amp__merge_ids` AS
SELECT
  src.amplitude_id,
  src.merged_amplitude_id,
  src.merge_server_time,
  src.merge_event_time
FROM `fennmoor-raw.amplitude_mobile.MERGE_IDS_318842` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_braze__campaign` AS
SELECT
  src.id AS campaign_id,
  src.name,
  src.created_at,
  src.channels,
  src.tags,
  src.archived,
  src.first_sent,
  src.last_sent,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.campaign` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_braze__canvas` AS
SELECT
  src.id AS canvas_id,
  src.name,
  src.created_at,
  src.tags,
  src.archived,
  src.enabled,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.canvas` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_braze__conversion` AS
SELECT
  src.id AS conversion_id,
  src.external_user_id,
  src.campaign_id,
  src.canvas_id,
  src.conversion_behavior,
  src.event_time,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.conversion` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_braze__email_event` AS
SELECT
  src.id AS email_event_id,
  src.event_type,
  src.external_user_id,
  src.campaign_id,
  src.canvas_id,
  src.dispatch_id,
  src.email_address,
  src.url,
  src.event_time,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.email_event` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_braze__message_send` AS
SELECT
  src.id AS message_send_id,
  src.user_id,
  src.external_user_id,
  src.campaign_id,
  src.canvas_id,
  src.canvas_step_id,
  src.channel,
  src.sent_at,
  src.message_variation_id,
  src.dispatch_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.message_send` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_braze__push_event` AS
SELECT
  src.id AS push_event_id,
  src.event_type,
  src.external_user_id,
  src.campaign_id,
  src.canvas_id,
  src.platform,
  src.event_time,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.push_event` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_braze__user_profile` AS
SELECT
  src.external_id,
  src.braze_id,
  src.email,
  src.phone,
  src.first_name,
  src.email_subscribe,
  src.push_subscribe,
  src.custom_attributes,
  src.updated_at,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.braze.user_profile` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_bureau__consumer_attributes_monthly` AS
SELECT
  src.ARCHIVE_DT AS archive_date,
  src.CIF AS cif_number,
  src.SSN_HASH AS ssn_hash,
  src.FICO_08 AS fico_08,
  src.VANTAGE_4 AS vantage_4,
  src.TOT_REV_BAL AS total_revolving_balance,
  src.TOT_REV_LMT AS total_revolving_limit,
  src.UTIL_PCT AS utilization_pct,
  src.NUM_TRD_OPEN AS num_trades_open,
  src.NUM_INQ_6M AS num_inquiries_6m,
  src.NUM_DLQ_30_24M AS num_delinquent_30_24m,
  src.BK_FLG = 'Y' AS is_bankruptcy,
  src.MOS_SINCE_DLQ AS months_since_delinquent,
  src.EST_INCOME AS estimated_income,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.credit_bureau.consumer_attributes_monthly` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__authorization` AS
SELECT
  src.auth_id,
  src.card_token,
  src.account_id,
  src.auth_ts,
  CAST(src.amount_cents AS NUMERIC) / 100 AS amount,
  src.currency_code,
  src.merchant_id,
  src.mcc,
  src.pos_entry_mode,
  src.channel,
  src.response_code,
  src.decline_reason,
  src.vendor_fraud_score,
  src.avs_result,
  src.cvv_result,
  src.is_recurring,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.authorization` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__card` AS
SELECT
  src.card_token,
  src.account_id,
  src.card_role,
  src.pan_last4,
  src.expiry_yyyymm,
  src.issue_date,
  src.activation_date,
  src.status,
  src.replacement_reason,
  src.embossed_name,
  src.is_virtual,
  src.digital_wallet,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.card` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__card_account` AS
SELECT
  src.account_id,
  src.bank_customer_ref,
  src.product_code,
  CAST(src.credit_limit_cents AS NUMERIC) / 100 AS credit_limit,
  CAST(src.cash_limit_cents AS NUMERIC) / 100 AS cash_limit,
  CAST(src.current_balance_cents AS NUMERIC) / 100 AS current_balance,
  CAST(src.statement_balance_cents AS NUMERIC) / 100 AS statement_balance,
  CAST(src.min_payment_due_cents AS NUMERIC) / 100 AS min_payment_due,
  CAST(src.apr_purchase_bps AS NUMERIC) / 100 AS apr_purchase_pct,
  CAST(src.apr_cash_bps AS NUMERIC) / 100 AS apr_cash_pct,
  src.open_date,
  src.close_date,
  src.status,
  src.close_reason,
  src.cycle_day,
  src.autopay_flag,
  src.delinquency_bucket,
  src.last_payment_date,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.card_account` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__card_status_change` AS
SELECT
  src.card_token,
  src.account_id,
  src.change_ts,
  src.old_status,
  src.new_status,
  src.reason,
  src.channel,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.card_status_change` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__dispute` AS
SELECT
  src.dispute_id,
  src.settlement_id,
  src.account_id,
  src.opened_date,
  src.reason_code,
  CAST(src.dispute_amount_cents AS NUMERIC) / 100 AS dispute_amount,
  src.status,
  src.resolution,
  src.resolved_date,
  src.chargeback_flag,
  CAST(src.provisional_credit_cents AS NUMERIC) / 100 AS provisional_credit,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.dispute` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__mcc_code` AS
SELECT
  src.mcc,
  src.description,
  src.category_group,
  src.irs_reportable,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.mcc_code` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__merchant` AS
SELECT
  src.merchant_id,
  src.merchant_name,
  src.dba_name,
  src.mcc,
  src.city,
  src.state,
  src.country,
  src.postal_code,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.merchant` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__rewards_ledger` AS
SELECT
  src.account_id,
  src.activity_date,
  src.points,
  src.activity_type,
  src.settlement_id,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.rewards_ledger` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__settlement` AS
SELECT
  src.settlement_id,
  src.auth_id,
  src.card_token,
  src.account_id,
  src.post_date,
  src.txn_date,
  CAST(src.amount_cents AS NUMERIC) / 100 AS amount,
  src.txn_type,
  src.merchant_id,
  src.mcc,
  src.merchant_name_raw,
  src.merchant_city,
  src.merchant_state,
  src.merchant_country,
  src.network,
  CAST(src.interchange_cents AS NUMERIC) / 100 AS interchange,
  src.reward_points,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.settlement` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_cards__statement` AS
SELECT
  src.account_id,
  src.statement_date,
  CAST(src.closing_balance_cents AS NUMERIC) / 100 AS closing_balance,
  CAST(src.min_due_cents AS NUMERIC) / 100 AS min_due,
  src.due_date,
  CAST(src.interest_charged_cents AS NUMERIC) / 100 AS interest_charged,
  CAST(src.fees_charged_cents AS NUMERIC) / 100 AS fees_charged,
  CAST(src.purchases_cents AS NUMERIC) / 100 AS purchases,
  CAST(src.payments_cents AS NUMERIC) / 100 AS payments,
  src._load_ts AS _loaded_at
FROM `fennmoor-raw.card_processor.statement` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__account` AS
SELECT
  src.ACCT_ID AS account_id,
  RIGHT(src.ACCT_NO, 4) AS account_number_last4,
  src.PROD_CD AS product_code,
  src.BRNCH_ID AS branch_id,
  src.ACCT_STAT_CD AS account_status_code,
  src.OPEN_DT AS open_date,
  src.CLS_DT AS close_date,
  src.CLS_RSN_CD AS close_reason_code,
  src.OPEN_CHNL_CD AS open_channel_code,
  src.CCY_CD AS currency_code,
  src.INT_RT AS interest_rate,
  src.OD_LMT_AMT AS overdraft_limit_amount,
  src.STMT_CYC_CD AS statement_cycle_code,
  src.ESCHEAT_FLG = 'Y' AS is_escheat,
  src.CRT_TS AS created_at,
  src.LST_UPD_TS AS last_updated_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.ACCOUNT` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__account_balance_daily` AS
SELECT
  src.ACCT_ID AS account_id,
  src.BAL_DT AS balance_date,
  src.LEDGER_BAL_AMT AS ledger_balance_amount,
  src.AVAIL_BAL_AMT AS available_balance_amount,
  src.COLL_BAL_AMT AS collected_balance_amount,
  src.AVG_MTD_BAL_AMT AS avg_mtd_balance_amount,
  src.ACCRD_INT_AMT AS accrued_interest_amount,
  src.HOLD_AMT AS hold_amount,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.ACCOUNT_BALANCE_DLY` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__account_customer_relationship` AS
SELECT
  src.ACCT_ID AS account_id,
  src.CIF_NO AS cif_number,
  src.REL_TYP_CD AS relationship_type_code,
  src.REL_EFF_DT AS relationship_effective_date,
  src.REL_END_DT AS relationship_end_date,
  src.LST_UPD_TS AS last_updated_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.ACCOUNT_CUSTOMER_REL` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__account_status_history` AS
SELECT
  src.ACCT_ID AS account_id,
  src.STAT_CD AS status_code,
  src.PREV_STAT_CD AS previous_status_code,
  src.CHG_TS AS changed_at,
  src.CHG_RSN_CD AS change_reason_code,
  src.CHG_USER_ID AS change_user_id,
  src.CHG_CHNL_CD AS change_channel_code,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.ACCOUNT_STATUS_HIST` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__branch` AS
SELECT
  src.BRNCH_ID AS branch_id,
  src.BRNCH_NM AS branch_name,
  src.BRNCH_TYP_CD AS branch_type_code,
  src.ADDR_LN_1 AS address_line_1,
  src.CITY_NM AS city_name,
  src.ST_CD AS state_code,
  src.ZIP_CD AS zip_code,
  src.RGN_CD AS region_code,
  src.MKT_CD AS market_code,
  src.MGR_EMP_ID AS manager_employee_id,
  src.CC_ID AS cost_center_id,
  src.OPEN_DT AS open_date,
  src.CLS_DT AS close_date,
  src.LAT AS latitude,
  src.LNG AS longitude,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.BRANCH` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__cd_maturity_schedule` AS
SELECT
  src.ACCT_ID AS account_id,
  src.MAT_DT AS maturity_date,
  src.TERM_MTHS AS term_months,
  src.RENEW_OPT_CD AS renewal_option_code,
  src.PRIN_AMT AS principal_amount,
  src.RT AS rate,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.CD_MATURITY_SCHED` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__customer` AS
SELECT
  src.CIF_NO AS cif_number,
  src.CUST_TYP_CD AS customer_type_code,
  src.FRST_NM AS first_name,
  src.MIDL_NM AS middle_name,
  src.LST_NM AS last_name,
  src.BUS_NM AS business_name,
  TO_HEX(SHA256(src.TAX_ID)) AS tax_id_hash,
  src.BIRTH_DT AS birth_date,
  src.CUST_SINCE_DT AS customer_since_date,
  src.CUST_STAT_CD AS customer_status_code,
  src.PREF_BRNCH_ID AS preferred_branch_id,
  src.PREF_LANG_CD AS preferred_language_code,
  src.EMP_FLG = 'Y' AS is_employee,
  src.SEG_CD AS segment_code,
  src.RISK_RTNG_CD AS risk_rating_code,
  src.DECEASED_DT AS deceased_date,
  src.CRT_TS AS created_at,
  src.LST_UPD_TS AS last_updated_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.CUSTOMER` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__customer_address` AS
SELECT
  src.CIF_NO AS cif_number,
  src.ADDR_SEQ_NO AS address_sequence_number,
  src.ADDR_TYP_CD AS address_type_code,
  src.ADDR_LN_1 AS address_line_1,
  src.ADDR_LN_2 AS address_line_2,
  src.CITY_NM AS city_name,
  src.ST_CD AS state_code,
  src.ZIP_CD AS zip_code,
  src.CNTRY_CD AS country_code,
  src.PRIM_FLG = 'Y' AS is_primary,
  src.EFF_DT AS effective_date,
  src.END_DT AS end_date,
  src.LST_UPD_TS AS last_updated_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.CUSTOMER_ADDRESS` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__customer_contact` AS
SELECT
  src.CIF_NO AS cif_number,
  src.CNTCT_SEQ_NO AS contact_sequence_number,
  src.CNTCT_TYP_CD AS contact_type_code,
  src.CNTCT_VAL AS contact_value,
  src.VRFD_FLG = 'Y' AS is_verified,
  src.PRIM_FLG = 'Y' AS is_primary,
  src.OPT_IN_FLG = 'Y' AS is_opted_in,
  src.LST_UPD_TS AS last_updated_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.CUSTOMER_CONTACT` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__deposit_transaction` AS
SELECT
  src.TXN_ID AS transaction_id,
  src.ACCT_ID AS account_id,
  src.POST_DT AS posted_date,
  src.EFF_DT AS effective_date,
  src.TXN_TYP_CD AS transaction_type_code,
  src.TXN_AMT AS transaction_amount,
  src.DR_CR_IND AS debit_credit_indicator,
  src.TXN_DESC AS transaction_description,
  src.CHNL_CD AS channel_code,
  src.BRNCH_ID AS branch_id,
  src.TELLER_ID AS teller_id,
  src.ATM_ID AS atm_id,
  src.ACH_TRACE_NO AS ach_trace_number,
  src.CHK_NO AS check_number,
  src.RUN_BAL_AMT AS running_balance_amount,
  src.REVERSAL_FLG = 'Y' AS is_reversal,
  src.CRT_TS AS created_at,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.DEPOSIT_TXN` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__fee_assessed` AS
SELECT
  src.FEE_ID AS fee_id,
  src.ACCT_ID AS account_id,
  src.FEE_TYP_CD AS fee_type_code,
  src.FEE_AMT AS fee_amount,
  src.ASSESS_DT AS assessed_date,
  src.WAIVED_FLG = 'Y' AS is_waived,
  src.WAIVE_RSN_CD AS waive_reason_code,
  src.WAIVED_BY_USER_ID AS waived_by_user_id,
  src.REVERSED_FLG = 'Y' AS is_reversed,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.FEE_ASSESSED` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__interest_accrual` AS
SELECT
  src.ACCT_ID AS account_id,
  src.ACCR_DT AS accrual_date,
  src.ACCR_AMT AS accrual_amount,
  src.RT AS rate,
  src.BAL_AMT AS balance_amount,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.INTEREST_ACCRUAL` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_core__product` AS
SELECT
  src.PROD_CD AS product_code,
  src.PROD_NM AS product_name,
  src.PROD_FMLY_CD AS product_family_code,
  src.PROD_TYP_CD AS product_type_code,
  src.MIN_BAL_AMT AS min_balance_amount,
  src.MTHLY_FEE_AMT AS monthly_fee_amount,
  src.INT_RT AS interest_rate,
  src.TERM_MTHS AS term_months,
  src.ACTV_FLG = 'Y' AS is_active,
  src.EFF_DT AS effective_date,
  src.END_DT AS end_date,
  TIMESTAMP_MILLIS(src.datastream_metadata.source_timestamp) AS _loaded_at
FROM `fennmoor-raw.core_banking_cdc.PRODUCT` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_fraud__alert` AS
SELECT
  src.alert_id,
  src.alert_ts,
  src.entity_type,
  src.entity_ref,
  src.cif_number,
  src.rule_id,
  src.model_score,
  src.alert_status,
  src.priority,
  src.channel,
  src.amount,
  src.disposition,
  src.dispositioned_at,
  src.analyst_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.alert` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_fraud__case_alert_link` AS
SELECT
  src.case_id,
  src.alert_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.case_alert_link` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_fraud__fraud_case` AS
SELECT
  src.case_id,
  src.opened_at,
  src.closed_at,
  src.case_type,
  src.status,
  src.cif_number,
  src.total_loss_amount,
  src.recovered_amount,
  src.confirmed_fraud,
  src.fraud_type,
  src.assigned_analyst,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.fraud_case` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_fraud__model_score_realtime` AS
SELECT
  src.score_id,
  src.scored_at,
  src.entity_type,
  src.entity_ref,
  src.model_name,
  src.model_version,
  src.score,
  src.reason_codes,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.model_score_realtime` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_fraud__rule` AS
SELECT
  src.rule_id,
  src.rule_version,
  src.rule_name,
  src.channel,
  src.active,
  src.threshold,
  src.created_at,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.fraud_platform.rule` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_ga4__events` AS
SELECT
  PARSE_DATE('%Y%m%d', src.event_date) AS event_date,
  TIMESTAMP_MICROS(src.event_timestamp) AS event_ts,
  src.event_name,
  src.user_id,
  src.user_pseudo_id,
  (SELECT ep.value.int_value FROM UNNEST(src.event_params) AS ep WHERE ep.key = 'ga_session_id') AS ga_session_id,
  (SELECT ep.value.int_value FROM UNNEST(src.event_params) AS ep WHERE ep.key = 'ga_session_number') AS ga_session_number,
  (SELECT ep.value.string_value FROM UNNEST(src.event_params) AS ep WHERE ep.key = 'page_location') AS page_location,
  (SELECT ep.value.string_value FROM UNNEST(src.event_params) AS ep WHERE ep.key = 'page_title') AS page_title,
  (SELECT ep.value.string_value FROM UNNEST(src.event_params) AS ep WHERE ep.key = 'page_referrer') AS page_referrer,
  (SELECT ep.value.int_value FROM UNNEST(src.event_params) AS ep WHERE ep.key = 'engagement_time_msec') AS engagement_time_msec,
  (SELECT ep.value.string_value FROM UNNEST(src.event_params) AS ep WHERE ep.key = 'application_step') AS application_step,
  (SELECT ep.value.string_value FROM UNNEST(src.event_params) AS ep WHERE ep.key = 'product_code') AS product_code,
  src.device.category AS device_category,
  src.device.operating_system AS operating_system,
  src.device.web_info.browser AS browser,
  src.geo.region AS geo_region,
  src.geo.city AS geo_city,
  src.traffic_source.source AS traffic_source,
  src.traffic_source.medium AS traffic_medium,
  src.collected_traffic_source.manual_campaign_name AS campaign_name,
  src.collected_traffic_source.gclid AS gclid
FROM `fennmoor-raw.analytics_312874659.events_*` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_genesys__conversation` AS
SELECT
  src.conversation_id,
  src.conversation_start,
  src.conversation_end,
  src.originating_direction,
  src.media_type,
  src.division_id,
  src.ani_hash,
  src.dnis,
  src.external_tag,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.conversation` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_genesys__evaluation` AS
SELECT
  src.evaluation_id,
  src.conversation_id,
  src.agent_id,
  src.evaluator_id,
  src.form_name,
  src.total_score,
  src.critical_score,
  src.released_date,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.evaluation` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_genesys__ivr_flow_outcome` AS
SELECT
  src.conversation_id,
  src.flow_id,
  src.flow_name,
  src.outcome_id,
  src.outcome_name,
  src.outcome_value,
  src.outcome_start,
  src.outcome_end,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.ivr_flow_outcome` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_genesys__participant` AS
SELECT
  src.participant_id,
  src.conversation_id,
  src.purpose,
  src.user_id,
  src.queue_id,
  src.participant_name,
  src.start_time,
  src.end_time,
  src.attributes,
  JSON_VALUE(src.attributes, '$.cif') AS cif_number,
  JSON_VALUE(src.attributes, '$.ivr_auth') AS ivr_auth_result,
  JSON_VALUE(src.attributes, '$.intent') AS intent,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.participant` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_genesys__queue` AS
SELECT
  src.id AS queue_id,
  src.name,
  src.division_id,
  src.description,
  src.acw_timeout_ms,
  src.skill_evaluation_method,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.queue` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_genesys__segment` AS
SELECT
  src.segment_id,
  src.conversation_id,
  src.participant_id,
  src.segment_type,
  src.segment_start,
  src.segment_end,
  src.queue_id,
  src.wrap_up_code,
  src.wrap_up_note,
  src.disconnect_type,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.segment` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_genesys__survey_response` AS
SELECT
  src.survey_id,
  src.conversation_id,
  src.agent_user_id,
  src.sent_at,
  src.completed_at,
  src.csat_score,
  src.nps_score,
  src.verbatim,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.survey_response` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_genesys__user` AS
SELECT
  src.id AS user_id,
  src.name,
  src.email,
  src.department,
  src.title,
  src.manager_id,
  src.location_name,
  src.employee_id,
  src.state,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.user` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_genesys__wrapup_code` AS
SELECT
  src.id AS wrapup_code_id,
  src.name,
  src.description,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.genesys_cloud.wrapup_code` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_gl__cc_expense_summary` AS
SELECT
  src.PERIOD_NAME AS period_name,
  src.CC_ID AS cost_center_id,
  src.GL_ACCT AS gl_account_code,
  src.ACTUAL_AMT AS actual_amount,
  src.BUDGET_AMT AS budget_amount,
  src.VARIANCE_AMT AS variance_amount,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.gl_erp.CC_EXPENSE_SUMMARY` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_gl__cost_center` AS
SELECT
  src.cost_center_id,
  src.cost_center_name,
  src.department_code,
  src.owner_worker_id,
  src.region,
  src.is_active,
  src.effective_date,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.gl_erp.cost_center` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_gl__gl_account` AS
SELECT
  src.gl_account_code,
  src.account_name,
  src.account_type,
  src.parent_code,
  src.is_active,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.gl_erp.gl_account` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_gl__journal_line` AS
SELECT
  src.journal_id,
  src.line_number,
  src.period_name,
  src.accounting_date,
  src.gl_account_code,
  src.cost_center_id,
  src.entered_dr,
  src.entered_cr,
  src.line_description,
  src.source,
  src.currency_code,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.gl_erp.journal_line` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_gl__vendor_invoice` AS
SELECT
  src.invoice_id,
  src.vendor_name,
  src.cost_center_id,
  src.gl_account_code,
  src.invoice_date,
  src.amount,
  src.po_number,
  src.line_description,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.gl_erp.vendor_invoice` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_los__applicant` AS
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
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_los__application` AS
SELECT
  src.applicationId AS application_id,
  src.applicantCifNumber AS applicant_cif_number,
  src.coApplicantCifNumber AS co_applicant_cif_number,
  src.productCode AS product_code,
  src.channel,
  src.requestedAmount AS requested_amount,
  src.submittedAt AS submitted_at,
  src.decisionStatus AS decision_status,
  src.decisionAt AS decision_at,
  src.decisionReasonCodes AS decision_reason_codes,
  src.statedIncome AS stated_income,
  src.employmentStatus AS employment_status,
  src.housingStatus AS housing_status,
  src.branchNumber AS branch_number,
  src.loanOfficerId AS loan_officer_id,
  src.offerCode AS offer_code,
  src.creditScoreAtApp AS credit_score_at_app,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.application` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_los__collateral` AS
SELECT
  src.collateralId AS collateral_id,
  src.loanNumber AS loan_number,
  src.collateralType AS collateral_type,
  src.vin,
  src.appraisedValue AS appraised_value,
  src.appraisalDate AS appraisal_date,
  src.lienPosition AS lien_position,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.collateral` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_los__credit_pull` AS
SELECT
  src.pullId AS pull_id,
  src.applicationId AS application_id,
  src.bureau,
  src.pulledAt AS pulled_at,
  src.ficoScore AS fico_score,
  src.totalDebt AS total_debt,
  src.dtiRatio AS dti_ratio,
  src.inquiriesLast6m AS inquiries_last6m,
  src.tradelinesOpen AS tradelines_open,
  src.derogatoryCount AS derogatory_count,
  src.rawReportUri AS raw_report_uri,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.credit_pull` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_los__decision` AS
SELECT
  src.applicationId AS application_id,
  src.decisionSeq AS decision_seq,
  src.decidedBy AS decided_by,
  src.outcome,
  src.approvedAmount AS approved_amount,
  src.approvedApr AS approved_apr,
  src.conditions,
  src.decidedAt AS decided_at,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.decision` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_los__delinquency_snapshot` AS
SELECT
  src.snapshotDate AS snapshot_date,
  src.loanNumber AS loan_number,
  src.dpd,
  src.bucket,
  src.pastDueAmount AS past_due_amount,
  src.collectorId AS collector_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.delinquency_snapshot` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_los__loan` AS
SELECT
  src.loanNumber AS loan_number,
  src.applicationId AS application_id,
  src.borrowerCif AS borrower_cif,
  src.productCode AS product_code,
  src.originationDate AS origination_date,
  src.principalAmount AS principal_amount,
  src.currentPrincipal AS current_principal,
  src.interestRate AS interest_rate,
  src.termMonths AS term_months,
  src.maturityDate AS maturity_date,
  src.paymentAmount AS payment_amount,
  src.loanStatus AS loan_status,
  src.collateralType AS collateral_type,
  src.branchNumber AS branch_number,
  src.dpd,
  src.chargeOffDate AS charge_off_date,
  src.chargeOffAmount AS charge_off_amount,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.loan` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_los__loan_payment` AS
SELECT
  src.paymentId AS payment_id,
  src.loanNumber AS loan_number,
  src.paymentDate AS payment_date,
  src.amount,
  src.principalPortion AS principal_portion,
  src.interestPortion AS interest_portion,
  src.feePortion AS fee_portion,
  src.paymentMethod AS payment_method,
  src.isLate AS is_late,
  src.returnedFlag AS returned_flag,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.loan_origination.loan_payment` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_olb__alert_subscription` AS
SELECT
  src.olb_user_id,
  src.alert_type,
  src.channel,
  src.threshold_amount,
  src.enabled,
  src.updated_at,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.alert_subscription` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_olb__bill_pay` AS
SELECT
  src.payment_id,
  src.olb_user_id,
  src.from_account_id,
  src.payee_id,
  src.payee_name,
  src.amount,
  src.scheduled_date,
  src.sent_date,
  src.status,
  src.is_recurring,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.bill_pay` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_olb__device` AS
SELECT
  src.device_id,
  src.olb_user_id,
  src.platform,
  src.model,
  src.os_version,
  src.registered_at,
  src.last_seen_at,
  src.trusted,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.device` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_olb__login_event` AS
SELECT
  src.login_event_id,
  src.olb_user_id,
  src.session_id,
  src.event_ts,
  src.channel,
  src.result,
  src.ip_address,
  src.device_id,
  src.geo_country,
  src.user_agent,
  src.risk_score,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.login_event` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_olb__mobile_deposit` AS
SELECT
  src.deposit_id,
  src.olb_user_id,
  src.account_id,
  src.amount,
  src.check_number,
  src.submitted_at,
  src.status,
  src.hold_until_date,
  src.reject_reason,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.mobile_deposit` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_olb__online_user` AS
SELECT
  src.olb_user_id,
  src.cif_number,
  src.ga4_user_id,
  src.username,
  src.enrolled_at,
  src.enrollment_channel,
  src.status,
  src.mfa_method,
  src.last_login_at,
  src.is_business,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.online_user` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_olb__p2p_transfer` AS
SELECT
  src.transfer_id,
  src.olb_user_id,
  src.from_account_id,
  src.direction,
  src.counterparty_token,
  src.counterparty_name,
  src.amount,
  src.initiated_at,
  src.status,
  src.fraud_hold,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.digital_banking.p2p_transfer` AS src
WHERE NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_ref__contact_center_site` AS
SELECT
  src.site_id,
  src.site_name,
  src.city,
  src.state,
  src.country,
  src.operator,
  src.is_outsourced,
  src.cost_center_id,
  src.seat_count,
  src.go_live_date,
  src.genesys_queue_prefix,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.contact_center_site` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_ref__fx_rate_daily` AS
SELECT
  src.rate_date,
  src.from_ccy,
  src.to_ccy,
  src.rate,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.fx_rate_daily` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_ref__holiday_calendar` AS
SELECT
  src.holiday_date,
  src.holiday_name,
  src.is_bank_holiday,
  src.fed_closed,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.holiday_calendar` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_ref__product_hierarchy` AS
SELECT
  src.prod_cd,
  src.product_line,
  src.product_group,
  src.reporting_category,
  src.fee_bearing,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.product_hierarchy_FINAL_v3` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_ref__zip_region_map` AS
SELECT
  src.zip,
  src.state,
  src.msa_name,
  src.fennmoor_region,
  src.market_cd,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.zip_region_map` AS src;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__account` AS
SELECT
  src.id AS account_id,
  src.name,
  src.type,
  src.record_type_id,
  src.owner_id,
  src.primary_branch__c AS primary_branch,
  src.household_segment__c AS household_segment,
  src.total_relationship_balance__c AS total_relationship_balance,
  src.billing_state,
  src.billing_postal_code,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.account` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__campaign` AS
SELECT
  src.id AS campaign_id,
  src.name,
  src.type,
  src.status,
  src.start_date,
  src.end_date,
  src.braze_campaign_id__c AS braze_campaign_id,
  src.budgeted_cost,
  src.actual_cost,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.campaign` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__campaign_member` AS
SELECT
  src.id AS campaign_member_id,
  src.campaign_id,
  src.contact_id,
  src.lead_id,
  src.status,
  src.has_responded,
  src.first_responded_date,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.campaign_member` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__case` AS
SELECT
  src.id AS case_id,
  src.case_number,
  src.contact_id,
  src.account_id,
  src.origin,
  src.type,
  src.reason,
  src.sub_reason__c AS sub_reason,
  src.status,
  src.priority,
  src.subject,
  src.description,
  src.closed_date,
  src.is_closed,
  src.is_escalated,
  src.owner_id,
  src.genesys_conversation_id__c AS genesys_conversation_id,
  RIGHT(src.related_account_number__c, 4) AS related_account_number_last4,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.case` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__contact` AS
SELECT
  src.id AS contact_id,
  src.account_id,
  src.cif_number__c AS cif_number,
  src.first_name,
  src.last_name,
  src.email,
  src.phone,
  src.mobile_phone,
  src.birthdate,
  src.mailing_street,
  src.mailing_city,
  src.mailing_state,
  src.mailing_postal_code,
  src.do_not_call,
  src.has_opted_out_of_email,
  src.preferred_channel__c AS preferred_channel,
  src.owner_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.contact` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__financial_account` AS
SELECT
  src.id AS financial_account_id,
  src.name,
  RIGHT(src.account_number__c, 4) AS account_number_last4,
  src.core_account_id__c AS core_account_id,
  src.primary_owner__c AS primary_owner,
  src.product_code__c AS product_code,
  src.balance__c AS balance,
  src.open_date__c AS open_date,
  src.status__c AS status,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.financial_account__c` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__lead` AS
SELECT
  src.id AS lead_id,
  src.first_name,
  src.last_name,
  src.email,
  src.phone,
  src.status,
  src.lead_source,
  src.converted_contact_id,
  src.is_converted,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.lead` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__opportunity` AS
SELECT
  src.id AS opportunity_id,
  src.account_id,
  src.primary_contact__c AS primary_contact,
  src.name,
  src.stage_name,
  src.amount,
  src.close_date,
  src.product_code__c AS product_code,
  src.lead_source,
  src.campaign_id,
  src.is_won,
  src.probability,
  src.owner_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.opportunity` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__record_type` AS
SELECT
  src.id AS record_type_id,
  src.name,
  src.developer_name,
  src.sobject_type,
  src.is_active,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.record_type` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__task` AS
SELECT
  src.id AS task_id,
  src.who_id,
  src.what_id,
  src.subject,
  src.type,
  src.status,
  src.activity_date,
  src.call_duration_in_seconds,
  src.call_disposition,
  src.owner_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.task` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;

CREATE OR REPLACE VIEW `fennmoor-dw.dw_staging.stg_sf__user` AS
SELECT
  src.id AS user_id,
  src.name,
  src.email,
  src.username,
  src.profile_id,
  src.user_role_id,
  src.is_active,
  src.employee_number,
  src.department,
  src.division,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.user` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted;
