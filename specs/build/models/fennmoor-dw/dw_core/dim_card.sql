SELECT
  c.card_token,
  c.account_id AS card_account_id,
  ca.bank_customer_ref AS cif_number,
  c.card_role,
  c.pan_last4,
  c.issue_date,
  c.activation_date,
  c.status,
  c.is_virtual,
  c.digital_wallet,
  c.embossed_name
FROM `fennmoor-dw.dw_staging.stg_cards__card` c
JOIN `fennmoor-dw.dw_staging.stg_cards__card_account` ca ON ca.account_id = c.account_id
