SELECT
  src.id AS financial_account_id,
  src.name,
  RIGHT(src.account_number__c, 4) AS account_number_last4,
  src.core_account_id__c AS core_account_id,
  src.primary_owner__c AS primary_owner,
  src.product_code__c AS product_code,
  src.balance__c AS balance,
  src.open_date__c AS open_date,
  src.status__c AS status,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.financial_account__c` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted
