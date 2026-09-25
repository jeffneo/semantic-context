SELECT
  src.id AS account_id,
  src.name,
  src.type,
  src.record_type_id,
  src.owner_id,
  src.primary_branch__c AS primary_branch,
  src.household_segment__c AS household_segment,
  src.total_relationship_balance__c AS total_relationship_balance,
  src.billing_state,
  src.billing_postal_code,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.account` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted
