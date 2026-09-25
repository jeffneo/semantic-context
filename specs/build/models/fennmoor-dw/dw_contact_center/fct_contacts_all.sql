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
FROM u
