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
WHERE NOT src._fivetran_deleted
