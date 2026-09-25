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
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted
