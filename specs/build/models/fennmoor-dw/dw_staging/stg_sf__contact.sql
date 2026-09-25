SELECT
  src.id AS contact_id,
  src.account_id,
  src.cif_number__c AS cif_number,
  src.first_name,
  src.last_name,
  src.email,
  src.phone,
  src.mobile_phone,
  src.birthdate,
  src.mailing_street,
  src.mailing_city,
  src.mailing_state,
  src.mailing_postal_code,
  src.do_not_call,
  src.has_opted_out_of_email,
  src.preferred_channel__c AS preferred_channel,
  src.owner_id,
  src._fivetran_synced AS _loaded_at
FROM `fennmoor-raw.salesforce.contact` AS src
WHERE NOT src.is_deleted AND NOT src._fivetran_deleted
