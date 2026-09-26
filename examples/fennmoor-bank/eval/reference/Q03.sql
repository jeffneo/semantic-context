-- Q03: landing pages of customers' web sessions in the three days up to a call. Only logged-in sessions
-- resolve to a customer (GA4 user_id -> online_user.ga4_user_id -> CIF); logged_in_share says how many.
WITH calls AS (
  SELECT DISTINCT customer_key, conversation_date
  FROM `fennmoor-dw.dw_contact_center.fct_calls`
  WHERE customer_key IS NOT NULL
),
sessions AS (
  SELECT customer_key, session_date, landing_page,
         COUNTIF(is_logged_in) OVER () / COUNT(*) OVER () AS logged_in_share
  FROM `fennmoor-dw.dw_digital.fct_web_sessions`
)
SELECT s.landing_page, COUNT(*) AS sessions_before_a_call, ROUND(ANY_VALUE(s.logged_in_share), 3) AS logged_in_share
FROM sessions s
JOIN calls c ON c.customer_key = s.customer_key
 AND s.session_date BETWEEN DATE_SUB(c.conversation_date, INTERVAL 3 DAY) AND c.conversation_date
GROUP BY s.landing_page
ORDER BY sessions_before_a_call DESC
