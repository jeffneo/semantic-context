SELECT
  s.session_key,
  s.session_date,
  s.session_start,
  s.user_pseudo_id,
  s.ga4_user_id,
  u.olb_user_id,
  c.customer_key,
  s.ga4_user_id IS NOT NULL AS is_logged_in,
  s.page_views,
  s.engaged_sec,
  s.landing_page,
  s.traffic_medium,
  s.campaign_name,
  s.device_category,
  s.started_application,
  s.submitted_application,
  s.visited_help
FROM `fennmoor-dw.dw_intermediate.int_digital_sessions` s
LEFT JOIN `fennmoor-dw.dw_staging.stg_olb__online_user` u ON u.ga4_user_id = s.ga4_user_id
LEFT JOIN `fennmoor-dw.dw_core.dim_customer` c ON c.cif_number = u.cif_number
