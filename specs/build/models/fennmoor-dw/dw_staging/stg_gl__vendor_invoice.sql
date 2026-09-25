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
WHERE NOT src._fivetran_deleted
