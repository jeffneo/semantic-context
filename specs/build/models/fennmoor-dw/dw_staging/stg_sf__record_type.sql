SELECT
  src.id AS record_type_id,
  src.name,
  src.developer_name,
  src.sobject_type,
  src.is_active,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.record_type` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted
