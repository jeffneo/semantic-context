SELECT
  d AS date_day,
  DATE_TRUNC(d, MONTH) AS month_start,
  DATE_TRUNC(d, WEEK(MONDAY)) AS week_start,
  EXTRACT(QUARTER FROM d) AS quarter,
  EXTRACT(YEAR FROM d) AS year,
  FORMAT_DATE('%A', d) AS day_of_week,
  EXTRACT(DAYOFWEEK FROM d) IN (1, 7) AS is_weekend,
  COALESCE(h.is_bank_holiday, FALSE) AS is_bank_holiday,
  EXTRACT(DAYOFWEEK FROM d) NOT IN (1, 7) AND NOT COALESCE(h.is_bank_holiday, FALSE) AS is_business_day,
  UPPER(FORMAT_DATE('%b-%y', d)) AS fiscal_period_name
FROM UNNEST(GENERATE_DATE_ARRAY('2015-01-01', '2030-12-31')) AS d
LEFT JOIN `fennmoor-dw.dw_staging.stg_ref__holiday_calendar` h ON h.holiday_date = d
