SELECT
  b.campaign_id,
  b.name AS campaign_name,
  b.channels,
  b.tags,
  b.first_sent,
  b.last_sent,
  b.archived AS is_archived,
  s.campaign_id AS sf_campaign_id,
  s.budgeted_cost,
  s.actual_cost
FROM `fennmoor-dw.dw_staging.stg_braze__campaign` b
LEFT JOIN `fennmoor-dw.dw_staging.stg_sf__campaign` s ON s.braze_campaign_id = b.campaign_id
