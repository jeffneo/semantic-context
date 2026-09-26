-- Q06: where SSNs are stored, raw or hashed. The catalog answers where; this counts the values each holds.
-- Raw: CUSTOMER (restricted source), party (restricted source), and three copies outside restricted
-- datasets: CUST_MSTR, its backup, and the KYC sandbox extract (F08).
SELECT 'core_banking_cdc.CUSTOMER.TAX_ID' AS column_, 'raw' AS form, COUNTIF(TAX_ID IS NOT NULL) AS values_
FROM `fennmoor-raw.core_banking_cdc.CUSTOMER`
UNION ALL SELECT 'aml_kyc.party.tax_id', 'raw', COUNTIF(tax_id IS NOT NULL) FROM `fennmoor-raw.aml_kyc.party`
UNION ALL SELECT 'legacy_edw.CUST_MSTR.SSN_NBR', 'raw', COUNTIF(SSN_NBR IS NOT NULL) FROM `fennmoor-analytics.legacy_edw.CUST_MSTR`
UNION ALL SELECT 'legacy_edw.CUST_MSTR_BKP_20250211.SSN_NBR', 'raw', COUNTIF(SSN_NBR IS NOT NULL)
          FROM `fennmoor-analytics.legacy_edw.CUST_MSTR_BKP_20250211`
UNION ALL SELECT 'sbx_risk.kyc_review_extract.tax_id', 'raw', COUNTIF(tax_id IS NOT NULL) FROM `fennmoor-analytics.sbx_risk.kyc_review_extract`
UNION ALL SELECT 'dw_core.dim_customer.tax_id_hash', 'hashed', COUNTIF(tax_id_hash IS NOT NULL) FROM `fennmoor-dw.dw_core.dim_customer`
UNION ALL SELECT 'dw_compliance.dim_aml_party.tax_id_hash', 'hashed', COUNTIF(tax_id_hash IS NOT NULL) FROM `fennmoor-dw.dw_compliance.dim_aml_party`
UNION ALL SELECT 'credit_bureau.consumer_attributes_monthly.SSN_HASH', 'hashed', COUNTIF(SSN_HASH IS NOT NULL)
          FROM `fennmoor-raw.credit_bureau.consumer_attributes_monthly`
ORDER BY form DESC, column_
