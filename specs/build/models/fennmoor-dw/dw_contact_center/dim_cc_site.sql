SELECT
  s.site_id,
  s.site_name,
  s.city,
  s.state,
  s.operator,
  s.is_outsourced,
  s.cost_center_id,
  cc.cost_center_name,
  s.seat_count,
  s.go_live_date,
  s.genesys_queue_prefix AS queue_prefix
FROM `fennmoor-dw.dw_staging.stg_ref__contact_center_site` s
LEFT JOIN `fennmoor-dw.dw_staging.stg_gl__cost_center` cc ON cc.cost_center_id = s.cost_center_id
