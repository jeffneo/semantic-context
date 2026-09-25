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
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted
