SELECT
  s.*
FROM `fennmoor-dw.dw_marketing.fct_campaign_sends` AS s
WHERE s.sent_date < '2025-07-01'
