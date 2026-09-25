SELECT
  src.site_id,
  src.site_name,
  src.city,
  src.state,
  src.country,
  src.operator,
  src.is_outsourced,
  src.cost_center_id,
  src.seat_count,
  src.go_live_date,
  src.genesys_queue_prefix,
  src._uploaded_at AS _loaded_at
FROM `fennmoor-raw.reference_data.contact_center_site` AS src
