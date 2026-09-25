SELECT
  n.customer_key,
  n.offer_product_code,
  n.propensity
FROM `fennmoor-dw.ml_scores.next_best_offer` n
WHERE n.rank = 1 AND STARTS_WITH(n.offer_product_code, 'CC-')
