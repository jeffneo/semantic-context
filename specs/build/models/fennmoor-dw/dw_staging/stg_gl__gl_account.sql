SELECT
  src.gl_account_code,
  src.account_name,
  src.account_type,
  src.parent_code,
  src.is_active,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.gl_erp.gl_account` AS src
WHERE NOT src._fivetran_deleted
