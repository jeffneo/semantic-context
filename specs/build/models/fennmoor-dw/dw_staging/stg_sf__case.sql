SELECT
  src.id AS case_id,
  src.case_number,
  src.contact_id,
  src.account_id,
  src.origin,
  src.type,
  src.reason,
  src.sub_reason__c AS sub_reason,
  src.status,
  src.priority,
  src.subject,
  src.description,
  src.closed_date,
  src.is_closed,
  src.is_escalated,
  src.owner_id,
  src.genesys_conversation_id__c AS genesys_conversation_id,
  RIGHT(src.related_account_number__c, 4) AS related_account_number_last4,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.case` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted
