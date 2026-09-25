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
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted
