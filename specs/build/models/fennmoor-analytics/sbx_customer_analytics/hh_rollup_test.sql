SELECT
  c.sf_household_id,
  COUNT(*) AS members,
  ANY_VALUE(c.segment) AS segment
FROM `fennmoor-dw.dw_core.dim_customer` c
WHERE c.sf_household_id IS NOT NULL
GROUP BY ALL
