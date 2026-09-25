SELECT
  s.survey_id,
  s.conversation_id,
  c.conversation_date,
  c.site_id,
  s.agent_user_id,
  c.customer_key,
  s.csat_score,
  s.nps_score,
  s.nps_score >= 9 AS is_promoter,
  s.nps_score <= 6 AS is_detractor
FROM `fennmoor-dw.dw_staging.stg_genesys__survey_response` s
LEFT JOIN `fennmoor-dw.dw_contact_center.fct_calls` c ON c.conversation_id = s.conversation_id
