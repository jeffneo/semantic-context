-- Q08: campaigns credited with credit card applications (Braze conversions attributed to the last send).
SELECT c.campaign_name, COUNT(*) AS card_applications
FROM `fennmoor-dw.dw_marketing.fct_campaign_attribution` a
JOIN `fennmoor-dw.dw_marketing.dim_campaign` c ON c.campaign_id = a.campaign_id
WHERE a.conversion_behavior = 'card_application_submitted'
GROUP BY c.campaign_name
ORDER BY card_applications DESC
