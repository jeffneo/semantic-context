-- compare: cif_number
-- Q12, the literal reading: the affluent segment only. The reference also includes private-banking
-- customers, as the business's own April extract did (sbx_marketing.email_list_affluent_apr26).
SELECT c.cif_number, c.full_name, c.primary_email, c.segment
FROM `fennmoor-dw.dw_customer.customer_360` c
JOIN `fennmoor-dw.dw_core.dim_customer` d ON d.customer_key = c.customer_key
WHERE c.segment = 'affluent' AND d.email_opt_in AND c.primary_email IS NOT NULL
ORDER BY c.cif_number
