SELECT
  q.queue_id,
  q.name AS queue_name,
  s.site_id,
  REGEXP_EXTRACT(q.name, r'^[A-Z]+_(.*)$') AS line_of_business,
  q.division_id
FROM `fennmoor-dw.dw_staging.stg_genesys__queue` q
LEFT JOIN `fennmoor-dw.dw_staging.stg_ref__contact_center_site` s ON STARTS_WITH(q.name, s.genesys_queue_prefix)
