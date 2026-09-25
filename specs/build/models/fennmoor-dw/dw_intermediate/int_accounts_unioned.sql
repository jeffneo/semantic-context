WITH dep AS (
SELECT CONCAT('DEP-', CAST(a.account_id AS STRING)) AS account_natural_key,
       'DEPOSIT' AS account_family, a.account_id AS core_account_id,
       CAST(NULL AS INT64) AS card_account_id, CAST(NULL AS STRING) AS loan_number,
       h.cif_number AS primary_cif_number, a.product_code, a.branch_id,
       a.open_date, a.close_date, a.close_reason_code AS close_reason,
       a.account_status_code AS status_code, a.open_channel_code AS open_channel
FROM `fennmoor-dw.dw_staging.stg_core__account` a
LEFT JOIN `fennmoor-dw.dw_intermediate.int_account_holders` h
  ON h.account_id = a.account_id AND h.is_primary_holder
),
crd AS (
SELECT CONCAT('CRD-', CAST(ca.account_id AS STRING)), 'CARD', CAST(NULL AS INT64),
       ca.account_id, CAST(NULL AS STRING), ca.bank_customer_ref, ca.product_code,
       CAST(NULL AS INT64), ca.open_date, ca.close_date, ca.close_reason, ca.status,
       CAST(NULL AS STRING)
FROM `fennmoor-dw.dw_staging.stg_cards__card_account` ca
),
lon AS (
SELECT CONCAT('LN-', l.loan_number), 'LOAN', CAST(NULL AS INT64), CAST(NULL AS INT64),
       l.loan_number, l.borrower_cif, l.product_code, l.branch_number,
       l.origination_date, COALESCE(l.charge_off_date, IF(l.loan_status = 'PAIDOFF', l.maturity_date, NULL)),
       IF(l.loan_status = 'CHARGEDOFF', 'CHARGE_OFF', NULL), l.loan_status, CAST(NULL AS STRING)
FROM `fennmoor-dw.dw_staging.stg_los__loan` l
),
unioned AS (
SELECT * FROM dep UNION ALL SELECT * FROM crd UNION ALL SELECT * FROM lon
)
SELECT
  u.account_natural_key,
  u.account_family,
  u.core_account_id,
  u.card_account_id,
  u.loan_number,
  u.primary_cif_number,
  u.product_code,
  u.branch_id,
  u.open_date,
  u.close_date,
  u.close_reason,
  u.status_code,
  u.open_channel
FROM unioned u
