-- Q12: contact details of affluent (and private) customers who opted in to email.
SELECT c.cif_number, c.full_name, c.primary_email, c.segment
FROM `fennmoor-dw.dw_customer.customer_360` c
JOIN `fennmoor-dw.dw_core.dim_customer` d ON d.customer_key = c.customer_key
WHERE c.segment IN ('affluent', 'private') AND d.email_opt_in AND c.primary_email IS NOT NULL
ORDER BY c.cif_number
