SELECT
  e.campaign_id,
  c.campaign_name,
  COUNTIF(e.delivered) AS delivered,
  COUNTIF(e.opened) AS opens,
  COUNTIF(e.clicked) AS clicks,
  COUNTIF(e.unsubscribed) AS unsubscribes,
  SAFE_DIVIDE(COUNTIF(e.opened), COUNTIF(e.delivered)) AS open_rate
FROM `fennmoor-dw.dw_marketing.fct_campaign_engagement` e
LEFT JOIN `fennmoor-dw.dw_marketing.dim_campaign` c ON c.campaign_id = e.campaign_id
GROUP BY ALL
