SELECT
  cdr.CALL_ID AS legacy_call_id,
  TIMESTAMP(cdr.CALL_START_DTTM, 'America/Chicago') AS conversation_start,
  DATE(cdr.CALL_START_DTTM) AS conversation_date,
  cdr.SITE_CD AS site_id,
  cdr.CIF_NO AS cif_number,
  cdr.AGENT_LOGIN_ID AS agent_login_id,
  cdr.TALK_SEC AS talk_sec,
  cdr.HOLD_SEC AS hold_sec,
  cdr.ACW_SEC AS acw_sec,
  cdr.DISPOSITION_CD AS disposition_code,
  cdr.ABANDON_FLG = 'Y' AS is_abandoned,
  cdr.TRANSFER_FLG = 'Y' AS was_transferred
FROM `fennmoor-raw.contact_center_legacy.cdr_*` cdr
