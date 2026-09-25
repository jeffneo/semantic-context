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
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted
