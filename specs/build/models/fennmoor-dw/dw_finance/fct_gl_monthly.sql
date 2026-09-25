SELECT
  DATE_TRUNC(j.accounting_date, MONTH) AS month_start,
  j.period_name,
  j.gl_account_code,
  g.account_type,
  j.cost_center_id,
  SUM(j.entered_dr - j.entered_cr) AS net_amount
FROM `fennmoor-dw.dw_staging.stg_gl__journal_line` j
JOIN `fennmoor-dw.dw_staging.stg_gl__gl_account` g ON g.gl_account_code = j.gl_account_code
GROUP BY ALL
