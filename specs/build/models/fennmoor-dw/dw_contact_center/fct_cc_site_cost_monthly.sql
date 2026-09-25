WITH gl AS (
SELECT DATE_TRUNC(j.accounting_date, MONTH) AS month_start, j.cost_center_id,
       SUM(j.entered_dr) - SUM(j.entered_cr) AS total_expense,
       SUM(IF(j.source = 'PAYROLL', j.entered_dr - j.entered_cr, 0)) AS payroll_expense,
       SUM(IF(j.source = 'AP', j.entered_dr - j.entered_cr, 0)) AS vendor_expense
FROM `fennmoor-dw.dw_staging.stg_gl__journal_line` j
JOIN `fennmoor-dw.dw_staging.stg_gl__gl_account` ga ON ga.gl_account_code = j.gl_account_code
WHERE ga.account_type = 'EXPENSE'
GROUP BY 1, 2
)
SELECT
  s.site_id,
  gl.month_start,
  s.cost_center_id,
  gl.total_expense,
  gl.payroll_expense,
  gl.vendor_expense,
  gl.total_expense - gl.payroll_expense - gl.vendor_expense AS other_expense
FROM `fennmoor-dw.dw_staging.stg_ref__contact_center_site` s
JOIN gl ON gl.cost_center_id = s.cost_center_id
