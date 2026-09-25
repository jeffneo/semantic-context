SELECT
  s.* EXCEPT (birth_date, tax_id_hash)
FROM `fennmoor-analytics.sbx_tom_okafor.tom_test` AS s
