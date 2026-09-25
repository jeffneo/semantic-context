SELECT
  a.month_start,
  a.site_id,
  s.site_name,
  s.is_outsourced,
  a.contacts,
  a.closure_calls,
  k.total_expense,
  SAFE_DIVIDE(k.total_expense, a.contacts) AS cost_per_contact
FROM `fennmoor-dw.dw_contact_center.agg_site_monthly` a
LEFT JOIN `fennmoor-dw.dw_contact_center.fct_cc_site_cost_monthly` k ON k.site_id = a.site_id AND k.month_start = a.month_start
LEFT JOIN `fennmoor-dw.dw_contact_center.dim_cc_site` s ON s.site_id = a.site_id
