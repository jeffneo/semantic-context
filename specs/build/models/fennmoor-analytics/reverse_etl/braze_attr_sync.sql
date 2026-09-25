SELECT
  c.cif_number AS external_id,
  c.segment,
  c.is_digitally_enrolled,
  c.open_card_accounts,
  n.offer_product_code AS next_best_offer
FROM `fennmoor-dw.dw_customer.customer_360` c
LEFT JOIN `fennmoor-dw.ml_scores.next_best_offer` n ON n.customer_key = c.customer_key AND n.rank = 1 AND n.score_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
